#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""合并采集器 - 合并所有并行采集器的JSON输出，保留分组"""
import json, os

def load(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except: return {}

def main():
    news = []
    groups_holder = {}
    stocks_holder = []
    forex_holder = {}
    
    # 1. 主采集器 (国内新闻带分组)
    data = load('news_data.json')
    if 'news' in data:
        news.extend(data['news'])
        print(f'主采集器: {len(data["news"])}')
    if 'groups' in data and data['groups']:
        groups_holder = data['groups']
    if 'stocks' in data:
        stocks_holder = data.get('stocks', [])
    if 'forex' in data:
        forex_holder = data.get('forex', {})
    
    # 2. RSS采集器 (国际新闻)
    data = load('rss_news.json')
    if 'rss' in data:
        news.extend(data['rss'])
        print(f'RSS: {len(data["rss"])}')
    
    # 3. 垂直领域采集器
    data = load('more_news.json')
    if 'more' in data:
        news.extend(data['more'])
        print(f'垂直: {len(data["more"])}')
    
    # 去重
    seen = set()
    deduped = []
    for n in news:
        key = n.get('t','')[:10]
        if key and key not in seen and len(n.get('t','')) >= 4:
            seen.add(key)
            deduped.append(n)
    
    print(f'→ {len(deduped)} 条')
    
    # 重建分组（从主采集器继承）
    groups = {'finance':[],'macro':[],'hot':[],'tech':[],'oppo':[]}
    for key in groups:
        if key in groups_holder:
            groups[key] = [x for x in groups_holder[key] if x.get('t','')[:10] in seen]
    
    # 对没分组的新闻自动归类
    for n in deduped:
        cat = n.get('cat','hot')
        if cat not in groups: cat = 'hot'
        # 检查是否已经在分组里
        already = False
        for g in groups.values():
            for x in g:
                if x.get('t','')[:10] == n.get('t','')[:10]:
                    already = True
                    break
            if already: break
        if not already:
            groups[cat].append(n)
    
    output = {'news': deduped, 'groups': groups,
              'stocks': stocks_holder or [], 'forex': forex_holder or {},
              'labels': data.get('labels', []) if data else []}
    
    with open('news_data.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False)
    print(f'写入 {len(deduped)} 条, {sum(len(v) for v in groups.values())} 已分组')

if __name__ == '__main__':
    main()
