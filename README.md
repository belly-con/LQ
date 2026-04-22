# 🍽️ 北京美食分析与推荐系统

一个基于Django框架开发的美食信息管理、数据分析和智能推荐系统，为北京地区的美食爱好者提供全面的店铺信息查询、多维度数据分析、可视化展示和个性化推荐服务。

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Django](https://img.shields.io/badge/Django-5.2.10-green.svg)
![MySQL](https://img.shields.io/badge/MySQL-8.0+-orange.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## ✨ 功能特性

### 👤 用户管理
- ✅ 用户注册/登录/注销
- ✅ 统一的用户中心（整合首页、个人信息、密码修改）
- ✅ 用户权限管理（普通用户/管理员）

### 🍽️ 美食浏览
- ✅ 店铺列表（分页、搜索、多条件筛选）
- ✅ 店铺详情页（完整信息、评分构成、评论、相似店铺）
- ✅ 收藏/取消收藏功能
- ✅ 我的收藏管理

### 📊 数据分析
- ✅ **Top10排行榜**（6个维度：综合人气、评分最高、评论最多、人均最高/最低、米其林推荐）
- ✅ 区县分布分析（柱状图+数据表格）
- ✅ 评分分布统计（饼图+柱状图）
- ✅ 人均消费分析（价格区间+散点图）
- ✅ 菜系类型分析（饼图+柱状图）
- ✅ 商圈分析（Top20商圈统计）

### 📈 数据可视化
- ✅ 店铺分布热力图（百度地图）
- ✅ 评论情感分析（情感分布+趋势图+店铺好评榜）
- ✅ 综合数据图表（菜系分布+评分趋势）
- ✅ **可视化大屏**（全屏暗色主题，KPI+图表展示）

### 🗺️ 地图功能
- ✅ 店铺位置地图（标记点+信息窗口）
- ✅ 地图筛选（区县、商圈）
- ✅ 独立地图页面（iframe嵌入）

### 🤖 智能推荐
- ✅ **协同过滤推荐**（ItemCF算法）
- ✅ **内容相似度推荐**（菜系+区县+价格）
- ✅ **价格区间匹配**
- ✅ **热门推荐**（冷启动）
- ✅ **可解释推荐理由**

### 💬 情感分析（管理员）
- ✅ 批量情感分析任务创建
- ✅ 任务状态实时监控
- ✅ 分析结果统计和可视化
- ✅ 单条评论测试分析

## 🚀 快速开始

### 环境要求

- Python 3.10+
- MySQL 8.0+
- pip 包管理器

### 安装步骤

#### 1. 克隆项目

```bash
git clone <repository-url>
cd bj_food_analysis
```

#### 2. 创建虚拟环境

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

#### 3. 安装依赖

```bash
pip install -r requirements.txt
```

#### 4. 配置数据库

编辑 `bj_food_analysis/settings.py`，修改数据库配置：

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'bj_food_db',          # 数据库名
        'USER': 'root',                 # 数据库用户名
        'PASSWORD': 'your_password',    # 数据库密码
        'HOST': 'localhost',
        'PORT': '3306',
        'OPTIONS': {'charset': 'utf8mb4'}
    }
}
```

#### 5. 创建数据库

在MySQL中创建数据库：

```sql
CREATE DATABASE bj_food_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

#### 6. 执行数据库迁移

```bash
python manage.py makemigrations
python manage.py migrate
```

#### 7. 创建超级管理员

```bash
python manage.py createsuperuser
```

#### 8. 配置百度地图API Key

编辑 `bj_food_analysis/settings.py`，设置百度地图API Key：

```python
BAIDU_MAP_AK = 'your_baidu_map_api_key'
```

> 📝 **获取API Key**: 访问 [百度地图开放平台](https://lbsyun.baidu.com/) 申请

#### 9. 运行开发服务器

```bash
python manage.py runserver
```

#### 10. 访问系统

- 前端系统: http://127.0.0.1:8000/
- 管理员后台: http://127.0.0.1:8000/admin/

## 📁 项目结构

```
bj_food_analysis/
├── bj_food_analysis/          # 项目配置目录
│   ├── settings.py            # 项目配置文件
│   ├── urls.py                # 主URL路由配置
│   ├── wsgi.py                # WSGI配置
│   └── asgi.py                # ASGI配置
│
├── user_system/               # 主应用模块
│   ├── models.py             # 数据模型定义
│   ├── views.py              # 视图函数（业务逻辑）
│   ├── urls.py               # URL路由配置
│   ├── admin.py              # Django后台管理配置
│   ├── sentiment_core.py     # 情感分析核心算法
│   ├── redis_queue.py        # Redis队列管理
│   └── migrations/          # 数据库迁移文件
│
├── templates/                # HTML模板文件
│   ├── base.html            # 基础模板（导航栏）
│   ├── user_center.html     # 用户中心
│   ├── food_list.html       # 店铺列表
│   ├── shop_detail.html     # 店铺详情
│   ├── top10_rankings.html  # Top10排行榜
│   ├── data_dashboard.html  # 可视化大屏
│   └── ...                  # 其他模板
│
├── static/                   # 静态文件目录
│   └── images/              # 图片资源
│
├── manage.py                 # Django管理脚本
├── requirements.txt          # Python依赖包列表
├── README.md                 # 项目说明文档
└── 项目报告.md                # 详细项目报告
```

## 🗄️ 数据库设计

### 核心数据表

1. **food_shop_info** - 店铺信息表
   - 店铺基本信息、位置、评分、价格等

2. **food_comment_info** - 评论信息表
   - 用户评论、评分、情感分析结果

3. **user_shop_collect** - 用户收藏表
   - 用户收藏店铺记录

4. **sentiment_analysis_task** - 情感分析任务表
   - 任务状态、进度、结果

## 🎯 主要功能说明

### 用户中心
访问路径: `/user/user_center/`

整合了用户首页、个人信息和密码修改功能，提供统一的用户管理界面。

### Top10排行榜
访问路径: `/user/top10_popular/`

提供6个维度的排行榜：
- 🔥 综合人气（评论数+评分综合排序）
- ⭐ 评分最高
- 💬 评论最多
- 💰 人均最高
- 💵 人均最低
- ⭐ 米其林推荐

### 可视化大屏
访问路径: `/user/data_dashboard/`

全屏数据可视化展示，包含：
- KPI指标卡片
- Top10人气榜单
- 区县分布图
- 菜系占比图
- 评分分布图
- 情感趋势图

**使用提示**: 按 `ESC` 键退出大屏模式

### 智能推荐
访问路径: `/user/shop_recommendation/`

基于多种算法的个性化推荐：
- 协同过滤（ItemCF）
- 内容相似度
- 价格区间匹配
- 热门推荐

**获得更好推荐**: 收藏3-5家您喜欢的店铺，系统会自动学习您的偏好。

### 地图功能
访问路径: `/user/shop_map/`

- 显示所有店铺位置
- 支持区县和商圈筛选
- 点击标记查看店铺详情

**注意事项**: 
- 需要配置百度地图API Key
- 如果地图无法加载，请关闭VPN/代理

## 🔧 配置说明

### 环境变量（可选）

可以通过环境变量配置敏感信息：

```bash
# Windows PowerShell
$env:BAIDU_MAP_AK="your_api_key"
$env:DB_PASSWORD="your_db_password"

# Linux/Mac
export BAIDU_MAP_AK="your_api_key"
export DB_PASSWORD="your_db_password"
```

### 静态文件配置

开发环境已配置，生产环境需要收集静态文件：

```bash
python manage.py collectstatic
```

## 🐛 常见问题

### Q1: 地图无法加载？
**A**: 
1. 检查是否开启了VPN/代理，建议关闭
2. 确认百度地图API Key已正确配置
3. 检查浏览器控制台（F12）的错误信息
4. 参考 `BAIDU_MAP_SETUP.md` 进行配置

### Q2: 数据库连接失败？
**A**: 
1. 确认MySQL服务已启动
2. 检查数据库配置（用户名、密码、数据库名）
3. 确认数据库已创建

### Q3: 推荐结果为空？
**A**: 
1. 至少收藏2-3家店铺
2. 刷新推荐页面
3. 检查数据库中是否有店铺数据

### Q4: 情感分析功能如何使用？
**A**: 
1. 登录管理员后台
2. 进入情感分析任务管理
3. 创建分析任务
4. 等待任务完成
5. 在前端查看分析结果

## 📚 相关文档

- [项目报告](项目报告.md) - 详细的系统设计和测试报告
- [功能总结](FEATURES_SUMMARY.md) - 功能特性总结
- [升级说明](UPGRADE_SUMMARY.md) - 系统升级记录
- [快速开始](QUICK_START.md) - 快速上手指南
- [百度地图配置](BAIDU_MAP_SETUP.md) - 地图API配置说明

## 🛠️ 开发工具

### 推荐IDE
- PyCharm Professional
- Visual Studio Code
- Cursor

### 数据库管理
- Navicat for MySQL
- MySQL Workbench
- DBeaver

## 📝 更新日志

### v2.0.0 (2026-01-12)
- ✅ 整合用户中心功能
- ✅ 多维度Top10排行榜
- ✅ 可视化大屏优化
- ✅ 推荐算法升级
- ✅ UI/UX全面优化
- ✅ 地图功能修复

### v1.0.0
- ✅ 基础功能实现

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

## 📄 许可证

MIT License

## 👥 作者

北京美食分析系统开发团队

## 🙏 致谢

- Django框架
- ECharts图表库
- 百度地图API
- SimpleUI

---

**如有问题，请查看文档或提交Issue**
