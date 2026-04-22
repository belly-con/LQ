# user_system/management/commands/analyze_async.py
from django.core.management.base import BaseCommand
from user_system.models import SentimentAnalysisTask, FoodComment
from user_system.redis_queue import RedisQueue
import uuid
from django.db.models import Q
import json


class Command(BaseCommand):
    help = '创建异步情感分析任务'

    def add_arguments(self, parser):
        parser.add_argument(
            '--task-type',
            type=str,
            choices=['full', 'incremental', 'reanalyze'],
            default='full',
            help='任务类型：full(全部分析), incremental(增量分析), reanalyze(重新分析)'
        )
        parser.add_argument(
            '--task-name',
            type=str,
            help='任务名称'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=500,
            help='批处理大小'
        )
        parser.add_argument(
            '--use-enhanced',
            action='store_true',
            help='使用增强算法'
        )

    def handle(self, *args, **options):
        task_type = options['task_type']
        task_name = options['task_name']
        batch_size = options['batch_size']
        use_enhanced = options['use_enhanced']

        # 生成任务ID
        task_id = str(uuid.uuid4())

        if not task_name:
            task_name = f'情感分析任务-{task_type}-{task_id[:8]}'

        # 计算总评论数
        if task_type == 'incremental':
            total = FoodComment.objects.filter(
                Q(sentiment__isnull=True) | Q(sentiment='')
            ).count()
        else:
            total = FoodComment.objects.count()

        # 创建数据库任务记录
        task = SentimentAnalysisTask.objects.create(
            task_id=task_id,
            task_name=task_name,
            task_type=task_type,
            total_comments=total,
            use_enhanced_algorithm=use_enhanced,
            batch_size=batch_size
        )

        # 创建Redis任务
        queue = RedisQueue()
        task_data = {
            'task_id': task_id,
            'task_type': task_type,
            'batch_size': batch_size,
            'total': total,
            'use_enhanced': use_enhanced,
            'created_at': str(task.created_at)
        }

        queue.create_task(task_data)

        self.stdout.write(self.style.SUCCESS(
            f"✅ 任务创建成功！"
        ))
        self.stdout.write(f"任务ID: {task_id}")
        self.stdout.write(f"任务名称: {task_name}")
        self.stdout.write(f"任务类型: {task_type}")
        self.stdout.write(f"总评论数: {total}")
        self.stdout.write(f"批处理大小: {batch_size}")
        self.stdout.write(f"使用增强算法: {'是' if use_enhanced else '否'}")
        self.stdout.write("\n任务已加入队列，等待工作进程处理...")