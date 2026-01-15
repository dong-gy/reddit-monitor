"""
Reddit监测工具 - 主入口
队列处理模式：收集 → 预过滤 → 入队 → 取40条 → AI分析 → 发飞书

每30分钟运行一次，每次只处理40条（2批），分散API压力
"""

import os
import sys
import time
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.reddit_fetcher import fetch_all_new_posts, load_processed_posts, save_processed_posts
from src.gemini_analyzer import analyze_batch, BATCH_SIZE, REQUEST_DELAY
from src.prefilter import pre_filter
from src.queue_manager import (
    add_to_queue, get_items_to_process, remove_from_queue, 
    get_queue_stats, ITEMS_PER_RUN
)
from src.feishu_notifier import send_batch_to_feishu, send_summary_to_feishu


def count_by_type(items: list) -> dict:
    """统计各类型内容数量"""
    counts = {'post': 0, 'comment': 0, 'search': 0}
    for item in items:
        t = item.get('type', 'post')
        counts[t] = counts.get(t, 0) + 1
    return counts


def chunk_list(items: list, chunk_size: int) -> list:
    """将列表分成固定大小的块"""
    return [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]


def main():
    """主函数 - 队列处理模式"""
    print("=" * 60)
    print(f"Reddit监测工具启动 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 检查环境变量
    if not os.environ.get('GEMINI_API_KEY'):
        print("[错误] 请设置 GEMINI_API_KEY 环境变量")
        sys.exit(1)
    
    if not os.environ.get('FEISHU_WEBHOOK_URL'):
        print("[错误] 请设置 FEISHU_WEBHOOK_URL 环境变量")
        sys.exit(1)
    
    # 加载已处理记录
    processed_ids = load_processed_posts()
    
    # ========== 阶段1: 收集新内容 ==========
    print("\n📡 阶段1: 收集Reddit新内容...")
    new_items = fetch_all_new_posts()
    
    fetch_stats = count_by_type(new_items) if new_items else {}
    
    if new_items:
        # 预过滤
        print("\n🔍 预过滤...")
        filtered_items = pre_filter(new_items)
        
        # 加入队列
        if filtered_items:
            added = add_to_queue(filtered_items, processed_ids)
            print(f"  [队列] 新增 {added} 条待处理内容")
    else:
        print("  没有新内容")
    
    # 显示队列状态
    queue_stats = get_queue_stats()
    print(f"\n📋 队列状态: 共 {queue_stats['total']} 条待处理")
    if queue_stats['total'] > 0:
        print(f"   - 高优先级(≥3): {queue_stats['by_score']['high']} 条")
        print(f"   - 中优先级(1-2): {queue_stats['by_score']['medium']} 条")
        print(f"   - 低优先级(0): {queue_stats['by_score']['low']} 条")
    
    # ========== 阶段2: 处理队列 ==========
    print(f"\n🤖 阶段2: 处理队列（最多 {ITEMS_PER_RUN} 条）...")
    
    # 获取待处理内容
    items_to_process = get_items_to_process(ITEMS_PER_RUN)
    
    if not items_to_process:
        print("  队列为空，无需处理")
        print("\n✅ 运行完成!")
        return
    
    print(f"  本次处理 {len(items_to_process)} 条")
    
    # 分批处理
    batches = chunk_list(items_to_process, BATCH_SIZE)
    total_batches = len(batches)
    
    print(f"  分 {total_batches} 批，每批 {BATCH_SIZE} 条，间隔 {REQUEST_DELAY} 秒")
    print("-" * 50)
    
    # 统计
    total_relevant = 0
    total_sent = 0
    processed_item_ids = []
    relevant_stats = {'post': 0, 'comment': 0, 'search': 0}
    
    for batch_idx, batch_items in enumerate(batches):
        batch_num = batch_idx + 1
        
        # 分析当前批次
        results = analyze_batch(batch_items, batch_num)
        
        # 处理分析结果
        relevant_in_batch = []
        for result in results:
            if not isinstance(result, dict):
                continue
            
            idx = result.get('index')
            if idx is None or idx >= len(batch_items):
                continue
            
            if result.get('is_relevant', False):
                item = batch_items[idx].copy()
                item['analysis'] = {
                    'is_relevant': True,
                    'reason': result.get('reason', ''),
                    'reply_draft': result.get('reply_draft', '')
                }
                relevant_in_batch.append(item)
                
                # 更新统计
                content_type = item.get('type', 'post')
                relevant_stats[content_type] = relevant_stats.get(content_type, 0) + 1
        
        # 立即发送飞书通知
        if relevant_in_batch:
            sent = send_batch_to_feishu(relevant_in_batch)
            total_sent += sent
            total_relevant += len(relevant_in_batch)
            print(f"  批次 {batch_num}: 发现 {len(relevant_in_batch)} 条相关，已发送飞书")
        else:
            print(f"  批次 {batch_num}: 无相关内容")
        
        # 记录已处理的ID
        for item in batch_items:
            item_id = item.get('id', '')
            if item_id:
                processed_item_ids.append(item_id)
                processed_ids.add(item_id)
        
        # 每批处理后立即保存（增量保存）
        save_processed_posts(processed_ids)
        
        # 如果不是最后一批，等待
        if batch_num < total_batches:
            print(f"  等待 {REQUEST_DELAY} 秒...")
            time.sleep(REQUEST_DELAY)
    
    print("-" * 50)
    
    # 从队列中移除已处理的
    remove_from_queue(processed_item_ids)
    
    # 发送汇总通知
    if total_relevant > 0:
        print("\n📤 发送汇总通知...")
        send_summary_to_feishu({
            'total': len(items_to_process),
            'relevant': total_relevant,
            'sent': total_sent,
            'queue_remaining': queue_stats['total'] - len(processed_item_ids),
            'relevant_posts': relevant_stats.get('post', 0),
            'relevant_comments': relevant_stats.get('comment', 0),
            'relevant_search': relevant_stats.get('search', 0),
        })
    
    # 最终队列状态
    final_stats = get_queue_stats()
    
    # 完成
    print("\n" + "=" * 60)
    print("✅ 运行完成!")
    print(f"   本次处理: {len(items_to_process)} 条")
    print(f"   相关内容: {total_relevant} 条")
    print(f"   成功推送: {total_sent} 条")
    print(f"   队列剩余: {final_stats['total']} 条")
    print("=" * 60)


if __name__ == "__main__":
    main()
