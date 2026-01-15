# 部署指南

本项目是一个自动化社交媒体监测和互动工具，可适配不同平台。

---

## 一、项目结构

```
├── .github/workflows/
│   └── monitor.yml          # GitHub Actions 定时任务
├── data/
│   ├── processed_posts.json # 已处理记录
│   └── pending_queue.json   # 待处理队列
├── src/
│   ├── main.py              # 主入口
│   ├── reddit_fetcher.py    # 数据抓取模块
│   ├── gemini_analyzer.py   # AI分析模块（含Prompt）
│   ├── prefilter.py         # 预过滤模块
│   ├── queue_manager.py     # 队列管理
│   └── feishu_notifier.py   # 飞书通知模块
├── config.py                # 配置文件（核心）
└── requirements.txt         # 依赖
```

---

## 二、核心配置项

### 1. config.py - 数据源配置

```python
# ============ 监控目标 ============
SUBREDDITS = [
    "gamedev",        # 子版块列表
    "indiegaming",
    # 添加更多...
]
POSTS_PER_SUBREDDIT = 10    # 每个版块获取帖子数

# ============ 关键词搜索 ============
ENABLE_KEYWORD_SEARCH = True
SEARCH_KEYWORDS = [
    "no code game",   # 搜索关键词
    "AI game maker",
    # 添加更多...
]
SEARCH_RESULTS_PER_KEYWORD = 10

# ============ 产品信息 ============
PRODUCT_NAME = "wefun.ai"
PRODUCT_DESCRIPTION = "产品描述..."

# ============ 预过滤 ============
RELEVANCE_KEYWORDS = [...]  # 相关性关键词（优先处理）
EXCLUDE_KEYWORDS = [...]    # 排除关键词（直接跳过）
```

### 2. gemini_analyzer.py - AI配置

```python
# ============ 模型配置 ============
GEMINI_MODEL = "gemini-2.0-flash-lite"  # 主模型
DEEPSEEK_MODEL = "deepseek-chat"        # 备用模型

# ============ 处理配置 ============
BATCH_SIZE = 20          # 每批处理数量
REQUEST_DELAY = 15.0     # 批次间隔（秒）
MAX_RETRIES = 1          # 重试次数
```

### 3. queue_manager.py - 队列配置

```python
ITEMS_PER_RUN = 40       # 每次运行处理的数量
```

### 4. monitor.yml - 定时配置

```yaml
schedule:
  - cron: '*/30 * * * *'   # 每30分钟运行
```

---

## 三、AI Prompt 模板

位置：`src/gemini_analyzer.py` 中的 `BATCH_ANALYSIS_PROMPT`

```python
BATCH_ANALYSIS_PROMPT = f"""# Role & Persona
You are a scatterbrained, slightly tired indie dev browsing Reddit at 3 AM.

About {PRODUCT_NAME}: {PRODUCT_DESCRIPTION}

# Target Users (ACCEPT):
- Users frustrated with coding/programming
- Users asking for no-code tools
- Beginners wanting help
# ... 更多规则

# Reply Style Rules:
1. lowercase only
2. no transitions
3. fragments ok
4. DO NOT always mention product - only ~20% of time
5. under 50 words
6. sound like real community member

# Output Format
JSON ARRAY: [{{"index": 0, "is_relevant": true, "reason": "...", "reply_draft": "..."}}]
"""
```

---

## 四、环境变量 (GitHub Secrets)

| 名称 | 说明 | 获取方式 |
|------|------|----------|
| `GEMINI_API_KEY` | Google Gemini API | https://aistudio.google.com/app/apikey |
| `DEEPSEEK_API_KEY` | DeepSeek API（备用） | https://platform.deepseek.com/api_keys |
| `FEISHU_WEBHOOK_URL` | 飞书机器人 Webhook | 飞书群 → 设置 → 机器人 → 添加自定义机器人 |

---

## 五、部署步骤

### 1. Fork/克隆仓库
```bash
git clone https://github.com/YOUR_USERNAME/reddit-monitor.git
```

### 2. 修改配置
- 编辑 `config.py` 中的目标平台、关键词、产品信息
- 编辑 `src/gemini_analyzer.py` 中的 Prompt

### 3. 设置 GitHub Secrets
仓库 → Settings → Secrets and variables → Actions → New repository secret

### 4. 启用 GitHub Actions
仓库 → Actions → 点击 "I understand my workflows, go ahead and enable them"

### 5. 手动测试
Actions → Reddit Monitor → Run workflow

---

## 六、适配其他平台

### 替换数据源
修改 `src/reddit_fetcher.py`：
- `fetch_subreddit_posts()` → 替换为目标平台的抓取逻辑
- 使用 RSS、API 或爬虫

### 数据格式
确保返回的数据包含：
```python
{
    'id': '唯一标识',
    'type': 'post',
    'title': '标题',
    'content': '内容',
    'link': '原文链接',
    'author': '作者',
    'subreddit': '来源/分类',  # 可选
}
```

### 修改通知渠道
修改 `src/feishu_notifier.py`：
- 替换为 Slack、Discord、Telegram 等

---

## 七、监控与调试

### 查看运行日志
GitHub → Actions → 点击具体运行记录

### 查看队列状态
`data/pending_queue.json` - 待处理内容

### 查看已处理记录
`data/processed_posts.json` - 已处理ID列表

---

## 八、常见问题

### Q: 429 配额错误
A: Gemini 免费配额用完，会自动切换到 DeepSeek

### Q: 没有收到飞书通知
A: 检查是否有相关内容被识别，查看 Actions 日志

### Q: 定时任务不运行
A: GitHub Actions 在仓库60天无活动后会自动禁用，需手动重新启用

---

## 九、费用估算

| 服务 | 费用 |
|------|------|
| GitHub Actions | 免费（公开仓库） |
| Gemini API | 免费配额有限，超出需付费 |
| DeepSeek API | ¥1/百万tokens，¥10可用很久 |
| 飞书机器人 | 免费 |

---

*最后更新: 2026-01-15*
