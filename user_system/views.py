from django.shortcuts import render, redirect,HttpResponse, get_object_or_404
# 导入Django内置的用户认证相关模块【核心修复点】
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.models import User
from django.db import models
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json
from datetime import datetime
from bj_food_analysis import settings
from .models import FoodShop, ShopCollect, UserProfile, AIChatHistory, MerchantProfile, ShopApplication, ShopClickLog

# ========== 1. 用户注册 ==========
def register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        email = request.POST.get('email', '')

        # 数据校验
        if not username or not password1:
            return render(request, 'register.html', {'msg': '用户名和密码不能为空！'})
        if password1 != password2:
            return render(request, 'register.html', {'msg': '两次输入的密码不一致！'})
        if len(password1) < 6:
            return render(request, 'register.html', {'msg': '密码长度不能少于6位！'})
        # 用户名唯一校验
        try:
            User.objects.create_user(username=username, password=password1, email=email)
            return redirect('/user/login/')
        except:
            return render(request, 'register.html', {'msg': '用户名已存在！请更换其他用户名'})
    return render(request, 'register.html')


# ========== 2. 用户登录 ==========
def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        # 内置认证函数校验账号密码
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)  # 登录成功，写入session
            return redirect('/user/index/')
        else:
            return render(request, 'login.html', {'msg': '用户名或密码错误！'})
    return render(request, 'login.html')


# ========== 3. 用户注销 ==========
def user_logout(request):
    logout(request)  # 清空登录状态
    return redirect('/user/login/')


# ========== 4. 用户中心（整合首页/个人信息/修改密码） ==========
def user_center(request):
    """统一的用户中心页面"""
    if not request.user.is_authenticated:
        return redirect('/user/login/')
    
    # 处理密码修改
    msg = None
    if request.method == 'POST':
        old_pwd = request.POST.get('old_pwd')
        new_pwd1 = request.POST.get('new_pwd1')
        new_pwd2 = request.POST.get('new_pwd2')

        # 校验原密码
        if not request.user.check_password(old_pwd):
            msg = '原密码输入错误！'
        elif new_pwd1 != new_pwd2:
            msg = '两次新密码不一致！'
        elif len(new_pwd1) < 6:
            msg = '新密码长度不能少于6位！'
        else:
            # 修改密码并保存
            request.user.set_password(new_pwd1)
            request.user.save()
            update_session_auth_hash(request, request.user)
            msg = '✅ 密码修改成功！'
    
    # 统计信息
    from datetime import datetime
    collect_count = ShopCollect.objects.filter(user=request.user).count()
    days_since_joined = (datetime.now() - request.user.date_joined.replace(tzinfo=None)).days
    return render(request, 'user_center.html', {
        'msg': msg,
        'collect_count': collect_count,
        'days_since_joined': days_since_joined
    })

# 兼容旧路由
def index(request):
    return redirect('/user/user_center/')

def profile(request):
    return redirect('/user/user_center/')

def change_pwd(request):
    return redirect('/user/user_center/')
from django.db.models import Count, Avg, Sum
from .models import FoodShop, FoodComment



from django.shortcuts import render
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Max, Min, Avg

from django.shortcuts import render, redirect, HttpResponse, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Max, Min, Avg
from .models import FoodShop, ShopCollect

def food_list(request):
    # 1. 基础查询集
    shop_list = FoodShop.objects.all()
    collect_shop_ids = []
    if request.user.is_authenticated:
        collect_shop_ids = ShopCollect.objects.filter(user=request.user).values_list("shop__shop_id", flat=True)

    # 2. 搜索功能：按店铺名称模糊搜索
    search_name = request.GET.get('search_name', '').strip()
    if search_name:
        shop_list = shop_list.filter(shop_name__icontains=search_name)

    # 3. 筛选功能：菜系类型/城市/商圈
    food_type = request.GET.get('food_type', '')
    if food_type:
        shop_list = shop_list.filter(food_type=food_type)

    county = request.GET.get('county', '')
    if county:
        shop_list = shop_list.filter(county=county)

    business_circle = request.GET.get('business_circle', '')
    if business_circle:
        shop_list = shop_list.filter(business_circle=business_circle)

    # 4. 分页功能：每页显示20条
    paginator = Paginator(shop_list, 20)
    page = request.GET.get('page', 1)
    try:
        shops = paginator.page(page)
    except PageNotAnInteger:
        shops = paginator.page(1)
    except EmptyPage:
        shops = paginator.page(paginator.num_pages)

    # 5. 统计数据
    total_shops = paginator.count
    max_score = round(FoodShop.objects.aggregate(Max('shop_score'))['shop_score__max'] or 0.0, 1)
    min_score = round(FoodShop.objects.aggregate(Min('shop_score'))['shop_score__min'] or 0.0, 1)
    avg_score = round(FoodShop.objects.aggregate(Avg('shop_score'))['shop_score__avg'] or 0.0, 1)

    # 6. 筛选下拉框的去重选项
    food_type_choices = FoodShop.objects.values_list('food_type', flat=True).distinct().exclude(food_type='')
    city_choices = FoodShop.objects.values_list('county', flat=True).distinct().exclude(county='')
    business_circle_choices = FoodShop.objects.values_list('business_circle', flat=True).distinct().exclude(business_circle='')

    context = {
        'shops': shops,
        'search_name': search_name,
        'food_type': food_type,
        'county': county,
        'business_circle': business_circle,
        'food_type_choices': food_type_choices,
        'city_choices': city_choices,
        'business_circle_choices': business_circle_choices,
        'total_shops': total_shops,
        'max_score': max_score,
        'min_score': min_score,
        'avg_score': avg_score,
        'collect_shop_ids': collect_shop_ids
    }
    return render(request, 'food_list.html', context)

@login_required(login_url="/login/")
def collect_shop(request, shop_id):
    """列表页 收藏/取消收藏 核心接口"""
    shop = get_object_or_404(FoodShop, shop_id=shop_id)
    collect_obj = ShopCollect.objects.filter(user=request.user, shop=shop).first()

    if collect_obj:
        collect_obj.delete()
        messages.success(request, f"✅ 已取消收藏【{shop.shop_name}】")
    else:
        ShopCollect.objects.create(user=request.user, shop=shop)
        messages.success(request, f"❤️ 收藏成功【{shop.shop_name}】")

    return redirect(request.META.get('HTTP_REFERER', '/food_list/'))

@login_required(login_url="/login/")
def cancel_collect(request, shop_id):
    """收藏页 单独取消收藏接口 ✅ 新增消息提示 核心修复"""
    shop = get_object_or_404(FoodShop, shop_id=shop_id)
    ShopCollect.objects.filter(user=request.user, shop__shop_id=shop_id).delete()
    messages.success(request, f"✅ 已取消收藏【{shop.shop_name}】") # 就是少了这一行！！！
    return redirect('/user/my_collect/')

@login_required(login_url="/login/")
def my_collect(request):
    collect_list = ShopCollect.objects.filter(user=request.user).order_by("-collect_time")
    collect_shop_list = [item.shop for item in collect_list]
    collect_count = len(collect_shop_list)

    return render(request, "my_collect.html", {
        "collect_shop_list": collect_shop_list,
        "collect_count": collect_count,
        "collect_list": collect_list
    })

# 2. 商铺评分数据分析
def food_score(request):
    if not request.user.is_authenticated:
        return redirect('/user/login/')
    # 评分分段统计
    high_score     = FoodShop.objects.filter(shop_score__gte=4.5).count()
    mid_high_score = FoodShop.objects.filter(shop_score__gte=4.0, shop_score__lt=4.5).count()
    mid_score      = FoodShop.objects.filter(shop_score__gte=3.0, shop_score__lt=4.0).count()
    low_score      = FoodShop.objects.filter(shop_score__lt=3.0).count()
    avg_score      = round(FoodShop.objects.aggregate(Avg('shop_score'))['shop_score__avg'] or 0, 2)
    max_score      = FoodShop.objects.aggregate(models.Max('shop_score'))['shop_score__max'] or 0
    min_score      = FoodShop.objects.aggregate(models.Min('shop_score'))['shop_score__min'] or 0
    total          = FoodShop.objects.count() or 1

    # 高分占比
    high_pct = round(high_score / total * 100, 1)
    low_pct  = round(low_score / total * 100, 1)

    # 生成智能建议
    suggestions = []
    if high_pct >= 40:
        suggestions.append(f"✅ 北京餐饮整体口碑优秀！{high_pct}% 的店铺评分达到 4.5 分以上，出行时可以放心选择高分店。")
    else:
        suggestions.append(f"📊 目前高分（4.5+）店铺占比 {high_pct}%，找餐厅时建议优先筛选 4.0 分以上，避免踩雷。")
    if low_pct > 10:
        suggestions.append(f"⚠️ 有 {low_pct}% 的店铺评分低于 3.0，前往陌生区域就餐时，务必提前查看评分再做决定。")
    suggestions.append(f"💡 北京餐饮平均评分为 {avg_score} 分，低于 {avg_score} 分的店铺属于市场平均水平以下，建议谨慎选择。")
    suggestions.append("🔍 点击「智能推荐」模块，系统将根据你的收藏偏好和真实评分，为你精准推荐高分好店。")

    return render(request, 'food_score.html', {
        'high_score': high_score, 'mid_high_score': mid_high_score,
        'mid_score': mid_score,   'low_score': low_score,
        'avg_score': avg_score,   'max_score': max_score, 'min_score': min_score,
        'high_pct': high_pct,     'low_pct': low_pct,
        'suggestions': suggestions,
    })

# 3. 餐饮品类占比分析
def food_type(request):
    if not request.user.is_authenticated:
        return redirect('/user/login/')
    type_count = list(FoodShop.objects.values('food_type').annotate(
        count=Count('id'), avg_score=Avg('shop_score')
    ).order_by('-count'))
    total_type = len(type_count)
    total_shop = FoodShop.objects.count() or 1

    top3 = type_count[:3] if type_count else []
    top1_name = top3[0]['food_type'] if top3 else '未知'
    top1_pct  = round(top3[0]['count'] / total_shop * 100, 1) if top3 else 0
    top1_score = round(top3[0]['avg_score'] or 0, 2) if top3 else 0

    # 评分最高品类
    best_score_type = max(type_count, key=lambda x: x['avg_score'] or 0) if type_count else None

    suggestions = []
    suggestions.append(f"🏆 「{top1_name}」是北京最多的餐饮品类，占总数的 {top1_pct}%，选择空间大，竞争激烈，建议通过评分筛选优质门店。")
    if best_score_type:
        suggestions.append(f"⭐ 「{best_score_type['food_type']}」品类平均评分最高（{round(best_score_type['avg_score'] or 0, 2)}分），是高口碑赛道，推荐重点探索。")
    if total_type >= 20:
        suggestions.append(f"🍜 北京共有 {total_type} 个餐饮品类，多样性丰富！如果你平时口味单一，不妨尝试一些冷门品类，往往性价比更高、排队更少。")
    suggestions.append("💡 使用左侧菜单的「智能推荐」，系统会根据你收藏的品类偏好，自动推荐同类型高分店铺。")

    return render(request, 'food_type.html', {
        'type_count': type_count, 'total_type': total_type,
        'total_shop': total_shop, 'suggestions': suggestions,
    })

# 4. 趋势分析已删除（已整合进各分析页的建议模块）

# ========== 数据分析功能 ==========

# 5. Top10排行榜（多维度）
def top10_popular(request):
    """多维度Top10排行榜"""
    if not request.user.is_authenticated:
        return redirect('/user/login/')

    from django.db.models import F, ExpressionWrapper, FloatField

    # 1. 综合人气榜：评分(40%) + 评论数(30%) + 近30天点击量(20%) + 收藏数(10%)
    from datetime import timedelta
    from django.utils import timezone as tz
    thirty_days_ago = tz.now() - timedelta(days=30)

    max_comments  = FoodShop.objects.aggregate(models.Max('comment_count'))['comment_count__max'] or 1
    max_score     = FoodShop.objects.aggregate(models.Max('shop_score'))['shop_score__max'] or 1
    max_clicks_qs = ShopClickLog.objects.filter(clicked_at__gte=thirty_days_ago).values('shop').annotate(cnt=Count('id')).order_by('-cnt').first()
    max_clicks    = max_clicks_qs['cnt'] if max_clicks_qs else 1
    max_collects_qs = ShopCollect.objects.values('shop').annotate(cnt=Count('id')).order_by('-cnt').first()
    max_collects  = max_collects_qs['cnt'] if max_collects_qs else 1

    # 取所有店铺，在 Python 层合并点击量和收藏数计算综合分
    from collections import defaultdict
    click_map   = defaultdict(int, {
        item['shop']: item['cnt']
        for item in ShopClickLog.objects.filter(clicked_at__gte=thirty_days_ago)
            .values('shop').annotate(cnt=Count('id'))
    })
    collect_map = defaultdict(int, {
        item['shop']: item['cnt']
        for item in ShopCollect.objects.values('shop').annotate(cnt=Count('id'))
    })

    all_shops = list(FoodShop.objects.all())
    for shop in all_shops:
        score_norm   = float(shop.shop_score) / float(max_score)
        comment_norm = shop.comment_count / max_comments
        click_norm   = click_map[shop.pk] / max_clicks
        collect_norm = collect_map[shop.pk] / max_collects
        shop._popularity = score_norm * 0.40 + comment_norm * 0.30 + click_norm * 0.20 + collect_norm * 0.10

    popular_shops = sorted(all_shops, key=lambda s: s._popularity, reverse=True)[:10]

    # 2. 评分最高榜
    highest_score_shops = FoodShop.objects.all().order_by('-shop_score', '-comment_count')[:10]

    # 3. 评论最多榜
    most_comments_shops = FoodShop.objects.all().order_by('-comment_count', '-shop_score')[:10]

    # 4. 人均最高榜
    highest_price_shops = FoodShop.objects.filter(
        avg_price__isnull=False
    ).order_by('-avg_price', '-shop_score')[:10]

    # 5. 人均最低榜（性价比之选）
    lowest_price_shops = FoodShop.objects.filter(
        avg_price__isnull=False,
        avg_price__gt=0
    ).order_by('avg_price', '-shop_score')[:10]

    # 6. 米其林推荐榜
    michelin_shops = FoodShop.objects.filter(
        michelin__isnull=False
    ).exclude(
        michelin__in=['', '无', '-']
    ).order_by('-shop_score', '-comment_count')[:10]

    return render(request, 'top10_rankings.html', {
        'popular_shops': popular_shops,
        'highest_score_shops': highest_score_shops,
        'most_comments_shops': most_comments_shops,
        'highest_price_shops': highest_price_shops,
        'lowest_price_shops': lowest_price_shops,
        'michelin_shops': michelin_shops
    })

# 6. 区县分布分析
from django.db.models import Count, Avg, Sum
import json


def county_distribution(request):
    if not request.user.is_authenticated:
        return redirect('/user/login/')

    # 按区县分组统计店铺数量
    county_data = FoodShop.objects.values('county').annotate(
        count=Count('id'),
        avg_score=Avg('shop_score'),
        avg_price=Avg('avg_price')
    ).filter(county__isnull=False).exclude(county='').order_by('-count')

    county_data_list = list(county_data)
    county_names = [item['county'] for item in county_data_list]
    county_counts = [item['count'] for item in county_data_list]

    # 计算聚合值
    total_shops = sum(item['count'] for item in county_data_list)
    avg_score_overall = 0
    avg_price_overall = 0

    if county_data_list:
        # 计算加权平均评分（按店铺数量）
        total_score = sum(item['avg_score'] * item['count'] for item in county_data_list if item['avg_score'])
        avg_score_overall = total_score / total_shops if total_shops > 0 else 0

        # 计算加权平均价格（按店铺数量）
        total_price = sum(item['avg_price'] * item['count'] for item in county_data_list if item['avg_price'])
        avg_price_overall = total_price / total_shops if total_shops > 0 else 0

    # 智能建议
    top1 = county_data_list[0] if county_data_list else None
    top_score_county = max(county_data_list, key=lambda x: x['avg_score'] or 0) if county_data_list else None
    best_value = min(
        [c for c in county_data_list if c['avg_price'] and c['avg_price'] > 0],
        key=lambda x: (x['avg_price'] or 9999) / float(x['avg_score'] or 1),
        default=None
    )
    suggestions_county = []
    if top1:
        suggestions_county.append(f"🗺️ 「{top1['county']}」是北京餐饮最密集的区域（{top1['count']}家），选择最多，适合美食探索；但也要注意避开同质化严重的商圈。")
    if top_score_county:
        suggestions_county.append(f"⭐ 「{top_score_county['county']}」区域店铺平均评分最高（{round(top_score_county['avg_score'] or 0, 2)}分），品质更有保障，适合重要场合就餐。")
    if best_value:
        suggestions_county.append(f"💰 「{best_value['county']}」性价比突出，人均约 ¥{round(best_value['avg_price'] or 0, 0):.0f}、评分 {round(best_value['avg_score'] or 0, 2)} 分，是日常解决饭局的好选择。")
    suggestions_county.append("💡 建议：前往陌生区域就餐前，先在「店铺地图」查看餐厅分布，再结合评分和价格做决策，减少踩雷概率。")

    return render(request, 'county_distribution.html', {
        'county_data': county_data_list,
        'county_names': json.dumps(county_names),
        'county_counts': json.dumps(county_counts),
        'total_shops': total_shops,
        'avg_score_overall': round(avg_score_overall, 2),
        'avg_price_overall': round(avg_price_overall, 0),
        'county_count': len(county_data_list),
        'suggestions_county': suggestions_county,
    })

# 7. 人均消费分析
def price_analysis(request):
    if not request.user.is_authenticated:
        return redirect('/user/login/')
    # 价格区间统计
    price_ranges = [
        {'label': '0-50元', 'min': 0, 'max': 50},
        {'label': '50-100元', 'min': 50, 'max': 100},
        {'label': '100-200元', 'min': 100, 'max': 200},
        {'label': '200-300元', 'min': 200, 'max': 300},
        {'label': '300元以上', 'min': 300, 'max': 99999},
    ]
    range_data = []
    for pr in price_ranges:
        count = FoodShop.objects.filter(avg_price__gte=pr['min'], avg_price__lt=pr['max']).count()
        range_data.append({'label': pr['label'], 'count': count})
    
    # 平均价格
    avg_price = round(FoodShop.objects.aggregate(Avg('avg_price'))['avg_price__avg'] or 0, 2)
    max_price = FoodShop.objects.aggregate(Max('avg_price'))['avg_price__max'] or 0
    min_price = FoodShop.objects.aggregate(Min('avg_price'))['avg_price__min'] or 0
    
    # 价格与评分关系（用于散点图）
    price_score_data = [[float(price), float(score)] for price, score in 
                        FoodShop.objects.filter(avg_price__isnull=False).values_list('avg_price', 'shop_score')[:100]]
    
    # 主流消费区间
    dominant_range = max(range_data, key=lambda x: x['count']) if range_data else None
    budget_pct = round(next((r['count'] for r in range_data if r['label']=='0-50元'), 0) / max(sum(r['count'] for r in range_data),1) * 100, 1)
    premium_pct = round(next((r['count'] for r in range_data if r['label']=='300元以上'), 0) / max(sum(r['count'] for r in range_data),1) * 100, 1)

    suggestions_price = []
    if dominant_range:
        suggestions_price.append(f"💰 北京餐饮最主流的消费区间是「{dominant_range['label']}」，这个价位选择最多，竞争最激烈，也是大多数消费者的日常预算。")
    suggestions_price.append(f"🍜 人均 ¥{avg_price:.0f} 是北京整体平均水平。低于这个价格能找到性价比高的店，高于这个价格通常意味着更好的环境或食材品质。")
    if budget_pct >= 20:
        suggestions_price.append(f"😊 50元以内的平价餐厅占比达 {budget_pct}%，适合学生党和工作日快餐选择；可在「店铺列表」按价格升序筛选。")
    if premium_pct >= 5:
        suggestions_price.append(f"🍾 高端餐厅（300元以上）占比 {premium_pct}%，适合商务宴请或特殊场合。可在排行榜的「人均最高榜」找到顶级选择。")
    suggestions_price.append("💡 建议：价格≠品质。使用「智能推荐」时系统会综合评分+评论量+价格，为你匹配最值得去的店。")

    return render(request, 'price_analysis.html', {
        'range_data': range_data,
        'avg_price': avg_price,
        'max_price': max_price,
        'min_price': min_price,
        'price_score_data': json.dumps(price_score_data),
        'suggestions_price': suggestions_price,
    })

# 8. 商圈分析
def business_circle_analysis(request):
    if not request.user.is_authenticated:
        return redirect('/user/login/')
    # 按商圈统计
    circle_data = FoodShop.objects.values('business_circle').annotate(
        count=Count('id'),
        avg_score=Avg('shop_score'),
        avg_price=Avg('avg_price')
    ).filter(business_circle__isnull=False).exclude(business_circle='').order_by('-count')[:20]
    
    circle_names = [item['business_circle'] for item in circle_data]
    circle_counts = [item['count'] for item in circle_data]
    circle_avg_scores = [float(item['avg_score'] or 0) for item in circle_data]
    
    return render(request, 'business_circle_analysis.html', {
        'circle_data': list(circle_data),
        'circle_names': json.dumps(circle_names),
        'circle_counts': json.dumps(circle_counts),
        'circle_avg_scores': json.dumps(circle_avg_scores)
    })

# ========== 数据可视化功能 ==========

# 9. 店铺分布热力图
def shop_heatmap(request):
    if not request.user.is_authenticated:
        return redirect('/user/login/')
    # 获取所有店铺的经纬度和权重（评论数）
    shops = FoodShop.objects.filter(longitude__isnull=False, latitude__isnull=False).values(
        'longitude', 'latitude', 'comment_count', 'shop_name'
    )
    heatmap_data = [
        {'lng': float(shop['longitude']), 'lat': float(shop['latitude']), 'count': shop['comment_count'] or 0}
        for shop in shops
    ]
    from django.conf import settings
    return render(request, 'shop_heatmap.html', {
        'heatmap_data': heatmap_data,
        'heatmap_data_json': json.dumps(heatmap_data, ensure_ascii=False),
        'baidu_map_ak': settings.BAIDU_MAP_AK
    })


# user_system/views.py 中添加
import json
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from .models import FoodComment, SentimentAnalysisTask
from .redis_queue import RedisQueue
import uuid
from django.db.models import Q, Count, Avg
from django.core.paginator import Paginator
import jieba
from .sentiment_core import EnhancedSentimentAnalyzer


def sentiment_dashboard(request):
    """情感分析结果展示（用户端只读）"""
    if not request.user.is_authenticated:
        return redirect('/user/login/')
    
    from .models import FoodComment
    
    # 统计信息
    total_comments = FoodComment.objects.count()
    analyzed_comments = FoodComment.objects.exclude(
        Q(sentiment__isnull=True) | Q(sentiment='')
    ).count()

    # 情感分布
    positive_count = FoodComment.objects.filter(sentiment='正面').count()
    negative_count = FoodComment.objects.filter(sentiment='负面').count()
    neutral_count = FoodComment.objects.filter(sentiment='中性').count()

    # 按年份统计情感趋势
    from datetime import datetime
    current_year = datetime.now().year
    existing_years = list(FoodComment.objects.values_list('publish_year', flat=True).distinct().order_by('publish_year'))
    
    years_to_show = existing_years[-5:] if len(existing_years) >= 5 else existing_years
    
    sentiment_trend = {
        'years': years_to_show,
        'positive': [],
        'negative': [],
        'neutral': []
    }
    
    for year in years_to_show:
        sentiment_trend['positive'].append(FoodComment.objects.filter(publish_year=year, sentiment='正面').count())
        sentiment_trend['negative'].append(FoodComment.objects.filter(publish_year=year, sentiment='负面').count())
        sentiment_trend['neutral'].append(FoodComment.objects.filter(publish_year=year, sentiment='中性').count())

    # 店铺好评排行
    shop_ranking = list(FoodComment.objects.exclude(
        Q(sentiment__isnull=True) | Q(sentiment='')
    ).values(
        'shop_id__shop_name'
    ).annotate(
        total=Count('id'),
        positive=Count('id', filter=Q(sentiment='正面')),
        shop_name=models.F('shop_id__shop_name')
    ).filter(
        total__gte=10
    ).annotate(
        positive_rate=models.ExpressionWrapper(
            models.F('positive') * 100.0 / models.F('total'),
            output_field=models.FloatField()
        )
    ).order_by('-positive_rate')[:10])

    return render(request, 'sentiment_dashboard.html', {
        'total_comments': total_comments,
        'analyzed_comments': analyzed_comments,
        'analysis_percentage': round(analyzed_comments / total_comments * 100, 2) if total_comments > 0 else 0,
        'positive_count': positive_count,
        'negative_count': negative_count,
        'neutral_count': neutral_count,
        'sentiment_trend': json.dumps(sentiment_trend),
        'shop_ranking': json.dumps(shop_ranking, ensure_ascii=False)
    })


@csrf_exempt
def create_sentiment_task(request):
    """创建情感分析任务"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            # 生成任务ID
            task_id = str(uuid.uuid4())
            task_name = data.get('task_name', f'情感分析任务-{task_id[:8]}')
            task_type = data.get('task_type', 'full')
            batch_size = data.get('batch_size', 500)
            use_enhanced = data.get('use_enhanced', True)

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
                batch_size=batch_size,
                status='pending'
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

            return JsonResponse({
                'success': True,
                'task_id': task_id,
                'task_name': task_name,
                'message': '任务创建成功，已加入处理队列'
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'创建任务失败: {str(e)}'
            }, status=500)

    return JsonResponse({'error': '只支持POST请求'}, status=405)


def get_task_status(request, task_id):
    """获取任务状态"""
    try:
        task = SentimentAnalysisTask.objects.get(task_id=task_id)

        # 获取Redis进度
        queue = RedisQueue()
        progress = queue.get_progress(task_id)

        response_data = {
            'task_id': task.task_id,
            'task_name': task.task_name,
            'task_type': task.task_type,
            'status': task.status,
            'progress': task.progress,
            'total_comments': task.total_comments,
            'processed_comments': task.processed_comments,
            'success_count': task.success_count,
            'failed_count': task.failed_count,
            'created_at': task.created_at.isoformat() if task.created_at else None,
            'started_at': task.started_at.isoformat() if task.started_at else None,
            'completed_at': task.completed_at.isoformat() if task.completed_at else None,
        }

        if progress:
            response_data.update({
                'real_time_progress': progress.get('progress', 0),
                'real_time_processed': progress.get('processed', 0),
                'real_time_success': progress.get('success', 0),
                'real_time_failed': progress.get('failed', 0),
            })

        if task.status == 'completed' and task.result_summary:
            response_data['result_summary'] = task.result_summary
            response_data['processing_time'] = task.processing_time
            response_data['comments_per_second'] = task.comments_per_second

        if task.status == 'failed' and task.error_message:
            response_data['error_message'] = task.error_message

        return JsonResponse(response_data)

    except SentimentAnalysisTask.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': '任务不存在'
        }, status=404)


def list_tasks(request):
    """列出所有任务"""
    page = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size', 20))

    tasks = SentimentAnalysisTask.objects.all().order_by('-created_at')

    paginator = Paginator(tasks, page_size)
    page_obj = paginator.get_page(page)

    tasks_data = []
    for task in page_obj:
        tasks_data.append({
            'task_id': task.task_id,
            'task_name': task.task_name,
            'task_type': task.task_type,
            'status': task.status,
            'progress': task.progress,
            'total_comments': task.total_comments,
            'processed_comments': task.processed_comments,
            'created_at': task.created_at.isoformat(),
            'started_at': task.started_at.isoformat() if task.started_at else None,
            'completed_at': task.completed_at.isoformat() if task.completed_at else None,
        })

    return JsonResponse({
        'success': True,
        'tasks': tasks_data,
        'total_pages': paginator.num_pages,
        'current_page': page,
        'total_tasks': paginator.count,
    })


@csrf_exempt
def analyze_single_comment(request):
    """分析单条评论"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            comment_text = data.get('comment', '')

            if not comment_text:
                return JsonResponse({'error': '评论内容不能为空'}, status=400)

            analyzer = EnhancedSentimentAnalyzer()
            sentiment, score = analyzer.analyze(comment_text)

            # 分词结果
            words = jieba.lcut(comment_text)

            return JsonResponse({
                'success': True,
                'sentiment': sentiment,
                'score': score,
                'words': words,
                'color': {
                    '正面': '#52c41a',
                    '负面': '#f5222d',
                    '中性': '#faad14'
                }.get(sentiment, '#999'),
                'emoji': {
                    '正面': '👍',
                    '负面': '👎',
                    '中性': '😐'
                }.get(sentiment, '❓')
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'分析失败: {str(e)}'
            }, status=500)

    return JsonResponse({'error': '只支持POST请求'}, status=405)


def sentiment_statistics(request):
    """情感分析统计"""
    # 总体统计
    total_stats = FoodComment.objects.aggregate(
        total=Count('id'),
        analyzed=Count('id', filter=~Q(sentiment__isnull=True) & ~Q(sentiment='')),
        avg_sentiment=Avg('sentiment_score'),
        positive_count=Count('id', filter=Q(sentiment='正面')),
        negative_count=Count('id', filter=Q(sentiment='负面')),
        neutral_count=Count('id', filter=Q(sentiment='中性'))
    )

    # 时间趋势
    yearly_stats = FoodComment.objects.exclude(
        sentiment__isnull=True
    ).values('publish_year').annotate(
        count=Count('id'),
        avg_sentiment=Avg('sentiment_score'),
        positive_count=Count('id', filter=Q(sentiment='正面')),
        negative_count=Count('id', filter=Q(sentiment='负面'))
    ).order_by('publish_year')

    # 店铺排行
    shop_stats = FoodComment.objects.exclude(
        sentiment__isnull=True
    ).values(
        'shop_id__shop_name',
        'shop_id__shop_id',
        'shop_id__county',
        'shop_id__food_type'
    ).annotate(
        total_comments=Count('id'),
        avg_sentiment=Avg('sentiment_score'),
        positive_rate=Count('id', filter=Q(sentiment='正面')) * 100.0 / Count('id'),
        negative_rate=Count('id', filter=Q(sentiment='负面')) * 100.0 / Count('id')
    ).filter(total_comments__gte=10).order_by('-avg_sentiment')[:50]

    # 菜系情感分析
    food_type_stats = FoodComment.objects.exclude(
        sentiment__isnull=True
    ).values('shop_id__food_type').annotate(
        total=Count('id'),
        avg_sentiment=Avg('sentiment_score'),
        positive_count=Count('id', filter=Q(sentiment='正面'))
    ).filter(total__gte=100).order_by('-avg_sentiment')

    return JsonResponse({
        'success': True,
        'total_stats': total_stats,
        'yearly_stats': list(yearly_stats),
        'shop_stats': list(shop_stats),
        'food_type_stats': list(food_type_stats),
    })


def sentiment_results(request, task_id):
    """任务结果页面"""
    task = get_object_or_404(SentimentAnalysisTask, task_id=task_id)

    # 获取详细结果
    queue = RedisQueue()
    result = queue.get_result(task_id)

    # 获取情感分布
    sentiment_distribution = FoodComment.objects.exclude(
        sentiment__isnull=True
    ).values('sentiment').annotate(
        count=Count('id'),
        avg_score=Avg('sentiment_score')
    )

    # 获取最新分析的评论
    recent_analyzed = FoodComment.objects.exclude(
        sentiment__isnull=True
    ).select_related('shop_id').order_by('-id')[:20]

    return render(request, 'sentiment_results.html', {
        'task': task,
        'result': result,
        'sentiment_distribution': sentiment_distribution,
        'recent_analyzed': recent_analyzed,
    })
# ========== 地图功能 ==========

import json
from django.shortcuts import render
from django.db.models import Q
from django.conf import settings
from .models import FoodShop

# user_system/views.py
import json
from django.shortcuts import render
from django.db.models import Q
from django.conf import settings
from .models import FoodShop


# user_system/views.py
def shop_map(request):
    """地图主页面 - 使用iframe嵌入"""
    return render(request, 'shop_map.html')


def shop_map_standalone(request):
    """独立的地图页面 - 用于iframe嵌入"""
    try:
        # 获取筛选参数
        county = request.GET.get('county', '')
        business_circle = request.GET.get('business_circle', '')

        # 基础查询
        shops = FoodShop.objects.all()

        # 应用筛选条件
        if county:
            shops = shops.filter(county=county)
        if business_circle:
            shops = shops.filter(business_circle=business_circle)

        # 获取筛选选项 - 处理空值
        counties = FoodShop.objects.filter(
            county__isnull=False
        ).exclude(
            county=''
        ).order_by('county').values_list('county', flat=True).distinct()

        business_circles = FoodShop.objects.filter(
            business_circle__isnull=False
        ).exclude(
            business_circle=''
        ).order_by('business_circle').values_list('business_circle', flat=True).distinct()

        # 构建地图数据
        shops_data = []
        for shop in shops:
            try:
                lng = float(shop.longitude) if shop.longitude else 0
                lat = float(shop.latitude) if shop.latitude else 0
            except (ValueError, TypeError):
                lng = 116.404
                lat = 39.915

            shops_data.append({
                'lng': lng,
                'lat': lat,
                'shop_name': shop.shop_name,
                'score': float(shop.shop_score) if shop.shop_score else 0,
                'avg_price': shop.avg_price,
                'food_type': shop.food_type,
                'county': shop.county or '',
                'business_circle': shop.business_circle or '',
                'location': shop.location or ''
            })

        shops_json = json.dumps(shops_data, ensure_ascii=False)

        # 获取百度地图AK
        baidu_map_ak = getattr(settings, 'BAIDU_MAP_AK', '')

        return render(request, 'shop_map_standalone.html', {
            'shops_json': shops_json,
            'baidu_map_ak': baidu_map_ak,
            'shops_count': shops.count(),
            'counties': counties,
            'business_circles': business_circles,
            'county_filter': county,
            'business_circle_filter': business_circle
        })

    except Exception as e:
        print(f"地图页面错误: {e}")
        return render(request, 'shop_map_standalone.html', {
            'shops_json': '[]',
            'baidu_map_ak': getattr(settings, 'BAIDU_MAP_AK', ''),
            'shops_count': 0,
            'counties': [],
            'business_circles': [],
            'county_filter': '',
            'business_circle_filter': ''
        })
# ========== 推荐系统 ==========

# 12. 智能推荐（升级版：ItemCF + 内容相似度 + 可解释）
def shop_recommendation(request):
    if not request.user.is_authenticated:
        return redirect('/user/login/')

    recommended_shops = []
    recommendation_reasons = {}  # 推荐理由

    # 获取用户收藏
    user_collects = ShopCollect.objects.filter(user=request.user).select_related('shop')
    # 修改部分：添加安全检查，防止 shop 为 None
    collected_shop_ids = [c.shop.shop_id for c in user_collects if c.shop]

    # 修改部分：初始化变量，防止未定义错误
    avg_collected_price = 0
    collected_shops = []
    collected_types = set()
    collected_counties = set()

    if user_collects.exists():
        # 修改部分：过滤掉可能为 None 的 shop
        collected_shops = [c.shop for c in user_collects if c.shop]

        # 修改部分：只有有收藏店铺时才执行后续逻辑
        if collected_shops:
            # 方法1: 基于ItemCF（协同过滤）- 找收藏相似店铺的用户还收藏了什么
            # 修改部分：添加空值检查
            if collected_shop_ids:
                similar_users_collects = ShopCollect.objects.filter(
                    shop__shop_id__in=collected_shop_ids
                ).exclude(user=request.user).values('user_id').annotate(
                    common_count=Count('id')
                ).filter(common_count__gte=2).order_by('-common_count')[:10]

                similar_users_ids = [item['user_id'] for item in similar_users_collects]
                if similar_users_ids:
                    cf_recommendations = ShopCollect.objects.filter(
                        user_id__in=similar_users_ids
                    ).exclude(
                        shop__shop_id__in=collected_shop_ids
                    ).values('shop_id').annotate(
                        recommend_count=Count('id')
                    ).order_by('-recommend_count')[:10]

                    for rec in cf_recommendations:
                        # 修改部分：添加异常处理，防止店铺不存在
                        try:
                            shop = FoodShop.objects.get(shop_id=rec['shop_id'])
                            recommended_shops.append(shop)
                            recommendation_reasons[
                                shop.shop_id] = f"有 {rec['recommend_count']} 位用户同时收藏了您喜欢的店铺"
                        except FoodShop.DoesNotExist:
                            continue  # 如果店铺不存在，跳过

            # 方法2: 基于内容相似度（同菜系+同区县+相似价格）
            # 修改部分：避免列表推导式产生 None
            collected_types = set([s.food_type for s in collected_shops if s.food_type])
            collected_counties = set([s.county for s in collected_shops if s.county])

            # 修改部分：安全计算平均价格
            valid_prices = [s.avg_price for s in collected_shops if s.avg_price]
            if valid_prices:
                avg_collected_price = sum(valid_prices) / len(valid_prices)

            # 同菜系同区县
            # 修改部分：添加空值检查
            if collected_types and collected_counties:
                content_similar = FoodShop.objects.filter(
                    food_type__in=collected_types,
                    county__in=collected_counties
                ).exclude(shop_id__in=collected_shop_ids).order_by('-shop_score')[:10]

                for shop in content_similar:
                    if shop not in recommended_shops:
                        recommended_shops.append(shop)
                        recommendation_reasons[shop.shop_id] = f"与您收藏的 {shop.food_type} 店铺相似（{shop.county}）"

            # 方法3: 相似价格区间
            # 修改部分：添加 avg_collected_price 检查
            if avg_collected_price > 0:
                price_similar = FoodShop.objects.filter(
                    avg_price__gte=avg_collected_price * 0.7,
                    avg_price__lte=avg_collected_price * 1.3
                ).exclude(shop_id__in=collected_shop_ids).order_by('-shop_score')[:10]

                for shop in price_similar:
                    if shop not in recommended_shops:
                        recommended_shops.append(shop)
                        recommendation_reasons[
                            shop.shop_id] = f"价格相近（人均¥{shop.avg_price:.0f}，您常选¥{avg_collected_price:.0f}）"

    # 方法4: 热门店铺（冷启动/补充）
    if len(recommended_shops) < 15:
        # 修改部分：使用更安全的查询
        try:
            popular_shops = FoodShop.objects.annotate(
                popularity=models.F('shop_score') * models.F('comment_count')
            ).exclude(shop_id__in=collected_shop_ids).order_by('-popularity')[:20]

            for shop in popular_shops:
                if shop not in recommended_shops:
                    recommended_shops.append(shop)
                    recommendation_reasons[
                        shop.shop_id] = f"人气爆款（评分{shop.shop_score:.1f}，{shop.comment_count}条评论）"
        except Exception as e:
            # 修改部分：添加异常处理，防止查询出错
            print(f"查询热门店铺时出错: {e}")
            # 备用方案：简单的热门店铺
            popular_shops = FoodShop.objects.exclude(
                shop_id__in=collected_shop_ids
            ).order_by('-shop_score')[:20]
            for shop in popular_shops:
                if shop not in recommended_shops:
                    recommended_shops.append(shop)
                    recommendation_reasons[shop.shop_id] = "热门店铺推荐"

    # ===== 分组展示：每种理由最多 4 条，保证多样性 =====
    # 定义理由分组 key
    GROUP_LABELS = {
        'cf':      '与你品味相似的用户也喜欢',
        'content': '与你收藏的风格相似',
        'price':   '符合你的消费习惯',
        'popular': '北京热门人气好店',
    }

    groups = {'cf': [], 'content': [], 'price': [], 'popular': []}
    group_raw = {'cf': [], 'content': [], 'price': [], 'popular': []}

    def _classify(shop_id, reason_str):
        if '位用户' in reason_str:
            return 'cf'
        elif '相似' in reason_str:
            return 'content'
        elif '价格' in reason_str or '人均' in reason_str:
            return 'price'
        return 'popular'

    seen_ids = set()
    for shop in recommended_shops:
        if shop.shop_id in seen_ids:
            continue
        seen_ids.add(shop.shop_id)
        reason = recommendation_reasons.get(shop.shop_id, '北京热门好店')
        gkey = _classify(shop.shop_id, reason)
        if len(groups[gkey]) < 4:
            groups[gkey].append(shop)
            group_raw[gkey].append(reason)

    # 拼装分组列表，供模板渲染
    recommendation_groups = []
    for gkey, label in GROUP_LABELS.items():
        if groups[gkey]:
            recommendation_groups.append({
                'label': label,
                'key': gkey,
                'items': list(zip(groups[gkey], group_raw[gkey])),
            })

    total_recommended = sum(len(g['items']) for g in recommendation_groups)

    return render(request, 'shop_recommendation.html', {
        'recommendation_groups': recommendation_groups,
        'has_collections': user_collects.exists(),
        'total_recommended': total_recommended,
        'collected_count': len(collected_shops) if user_collects.exists() else 0
    })


def shop_detail(request, shop_id):
    """店铺详情页：详细信息、评论、相似店铺"""
    if not request.user.is_authenticated:
        return redirect('/user/login/')

    from .models import FoodComment
    shop = get_object_or_404(FoodShop, shop_id=shop_id)

    # 记录点击行为（用于综合人气算法）
    if request.user.is_authenticated:
        ShopClickLog.objects.create(user=request.user, shop=shop)

    # 是否已收藏
    is_collected = ShopCollect.objects.filter(user=request.user, shop=shop).exists()

    # 店铺评论
    comments = FoodComment.objects.filter(shop_id=shop).order_by('-publish_year')[:20]

    # 评论情感统计
    sentiment_stats = FoodComment.objects.filter(shop_id=shop).values('sentiment').annotate(
        count=Count('id')
    ).exclude(sentiment__isnull=True)

    # 评分构成
    # 修改部分：添加默认值处理
    env_avg = FoodComment.objects.filter(shop_id=shop).aggregate(Avg('env_score'))['env_score__avg']
    taste_avg = FoodComment.objects.filter(shop_id=shop).aggregate(Avg('taste_score'))['taste_score__avg']
    service_avg = FoodComment.objects.filter(shop_id=shop).aggregate(Avg('service_score'))['service_score__avg']

    score_stats = {
        'env': round(env_avg or 0, 1),
        'taste': round(taste_avg or 0, 1),
        'service': round(service_avg or 0, 1),
    }

    # 相似店铺（同菜系+同区县，按评分排序）
    # 修改部分：添加空值检查
    if shop.food_type and shop.county:
        similar_shops = FoodShop.objects.filter(
            food_type=shop.food_type,
            county=shop.county
        ).exclude(shop_id=shop_id).order_by('-shop_score')[:6]
    else:
        similar_shops = FoodShop.objects.none()

    # 如果同菜系同区县不够，补充同菜系不同区县
    if similar_shops.count() < 6 and shop.food_type:
        additional_shops = FoodShop.objects.filter(
            food_type=shop.food_type
        ).exclude(shop_id=shop_id).exclude(
            shop_id__in=[s.shop_id for s in similar_shops]
        ).order_by('-shop_score')[:(6 - similar_shops.count())]
        similar_shops = list(similar_shops) + list(additional_shops)

    from django.conf import settings
    # 修改部分：添加异常处理，防止 BAIDU_MAP_AK 未配置
    try:
        baidu_map_ak = settings.BAIDU_MAP_AK
    except AttributeError:
        baidu_map_ak = None

    return render(request, 'shop_detail.html', {
        'shop': shop,
        'is_collected': is_collected,
        'comments': comments,
        'sentiment_stats': list(sentiment_stats),
        'score_stats': score_stats,
        'similar_shops': similar_shops,
        'baidu_map_ak': baidu_map_ak
    })
# ========== 可视化大屏 ==========

def data_dashboard(request):
    """数据可视化大屏"""
    if not request.user.is_authenticated:
        return redirect('/user/login/')

    from .models import FoodComment
    from datetime import datetime, timedelta

    # KPI指标
    total_shops = FoodShop.objects.count()
    total_comments = FoodComment.objects.count()
    avg_score = round(FoodShop.objects.aggregate(Avg('shop_score'))['shop_score__avg'] or 0, 1)
    avg_price = round(FoodShop.objects.aggregate(Avg('avg_price'))['avg_price__avg'] or 0, 0)

    # Top10店铺
    top10_shops = FoodShop.objects.annotate(
        popularity=models.F('shop_score') * models.F('comment_count')
    ).order_by('-popularity')[:10]

    # 区县分布Top10
    county_data = list(FoodShop.objects.values('county').annotate(
        count=Count('id')
    ).filter(county__isnull=False).exclude(county='').order_by('-count')[:10])

    # 菜系分布Top8
    food_type_data = list(FoodShop.objects.values('food_type').annotate(
        count=Count('id')
    ).order_by('-count')[:8])

    # 评分分布
    score_distribution = {
        'high': FoodShop.objects.filter(shop_score__gte=4.5).count(),
        'mid_high': FoodShop.objects.filter(shop_score__gte=4.0, shop_score__lt=4.5).count(),
        'mid': FoodShop.objects.filter(shop_score__gte=3.0, shop_score__lt=4.0).count(),
        'low': FoodShop.objects.filter(shop_score__lt=3.0).count(),
    }

    # 情感趋势（近5年）
    sentiment_trend_data = []
    existing_years = FoodComment.objects.values_list('publish_year', flat=True).distinct().order_by('publish_year')

    if existing_years:
        years_to_show = list(existing_years)[-5:] if len(existing_years) >= 5 else list(existing_years)

        for year in years_to_show:
            year_data = {
                'year': year,
                'positive': FoodComment.objects.filter(publish_year=year, sentiment='正面').count(),
                'negative': FoodComment.objects.filter(publish_year=year, sentiment='负面').count(),
                'neutral': FoodComment.objects.filter(publish_year=year, sentiment='中性').count()
            }
            sentiment_trend_data.append(year_data)
    else:
        from datetime import datetime
        current_year = datetime.now().year
        for year in range(current_year - 4, current_year + 1):
            sentiment_trend_data.append({
                'year': year,
                'positive': 0,
                'negative': 0,
                'neutral': 0
            })

    # 价格区间分布
    price_ranges = [
        {'label': '0-50元', 'min': 0, 'max': 50, 'color': '#1890ff'},
        {'label': '50-100元', 'min': 50, 'max': 100, 'color': '#52c41a'},
        {'label': '100-200元', 'min': 100, 'max': 200, 'color': '#faad14'},
        {'label': '200-300元', 'min': 200, 'max': 300, 'color': '#f5222d'},
        {'label': '300元以上', 'min': 300, 'max': 99999, 'color': '#722ed1'},
    ]

    price_distribution = []
    for pr in price_ranges:
        count = FoodShop.objects.filter(avg_price__gte=pr['min'], avg_price__lt=pr['max']).count()
        price_distribution.append({
            'label': pr['label'],
            'count': count,
            'color': pr['color']
        })

    # 商圈数据Top10
    business_circle_data = list(FoodShop.objects.values('business_circle').annotate(
        count=Count('id'),
        avg_score=Avg('shop_score')
    ).filter(business_circle__isnull=False).exclude(business_circle='').order_by('-count')[:10])

    # 准备JSON数据
    top10_shops_json = json.dumps([{
        'shop_name': shop.shop_name,
        'shop_score': float(shop.shop_score),
        'comment_count': shop.comment_count,
        'avg_price': float(shop.avg_price) if shop.avg_price else 0,
        'county': shop.county,
        'today_comments_count': 0  # 可以后续添加今日评论统计
    } for shop in top10_shops], ensure_ascii=False)

    food_type_realtime_json = json.dumps([{
        'food_type': item['food_type'],
        'count': item['count'],
        'today_comments': 0  # 可以后续添加今日评论统计
    } for item in food_type_data], ensure_ascii=False)

    county_realtime_json = json.dumps([{
        'county': item['county'],
        'total': item['count']
    } for item in county_data], ensure_ascii=False)

    # 评分趋势数据（模拟，实际应该从历史数据获取）
    avg_score_float = float(avg_score)  # 转换为float类型
    score_trend_json = json.dumps([{
        'date': (datetime.now() - timedelta(days=i)).strftime('%m-%d'),
        'score': round(avg_score_float + (i % 3 - 1) * 0.1, 1)
    } for i in range(30, 0, -1)], ensure_ascii=False)

    # 低评分预警（至少取10条，确保有数据显示）
    low_score_shops = FoodShop.objects.filter(shop_score__lt=3.5).order_by('shop_score')[:10]
    low_score_alerts_json = json.dumps([{
        'shop_name': shop.shop_name,
        'shop_score': float(shop.shop_score),
        'county': shop.county if shop.county else '未知'
    } for shop in low_score_shops], ensure_ascii=False)

    # 情感实时数据（从已分析的评论中获取）
    sentiment_realtime_json = json.dumps({
        'positive': FoodComment.objects.filter(sentiment='正面').count(),
        'negative': FoodComment.objects.filter(sentiment='负面').count(),
        'neutral': FoodComment.objects.filter(sentiment='中性').count()
    }, ensure_ascii=False)

    # 价格分布JSON
    price_distribution_json = json.dumps(price_distribution, ensure_ascii=False)

    # 情感趋势JSON
    sentiment_trend_json = json.dumps(sentiment_trend_data, ensure_ascii=False)

    return render(request, 'data_dashboard.html', {
        'total_shops': total_shops,
        'total_comments': total_comments,
        'avg_score': avg_score,
        'avg_price': avg_price,
        'today_comments': 0,  # 可以后续添加今日评论统计
        'current_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'top10_shops_json': top10_shops_json,
        'food_type_realtime_json': food_type_realtime_json,
        'county_realtime_json': county_realtime_json,
        'score_trend_json': score_trend_json,
        'low_score_alerts_json': low_score_alerts_json,
        'sentiment_realtime_json': sentiment_realtime_json,
        'price_distribution_json': price_distribution_json,
        'score_distribution': score_distribution,
        'sentiment_trend_json': sentiment_trend_json,
        'current_year': datetime.now().year
    })


# 在 views.py 中添加
def shop_map_simple(request):
    """最简单的同步地图页面"""
    from django.conf import settings

    # 只获取必要的数据
    shops = FoodShop.objects.filter(
        longitude__isnull=False,
        latitude__isnull=False
    ).values('shop_id', 'shop_name', 'longitude', 'latitude')[:50]

    shops_json_data = [{
        'id': shop['shop_id'],
        'name': shop['shop_name'],
        'lng': float(shop['longitude']),
        'lat': float(shop['latitude']),
    } for shop in shops]

    return render(request, 'shop_map_simple.html', {
        'shops_json': json.dumps(shops_json_data, ensure_ascii=False),
        'baidu_map_ak': settings.BAIDU_MAP_AK
    })


# ========== AI 助手模块 ==========

def ai_assistant(request):
    """AI 助手主页面 —— 京城味蕾管家"""
    if not request.user.is_authenticated:
        return redirect('/user/login/')

    from .ai_service import get_smart_suggestions
    suggestions = get_smart_suggestions()

    # 获取最近 20 条对话记录（当前用户）
    history = AIChatHistory.objects.filter(user=request.user).order_by('-created_at')[:20]
    history = list(reversed(history))

    return render(request, 'ai_assistant.html', {
        'suggestions': suggestions,
        'history': history,
    })


@require_POST
def ai_chat(request):
    """AI 对话 AJAX 接口，返回 JSON"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': '请先登录'}, status=401)

    try:
        data = json.loads(request.body)
        user_query = data.get('message', '').strip()
    except Exception:
        return JsonResponse({'error': '请求格式错误'}, status=400)

    if not user_query:
        return JsonResponse({'error': '消息不能为空'}, status=400)

    if len(user_query) > 500:
        return JsonResponse({'error': '问题过长，请缩短后再试'}, status=400)

    # 获取用户偏好上下文
    user_context = None
    try:
        profile = request.user.profile
        user_context = profile.to_context_str()
    except UserProfile.DoesNotExist:
        pass

    # 获取近期历史（最多 6 轮）
    recent_history = list(
        AIChatHistory.objects.filter(user=request.user)
        .order_by('-created_at')[:12]
        .values('role', 'content')
    )
    recent_history = list(reversed(recent_history))

    # 调用 DeepSeek
    from .ai_service import call_deepseek_ai
    reply, error = call_deepseek_ai(user_query, user_context, recent_history)

    if error:
        return JsonResponse({'error': error}, status=500)

    # 存储对话历史
    AIChatHistory.objects.create(user=request.user, role='user', content=user_query)
    AIChatHistory.objects.create(user=request.user, role='assistant', content=reply)

    # 只保留最近 100 条，防止无限增长
    old_ids = AIChatHistory.objects.filter(user=request.user).order_by('-created_at')[100:].values_list('id', flat=True)
    if old_ids:
        AIChatHistory.objects.filter(id__in=list(old_ids)).delete()

    return JsonResponse({'reply': reply})


def ai_clear_history(request):
    """清空当前用户 AI 对话历史"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': '请先登录'}, status=401)
    AIChatHistory.objects.filter(user=request.user).delete()
    return JsonResponse({'success': True})


def user_profile_edit(request):
    """用户偏好设置页面"""
    if not request.user.is_authenticated:
        return redirect('/user/login/')

    # 获取或创建用户 Profile
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    msg = None
    msg_type = None

    if request.method == 'POST':
        profile.flavor_pref = request.POST.get('flavor_pref', '').strip()
        profile.dietary_restrictions = request.POST.get('dietary_restrictions', '').strip()
        profile.avg_budget = request.POST.get('avg_budget', '50_150')
        profile.frequent_areas = request.POST.get('frequent_areas', '').strip()
        profile.scene_weight = request.POST.get('scene_weight', 'balanced')
        profile.has_car = request.POST.get('has_car') == 'on'
        profile.has_child = request.POST.get('has_child') == 'on'
        profile.save()
        msg = '偏好设置已保存！AI 助手将为你提供更精准的推荐 🎉'
        msg_type = 'success'

    return render(request, 'user_profile_edit.html', {
        'profile': profile,
        'budget_choices': UserProfile.BUDGET_CHOICES,
        'scene_choices': UserProfile.SCENE_WEIGHT_CHOICES,
        'msg': msg,
        'msg_type': msg_type,
    })


# ========== AI 助手场景偏好保存（AJAX） ==========
@require_POST
def ai_save_scene_pref(request):
    """AI 页面内偏好保存接口，返回 JSON，不跳转"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': '请先登录'}, status=401)
    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({'error': '请求格式错误'}, status=400)

    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    if data.get('flavor_pref') is not None:
        profile.flavor_pref = data['flavor_pref']
    if data.get('dietary_restrictions') is not None:
        profile.dietary_restrictions = data['dietary_restrictions']
    if data.get('avg_budget') is not None:
        profile.avg_budget = data['avg_budget']
    if data.get('frequent_areas') is not None:
        profile.frequent_areas = data['frequent_areas']
    if data.get('scene_weight') is not None:
        profile.scene_weight = data['scene_weight']
    if data.get('has_car') is not None:
        profile.has_car = bool(data['has_car'])
    if data.get('has_child') is not None:
        profile.has_child = bool(data['has_child'])
    profile.save()
    return JsonResponse({'success': True, 'context': profile.to_context_str()})


# ========== 店铺点击记录（热度算法数据） ==========
def shop_click(request, shop_id):
    """记录店铺点击，用于综合人气算法；同时重定向到详情页"""
    if request.user.is_authenticated:
        try:
            shop = FoodShop.objects.get(shop_id=shop_id)
            ShopClickLog.objects.create(user=request.user, shop=shop)
        except FoodShop.DoesNotExist:
            pass
    return redirect(f'/user/shop_detail/{shop_id}/')


# ========== 商家模块 ==========

def merchant_register(request):
    """商家注册/申请成为商家"""
    if not request.user.is_authenticated:
        return redirect('/user/login/')

    profile = getattr(request.user, 'merchant_profile', None)

    msg = None
    msg_type = None

    if request.method == 'POST':
        business_name = request.POST.get('business_name', '').strip()
        contact_phone = request.POST.get('contact_phone', '').strip()
        legal_person_name = request.POST.get('legal_person_name', '').strip()
        id_card_no = request.POST.get('id_card_no', '').strip()
        business_license_no = request.POST.get('business_license_no', '').strip()
        business_address = request.POST.get('business_address', '').strip()
        shop_name = request.POST.get('shop_name', '').strip()
        shop_address = request.POST.get('shop_address', '').strip()
        business_scope = request.POST.get('business_scope', '').strip()
        license_image = request.FILES.get('license_image')
        id_card_front_image = request.FILES.get('id_card_front_image')
        shop_image = request.FILES.get('shop_image')

        required_ok = all([
            business_name, contact_phone, legal_person_name,
            id_card_no, business_license_no, business_address,
            shop_name, shop_address, business_scope
        ])
        required_images_ok = (
            license_image is not None or (profile and profile.license_image)
        ) and (
            id_card_front_image is not None or (profile and profile.id_card_front_image)
        ) and (
            shop_image is not None or (profile and profile.shop_image)
        )

        if not required_ok or not required_images_ok:
            msg = '请完整填写商家主体和店铺资质信息（地址、证照号、证照图片、店铺图片均为必填）'
            msg_type = 'error'
        else:
            if profile is None:
                profile = MerchantProfile(user=request.user)

            profile.business_name = business_name
            profile.contact_phone = contact_phone
            profile.legal_person_name = legal_person_name
            profile.id_card_no = id_card_no
            profile.business_license_no = business_license_no
            profile.business_address = business_address
            profile.shop_name = shop_name
            profile.shop_address = shop_address
            profile.business_scope = business_scope
            if license_image:
                profile.license_image = license_image
            if id_card_front_image:
                profile.id_card_front_image = id_card_front_image
            if shop_image:
                profile.shop_image = shop_image

            profile.qualification_status = 'pending'
            profile.review_note = ''
            profile.reviewed_by = None
            profile.reviewed_at = None
            profile.is_verified = False
            profile.save()

            return redirect('/user/merchant_dashboard/')

    return render(request, 'merchant_register.html', {'msg': msg, 'msg_type': msg_type, 'profile': profile})


def merchant_dashboard(request):
    """商家控制台：查看自己的申请列表"""
    if not request.user.is_authenticated:
        return redirect('/user/login/')
    if not hasattr(request.user, 'merchant_profile'):
        return redirect('/user/merchant_register/')

    applications = ShopApplication.objects.filter(merchant=request.user).order_by('-created_at')
    stats = {
        'total': applications.count(),
        'approved': applications.filter(status='approved').count(),
        'pending': applications.filter(status='pending').count(),
        'rejected': applications.filter(status='rejected').count(),
    }
    return render(request, 'merchant_dashboard.html', {
        'merchant': request.user.merchant_profile,
        'applications': applications,
        'stats': stats,
    })


def merchant_apply_shop(request):
    """商家提交店铺申请"""
    if not request.user.is_authenticated:
        return redirect('/user/login/')
    if not hasattr(request.user, 'merchant_profile'):
        return redirect('/user/merchant_register/')
    if request.user.merchant_profile.qualification_status != 'approved':
        return redirect('/user/merchant_dashboard/')

    msg = None
    msg_type = None

    if request.method == 'POST':
        shop_name       = request.POST.get('shop_name', '').strip()
        food_type       = request.POST.get('food_type', '').strip()
        county          = request.POST.get('county', '').strip()
        business_circle = request.POST.get('business_circle', '').strip()
        location        = request.POST.get('location', '').strip()
        phone           = request.POST.get('phone', '').strip()
        business_hours  = request.POST.get('business_hours', '').strip()
        avg_price_str   = request.POST.get('avg_price', '0').strip()
        description     = request.POST.get('description', '').strip()

        if not shop_name or not food_type or not county or not location:
            msg = '店铺名称、菜系、区县和地址为必填项'
            msg_type = 'error'
        else:
            try:
                avg_price = float(avg_price_str) if avg_price_str else 0
            except ValueError:
                avg_price = 0

            ShopApplication.objects.create(
                merchant=request.user,
                shop_name=shop_name,
                food_type=food_type,
                county=county,
                business_circle=business_circle,
                location=location,
                phone=phone,
                business_hours=business_hours,
                avg_price=avg_price,
                description=description,
            )
            msg = '申请已提交，请等待管理员审核！'
            msg_type = 'success'

    # 可选菜系/区县选项
    food_types = FoodShop.objects.values_list('food_type', flat=True).distinct().exclude(food_type='')
    counties   = FoodShop.objects.values_list('county', flat=True).distinct().exclude(county='')

    return render(request, 'merchant_apply_shop.html', {
        'msg': msg,
        'msg_type': msg_type,
        'food_types': food_types,
        'counties': counties,
    })


def merchant_application_detail(request, app_id):
    """商家查看单个申请详情/进度"""
    if not request.user.is_authenticated:
        return redirect('/user/login/')
    app = get_object_or_404(ShopApplication, id=app_id, merchant=request.user)
    return render(request, 'merchant_application_detail.html', {'app': app})


# ========== 管理员审核模块 ==========

def admin_review_list(request):
    """管理员：查看所有待审核/历史申请"""
    if not request.user.is_authenticated:
        return redirect('/user/login/')
    if not request.user.is_staff:
        return redirect('/user/index/')

    status_filter = request.GET.get('status', 'pending')
    apps = ShopApplication.objects.all()
    if status_filter in ('pending', 'approved', 'rejected'):
        apps = apps.filter(status=status_filter)
    apps = apps.order_by('-created_at')

    counts = {
        'pending':  ShopApplication.objects.filter(status='pending').count(),
        'approved': ShopApplication.objects.filter(status='approved').count(),
        'rejected': ShopApplication.objects.filter(status='rejected').count(),
    }

    return render(request, 'admin_review_list.html', {
        'apps': apps,
        'status_filter': status_filter,
        'counts': counts,
    })


def admin_merchant_review_list(request):
    """管理员：商家资质审核列表"""
    if not request.user.is_authenticated:
        return redirect('/user/login/')
    if not request.user.is_staff:
        return redirect('/user/index/')

    status_filter = request.GET.get('status', 'pending')
    merchants = MerchantProfile.objects.select_related('user').all()
    if status_filter in ('pending', 'approved', 'rejected'):
        merchants = merchants.filter(qualification_status=status_filter)
    merchants = merchants.order_by('-created_at')

    counts = {
        'pending': MerchantProfile.objects.filter(qualification_status='pending').count(),
        'approved': MerchantProfile.objects.filter(qualification_status='approved').count(),
        'rejected': MerchantProfile.objects.filter(qualification_status='rejected').count(),
    }

    return render(request, 'admin_merchant_review_list.html', {
        'merchants': merchants,
        'status_filter': status_filter,
        'counts': counts,
    })


def admin_merchant_review_detail(request, merchant_id):
    """管理员：审核商家资质（通过/驳回）"""
    if not request.user.is_authenticated:
        return redirect('/user/login/')
    if not request.user.is_staff:
        return redirect('/user/index/')

    merchant = get_object_or_404(MerchantProfile, id=merchant_id)

    if request.method == 'POST':
        if request.content_type and 'application/json' in request.content_type:
            try:
                payload = json.loads(request.body or '{}')
            except Exception:
                return JsonResponse({'success': False, 'msg': '请求格式错误'}, status=400)
        else:
            payload = request.POST

        action = payload.get('action')
        note = (payload.get('review_note') or '').strip()
        from django.utils import timezone as tz

        if action == 'approve':
            merchant.qualification_status = 'approved'
            merchant.is_verified = True
            merchant.review_note = note
            merchant.reviewed_by = request.user
            merchant.reviewed_at = tz.now()
            merchant.save()
            return JsonResponse({'success': True, 'msg': '商家资质审核通过'})

        if action == 'reject':
            if not note:
                return JsonResponse({'success': False, 'msg': '请填写驳回原因'}, status=400)
            merchant.qualification_status = 'rejected'
            merchant.is_verified = False
            merchant.review_note = note
            merchant.reviewed_by = request.user
            merchant.reviewed_at = tz.now()
            merchant.save()
            return JsonResponse({'success': True, 'msg': '已驳回商家资质'})

        return JsonResponse({'success': False, 'msg': '无效操作'}, status=400)

    return render(request, 'admin_merchant_review_detail.html', {'merchant': merchant})


def admin_review_detail(request, app_id):
    """管理员：审核单个申请（通过/驳回）"""
    if not request.user.is_authenticated:
        return redirect('/user/login/')
    if not request.user.is_staff:
        return redirect('/user/index/')

    app = get_object_or_404(ShopApplication, id=app_id)

    if request.method == 'POST':
        if request.content_type and 'application/json' in request.content_type:
            try:
                payload = json.loads(request.body or '{}')
            except Exception:
                return JsonResponse({'success': False, 'msg': '请求格式错误'}, status=400)
        else:
            payload = request.POST

        action = payload.get('action')  # 'approve' or 'reject'
        from django.utils import timezone as tz
        import uuid

        if action == 'approve' and app.status == 'pending':
            # 生成唯一 shop_id
            new_shop_id = 'M' + str(uuid.uuid4().hex[:10]).upper()
            shop = FoodShop.objects.create(
                shop_id=new_shop_id,
                shop_name=app.shop_name,
                food_type=app.food_type,
                county=app.county,
                business_circle=app.business_circle or '',
                location=app.location,
                phone=app.phone or '',
                business_hours=app.business_hours or '',
                avg_price=app.avg_price or 0,
                longitude=app.longitude,
                latitude=app.latitude,
                shop_score=0.0,
                comment_count=0,
                michelin='',
                distance_desc='',
                city='北京',
            )
            app.status = 'approved'
            app.approved_shop = shop
            app.reviewed_by = request.user
            app.reviewed_at = tz.now()
            app.save()
            return JsonResponse({'success': True, 'msg': '审核通过，店铺已上架', 'shop_id': new_shop_id})

        elif action == 'reject' and app.status == 'pending':
            reject_reason = (payload.get('reject_reason') or '').strip()
            if not reject_reason:
                return JsonResponse({'success': False, 'msg': '请填写驳回理由'}, status=400)
            app.status = 'rejected'
            app.reject_reason = reject_reason
            app.reviewed_by = request.user
            app.reviewed_at = tz.now()
            app.save()
            return JsonResponse({'success': True, 'msg': '已驳回'})

        return JsonResponse({'success': False, 'msg': '操作无效'}, status=400)

    return render(request, 'admin_review_detail.html', {'app': app})