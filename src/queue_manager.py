"""
队列管理模块
管理待处理内容的优先级队列，使用 JSON 文件存储
"""

import json
import os
from datetime import datetime
from typing import List, Dict

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import RELEVANCE_KEYWORDS

# 队列文件路径
QUEUE_FILE = "data/pending_queue.json"

# 每次处理的数量
ITEMS_PER_RUN = 40


def calculate_relevance_score(item: dict) -> int:
    """
    计算内容的相关性分数
    分数越高，越优先处理
    """
    text = (item.get('title', '') + ' ' + item.get('content', '')).lower()
    score = sum(1 for kw in RELEVANCE_KEYWORDS if kw.lower() in text)
    return score


def load_queue() -> List[Dict]:
    """加载待处理队列"""
    try:
        if os.path.exists(QUEUE_FILE):
            with open(QUEUE_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('queue', [])
    except Exception as e:
        print(f"[警告] 加载队列失败: {e}")
    return []


def save_queue(queue: List[Dict]):
    """保存队列到文件"""
    try:
        os.makedirs(os.path.dirname(QUEUE_FILE), exist_ok=True)
        data = {
            'queue': queue,
            'last_updated': datetime.now().isoformat()
        }
        with open(QUEUE_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[错误] 保存队列失败: {e}")


def add_to_queue(items: List[Dict], processed_ids: set) -> int:
    """
    将新内容添加到队列
    
    Args:
        items: 预过滤后的新内容列表
        processed_ids: 已处理的ID集合（避免重复）
    
    Returns:
        新增的数量
    """
    queue = load_queue()
    existing_ids = {item.get('id') for item in queue}
    
    added_count = 0
    for item in items:
        item_id = item.get('id', item.get('link', ''))
        
        # 跳过已在队列或已处理的
        if item_id in existing_ids or item_id in processed_ids:
            continue
        
        # 计算优先级分数
        score = calculate_relevance_score(item)
        
        # 添加到队列
        queue_item = {
            'id': item_id,
            'type': item.get('type', 'post'),
            'subreddit': item.get('subreddit', ''),
            'title': item.get('title', ''),
            'content': item.get('content', ''),
            'link': item.get('link', ''),
            'author': item.get('author', ''),
            'search_keyword': item.get('search_keyword', ''),
            'relevance_score': score,
            'added_at': datetime.now().isoformat()
        }
        queue.append(queue_item)
        added_count += 1
    
    # 按优先级排序（分数高的在前）
    queue.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
    
    save_queue(queue)
    return added_count


def get_items_to_process(count: int = ITEMS_PER_RUN) -> List[Dict]:
    """
    获取待处理的内容（优先级最高的）
    
    Args:
        count: 获取的数量
    
    Returns:
        待处理的内容列表
    """
    queue = load_queue()
    
    # 取前 count 条（已按优先级排序）
    items = queue[:count]
    
    return items


def remove_from_queue(item_ids: List[str]):
    """
    从队列中移除已处理的内容
    
    Args:
        item_ids: 要移除的ID列表
    """
    queue = load_queue()
    ids_to_remove = set(item_ids)
    
    # 过滤掉已处理的
    new_queue = [item for item in queue if item.get('id') not in ids_to_remove]
    
    save_queue(new_queue)
    
    removed_count = len(queue) - len(new_queue)
    if removed_count > 0:
        print(f"  [队列] 移除 {removed_count} 条已处理内容")


def get_queue_stats() -> Dict:
    """获取队列统计信息"""
    queue = load_queue()
    
    stats = {
        'total': len(queue),
        'by_type': {},
        'by_score': {
            'high': 0,    # score >= 3
            'medium': 0,  # score 1-2
            'low': 0      # score 0
        }
    }
    
    for item in queue:
        # 按类型统计
        item_type = item.get('type', 'post')
        stats['by_type'][item_type] = stats['by_type'].get(item_type, 0) + 1
        
        # 按分数统计
        score = item.get('relevance_score', 0)
        if score >= 3:
            stats['by_score']['high'] += 1
        elif score >= 1:
            stats['by_score']['medium'] += 1
        else:
            stats['by_score']['low'] += 1
    
    return stats
