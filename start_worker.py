# user_system/management/commands/start_worker.py
from django.core.management.base import BaseCommand
from user_system.redis_queue import get_worker
import signal
import sys


class Command(BaseCommand):
    help = '启动情感分析工作进程'

    def handle(self, *args, **options):
        worker = get_worker()

        # 设置信号处理
        def signal_handler(sig, frame):
            self.stdout.write('收到停止信号，正在停止工作进程...')
            worker.stop()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        self.stdout.write('情感分析工作进程启动中...')

        try:
            worker.start()
        except KeyboardInterrupt:
            worker.stop()
            self.stdout.write('工作进程已停止')
        except Exception as e:
            self.stderr.write(f'工作进程异常: {e}')
            worker.stop()