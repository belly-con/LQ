# 百度地图API配置说明

## 获取百度地图API Key

1. 访问百度地图开放平台：https://lbsyun.baidu.com/
2. 注册/登录账号
3. 进入控制台 -> 应用管理 -> 我的应用
4. 点击"创建应用"
5. 填写应用信息：
   - 应用名称：北京美食分析系统
   - 应用类型：浏览器端
   - 白名单：填写你的域名（开发环境可以填写 `*` 表示允许所有域名）
6. 创建成功后，复制生成的AK（Access Key）

## 配置API Key

有两种方式配置：

### 方式1：在settings.py中直接配置（推荐用于开发环境）

编辑 `bj_food_analysis/settings.py` 文件，找到：

```python
BAIDU_MAP_AK = os.environ.get('BAIDU_MAP_AK', 'YOUR_BAIDU_MAP_AK')
```

将 `YOUR_BAIDU_MAP_AK` 替换为你的实际AK，例如：

```python
BAIDU_MAP_AK = os.environ.get('BAIDU_MAP_AK', 'your_actual_ak_here')
```

### 方式2：使用环境变量（推荐用于生产环境）

在系统环境变量中设置 `BAIDU_MAP_AK`，或者在启动Django前设置：

**Windows (PowerShell):**
```powershell
$env:BAIDU_MAP_AK="your_actual_ak_here"
python manage.py runserver
```

**Linux/Mac:**
```bash
export BAIDU_MAP_AK="your_actual_ak_here"
python manage.py runserver
```

## 功能说明

配置完成后，以下功能将正常使用：

1. **店铺位置地图** (`/user/shop_map/`) - 显示所有店铺在地图上的位置
2. **店铺分布热力图** (`/user/shop_heatmap/`) - 基于店铺位置和评论数的热力图

## 注意事项

- API Key有每日调用次数限制，请根据实际使用情况选择合适的配额
- 生产环境请务必设置白名单，限制API Key的使用域名
- 如果遇到地图无法显示的问题，请检查浏览器控制台的错误信息
