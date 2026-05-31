#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
降噪模块：在 merge_news.py 之后处理，对接入 news_data.json 做三步降噪
1. 标题相似度去重 (Cosine > 0.85 视为重复)
2. 广度优先去重: 转述版取评分最高者保留
3. 低质量过滤: 标题过短(<4字)/空心标题(纯数字+符号)/纯链接标题
"""
import json, re, sys, os
from collections import defaultdict

# ── 简单 Jaccard 相似度（比 Cosine 轻量，不依赖第三方库）──
def jaccard_similarity(a: str, b: str) -> float:
    """基于3-gram的Jaccard相似度 0~1"""
    def ngrams(s, n=3):
        s = re.sub(r'[^\u4e00-\u9fff\w]', '', s)  # 只保留中文和字母数字
        return set(s[i:i+n] for i in range(len(s)-n+1))
    
    set_a = ngrams(a)
    set_b = ngrams(b)
    
    if not set_a or not set_b:
        return 0.0
    
    intersection = set_a & set_b
    union = set_a | set_b
    return len(intersection) / len(union)


def is_low_quality(item) -> bool:
    """判断一条新闻是否低质量"""
    t = item.get('t', '').strip()
    
    # 标题太短
    if len(t) < 4:
        return True
    
    # 纯数字/符号/英文标题
    if re.match(r'^[\d\s\+\-\.,:;!?/\\%#@&*()\[\]{}"\'<>]+$', t):
        return True
    
    # 模板化标题（常见的RSS灌水模式）
    if re.match(r'^[【\[]?(公告|提示|通知|声明|免责|调研])', t):
        return True
    
    # 只有URL的标题
    if t.startswith('http'):
        return True
    
    return False


def dedup_by_similarity(news, threshold=0.85):
    """标题去重：保留评分最高的版本"""
    # 按评分降序排序，优先保留高分
    scored = sorted(news, key=lambda x: x.get('_vscore', 0), reverse=True)
    
    kept = []
    for item in scored:
        title = item.get('t', '')
        if not title:
            continue
        
        # vs 已保留的每一条
        duplicate = False
        for existing in kept:
            sim = jaccard_similarity(title, existing.get('t', ''))
            if sim >= threshold:
                duplicate = True
                break
        
        if not duplicate:
            kept.append(item)
    
    return kept


def filter_quality(news):
    """过滤低质量条目"""
    return [n for n in news if not is_low_quality(n)]


def main():
    data_path = 'news_data.json'
    if not os.path.exists(data_path):
        print(f'[警告] {data_path} 不存在, 跳过降噪')
        return
    
    with open(data_path, 'r', encoding='utf-8') as f:
        raw = json.load(f)
    
    news = raw.get('news', [])
    groups = raw.get('groups', {})
    
    before = len(news)
    
    # 第一步：低质量过滤
    news = filter_quality(news)
    after_filter = len(news)
    
    # 第二步：标题相似度去重
    news = dedup_by_similarity(news, threshold=0.85)
    after_dedup = len(news)
    
    # 更新
    raw['news'] = news
    
    # 分组数据也做同样的处理（但分组数据按分类保留）
    for cat in list(groups.keys()):
        cat_items = groups[cat]
        cat_before = len(cat_items)
        cat_items = filter_quality(cat_items)
        # 组内去重
        cat_items = dedup_by_similarity(cat_items, threshold=0.90)  # 组内用更严格阈值
        groups[cat] = cat_items
    
    raw['groups'] = groups
    
    # 更新统计
    raw['_stats'] = raw.get('_stats', {})
    raw['_stats']['dedup'] = {
        'before': before,
        'after_filter': after_filter,
        'after_dedup': after_dedup,
        'removed_low_quality': before - after_filter,
        'removed_duplicates': after_filter - after_dedup,
        'cat_removed': sum((len(groups[c]) - len(groups[c])) for c in groups if c in raw.get('groups', {}))
    }
    
    with open(data_path, 'w', encoding='utf-8') as f:
        json.dump(raw, f, ensure_ascii=False, indent=2 if os.environ.get('DEBUG') else None)
    
    print(f'降噪完成: {before}→{after_dedup} 条')
    print(f'  低质量: {before - after_filter} 条')
    print(f'  相似重复: {after_filter - after_dedup} 条')
    print(f'  最终保留: {after_dedup} 条')


if __name__ == '__main__':
    main()
