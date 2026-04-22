# user_system/sentiment_core.py
import jieba
import time
from collections import defaultdict
import re


class EnhancedSentimentAnalyzer:
    """增强版情感分析器"""

    def __init__(self):
        # 初始化jieba
        self.init_jieba()

        # 情感词典
        self.sentiment_dict = self.build_sentiment_dict()

        # 程度副词权重
        self.intensifier_weights = {
            '极其': 2.0, '极度': 2.0, '极端': 2.0, '至为': 2.0,
            '非常': 1.8, '特别': 1.8, '十分': 1.8, '格外': 1.8,
            '很': 1.5, '挺': 1.5, '相当': 1.5, '颇': 1.5,
            '较': 1.3, '比较': 1.3, '稍微': 1.2, '略': 1.1,
            '有点': 1.1, '有些': 1.1, '有点': 1.1,
            '太': 1.7, '过于': 1.7, '过分': 1.7,
            '超级': 1.6, '超': 1.6, '巨': 1.6,
            '更': 1.4, '更加': 1.4, '越': 1.4,
            '尤其': 1.7, '尤为': 1.7, '特别': 1.8,
            '实在': 1.6, '确实': 1.6, '真': 1.6,
            '绝对': 1.9, '完全': 1.9, '全然': 1.9,
            '真是': 1.7, '实在是': 1.7,
            '万分': 1.8, '无比': 1.8, '异常': 1.8,
            '稍稍': 1.2, '略微': 1.2, '微微': 1.1,
            '稍稍': 1.2, '稍许': 1.2,
        }

        # 否定词
        self.negators = {
            '不', '没', '无', '非', '未', '莫', '勿', '毋', '弗',
            '别', '休', '毋', '勿', '莫', '罔', '靡',
            '没有', '不会', '不能', '不可', '不想', '不愿',
            '不至于', '谈不上', '说不上', '算不上',
            '毫无', '毫无', '毫无', '绝不', '绝非',
            '并非', '并无', '从未', '从没',
            '不太', '不太', '不太', '不太',
        }

        # 双重否定词
        self.double_negatives = {
            '不得不', '不能不', '不可不', '不会不', '不是不',
            '无不', '非不', '未不', '莫不', '无不',
        }

        # 转折词
        self.conjunctions = {
            '但是', '可是', '然而', '不过', '却',
            '虽然', '尽管', '即使', '即便',
        }

    def init_jieba(self):
        """初始化jieba分词器"""
        # 添加自定义词典
        custom_words = [
            # 复合情感词
            ('美味可口', 1000), ('物美价廉', 1000), ('物超所值', 1000),
            ('难以下咽', 1000), ('味同嚼蜡', 1000), ('大失所望', 1000),
            ('服务周到', 1000), ('环境优雅', 1000), ('干净整洁', 1000),
            ('态度恶劣', 1000), ('价格昂贵', 1000), ('上菜慢', 1000),

            # 程度副词
            ('极其', 1000), ('非常', 1000), ('特别', 1000),
            ('超级', 1000), ('太', 1000), ('很', 1000),

            # 否定词
            ('不得不', 1000), ('不能不', 1000), ('不是不', 1000),
        ]

        for word, freq in custom_words:
            jieba.add_word(word, freq=freq)

    def build_sentiment_dict(self):
        """构建情感词典"""
        sentiment_dict = {}

        # 正面情感词
        positive_words = {
            # 味道相关
            '好': 0.8, '好吃': 1.0, '美味': 1.0, '可口': 0.9, '香甜': 0.9,
            '鲜': 0.8, '新鲜': 0.9, '美味可口': 1.2, '好吃极了': 1.3,
            '香': 0.8, '香浓': 0.9, '香醇': 0.9, '香气扑鼻': 1.1,
            '爽口': 0.8, '爽脆': 0.8, '爽滑': 0.8,
            '嫩': 0.7, '鲜嫩': 0.9, '滑嫩': 0.9,
            '酥': 0.7, '酥脆': 0.8, '酥软': 0.8,

            # 评价相关
            '棒': 0.9, '很棒': 1.1, '超棒': 1.3, '极棒': 1.4,
            '赞': 0.9, '点赞': 1.0, '大赞': 1.2, '狂赞': 1.4,
            '优秀': 0.9, '优良': 0.8, '优异': 1.0, '优越': 0.9,
            '完美': 1.1, '绝佳': 1.2, '顶级': 1.2, '一流': 1.1,
            '惊艳': 1.2, '惊喜': 1.1, '意外的好': 1.2,

            # 满意度
            '满意': 0.8, '很满意': 1.1, '非常满意': 1.3, '十分满意': 1.2,
            '满足': 0.8, '很满足': 1.1, '非常满足': 1.2,
            '喜欢': 0.7, '很喜欢': 1.0, '特别喜欢': 1.2, '最爱': 1.3,
            '爱上': 1.1, '迷恋': 1.2,

            # 推荐相关
            '推荐': 0.9, '强烈推荐': 1.3, '极力推荐': 1.4, '必推': 1.5,
            '值得': 0.8, '很值得': 1.0, '非常值得': 1.2,
            '回头': 0.9, '再来': 0.9, '还会再来': 1.1, '经常来': 1.0,

            # 价格相关
            '划算': 0.7, '超值': 0.9, '物超所值': 1.1, '性价比高': 1.0,
            '实惠': 0.7, '便宜': 0.6, '经济实惠': 0.9, '物美价廉': 1.1,
            '公道': 0.7, '合理': 0.6,

            # 环境相关
            '干净': 0.7, '整洁': 0.7, '卫生': 0.8, '一尘不染': 1.0,
            '舒适': 0.8, '舒服': 0.8, '惬意': 0.9, '享受': 1.0,
            '优雅': 0.9, '高雅': 0.9, '高端': 0.9, '上档次': 0.9,
            '温馨': 0.8, '浪漫': 0.8, '有情调': 0.9,
            '安静': 0.7, '清静': 0.7, '宁静': 0.7,

            # 服务相关
            '热情': 0.8, '热心': 0.8, '周到': 0.9, '贴心': 1.0,
            '专业': 0.8, '专注': 0.7, '精湛': 0.9, '娴熟': 0.8,
            '快捷': 0.7, '迅速': 0.7, '及时': 0.7, '高效': 0.8,
            '耐心': 0.7, '细心': 0.8, '细致': 0.8, '认真': 0.7,

            # 菜品相关
            '丰富': 0.7, '多样': 0.7, '品种多': 0.7,
            '精致': 0.8, '精美': 0.8, '讲究': 0.8,
            '创新': 0.8, '创意': 0.8, '独特': 0.9,
            '健康': 0.7, '营养': 0.7, '养生': 0.7,
        }

        # 负面情感词
        negative_words = {
            # 味道相关
            '差': -0.8, '很差': -1.1, '极差': -1.4, '差劲': -1.0,
            '难吃': -1.2, '难以下咽': -1.5, '味同嚼蜡': -1.4,
            '不好吃': -1.0, '吃不惯': -0.7, '不合口味': -0.6,
            '怪味': -0.9, '异味': -1.0, '腥味': -0.8, '膻味': -0.8,
            '馊了': -1.4, '变质': -1.3, '不新鲜': -1.0,
            '老': -0.7, '硬': -0.7, '柴': -0.8,
            '咸': -0.6, '太咸': -0.9, '齁咸': -1.1,
            '甜': -0.5, '太甜': -0.8, '腻': -0.7, '油腻': -0.9,
            '辣': -0.5, '太辣': -0.8, '麻辣': -0.6,
            '酸': -0.5, '太酸': -0.8, '酸涩': -0.9,
            '苦': -0.6, '太苦': -0.9, '苦涩': -1.0,

            # 评价相关
            '失望': -0.9, '很失望': -1.2, '大失所望': -1.4,
            '糟糕': -1.0, '很糟糕': -1.3, '极其糟糕': -1.5,
            '失败': -1.0, '很失败': -1.2, '彻底失败': -1.4,
            '不行': -0.8, '不好': -0.9, '不怎么样': -0.8,

            # 价格相关
            '贵': -0.7, '昂贵': -0.9, '天价': -1.2, '宰客': -1.3,
            '不值': -0.8, '不值得': -0.9, '上当': -1.1, '被坑': -1.2,
            '浪费': -0.9, '浪费钱': -1.0, '白花钱': -1.1,

            # 环境相关
            '脏': -0.9, '很脏': -1.2, '肮脏': -1.1, '污秽': -1.3,
            '乱': -0.7, '混乱': -0.9, '杂乱': -0.8, '一团糟': -1.1,
            '吵': -0.6, '嘈杂': -0.8, '喧闹': -0.9, '震耳欲聋': -1.2,
            '拥挤': -0.7, '很挤': -0.8, '人山人海': -0.9,
            '破旧': -0.8, '简陋': -0.7, '寒酸': -0.9,
            '闷': -0.6, '闷热': -0.8, '不透气': -0.7,

            # 服务相关
            '服务差': -1.0, '态度差': -1.1, '恶劣': -1.3,
            '冷漠': -0.8, '冷淡': -0.8, '不耐烦': -0.9,
            '慢': -0.6, '很慢': -0.9, '极慢': -1.2, '龟速': -1.3,
            '等位久': -0.8, '排队久': -0.8, '等半天': -0.9,
            '上菜慢': -0.8, '等菜久': -0.8,
            '敷衍': -0.8, '马虎': -0.7, '草率': -0.8,
            '不专业': -0.8, '业余': -0.7,

            # 菜品相关
            '量少': -0.7, '不够吃': -0.8, '吃不饱': -0.9,
            '单调': -0.6, '品种少': -0.6,
            '不卫生': -1.0, '脏兮兮': -1.1,
            '凉了': -0.7, '冷了': -0.7,
        }

        # 合并词典
        sentiment_dict.update(positive_words)
        sentiment_dict.update(negative_words)

        return sentiment_dict

    def analyze(self, text):
        """分析文本情感"""
        if not text or not isinstance(text, str) or len(text.strip()) < 2:
            return '中性', 0.5

        # 预处理文本
        text = text.strip()

        # 分词
        words = jieba.lcut(text)

        # 初始化
        sentiment_score = 0.0
        effective_words = 0
        negation_stack = []

        i = 0
        while i < len(words):
            current_word = words[i]
            weight = 1.0

            # 检查双重否定词
            if i + 1 < len(words):
                two_word = current_word + words[i + 1]
                if two_word in self.double_negatives:
                    # 双重否定 = 肯定
                    if len(negation_stack) > 0:
                        negation_stack.pop()  # 抵消一个否定
                    i += 2
                    continue

            # 检查是否是否定词
            if current_word in self.negators:
                negation_stack.append(True)
                i += 1
                continue

            # 检查是否是程度副词
            if current_word in self.intensifier_weights:
                weight = self.intensifier_weights[current_word]
                i += 1
                if i >= len(words):
                    break
                current_word = words[i]

            # 检查是否是否定词+程度副词
            if i + 1 < len(words):
                two_word = current_word + words[i + 1]
                if current_word in self.negators and two_word in self.intensifier_weights:
                    negation_stack.append(True)
                    weight = self.intensifier_weights[two_word]
                    i += 2
                    if i >= len(words):
                        break
                    current_word = words[i]

            # 检查是否是转折词
            if current_word in self.conjunctions:
                # 转折词后重置否定栈和权重
                negation_stack = []
                weight = 1.0
                i += 1
                continue

            # 计算情感得分
            if current_word in self.sentiment_dict:
                word_score = self.sentiment_dict[current_word] * weight

                # 应用否定词
                if negation_stack:
                    word_score = -word_score * 0.6  # 否定后权重降低
                    if len(negation_stack) > 0:
                        negation_stack.pop()  # 使用一个否定词

                sentiment_score += word_score
                effective_words += 1

            i += 1

        # 计算最终得分
        if effective_words > 0:
            # 归一化处理
            normalized_score = sentiment_score / (effective_words * 1.2)
            final_score = 0.5 + normalized_score

            # 限制在0-1范围内
            final_score = max(0.0, min(1.0, final_score))
        else:
            final_score = 0.5

        # 情感分类
        if final_score > 0.65:
            sentiment = '正面'
        elif final_score < 0.35:
            sentiment = '负面'
        else:
            sentiment = '中性'

        return sentiment, round(final_score, 4)

    def batch_analyze(self, texts):
        """批量分析"""
        results = []
        for text in texts:
            sentiment, score = self.analyze(text)
            results.append({
                'text': text,
                'sentiment': sentiment,
                'score': score
            })
        return results