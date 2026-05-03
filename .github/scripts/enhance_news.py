#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""内容增强：标题去噪、分类修正、质量评分"""
import json, re

# 高质关键词（加分）
QUALITY_KW = set(['突破','首次','发布','重磅','涨停','新高','风向','关键','紧急','独家','聚焦','深度',
                  '核弹','里程碑','首款','落地','获批','投产'])
# 低质模式（降分或移除）
LOW_PATTERNS = [
    (r'^.{2,4}：.{0,8}日报', '简报'),
    (r'^.{2,6}快讯', '快讯'),
    (r'^.{2,6}早报', '早报'),
    (r'^.{2,6}晚报', '晚报'),
    (r'直播[^]{0,4}>\d+', '直播'),
    (r'^[【\[][^】\]]{2,6}[】\]]', '标签'),
]

def enhance_item(item):
    """对单条新闻进行增强"""
    t = item.get('t','')
    if not t:
        return None
    
    # 1. 清洗：去掉多余空格、乱码
    t = re.sub(r'\s+', ' ', t).strip()
    # 去掉开头无意义的短词
    t = re.sub(r'^报名|直播|快讯|投票|\d{1,2}月\d{1,2}日', '', t).strip()
    # 去掉末尾无意义
    t = re.sub(r'\s*\【[^】]*\】\s*$', '', t).strip()
    
    if len(t) < 6:
        return None
    
    item['t'] = t[:50]
    
    # 2. 质量评分（0-100）
    score = 50
    for k in QUALITY_KW:
        if k in t:
            score += 10
    for p, label in LOW_PATTERNS:
        if re.search(p, t):
            score -= 15
    
    # 长度适中加分
    if 12 <= len(t) <= 35:
        score += 10
    elif len(t) < 8:
        score -= 20
    
    item['_score'] = min(100, max(0, score))
    return item

def classify_item(item):
    """智能分类修正"""
    t = item.get('t','')
    cat = item.get('cat','hot')
    
    # 关键词分类
    tech_kw = ['AI','大模型','芯片','苹果','华为','小米','科技','网络','数据','智能',
               '手机','电脑','汽车','新能源','机器','软件','算法','算力','数字化','5G','6G']
    finance_kw = ['涨停','跌停','A股','股市','基金','银行','保险','债券','投资','理财',
                  '融资','上市','退市','量化','ETF','市值','板块','券商','期货']
    macro_kw = ['政策','央行','降息','加息','GDP','CPI','PMI','宏观','经济','财政',
                '出口','进口','关税','储备','国债','人民币','美元','欧元']
    oppo_kw = ['机会','风向','赛道','蓝海','增长','扩张','布局','潜力','战略','未来']
    
    # 按优先级分类
    for kw in tech_kw:
        if kw in t: return 'tech'
    for kw in macro_kw:
        if kw in t and cat != 'finance': return 'macro'
    for kw in oppo_kw:
        if kw in t: return 'oppo'
    for kw in finance_kw:
        if kw in t: return 'finance'
    
    return cat

def main():
    # 读取原始数据
    with open('news_data.json', 'r', encoding='utf-8') as f:
        raw = json.load(f)
    
    changed = 0
    total = 0
    
    # 增强所有新闻
    news = []
    for item in raw.get('news', []):
        total += 1
        ei = enhance_item(item)
        if ei:
            ei['cat'] = classify_item(ei)
            news.append(ei)
            if ei['_score'] >= 50:
                changed += 1
    
    # 增强分组数据
    groups = raw.get('groups', {})
    for cat in groups:
        new_items = []
        for item in groups[cat]:
            ei = enhance_item(item)
            if ei:
                ei['cat'] = classify_item(ei)
                new_items.append(ei)
        groups[cat] = new_items
    
    raw['news'] = news
    raw['groups'] = groups
    
    # 写入
    with open('news_data.json', 'w', encoding='utf-8') as f:
        json.dump(raw, f, ensure_ascii=False)
    
    # 统计低质新闻
    low_quality = [n for n in news if n.get('_score',0) < 40]
    
    print(f'增强完成: {total}条 → {len(news)}条保留')
    print(f'质量合格: {changed}条')
    print(f'低质过滤: {len(low_quality)}条')
    if low_quality:
        print(f'低质示例:')
        for n in low_quality[:5]:
            print(f'  [{n["_score"]}] {n["t"][:30]}')
    
    # 分类分布
    cat_dist = {}
    for n in news:
        c = n.get('cat','hot')
        cat_dist[c] = cat_dist.get(c,0)+1
    print(f'分类分布: {cat_dist}')

if __name__ == '__main__':
    main()
