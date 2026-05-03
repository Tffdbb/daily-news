#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""合并采集器 - 合并所有并行采集器的JSON输出，保留分组，新增热卖榜"""
import json, os

def load(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except: return {}

def main():
    news = []
    groups_holder = {}
    shop_items = []
    ranks_from_shop = []
    metals_holder = []
    volumes_holder = []
    quant_holder = []
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
    
    # 2. RSS采集器
    data = load('rss_news.json')
    if 'rss' in data:
        news.extend(data['rss'])
        print(f'RSS: {len(data["rss"])}')
    
    # 3. 垂直领域采集器
    data = load('more_news.json')
    if 'more' in data:
        news.extend(data['more'])
        print(f'垂直: {len(data["more"])}')
    
    # 4. 热议话题采集器
    data = load('shop_news.json')
    if 'shop' in data:
        shop_items = data['shop']
        print(f'热卖榜: {len(shop_items)}')
    if 'ranks' in data:
        ranks_from_shop = data['ranks']
        print(f'排名: {len(ranks_from_shop)}')
    
    # 5. 贵金属+成交额
    data5 = load('metal_volume.json')
    if 'metals' in data5:
        metals_holder = data5['metals']
        print(f'贵金属: {len(metals_holder)}')
    if 'volume' in data5:
        volumes_holder = data5['volume']
        print(f'成交额: {len(volumes_holder)}')
    
    # 6. 量化选股
    data6 = load('quant_picks.json')
    if 'picks' in data6:
        quant_holder = data6['picks']
        print(f'量化选股: {len(quant_holder)}')
    
    # 去重
    seen = set()
    deduped = []
    for n in news:
        key = n.get('t','')[:10]
        if key and key not in seen and len(n.get('t','')) >= 4:
            seen.add(key)
            deduped.append(n)
    
    print(f'→ {len(deduped)} 条')
    
    # 重建分组
    groups = {'finance':[],'macro':[],'hot':[],'tech':[],'oppo':[]}
    for key in groups:
        if key in groups_holder:
            groups[key] = [x for x in groups_holder[key] if x.get('t','')[:10] in seen]
    
    for n in deduped:
        cat = n.get('cat','hot')
        if cat not in groups: cat = 'hot'
        already = False
        for g in groups.values():
            for x in g:
                if x.get('t','')[:10] == n.get('t','')[:10]:
                    already = True
                    break
            if already: break
        if not already:
            groups[cat].append(n)
    
    # 热卖榜去重
    seen_shop = set()
    deduped_shop = []
    for n in shop_items:
        k = n.get('t','')[:10]
        if k and k not in seen_shop:
            seen_shop.add(k)
            deduped_shop.append(n)
    
    output = {'news': deduped, 'groups': groups,
              'shop': deduped_shop,
              'ranks': ranks_from_shop,
              'metals': metals_holder,
              'volumes': volumes_holder,
              'quant': quant_holder,
              'trending': trending_holder,
              'zhihu': zhihu_holder,
              'stocks': stocks_holder or [], 'forex': forex_holder or {},
              'labels': data.get('labels', []) if data else []}
    
    with open('news_data.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False)
    print(f'写入 {len(deduped)} 条, {sum(len(v) for v in groups.values())} 已分组, 热卖 {len(deduped_shop)} 条, Trending {len(trending_holder)}, 知乎 {len(zhihu_holder)}')

if __name__ == '__main__':
    main()
