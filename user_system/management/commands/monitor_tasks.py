# user_system/management/commands/monitor_tasks.py
from django.core.management.base import BaseCommand
from user_system.models import SentimentAnalysisTask
from user_system.redis_queue import RedisQueue
from datetime import datetime, timedelta
import time


class Command(BaseCommand):
    help = '监控情感分析任务'

    def add_arguments(self, parser):
        parser.add_argument(
            '--task-id',
            type=str,
            help='指定任务ID'
        )
        parser.add_argument(
            '--interval',
            type=int,
            default=5,
            help='刷新间隔(秒)'
        )
        parser.add_argument(
            '--watch',
            action='store_true',
            help='持续监控'
        )

    def handle(self, *args, **options):
        task_id = options['task_id']
        interval = options['interval']
        watch = options['watch']

        queue = RedisQueue()

        if task_id:
            # 监控特定任务
            self.monitor_single_task(task_id, queue, interval, watch)
        else:
            # 显示所有任务
            self.show_all_tasks(queue)

    def monitor_single_task(self, task_id, queue, interval, watch):
        """监控单个任务"""
        try:
            task = SentimentAnalysisTask.objects.get(task_id=task_id)
        except SentimentAnalysisTask.DoesNotExist:
            self.stderr.write(f"任务不存在: {task_id}")
            return

        print(f"监控任务: {task.task_name}")
        print("=" * 80)

        while True:
            try:
                # 从数据库获取最新状态
                task.refresh_from_db()

                # 从Redis获取进度
                progress = queue.get_progress(task_id)

                self.display_task_info(task, progress)

                if not watch or task.status in ['completed', 'failed', 'cancelled']:
                    break

                time.sleep(interval)

            except KeyboardInterrupt:
                print("\n监控已停止")
                break
            except Exception as e:
                self.stderr.write(f"监控出错: {e}")
                break

    def show_all_tasks(self, queue):
        """显示所有任务"""
        tasks = SentimentAnalysisTask.objects.all().order_by('-created_at')[:20]

        print("情感分析任务列表")
        print("=" * 120)
        print(f"{'ID':<10} {'名称':<30} {'类型':<10} {'状态':<10} {'进度':<8} {'创建时间':<20} {'完成时间':<20}")
        print("-" * 120)

        for task in tasks:
            progress = queue.get_progress(task.task_id)
            if progress:
                progress_display = f"{progress.get('progress', 0):.1f}%"
            else:
                progress_display = f"{task.progress:.1f}%"

            print(f"{task.task_id[:8]:<10} {task.task_name[:28]:<30} "
                  f"{task.get_task_type_display():<10} "
                  f"{task.get_status_display():<10} "
                  f"{progress_display:<8} "
                  f"{task.created_at.strftime('%Y-%m-%d %H:%M:%S'):<20} "
                  f"{task.completed_at.strftime('%Y-%m-%d %H:%M:%S') if task.completed_at else '-':<20}")

        print("=" * 120)
        print(f"共 {len(tasks)} 个任务")

    def display_task_info(self, task, progress):
        """显示任务信息"""
        import os
        os.system('cls' if os.name == 'nt' else 'clear')

        print(f"任务监控: {task.task_name}")
        print(f"任务ID: {task.task_id}")
        print(f"任务类型: {task.get_task_type_display()}")
        print(f"状态: {task.get_status_display()}")
        print(f"创建时间: {task.created_at.strftime('%Y-%m-%d %H:%M:%S')}")

        if task.started_at:
            print(f"开始时间: {task.started_at.strftime('%Y-%m-%d %H:%M:%S')}")

        if progress:
            print(f"\n实时进度:")
            print(f"  总评论数: {progress.get('total', 0)}")
            print(f"  已处理: {progress.get('processed', 0)}")
            print(f"  成功: {progress.get('success', 0)}")
            print(f"  失败: {progress.get('failed', 0)}")
            print(f"  进度: {progress.get('progress', 0):.1f}%")

            # 显示进度条
            progress_percent = progress.get('progress', 0)
            bar_length = 50
            filled_length = int(bar_length * progress_percent / 100)
            bar = '█' * filled_length + '░' * (bar_length - filled_length)
            print(f"  [{bar}] {progress_percent:.1f}%")

        if task.status == 'completed' and task.result_summary:
            print(f"\n任务结果:")
            result = task.result_summary
            print(f"  总评论数: {result.get('total', 0)}")
            print(f"  成功分析: {result.get('success', 0)}")
            print(f"  失败分析: {result.get('failed', 0)}")
            print(f"  成功率: {result.get('success_rate', 0):.1f}%")

            if task.processing_time:
                print(f"  处理时间: {task.processing_time:.1f}秒")
                print(f"  处理速度: {task.comments_per_second:.1f}条/秒")

        if task.status == 'failed' and task.error_message:
            print(f"\n错误信息: {task.error_message}")

        print(f"\n{'=' * 80}")
        print("按 Ctrl+C 停止监控")