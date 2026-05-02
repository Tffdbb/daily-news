#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""合并采集器 - 合并所有并行采集器的JSON输出"""
import json, os

def load(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except: return {}

def main():
    news = []
    
    # 1. 主采集器 (国内新闻)
    data = load('news_data.json')
    if 'news' in data:
        news.extend(data['news'])
        print(f'主采集器: {len(data["news"])} items')
    # also handle flat structure (fetch_news.py outputs {"news":...})
    
    # 2. RSS采集器 (国际新闻)
    data = load('rss_news.json')
    if 'rss' in data:
        news.extend(data['rss'])
        print(f'RSS采集器: {len(data["rss"])} items')
    
    # 3. 垂直领域采集器  
    data = load('more_news.json')
    if 'more' in data:
        news.extend(data['more'])
        print(f'垂直采集器: {len(data["more"])} items')
    
    # If all failed, try loading legacy fallback
    if not news:
        print('WARN: all collectors returned empty, trying legacy news_data...')
    
    # 去重 (by first 10 chars of title)
    seen = set()
    deduped = []
    for n in news:
        key = n.get('t','')[:10]
        if key and key not in seen and len(n.get('t','')) >= 4:
            seen.add(key)
            deduped.append(n)
    
    print(f'\n合并后: {len(news)} raw → {len(deduped)} deduped')
    
    # 写入最终news_data.json (供generate_site.py使用)
    output = {'news': deduped}
    
    # 保留行情/汇率数据 (从主采集器)
    main_data = load('news_data.json')
    for key in ['stocks', 'forex', 'labels']:
        if key in main_data and main_data[key]:
            output[key] = main_data[key]
    if 'stocks' not in output or not output.get('stocks'):
        output['stocks'] = []
    if 'forex' not in output or not output.get('forex'):
        output['forex'] = {}
    if 'labels' not in output:
        output['labels'] = []
    
    with open('news_data.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False)
    print(f'写入 news_data.json: {len(deduped)} 条新闻')

if __name__ == '__main__':
    main()
