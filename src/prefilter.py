"""
预过滤模块
在调用 AI 前用关键词快速筛选可能相关的内容，减少 API 调用量
"""

import os
import sys
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import RELEVANCE_KEYWORDS, EXCLUDE_KEYWORDS

# 帖子最大年龄（天数），超过此时间的帖子将被过滤
MAX_POST_AGE_DAYS = 7


def is_post_too_old(item: dict) -> bool:
    """
    检查帖子是否超过最大年龄限制
    
    Args:
        item: 内容项，包含 published 字段
        
    Returns:
        True 如果帖子太旧，应该被过滤
    """
    published = item.get('published', '')
    if not published:
        # 没有发布时间的内容保留（让AI判断）
        return False
    
    try:
        # RSS 的 published 字段通常是 RFC 2822 格式
        # 例如: "Mon, 13 Jan 2025 10:30:00 +0000"
        pub_date = parsedate_to_datetime(published)
        cutoff_date = datetime.now(pub_date.tzinfo) - timedelta(days=MAX_POST_AGE_DAYS)
        return pub_date < cutoff_date
    except Exception:
        # 解析失败的保留
        return False


def pre_filter(items: list) -> list:
    """
    预过滤内容，减少 AI 调用量
    
    规则：
    1. 排除超过 MAX_POST_AGE_DAYS 天的旧帖子
    2. 排除包含 EXCLUDE_KEYWORDS 的内容（明显不相关）
    3. 优先保留包含 RELEVANCE_KEYWORDS 的内容
    4. 对于既不包含排除词也不包含相关词的，也保留（让AI判断）
    
    Args:
        items: 原始内容列表
        
    Returns:
        过滤后的内容列表
    """
    if not items:
        return []
    
    filtered = []
    excluded_by_keyword = 0
    excluded_by_age = 0
    
    for item in items:
        # 检查是否太旧
        if is_post_too_old(item):
            excluded_by_age += 1
            continue
        
        # 合并标题和内容进行检查
        text = (item.get('title', '') + ' ' + item.get('content', '')).lower()
        
        # 检查是否包含排除关键词
        should_exclude = False
        for kw in EXCLUDE_KEYWORDS:
            if kw.lower() in text:
                should_exclude = True
                break
        
        if should_exclude:
            excluded_by_keyword += 1
            continue
        
        # 通过排除检查的内容保留
        filtered.append(item)
    
    # 打印过滤统计
    if excluded_by_age > 0:
        print(f"  [预过滤] 排除 {excluded_by_age} 条超过 {MAX_POST_AGE_DAYS} 天的旧帖子")
    if excluded_by_keyword > 0:
        print(f"  [预过滤] 排除 {excluded_by_keyword} 条明显不相关内容")
    print(f"  [预过滤] 保留 {len(filtered)} 条待分析")
    
    return filtered


def has_relevance_keywords(item: dict) -> bool:
    """检查内容是否包含相关关键词"""
    text = (item.get('title', '') + ' ' + item.get('content', '')).lower()
    return any(kw.lower() in text for kw in RELEVANCE_KEYWORDS)


def prioritize_by_relevance(items: list) -> list:
    """
    按相关性排序，包含相关关键词的排在前面
    这样即使后面的批次失败，前面更相关的内容已经被处理
    """
    with_keywords = []
    without_keywords = []
    
    for item in items:
        if has_relevance_keywords(item):
            with_keywords.append(item)
        else:
            without_keywords.append(item)
    
    return with_keywords + without_keywords
