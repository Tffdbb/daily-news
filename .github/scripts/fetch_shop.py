#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""热卖榜采集器 - 购物热搜/好价"""
import json, subprocess, re

def curl(url):
    try:
        r = subprocess.run(['timeout','10','curl','-sL',url,'-A','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36','--connect-timeout','8','--max-time','10','-o','-','-w',''], capture_output=True, timeout=12, text=True)
        return r.stdout
    except: return ''

def collect():
    all_items = []

    # 1. 百度热搜 - 看有没有购物相关的热搜词
    print('  Fetching 百度热搜...')
    h = curl('https://top.baidu.com/board?tab=realtime')
    for m in re.finditer(r'"word":"([^"]{4,30})"', h):
        t = m.group(1).strip()
        # 只取看起来像购物的热搜
        shop_keywords = ['手机','电脑','耳机','显卡','降价','新品','发布','上市','开售','抢购','限量','秒杀','补贴','降价','618','双11','特价','打折','优惠']
        if any(k in t for k in shop_keywords):
            if t[:8] not in [x.get('t','')[:8] for x in all_items]:
                all_items.append({'t':t[:40], 'src':'百度热搜', 'cat':'shop'})

    # 2. 京东热词 - 通过搜索建议
    print('  Fetching 京东热词...')
    h = curl('https://www.jd.com/')
    # 京东热词（在页面里的hotwords）
    for m in re.finditer(r'<a[^>]*class="[^"]*hotwords[^"]*"[^>]*>([^<]{4,30})</a>', h, re.DOTALL):
        t = m.group(1).strip()
        t = re.sub(r'<[^>]+>', '', t)
        if len(t) >= 4:
            if t[:8] not in [x.get('t','')[:8] for x in all_items]:
                all_items.append({'t':'🛒 ' + t, 'src':'京东热词', 'cat':'shop'})
    
    # 3. 什么值得买 - 好价头条
    print('  Fetching 什么值得买...')
    h = curl('https://www.smzdm.com/')
    # 用正则找好价标题
    for m in re.finditer(r'"title":"([^"]{6,60})"', h):
        t = m.group(1).strip()
        t = re.sub(r'\\u[0-9a-fA-F]{4}', '', t)  # 清理 unicode 转义
        if not t or len(t) < 6: continue
        if any(x in t for x in ['会员','广告','优惠券','签到','抽奖']): continue
        if '价格' in t or '元' in t or '券' in t or '降价' in t or '好价' in t:
            k = t[:10]
            if k not in [x.get('t','')[:10] for x in all_items]:
                all_items.append({'t':t[:50], 'src':'值得买好价', 'cat':'shop'})

    # 4. 小红书热词 - 通过搜索
    print('  Fetching 小红书热词...')
    h = curl('https://www.xiaohongshu.com/')
    for m in re.finditer(r'"title":"([^"]{4,40})"', h):
        t = m.group(1).strip()
        shop_words = ['测评','好物','推荐','开箱','必买','种草','穿搭','护肤','美妆']
        if any(k in t for k in shop_words):
            k = t[:10]
            if k not in [x.get('t','')[:10] for x in all_items]:
                all_items.append({'t':t[:40], 'src':'小红书好物', 'cat':'shop'})
                if len([x for x in all_items if x.get('src')=='小红书好物']) >= 4:
                    break

    # 去重
    seen=set();deduped=[]
    for item in all_items:
        k = item['t'][:10]
        if k not in seen:
            seen.add(k)
            deduped.append(item)
    return deduped[:15]

if __name__ == '__main__':
    items = collect()
    with open('shop_news.json', 'w', encoding='utf-8') as f:
        json.dump({'shop': items}, f, ensure_ascii=False)
    print(f'Shop collector done: {len(items)} items')
