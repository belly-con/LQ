from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),  # 注册
    path('login/', views.user_login, name='login'),      # 登录
    path('user_center/', views.user_center, name='user_center'),  # 用户中心（整合首页/个人信息/修改密码）
    path('index/', views.index, name='index'),           # 兼容旧路由
    path('profile/', views.profile, name='profile'),     # 兼容旧路由
    path('change_pwd/', views.change_pwd, name='change_pwd'), # 兼容旧路由
    path('logout/', views.user_logout, name='logout'),   # 注销
    path('food_list/', views.food_list, name='food_list'),  # 商铺列表
    path('collect_shop/<str:shop_id>/', views.collect_shop, name='collect_shop'),
    path('cancel_collect/<str:shop_id>/', views.cancel_collect, name='cancel_collect'),# 收藏/取消收藏，传入店铺id
    path('my_collect/', views.my_collect, name='my_collect'),  # 我的收藏页面
    path('food_score/', views.food_score, name='food_score'),  # 评分分析
    path('food_type/', views.food_type, name='food_type'),  # 品类占比
    # food_chart 已删除（趋势分析）
    # 数据分析功能
    path('top10_popular/', views.top10_popular, name='top10_popular'),  # Top10店铺
    path('county_distribution/', views.county_distribution, name='county_distribution'),  # 区县分布
    path('price_analysis/', views.price_analysis, name='price_analysis'),  # 价格分析
    path('business_circle_analysis/', views.business_circle_analysis, name='business_circle_analysis'),  # 商圈分析
    # 数据可视化功能
    path('shop_heatmap/', views.shop_heatmap, name='shop_heatmap'),  # 热力图
    path('sentiment_dashboard/', views.sentiment_dashboard, name='sentiment_dashboard'),
    path('create_sentiment_task/', views.create_sentiment_task, name='create_sentiment_task'),
    path('task_status/<str:task_id>/', views.get_task_status, name='task_status'),
    path('list_tasks/', views.list_tasks, name='list_tasks'),
    path('analyze_single_comment/', views.analyze_single_comment, name='analyze_single_comment'),
    path('sentiment_statistics/', views.sentiment_statistics, name='sentiment_statistics'),
    path('sentiment_results/<str:task_id>/', views.sentiment_results, name='sentiment_results'),
    # 地图功能
    # urls.py
    path('shop_map/', views.shop_map, name='shop_map'),  # 地图页面
    path('shop_map_standalone/', views.shop_map_standalone, name='shop_map_standalone'),
    # 推荐系统
    path('shop_recommendation/', views.shop_recommendation, name='shop_recommendation'),  # 智能推荐
    # 店铺详情
    path('shop_detail/<str:shop_id>/', views.shop_detail, name='shop_detail'),  # 店铺详情页
    # 可视化大屏
    path('data_dashboard/', views.data_dashboard, name='data_dashboard'),  # 数据可视化大屏
    path('shop_map_simple/', views.shop_map_simple, name='simple_shop_map'),
    # AI 助手模块
    path('ai_assistant/', views.ai_assistant, name='ai_assistant'),
    path('ai_chat/', views.ai_chat, name='ai_chat'),
    path('ai_clear_history/', views.ai_clear_history, name='ai_clear_history'),
    path('ai_save_scene_pref/', views.ai_save_scene_pref, name='ai_save_scene_pref'),
    path('user_profile_edit/', views.user_profile_edit, name='user_profile_edit'),
    # 点击记录
    path('shop_click/<str:shop_id>/', views.shop_click, name='shop_click'),
    # 商家模块
    path('merchant_register/', views.merchant_register, name='merchant_register'),
    path('merchant_dashboard/', views.merchant_dashboard, name='merchant_dashboard'),
    path('merchant_apply_shop/', views.merchant_apply_shop, name='merchant_apply_shop'),
    path('merchant_application/<int:app_id>/', views.merchant_application_detail, name='merchant_application_detail'),
    # 管理员审核
    path('admin_review/', views.admin_review_list, name='admin_review_list'),
    path('admin_review/<int:app_id>/', views.admin_review_detail, name='admin_review_detail'),
    path('admin_merchant_review/', views.admin_merchant_review_list, name='admin_merchant_review_list'),
    path('admin_merchant_review/<int:merchant_id>/', views.admin_merchant_review_detail, name='admin_merchant_review_detail'),
]