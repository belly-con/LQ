from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import FoodShop, FoodComment, ShopCollect, MerchantProfile, ShopApplication, ShopClickLog

# 注册餐饮商铺模型
@admin.register(FoodShop)
class FoodShopAdmin(admin.ModelAdmin):
    list_display = ["id", "shop_name", "avg_price", "shop_score", "county", "location", "business_circle", "food_type",
                    "business_hours", "phone"]
    search_fields = ["shop_name", "food_type"]  # 支持搜索商铺名/品类
    list_filter = ["food_type", "city", "business_circle", "michelin"]  # 支持按品类筛选
    ordering = ["-shop_score"]  # 默认按评分降序排列

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        # 加一行CSS，让列表表格支持横向滚动
        extra_context['extra_css'] = """
            <style>
                .results table { width: auto; min-width: 100%; }
                .results { overflow-x: auto; }
            </style>
        """
        return super().changelist_view(request, extra_context=extra_context)

# 注册评分明细模型
@admin.register(FoodComment)
class FoodScoreAdmin(admin.ModelAdmin):
    list_display = ["shop_id", "shop_name", "user_id", "total_score", "content", ]
    search_fields = ["shop_id__shop_id", "shop_name"]
    list_filter = ["taste_score"]

@admin.register(ShopCollect)
class ShopCollectAdmin(admin.ModelAdmin):
    # 列表展示字段：用户名、店铺名、店铺id、菜系、收藏时间
    list_display = ["id", "user", "user_username", "shop", "shop_name", "shop_food_type", "collect_time"]
    # 筛选条件：按用户筛选、按店铺筛选、按收藏时间筛选（重点！实现单个用户的所有收藏查看）
    list_filter = ["user", "shop", "collect_time"]
    # 搜索条件：支持搜索用户名、店铺名、店铺id，快速查找
    search_fields = ["user__username", "shop__shop_name", "shop__shop_id"]
    # 排序：按收藏时间倒序，最新收藏的在最前面
    ordering = ["-collect_time"]

    # 自定义展示字段：显示用户名
    def user_username(self, obj):
        return obj.user.username
    user_username.short_description = "用户名"

    # 自定义展示字段：显示店铺名称
    def shop_name(self, obj):
        return obj.shop.shop_name
    shop_name.short_description = "收藏店铺名称"

    # 自定义展示字段：显示店铺菜系
    def shop_food_type(self, obj):
        return obj.shop.food_type
    shop_food_type.short_description = "店铺菜系"


# ===== 商家相关模型 Admin =====
@admin.register(MerchantProfile)
class MerchantProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'business_name', 'contact_phone', 'is_verified', 'created_at']
    list_filter  = ['is_verified']
    search_fields = ['user__username', 'business_name']


@admin.register(ShopApplication)
class ShopApplicationAdmin(admin.ModelAdmin):
    list_display = ['shop_name', 'merchant', 'food_type', 'county', 'status', 'created_at', 'reviewed_at']
    list_filter  = ['status', 'food_type', 'county']
    search_fields = ['shop_name', 'merchant__username']
    readonly_fields = ['created_at', 'updated_at', 'reviewed_at']


@admin.register(ShopClickLog)
class ShopClickLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'shop', 'clicked_at']
    list_filter  = ['clicked_at']
    search_fields = ['user__username', 'shop__shop_name']