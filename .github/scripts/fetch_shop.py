#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""热卖榜采集器 - 使用无反爬的购物推荐API"""
import json, subprocess, re, urllib.request, urllib.error, ssl

def curl(url):
    try:
        r = subprocess.run(['timeout','10','curl','-sL',url,'-A','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36','--connect-timeout','8','--max-time','10','-o','-','-w',''], capture_output=True, timeout=12, text=True)
        return r.stdout
    except: return ''

_CTX = ssl.create_default_context()
_CTX.check_hostname = False; _CTX.verify_mode = ssl.CERT_NONE
def fallback(url):
    try:
        r = urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0'}), timeout=10, context=_CTX)
        return r.read().decode('utf-8','replace')
    except: return ''

def f(url):
    h = curl(url)
    if len(h) < 100:
        h2 = fallback(url)
        if len(h2) > len(h): return h2
    return h

def collect():
    all_items = []

    # 1. 百度热搜的购物相关热搜词（百度top没有反爬）
    print('  Fetching 百度热搜购物词...')
    h = f('https://top.baidu.com/board?tab=realtime')
    shop_keys = {'手机','电脑','耳机','显卡','降价','新品','发布','上市','抢购','限量','秒杀',
                 '618','双11','特价','打折','补贴','电动车','汽车','空调','冰箱','洗衣机',
                 'iPhone','华为','小米','OPPO','vivo','平板','手环','手表','无人机'}
    for m in re.finditer(r'"word":"([^"]{2,30})"', h):
        t = m.group(1).strip()
        if any(k in t for k in shop_keys):
            if t[:8] not in [x.get('t','')[:8] for x in all_items]:
                all_items.append({'t':'🔍 ' + t, 'src':'购物热搜', 'cat':'shop'})

    # 2. 什么值得买 - 直接抓原始HTML找好价（比JSON稳定）
    print('  Fetching 什么值得买...')
    h = f('https://www.smzdm.com/')
    # 从JSON数据里抓价格/商品
    for m in re.finditer(r'"price":"([^"]{1,10})"', h):
        p = m.group(1)
        if p.replace('.','').isdigit():
            pass  # 记录价格，后面看有没有对应标题
    for m in re.finditer(r'"title":"([^"]{8,60})"', h):
        t = m.group(1).strip()
        # 只保留有 "元"、"价"、"好" 等购物特征的
        t_clean = t.encode('utf-8').decode('unicode_escape') if '\\u' in t else t
        if any(k in t_clean for k in ['元','价','好价']):
            if t_clean[:10] not in [x.get('t','')[:10] for x in all_items]:
                all_items.append({'t':t_clean[:50], 'src':'值得买', 'cat':'shop'})
        if len([x for x in all_items if x['src']=='值得买']) >= 8:
            break

    # 3. 知乎好物推荐/购物话题
    print('  Fetching 知乎购物话题...')
    h = f('https://www.zhihu.com/topics')
    for m in re.finditer(r'<a[^>]*>([^<]{4,20})</a>', h):
        t = m.group(1).strip()
        shop_topic_keywords = ['购物','商品','好物','推荐','测评','穿搭','家居','数码','护肤']
        if any(k in t for k in shop_topic_keywords):
            if t[:8] not in [x.get('t','')[:8] for x in all_items]:
                all_items.append({'t':'📋 ' + t, 'src':'知乎话题', 'cat':'shop'})

    # 4. 新浪科技热词（常含新品发布）
    print('  Fetching 新品发布热搜...')
    h = f('https://news.sina.com.cn/')
    for m in re.finditer(r'<a[^>]*href="[^"]*"[^>]*>([^<]{6,40})</a>', h):
        t = m.group(1).strip()
        shop_words = ['发布','上市','开售','首发','新品','亮相']
        if any(k in t for k in shop_words):
            if t[:10] not in [x.get('t','')[:10] for x in all_items]:
                all_items.append({'t':'📱 ' + t, 'src':'新品', 'cat':'shop'})

    # 去重
    seen=set();deduped=[]
    for item in all_items:
        k = item['t'][:12]
        if k not in seen:
            seen.add(k)
            deduped.append(item)
    return deduped[:15]

if __name__ == '__main__':
    items = collect()
    with open('shop_news.json', 'w', encoding='utf-8') as f:
        json.dump({'shop': items}, f, ensure_ascii=False)
    print(f'Shop collector done: {len(items)} items')
