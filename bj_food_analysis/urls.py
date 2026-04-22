from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),  # Django自带的管理员后台【你的核心需求】
    path('user/', include('user_system.urls')),  # 用户功能路由
    path('', lambda request: redirect('/user/login/')),  # 根路径跳转登录页，解决404
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)