"""
Reddit监测工具配置文件
"""

# ============ Subreddit 监控配置 ============

# 要监控的Subreddit列表（独立开发者与SaaS相关）
SUBREDDITS = [
    "indiehackers",       # 独立开发者/创业者社区
    "SaaS",              # 软件即服务产品讨论
    "Entrepreneur",      # 创业者通用社区
    "NoCode",            # 无代码/低代码开发
    "Productivity",      # 效率工具与方法
    "Freelance",         # 自由职业者需求
    "AppIdeas",          # 应用创意与反馈
    "Startup",           # 初创公司与产品
]

# 每个Subreddit获取的帖子数量
POSTS_PER_SUBREDDIT = 10

# ============ 评论监控配置 ============

# 是否监控评论（关闭以提高速度）
MONITOR_COMMENTS = False

# 每个Subreddit获取的评论数量
COMMENTS_PER_SUBREDDIT = 25

# ============ 关键词搜索配置 ============

# 是否启用关键词全站搜索
ENABLE_KEYWORD_SEARCH = True

# 搜索关键词列表（精简为核心关键词，聚焦产品需求）
SEARCH_KEYWORDS = [
    "best tool for",
    "looking for a tool that",
    "is there a tool that",
    "SaaS idea",
    "how to automate",
    "no code solution",
    "workflow automation",
    "frustrated with",
    "best way to manage",
    "recommendations for"
]

# 每个关键词获取的搜索结果数量
SEARCH_RESULTS_PER_KEYWORD = 10

# ============ 产品信息 ============

PRODUCT_NAME = "YourSaaSProduct"
PRODUCT_DESCRIPTION = "一个通用的独立开发SaaS产品或效率工具"

# ============ 预过滤配置 ============

# 相关性关键词（包含这些词的内容更可能相关）
RELEVANCE_KEYWORDS = [
    # 痛点与需求词
    'frustrated', 'hate to', "can't find", "wish there was", 
    'struggling with', 'annoying', 'tedious', 'manual work',
    'recommend', 'looking for', 'best way', 'how do I',
    'what do you use', 'tool', 'software', 'app', 'solution',
    'workflow', 'process', 'manage', 'organize', 'track',
    'automation', 'save time', 'scale', 'growth'
]

# 排除关键词（只排除最明确不相关的内容）
EXCLUDE_KEYWORDS = [
    'job', 'hiring', 'looking for developer', 'freelancer needed',  # 招聘/外包
    'just launched', 'check out my product', 'showerthoughts',      # 纯推广/闲聊
    'NSFW', 'sale', 'black friday', 'promo',                      # 促销/成人内容
    'API', 'SDK', 'documentation', 'backend'                      # 技术文档/底层开发
]

# ============ 存储配置 ============

# 已处理帖子记录文件路径
PROCESSED_POSTS_FILE = "data/processed_posts.json"

# 最大保留的已处理帖子数量（防止文件过大）
MAX_PROCESSED_POSTS = 5000
