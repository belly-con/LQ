import pymysql
pymysql.install_as_MySQLdb()

# Celery 在部分部署环境（如 Vercel）不是必需依赖，缺失时不应阻塞 Django 启动。
try:
    from .celery import app as celery_app
    __all__ = ('celery_app',)
except ImportError:
    __all__ = ()