# user_system/redis_queue.py
import redis
import json
import time
import threading
from django.conf import settings
from django.db import transaction
from .models import FoodComment, SentimentAnalysisTask
from .sentiment_core import EnhancedSentimentAnalyzer


class RedisQueue:
    """Redis队列处理器"""

    def __init__(self):
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True
        )
        self.analyzer = EnhancedSentimentAnalyzer()

        # 队列名称
        self.task_queue_key = 'sentiment:tasks'
        self.progress_key_prefix = 'sentiment:progress:'
        self.result_key_prefix = 'sentiment:result:'

    def create_task(self, task_data):
        """创建任务"""
        task_id = task_data.get('task_id')
        if not task_id:
            raise ValueError('任务ID不能为空')

        # 将任务放入队列
        self.redis_client.rpush(self.task_queue_key, json.dumps(task_data))

        # 初始化进度
        progress_key = f'{self.progress_key_prefix}{task_id}'
        self.redis_client.hset(progress_key, 'total', task_data.get('total', 0))
        self.redis_client.hset(progress_key, 'processed', 0)
        self.redis_client.hset(progress_key, 'success', 0)
        self.redis_client.hset(progress_key, 'failed', 0)

        return task_id

    def get_task(self):
        """获取任务"""
        task_json = self.redis_client.lpop(self.task_queue_key)
        if task_json:
            return json.loads(task_json)
        return None

    def update_progress(self, task_id, processed, success, failed):
        """更新进度"""
        progress_key = f'{self.progress_key_prefix}{task_id}'
        self.redis_client.hset(progress_key, 'processed', processed)
        self.redis_client.hset(progress_key, 'success', success)
        self.redis_client.hset(progress_key, 'failed', failed)

        # 计算进度百分比
        total = self.redis_client.hget(progress_key, 'total')
        if total and int(total) > 0:
            progress = int(processed) / int(total) * 100
            self.redis_client.hset(progress_key, 'progress', progress)

    def get_progress(self, task_id):
        """获取进度"""
        progress_key = f'{self.progress_key_prefix}{task_id}'
        progress = self.redis_client.hgetall(progress_key)

        if not progress:
            return None

        # 转换为适当类型
        result = {}
        for key, value in progress.items():
            if key == 'progress':
                result[key] = float(value)
            else:
                result[key] = int(value)

        return result

    def save_result(self, task_id, result):
        """保存结果"""
        result_key = f'{self.result_key_prefix}{task_id}'
        self.redis_client.set(result_key, json.dumps(result))

    def get_result(self, task_id):
        """获取结果"""
        result_key = f'{self.result_key_prefix}{task_id}'
        result_json = self.redis_client.get(result_key)
        if result_json:
            return json.loads(result_json)
        return None

    def cleanup_task(self, task_id):
        """清理任务数据"""
        # 删除进度和结果数据
        progress_key = f'{self.progress_key_prefix}{task_id}'
        result_key = f'{self.result_key_prefix}{task_id}'

        self.redis_client.delete(progress_key)
        self.redis_client.delete(result_key)


class SentimentWorker:
    """情感分析工作进程"""

    def __init__(self):
        self.queue = RedisQueue()
        self.analyzer = EnhancedSentimentAnalyzer()
        self.running = False
        self.batch_size = 100  # 每批处理数量

    def start(self):
        """启动工作进程"""
        self.running = True
        print("情感分析工作进程已启动")

        while self.running:
            try:
                # 获取任务
                task_data = self.queue.get_task()

                if task_data:
                    self.process_task(task_data)
                else:
                    # 没有任务，等待一段时间
                    time.sleep(5)

            except Exception as e:
                print(f"处理任务时出错: {e}")
                time.sleep(10)

    def stop(self):
        """停止工作进程"""
        self.running = False
        print("情感分析工作进程已停止")

    def process_task(self, task_data):
        """处理单个任务"""
        task_id = task_data['task_id']
        task_type = task_data.get('task_type', 'full')
        batch_size = task_data.get('batch_size', 500)

        print(f"开始处理任务: {task_id} ({task_type})")

        try:
            # 更新数据库任务状态
            task = SentimentAnalysisTask.objects.get(task_id=task_id)
            task.mark_started()

            # 根据任务类型获取评论
            if task_type == 'full':
                comments = FoodComment.objects.all()
            elif task_type == 'incremental':
                comments = FoodComment.objects.filter(sentiment__isnull=True)
            elif task_type == 'reanalyze':
                comments = FoodComment.objects.all()
            else:
                comments = FoodComment.objects.all()

            total = comments.count()
            processed = 0
            success = 0
            failed = 0

            # 分批次处理
            for i in range(0, total, batch_size):
                batch = comments[i:i + batch_size]

                batch_processed = 0
                batch_success = 0
                batch_failed = 0

                for comment in batch:
                    try:
                        # 分析情感
                        sentiment, score = self.analyzer.analyze(comment.content)

                        # 更新评论
                        comment.sentiment = sentiment
                        comment.sentiment_score = score
                        comment.save()

                        batch_success += 1

                    except Exception as e:
                        print(f"处理评论 {comment.id} 失败: {e}")
                        batch_failed += 1

                    batch_processed += 1

                # 更新进度
                processed += batch_processed
                success += batch_success
                failed += batch_failed

                # 更新队列进度
                self.queue.update_progress(task_id, processed, success, failed)

                # 更新数据库任务进度
                task.update_progress(processed, total)

                print(f"批次进度: {processed}/{total} ({processed / total * 100:.1f}%)")

                # 短暂暂停，避免CPU占用过高
                time.sleep(0.1)

            # 任务完成
            result_summary = {
                'total': total,
                'success': success,
                'failed': failed,
                'success_rate': success / total * 100 if total > 0 else 0
            }

            task.mark_completed(result_summary)

            # 保存结果到Redis
            self.queue.save_result(task_id, result_summary)

            print(f"任务完成: {task_id}")

        except Exception as e:
            print(f"任务失败: {e}")

            # 更新数据库任务状态
            try:
                task = SentimentAnalysisTask.objects.get(task_id=task_id)
                task.mark_failed(str(e))
            except:
                pass


# 单例工作进程
_worker_instance = None


def get_worker():
    """获取工作进程实例"""
    global _worker_instance
    if _worker_instance is None:
        _worker_instance = SentimentWorker()
    return _worker_instance