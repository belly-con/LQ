from django.utils import timezone

from django.db import models
from django.db import models
from django.contrib.auth.models import User
# ===================== 商铺表：完全匹配你的字段 =====================
class FoodShop(models.Model):
    """商铺数据表 - 对应你的商铺数据字段"""
    shop_id = models.CharField(max_length=20, verbose_name="店铺id", unique=True)  # 你的店铺id
    shop_name = models.CharField(max_length=100, verbose_name="店铺名称")  # 你的店铺名称
    longitude = models.FloatField(verbose_name="经度")  # 经度
    latitude = models.FloatField(verbose_name="纬度")  # 纬度
    avg_price = models.FloatField(verbose_name="人均消费")  # 人均消费_处理

    shop_score = models.DecimalField(
        verbose_name="综合评分",
        max_digits=4,  # 总位数，比如 99.99 足够用
        decimal_places=1,  # 小数位数，固定为2，完美匹配需求！
        null=False  # 保留你的必填约束
    )
    comment_count = models.IntegerField(verbose_name="评论数量")  # 评论数量_处理
    distance_desc = models.CharField(max_length=50, verbose_name="距离描述", null=True)  # 距离描述
    michelin = models.CharField(max_length=10, verbose_name="米其林推荐")  # 米其林推荐指数
    business_circle = models.CharField(max_length=50, verbose_name="归属商圈", null=True)  # 归属商圈
    food_type = models.CharField(max_length=50, verbose_name="菜系类型")  # 菜系类型
    city = models.CharField(max_length=20, verbose_name="城市")  # city
    county = models.CharField(max_length=20, verbose_name="区县")  # county
    business_hours = models.CharField(max_length=50, verbose_name="营业时间", null=True)  # 营业时间_清理
    location = models.CharField(max_length=100, verbose_name="地址")
    phone = models.CharField(max_length=70, verbose_name="店铺电话", null=True)  # 店铺电话_处理

    class Meta:
        verbose_name = "商铺信息"
        verbose_name_plural = "商铺信息"
        db_table = "food_shop_info"

    def __str__(self):
        return self.shop_id

class FoodComment(models.Model):
    """评论数据表 - 重写！完全匹配你的最新表头：店铺id	店铺名称	user_id	content_清理	综合评分	评分_环境	评分_口味	评分_服务	pag_time_清理	发布年份
    关联规则：通过【店铺id】与FoodShop精准一对多关联，一个店铺对应多条评论，永不匹配错误
    """
    # 👇 严格按照你的表头顺序+字段名编写，一字不差，全部对应
    shop_id = models.ForeignKey(
        FoodShop,
        on_delete=models.CASCADE,
        verbose_name="关联店铺",
        db_column="店铺id",
        to_field='shop_id'  # ✅✅✅ 核心参数：强制关联 店铺表的 shop_id 字段 ✅✅✅
    )
    # 核心！用店铺id关联FoodShop，数据库字段名=店铺id
    shop_name = models.CharField(max_length=100, verbose_name="店铺名称", null=False) # 你的表头字段：店铺名称
    user_id = models.CharField(max_length=30, verbose_name="user_id", null=False)     # 你的表头字段：user_id
    content = models.TextField(verbose_name="content", null=False)             # 你的表头字段：content_清理 (评论内容核心)
    total_score = models.DecimalField(
        verbose_name="综合评分",
        max_digits=4,  # 总位数，比如 99.99 足够用
        decimal_places=1,  # 小数位数，固定为2，完美匹配需求！
        null=False  # 保留你的必填约束
    )        # 你的表头字段：综合评分
    env_score = models.FloatField(verbose_name="评分_环境", null=True, blank=True)   # 你的表头字段：评分_环境 (允许空值)
    taste_score = models.FloatField(verbose_name="评分_口味", null=True, blank=True) # 你的表头字段：评分_口味 (允许空值)
    service_score = models.FloatField(verbose_name="评分_服务", null=True, blank=True)#你的表头字段：评分_服务 (允许空值)
    pag_time = models.CharField(max_length=50, verbose_name="pag_time", null=True, blank=True) #你的表头字段：pag_time_清理
    publish_year = models.IntegerField(verbose_name="发布年份", null=False)          # 你的表头字段：发布年份

    # 👇 保留你之前需要的【情感分析字段】，运行情感分析后自动赋值，不影响你的原始数据
    sentiment = models.CharField(max_length=10, verbose_name="情感分类", null=True, blank=True, choices=[
        ("正面", "正面"), ("负面", "负面"), ("中性", "中性")
    ])
    sentiment_score = models.FloatField(verbose_name="情感评分(0-1)", null=True, blank=True)

    class Meta:
        verbose_name = "商铺评论信息"
        verbose_name_plural = "商铺评论信息"
        db_table = "food_comment_info" # 评论表数据库表名

    def __str__(self):
        return f"{self.shop_id.shop_id} - {self.user_id} - {self.content[:20]}"


class ShopCollect(models.Model):
    """
        用户收藏店铺表：存储用户的收藏行为，核心多对多关联表
        关联逻辑：用户(User) - 多对多 - 商铺(FoodShop)，通过该表实现，带收藏时间
        唯一约束：一个用户不能重复收藏同一个店铺
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="收藏用户", related_name="user_collects")
    shop = models.ForeignKey(FoodShop, on_delete=models.CASCADE, verbose_name="收藏店铺",
                                 related_name="shop_collects")
    collect_time = models.DateTimeField(verbose_name="收藏时间", auto_now_add=True)  # 自动记录收藏时间，无需手动赋值

    class Meta:
        verbose_name = "用户收藏店铺"
        verbose_name_plural = "用户收藏店铺"
        db_table = "user_shop_collect"
        # ✅ 核心约束：联合唯一索引，用户+店铺 唯一，避免重复收藏
        unique_together = ("user", "shop")

    def __str__(self):
        return f"{self.user.username} - 收藏 - {self.shop.shop_name}"



class SentimentAnalysisTask(models.Model):
    """情感分析任务模型"""
    TASK_STATUS_CHOICES = [
        ('pending', '等待中'),
        ('processing', '处理中'),
        ('completed', '已完成'),
        ('failed', '失败'),
        ('cancelled', '已取消'),
        ]

    TASK_TYPE_CHOICES = [
        ('full', '全部分析'),
        ('incremental', '增量分析'),
        ('reanalyze', '重新分析'),
        ('test', '测试分析'),
        ]

        # 基础信息
    task_id = models.CharField(max_length=100, unique=True, verbose_name="任务ID")
    task_name = models.CharField(max_length=200, verbose_name="任务名称")
    task_type = models.CharField(max_length=20, choices=TASK_TYPE_CHOICES, default='full',
                                         verbose_name="任务类型")

    # 进度信息
    total_comments = models.IntegerField(default=0, verbose_name="总评论数")
    processed_comments = models.IntegerField(default=0, verbose_name="已处理数")
    success_count = models.IntegerField(default=0, verbose_name="成功数")
    failed_count = models.IntegerField(default=0, verbose_name="失败数")

            # 状态信息
    status = models.CharField(max_length=20, choices=TASK_STATUS_CHOICES, default='pending',
                                      verbose_name="状态")
    progress = models.FloatField(default=0, verbose_name="进度(%)")

    # 算法配置
    use_enhanced_algorithm = models.BooleanField(default=True, verbose_name="使用增强算法")
    batch_size = models.IntegerField(default=500, verbose_name="批处理大小")

    # 时间信息
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    started_at = models.DateTimeField(null=True, blank=True, verbose_name="开始时间")
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="完成时间")
    # 结果信息
    result_summary = models.JSONField(null=True, blank=True, verbose_name="结果摘要")
    error_message = models.TextField(null=True, blank=True, verbose_name="错误信息")

    # 性能统计
    processing_time = models.FloatField(null=True, blank=True, verbose_name="处理时间(秒)")
    comments_per_second = models.FloatField(null=True, blank=True, verbose_name="处理速度(条/秒)")

    class Meta:
        verbose_name = "情感分析任务"
        verbose_name_plural = "情感分析任务"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['task_id']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
            ]

    def __str__(self):
            return f"{self.task_name} ({self.status})"

    def update_progress(self, processed, total):
        """更新进度"""
        self.processed_comments = processed
        self.total_comments = total
        if total > 0:
            self.progress = (processed / total) * 100
            self.save()

    def mark_started(self):
        """标记为开始"""
        self.status = 'processing'
        self.started_at = timezone.now()
        self.save()

    def mark_completed(self, result_summary=None):
        """标记为完成"""
        self.status = 'completed'
        self.completed_at = timezone.now()
        if result_summary:
            self.result_summary = result_summary

                # 计算处理时间
        if self.started_at:
            processing_time = (self.completed_at - self.started_at).total_seconds()
            self.processing_time = processing_time
            if processing_time > 0:
                self.comments_per_second = self.processed_comments / processing_time

        self.save()

    def mark_failed(self, error_message):
        """标记为失败"""
        self.status = 'failed'
        self.completed_at = timezone.now()
        self.error_message = error_message
        self.save()

    def get_status_display_color(self):
        """获取状态显示颜色"""
        colors = {
                'pending': 'info',
                'processing': 'primary',
                'completed': 'success',
                'failed': 'danger',
                'cancelled': 'warning',
        }
        return colors.get(self.status, 'secondary')

    def get_task_type_display_icon(self):
        """获取任务类型图标"""
        icons = {
            'full': '🔄',
            'incremental': '➕',
            'reanalyze': '🔄',
            'test': '🧪',
        }
        return icons.get(self.task_type, '📋')


# ===================== 用户偏好模型（AI 助手个性化推荐） =====================
class UserProfile(models.Model):
    """用户偏好设置表 - 为 AI 助手提供个性化推荐数据"""

    BUDGET_CHOICES = [
        ('lt50',    '50元以内'),
        ('50_150',  '50~150元'),
        ('150_500', '150~500元'),
        ('gt500',   '500元以上'),
    ]

    SCENE_WEIGHT_CHOICES = [
        ('taste_first',  '口味优先（老饕派）'),
        ('env_first',    '环境优先（商务派）'),
        ('price_first',  '性价比优先'),
        ('balanced',     '均衡考虑'),
    ]

    user = models.OneToOneField(
        User, on_delete=models.CASCADE,
        verbose_name="用户", related_name="profile"
    )

    # 基础口味偏好（多选，逗号分隔，如"辣,甜,清淡"）
    flavor_pref = models.CharField(
        max_length=200, blank=True, default='',
        verbose_name="口味偏好",
        help_text="如：辣、甜、咸、麻、清淡（多个用逗号分隔）"
    )

    # 饮食禁忌（自由文本，如"不吃香菜,清真,海鲜过敏"）
    dietary_restrictions = models.TextField(
        blank=True, default='',
        verbose_name="饮食禁忌",
        help_text="如：不吃香菜、清真、素食、海鲜过敏"
    )

    # 人均消费区间
    avg_budget = models.CharField(
        max_length=20, blank=True, default='50_150',
        choices=BUDGET_CHOICES,
        verbose_name="常用消费区间"
    )

    # 常驻区域（如"海淀,朝阳"）
    frequent_areas = models.CharField(
        max_length=200, blank=True, default='',
        verbose_name="常驻区域",
        help_text="如：海淀、朝阳、西城（多个用逗号分隔）"
    )

    # 场景权重偏好
    scene_weight = models.CharField(
        max_length=20, blank=True, default='balanced',
        choices=SCENE_WEIGHT_CHOICES,
        verbose_name="推荐偏好场景"
    )

    # 特殊需求
    has_car = models.BooleanField(default=False, verbose_name="需要停车位")
    has_child = models.BooleanField(default=False, verbose_name="携带儿童（需儿童座椅）")

    # 时间戳
    updated_at = models.DateTimeField(auto_now=True, verbose_name="最后更新时间")

    class Meta:
        verbose_name = "用户偏好设置"
        verbose_name_plural = "用户偏好设置"
        db_table = "user_profile"

    def __str__(self):
        return f"{self.user.username} 的偏好设置"

    def to_context_str(self):
        """将用户偏好转化为 AI 可理解的上下文字符串"""
        parts = []
        if self.flavor_pref:
            parts.append(f"口味偏好：{self.flavor_pref}")
        if self.dietary_restrictions:
            parts.append(f"饮食禁忌：{self.dietary_restrictions}")
        if self.avg_budget:
            budget_map = dict(self.BUDGET_CHOICES)
            parts.append(f"人均预算：{budget_map.get(self.avg_budget, self.avg_budget)}")
        if self.frequent_areas:
            parts.append(f"常在区域：{self.frequent_areas}")
        if self.scene_weight:
            scene_map = dict(self.SCENE_WEIGHT_CHOICES)
            parts.append(f"推荐偏好：{scene_map.get(self.scene_weight, self.scene_weight)}")
        if self.has_car:
            parts.append("需要停车位")
        if self.has_child:
            parts.append("携带儿童，需儿童座椅")
        return "；".join(parts) if parts else "暂无偏好设置"


# ===================== 商家角色模型 =====================
class MerchantProfile(models.Model):
    """商家资料表：绑定 User，标记其为商家角色"""
    STATUS_CHOICES = [
        ('pending', '待审核'),
        ('approved', '审核通过'),
        ('rejected', '审核驳回'),
    ]

    user = models.OneToOneField(
        User, on_delete=models.CASCADE,
        verbose_name="商家账号", related_name="merchant_profile"
    )
    business_name = models.CharField(max_length=100, verbose_name="商家名称/公司")
    contact_phone = models.CharField(max_length=30, verbose_name="联系电话")
    legal_person_name = models.CharField(max_length=50, blank=True, verbose_name="法人姓名")
    id_card_no = models.CharField(max_length=50, blank=True, verbose_name="身份证号")
    business_license_no = models.CharField(max_length=80, blank=True, verbose_name="营业执照号")
    business_address = models.CharField(max_length=255, blank=True, verbose_name="商家地址")
    shop_name = models.CharField(max_length=120, blank=True, verbose_name="店铺名称")
    shop_address = models.CharField(max_length=255, blank=True, verbose_name="店铺地址")
    business_scope = models.CharField(max_length=255, blank=True, verbose_name="经营范围")
    license_image = models.FileField(upload_to='merchant/license/', blank=True, null=True, verbose_name="营业执照图片")
    id_card_front_image = models.FileField(upload_to='merchant/id_card/', blank=True, null=True, verbose_name="身份证正面图片")
    shop_image = models.FileField(upload_to='merchant/shop/', blank=True, null=True, verbose_name="店铺门头/环境图")
    qualification_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="资质审核状态")
    review_note = models.TextField(blank=True, verbose_name="审核备注/驳回原因")
    reviewed_by = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="reviewed_merchants", verbose_name="资质审核人"
    )
    reviewed_at = models.DateTimeField(null=True, blank=True, verbose_name="资质审核时间")
    is_verified = models.BooleanField(default=False, verbose_name="已通过商家认证")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "商家资料"
        verbose_name_plural = "商家资料"
        db_table = "merchant_profile"

    def __str__(self):
        return f"{self.user.username} / {self.business_name}"


class ShopApplication(models.Model):
    """商家店铺申请表：商家填写后等待管理员审核"""

    STATUS_CHOICES = [
        ('pending',  '待审核'),
        ('approved', '已通过'),
        ('rejected', '已驳回'),
    ]

    # 申请人
    merchant = models.ForeignKey(
        User, on_delete=models.CASCADE,
        verbose_name="申请商家", related_name="shop_applications"
    )

    # 店铺信息（对应 FoodShop 字段）
    shop_name        = models.CharField(max_length=100, verbose_name="店铺名称")
    food_type        = models.CharField(max_length=50, verbose_name="菜系类型")
    county           = models.CharField(max_length=20, verbose_name="区县")
    business_circle  = models.CharField(max_length=50, blank=True, verbose_name="所属商圈")
    location         = models.CharField(max_length=200, verbose_name="详细地址")
    phone            = models.CharField(max_length=70, blank=True, verbose_name="店铺电话")
    business_hours   = models.CharField(max_length=100, blank=True, verbose_name="营业时间")
    avg_price        = models.FloatField(default=0, verbose_name="人均消费(元)")
    longitude        = models.FloatField(default=116.404, verbose_name="经度")
    latitude         = models.FloatField(default=39.915, verbose_name="纬度")
    description      = models.TextField(blank=True, verbose_name="店铺简介")

    # 审核信息
    status           = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="审核状态")
    reject_reason    = models.TextField(blank=True, verbose_name="驳回理由")
    reviewed_by      = models.ForeignKey(
        User, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="reviewed_applications",
        verbose_name="审核人"
    )
    reviewed_at      = models.DateTimeField(null=True, blank=True, verbose_name="审核时间")

    # 时间戳
    created_at       = models.DateTimeField(auto_now_add=True, verbose_name="申请时间")
    updated_at       = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    # 审核通过后关联到 FoodShop
    approved_shop    = models.OneToOneField(
        'FoodShop', null=True, blank=True,
        on_delete=models.SET_NULL, related_name="application",
        verbose_name="关联店铺"
    )

    class Meta:
        verbose_name = "商家店铺申请"
        verbose_name_plural = "商家店铺申请"
        db_table = "shop_application"
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.get_status_display()}] {self.shop_name} - {self.merchant.username}"


# ===================== 店铺点击记录（用于热度算法） =====================
class ShopClickLog(models.Model):
    """记录用户点击店铺详情，用于综合人气算法"""
    user  = models.ForeignKey(User, on_delete=models.CASCADE, related_name="click_logs")
    shop  = models.ForeignKey('FoodShop', on_delete=models.CASCADE, related_name="click_logs")
    clicked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "店铺点击记录"
        verbose_name_plural = "店铺点击记录"
        db_table = "shop_click_log"
        indexes = [
            models.Index(fields=['shop', 'clicked_at']),
        ]

    def __str__(self):
        return f"{self.user.username} -> {self.shop.shop_name}"


class AIChatHistory(models.Model):
    """AI 对话历史记录表"""
    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        verbose_name="用户", related_name="ai_chats"
    )
    role = models.CharField(
        max_length=10, verbose_name="角色",
        choices=[('user', '用户'), ('assistant', 'AI助手')]
    )
    content = models.TextField(verbose_name="消息内容")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        verbose_name = "AI对话历史"
        verbose_name_plural = "AI对话历史"
        db_table = "ai_chat_history"
        ordering = ['created_at']

    def __str__(self):
        return f"{self.user.username} [{self.role}] {self.content[:30]}"