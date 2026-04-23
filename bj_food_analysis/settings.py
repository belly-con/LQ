import os
from dotenv import load_dotenv
load_dotenv()
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SECRET_KEY = os.environ.get('SECRET_KEY')
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
ALLOWED_HOSTS = [
    host.strip() for host in os.environ.get('ALLOWED_HOSTS', '').split(',') if host.strip()
]
CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get('CSRF_TRUSTED_ORIGINS', '').split(',')
    if origin.strip()
]

# 在 Vercel 部署时，自动信任当前分配域名，避免登录/CSRF 失败
vercel_url = os.environ.get('VERCEL_URL', '').strip()
if vercel_url:
    ALLOWED_HOSTS.append(vercel_url)
    CSRF_TRUSTED_ORIGINS.append(f'https://{vercel_url}')

# 无论是否配置 ALLOWED_HOSTS，都确保包含常用部署域名
for default_host in ['.vercel.app', 'localhost', '127.0.0.1']:
    if default_host not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(default_host)
# 静态文件URL
STATIC_URL = '/static/'

# 静态文件目录
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_DB = 0

# Celery配置
CELERY_BROKER_URL = f'redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}'
CELERY_RESULT_BACKEND = f'redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}'
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Asia/Shanghai'
# 必须保留的内置app，包含admin和用户认证
INSTALLED_APPS = [
    'simpleui',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'user_system',

]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'bj_food_analysis.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'bj_food_analysis.wsgi.application'

# ========== 修改这里：你的MySQL密码 ==========
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get('MYSQL_DATABASE', 'bj_food_db'),
        'USER': os.environ.get('MYSQL_USER','default_user'),
        'PASSWORD': os.environ.get('MYSQL_PASSWORD'),  # 改成你自己的MySQL密码！！！
        'HOST': os.environ.get('MYSQL_HOST', '127.0.0.1'),
        'PORT': os.environ.get('MYSQL_PORT', '3306'),
        'OPTIONS': {'charset': 'utf8mb4'}
    }
}

PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
]

# 登录相关配置
LOGIN_URL = '/user/login/'
LOGIN_REDIRECT_URL = '/user/index/'
LOGOUT_REDIRECT_URL = '/user/login/'
SESSION_COOKIE_AGE = 3600

# 中文+时区
LANGUAGE_CODE = 'zh-hans'
TIME_ZONE = 'Asia/Shanghai'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

if not DEBUG:
    # Vercel/Railway 这类反向代理场景需要显式识别 https
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    CSRF_COOKIE_SAMESITE = 'Lax'
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True

# 媒体文件（商家资质图片上传）
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# 百度地图API配置
# 请访问 https://lbsyun.baidu.com/ 申请API Key
# 将申请的AK替换下面的YOUR_BAIDU_MAP_AK
BAIDU_MAP_AK = os.environ.get('BAIDU_MAP_AK', '')


# ========== DeepSeek AI 配置 ==========
# 请前往 https://platform.deepseek.com/ 申请 API Key
# 将申请的 Key 填入下方
DEEPSEEK_BASE_URL = 'https://api.deepseek.com'
DEEPSEEK_MODEL = 'deepseek-chat'  # 可选: deepseek-reasoner (R1)


