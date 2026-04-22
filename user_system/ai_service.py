"""
AI 服务模块 —— DeepSeek 驱动的京城味蕾管家
负责：
  1. 构建系统提示词
  2. 从数据库检索相关店铺上下文（RAG）
  3. 调用 DeepSeek API 并返回结果
  4. 时间段智能推荐问题生成
"""
import json
import re
from datetime import datetime
from django.conf import settings
from .models import FoodShop, FoodComment


# ===================== 系统提示词 =====================
SYSTEM_PROMPT = """## 角色设定
你是一位精通北京餐饮市场的智能助手，人称"京城味蕾管家"。你熟悉北京的大街小巷（从王府井到五道口），对各大菜系、店铺评价、排队情况有深刻理解。

## 你的任务
1. **基于数据回答**：用户会提供位置、预算、口味需求，你需要从以下【店铺数据】中筛选最优解，并说明理由。
2. **千人千面**：如果用户信息中包含饮食禁忌（如清真、不吃葱）或偏好（如爱辣、带娃），必须在推荐中首要考虑。
3. **评价脱水**：总结评论时直白指出优点（如：肉质嫩）和槽点（如：环境吵、服务态度差）。
4. **决策辅助**：不只给名字，要告诉用户"为什么选这家"（最近、性价比最高、评分最好等）。
5. **结构化输出**：推荐结果请用 Markdown 格式，每家店用加粗名称开头，换行列出关键信息。

## 语言风格
- 专业、热情、客观，带有轻微的北京特色，保持服务感。
- 逻辑清晰，善用加粗和列表，回答简洁不冗余。

## 约束条件
- 只基于提供的【店铺数据】推荐，严禁编造不存在的地址或电话。
- 拒绝回答与餐饮、北京旅游路线、食品健康完全无关的问题，礼貌转回主题。
- 如果用户需求不明确（如"我想吃好吃的"），请先反问预算、区域或菜系偏好。
- 如果数据库中没有匹配结果，如实告知并建议调整筛选条件。
"""


def _get_hour_suggestions():
    """根据当前时间返回智能推荐问题"""
    hour = datetime.now().hour
    if 6 <= hour < 10:
        return [
            "附近哪家老字号早点铺值得去？",
            "有没有适合边走边吃的北京早餐推荐？",
            "豆汁儿、焦圈哪里最正宗？",
        ]
    elif 10 <= hour < 14:
        return [
            "附近午市套餐性价比最高的是哪家？",
            "帮我找人均50以内、评分高的午餐",
            "有包间的商务午餐，海淀区推荐几家？",
        ]
    elif 14 <= hour < 18:
        return [
            "下午茶甜品店，环境好的有哪些？",
            "适合4人下班聚会的烧烤店，有停车位的？",
            "朝阳区有没有评价好的特色小吃街？",
        ]
    elif 18 <= hour < 22:
        return [
            "今晚聚餐，推荐人均150以内的火锅或烤肉",
            "周末家庭聚餐，有儿童座椅的餐厅哪家好？",
            "适合商务宴请、有包间的高档餐厅推荐",
        ]
    else:
        return [
            "此时此刻还在营业的宵夜推荐",
            "深夜食堂，哪家串串香评价最好？",
            "夜宵外送，评分4.5以上的有哪些？",
        ]


def _build_shop_context(user_query, limit=8):
    """
    RAG 检索：从数据库中提取与查询相关的店铺信息作为上下文
    策略：关键词匹配菜系/区县/商圈，按评分+评论数综合排序
    """
    queryset = FoodShop.objects.all()

    # 提取地理关键词
    area_keywords = ['海淀', '朝阳', '西城', '东城', '丰台', '石景山',
                     '通州', '顺义', '昌平', '大兴', '房山', '怀柔',
                     '密云', '平谷', '延庆', '门头沟',
                     '中关村', '国贸', '望京', '三里屯', '王府井',
                     '西单', '五道口', '上地', '回龙观', '天通苑']
    for kw in area_keywords:
        if kw in user_query:
            queryset = queryset.filter(
                county__icontains=kw
            ) | FoodShop.objects.filter(
                business_circle__icontains=kw
            )
            break

    # 提取菜系关键词
    cuisine_keywords = {
        '川菜': '川菜', '火锅': '火锅', '烤鸭': '烤鸭', '北京菜': '北京菜',
        '粤菜': '粤菜', '湘菜': '湘菜', '日料': '日本料理', '日本': '日本料理',
        '韩餐': '韩国料理', '烤肉': '烤肉', '海鲜': '海鲜', '早点': '早点',
        '早餐': '早点', '面条': '面食', '面食': '面食', '串串': '串串香',
        '烧烤': '烧烤', '甜品': '甜品', '咖啡': '咖啡', '西餐': '西餐',
    }
    for kw, cuisine in cuisine_keywords.items():
        if kw in user_query:
            queryset = queryset.filter(food_type__icontains=cuisine)
            break

    # 提取价格关键词
    price_patterns = [
        (r'人均\s*(\d+)\s*以内', 'lt'),
        (r'(\d+)\s*元以内', 'lt'),
        (r'人均\s*(\d+)', 'approx'),
    ]
    for pattern, mode in price_patterns:
        m = re.search(pattern, user_query)
        if m:
            price = int(m.group(1))
            if mode == 'lt':
                queryset = queryset.filter(avg_price__lte=price)
            else:
                queryset = queryset.filter(avg_price__lte=price * 1.3)
            break

    # 排序：评分 × log(评论数+1) 综合排序，取前 limit 条
    shops = list(
        queryset.order_by('-shop_score', '-comment_count')[:limit]
    )

    if not shops:
        # 无筛选结果时，返回综合热门前8
        shops = list(FoodShop.objects.order_by('-shop_score', '-comment_count')[:limit])

    # 拼接上下文文本
    context_lines = ["【当前可推荐的店铺数据如下，请基于此作答】\n"]
    for i, shop in enumerate(shops, 1):
        michelin_tag = f"🏅米其林{shop.michelin}" if shop.michelin and shop.michelin != '0' else ""
        context_lines.append(
            f"{i}. **{shop.shop_name}** {michelin_tag}\n"
            f"   - 菜系：{shop.food_type} | 区域：{shop.county} {shop.business_circle or ''}\n"
            f"   - 评分：{shop.shop_score}分 | 评论：{shop.comment_count}条 | 人均：{shop.avg_price}元\n"
            f"   - 地址：{shop.location}\n"
            f"   - 电话：{shop.phone or '暂无'} | 营业时间：{shop.business_hours or '请致电确认'}\n"
        )
    return "\n".join(context_lines)


def call_deepseek_ai(user_query, user_context=None, chat_history=None):
    """
    调用 DeepSeek API
    :param user_query: 用户当前问题
    :param user_context: 用户偏好字符串（来自 UserProfile.to_context_str()）
    :param chat_history: 历史对话列表 [{"role": "user"/"assistant", "content": "..."}]
    :return: (ai_reply_str, error_str)
    """
    try:
        from openai import OpenAI
    except ImportError:
        return None, "缺少 openai 依赖，请执行：pip install openai"

    api_key = getattr(settings, 'DEEPSEEK_API_KEY', '')
    if not api_key or api_key == 'your_deepseek_api_key_here':
        return None, "DeepSeek API Key 未配置，请在 settings.py 中填入 DEEPSEEK_API_KEY"

    try:
        client = OpenAI(
            api_key=api_key,
            base_url=getattr(settings, 'DEEPSEEK_BASE_URL', 'https://api.deepseek.com'),
        )

        # 构建店铺上下文（RAG）
        shop_context = _build_shop_context(user_query)

        # 构建用户信息前缀
        user_info = f"【用户偏好】{user_context}\n\n" if user_context else ""

        # 构建消息列表
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        # 加入历史（最多保留最近 6 轮，防止 token 超限）
        if chat_history:
            messages.extend(chat_history[-12:])  # 6轮 = 12条消息

        # 当前用户消息（含店铺上下文）
        messages.append({
            "role": "user",
            "content": f"{user_info}{shop_context}\n\n【用户问题】{user_query}"
        })

        model = getattr(settings, 'DEEPSEEK_MODEL', 'deepseek-chat')
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            stream=False,
            max_tokens=1500,
            temperature=0.7,
        )
        return response.choices[0].message.content, None

    except Exception as e:
        error_msg = str(e)
        if 'authentication' in error_msg.lower() or '401' in error_msg:
            return None, "API Key 无效，请检查 settings.py 中的 DEEPSEEK_API_KEY"
        elif 'connection' in error_msg.lower() or 'timeout' in error_msg.lower():
            return None, "网络连接失败，请检查网络后重试"
        else:
            return None, f"AI 服务暂时不可用：{error_msg}"


def get_smart_suggestions():
    """返回当前时段的智能推荐问题（冷启动）"""
    return _get_hour_suggestions()
