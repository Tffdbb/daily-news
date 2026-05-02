#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""每日生活资讯采集器 - 覆盖吃住行玩钱"""
import json, re, datetime, os, subprocess, sys, threading, concurrent.futures

CTX = None
try:
    import ssl
    CTX = ssl.create_default_context()
    CTX.check_hostname = False; CTX.verify_mode = ssl.CERT_NONE
except: pass

def curl_fetch(url, timeout_sec=6):
    try:
        r = subprocess.run(['timeout','8','curl','-sL',url,'-A','Mozilla/5.0','--connect-timeout','5','--max-time',str(timeout_sec),'-o','-','-w',''], capture_output=True, timeout=10, text=True)
        return r.stdout
    except: return ''

def urlopen(url, timeout=7):
    try:
        r = __import__('urllib.request', fromlist=['urlopen']).urlopen(__import__('urllib.request', fromlist=['Request']).Request(url, headers={'User-Agent':'Mozilla/5.0'}), timeout=timeout, context=CTX)
        return r.read().decode('utf-8','replace')
    except: return ''

def f_either(url, timeout=6):
    h = curl_fetch(url, timeout)
    if len(h) < 100:
        h2 = urlopen(url, timeout+1)
        if len(h2) > len(h): return h2
    return h

def pat(html, p, mx=5, mn=6):
    s=set();items=[];m=re.finditer(p,html)
    for x in m:
        if len(items)>=mx:break
        t=x.group(1).strip()
        if len(t)>=mn and len(t)<55 and t[:8] not in s and '\u66f4\u591a' not in t and '\u5e7f\u544a' not in t: s.add(t[:8]);items.append(t)
    return items

def lk(html,p,mx=5,mn=8):
    s=set();items=[];m=re.finditer(p,html)
    for x in m:
        if len(items)>=mx:break
        t=x.group(2).strip() if x.lastindex>=2 else '';u=x.group(1).strip()
        if len(t)>=mn and t[:8] not in s: s.add(t[:8]);items.append({'t':t[:50],'u':u})
    return items

# ═══════════════════════════════════════════
# 模块一：💰 钱（财经·工作·消费）
# ═══════════════════════════════════════════

def s1(): # 股市快讯 - 同花顺
    h=f_either('https://news.10jqka.com.cn/tapp/news/push/stock?type=all')
    try: return [{'t':i['title'].strip()[:55],'src':'同花顺','cat':'money','u':'https://www.10jqka.com.cn/'} for i in json.loads(h).get('data',{}).get('list',json.loads(h).get('data',[])) if i.get('title','')][:10]
    except: return []

def s2(): # 实时财经 - 华尔街见闻
    h=f_either('https://api.wallstreetcn.com/apiv1/content/lives?channel=global-channel&limit=10')
    try: return [{'t':(i.get('title') or i.get('content_text','')).replace('<em>','').replace('</em>','').strip()[:55],'src':'华尔街见闻','cat':'money','u':'https://wallstreetcn.com/live/global'} for i in json.loads(h).get('data',{}).get('items',[]) if (i.get('title') or i.get('content_text',''))][:5]
    except: return []

def s3(): # 财联社电报
    i=pat(f_either('https://www.cls.cn/'),r'"title"\s*:\s*"([^"]+)"',5)
    if len(i)<3: i=pat(f_either('https://www.cls.cn/'),r'"content":"([^"]{8,60})"',5)
    return [{'t':t,'src':'财联社','cat':'money','u':'https://www.cls.cn/'} for t in i]

def s4(): # 财经 - 东方财富
    i=lk(f_either('https://www.eastmoney.com/'),r'<a[^>]*href="(https?://[^"]*eastmoney\.com[^"]*)"[^>]*>([^<]{8,50})</a>',4)
    return [{'t':x['t'][:50],'src':'东方财富','cat':'money','u':x['u']} for x in i]

def s5(): # 财经 - 每日经济新闻
    h=f_either('https://www.nbd.com.cn/');i=pat(h,r'"title":"([^"]{6,50})"',3)
    if len(i)<2: i=lk(h,r'<a[^>]*href="(https?://www\.nbd\.com\.cn/[^"]+)"[^>]*>([^<]{8,50})</a>',3)
    return [{'t':t[:45],'src':'每经新闻','cat':'money','u':'https://www.nbd.com.cn/'} for t in i]

def s6(): # 财经 - 新浪财经
    i=lk(f_either('https://finance.sina.com.cn/'),r'<a[^>]*href="(https://finance\.sina\.com\.cn[^"]*)"[^>]*>([^<]{8,45})</a>',4)
    return [{'t':x['t'][:50],'src':'新浪财经','cat':'money','u':x['u']} for x in i if '\u66f4\u591a' not in x['t']]

# ═══════════════════════════════════════════
# 模块二：🏠 住（房产·本地生活·政策）
# ═══════════════════════════════════════════

def s7(): # 网易新闻-社会/政策
    return [{'t':x['t'][:50],'src':'网易新闻','cat':'live','u':x['u']} for x in lk(f_either('https://news.163.com/'),r'<a[^>]*href="(https://news\.163\.com/[^"]+)"[^>]*>([^<]{8,45})</a>',4)]

def s8(): # 政府/政策 - 央视新闻
    i=lk(f_either('https://news.cctv.com/'),r'<a[^>]*href="(https?://news\.cctv\.com[^"]+)"[^>]*>([^<]{8,50})</a>',4)
    return [{'t':x['t'][:50],'src':'央视新闻','cat':'live','u':x['u']} for x in i]

def s9(): # 社会 - 新华网
    i=lk(f_either('https://www.xinhuanet.com/'),r'<a[^>]*href="([^"]+\.htm)"[^>]*>([^<]{8,45})</a>',3)
    return [{'t':x['t'][:50],'src':'新华网','cat':'live','u':x['u'] if x['u'].startswith('http') else 'https://www.xinhuanet.com'+x['u']} for x in i]

def s10(): # 中国新闻网
    i=lk(f_either('https://www.chinanews.com.cn/'),r'<a[^>]*href="(https?://www\.chinanews\.com\.cn[^"]+)"[^>]*>([^<]{8,50})</a>',4)
    return [{'t':x['t'][:50],'src':'中国新闻网','cat':'live','u':x['u']} for x in i]

# ═══════════════════════════════════════════
# 模块三：🍜 吃（餐饮·食品·消费）
# ═══════════════════════════════════════════

def s11(): # 百度热搜（含民生热点）
    h=f_either('https://top.baidu.com/board?tab=realtime');i=[];s=set()
    for p in [r'data-title="([^"]+)"',r'"word":"([^"]+)"']:
        for m in re.finditer(p,h):
            if len(i)>=5:break
            t=m.group(1).strip()
            if len(t)>=4 and t[:8] not in s: s.add(t[:8]);i.append({'t':t[:50],'src':'百度热搜','cat':'life','u':'https://top.baidu.com/'})
    return i

def s12(): # 微博热搜
    h=f_either('https://weibo.com/ajax/side/hotSearch')
    try: j=json.loads(h);items=[];s=set()
    except: return []
    for item in j.get('data',{}).get('realtime',[]):
        t=item.get('word','')
        if t and t[:8] not in s: s.add(t[:8]);items.append({'t':t[:50],'src':'微博热搜','cat':'life','u':'https://weibo.com/'})
        if len(items)>=5:break
    return items

def s13(): # 澎湃新闻（综合）
    i=lk(f_either('https://www.thepaper.cn/'),r'<a[^>]*href="(https?://www\.thepaper\.cn[^"]+)"[^>]*>([^<]{8,50})</a>',4)
    return [{'t':x['t'][:50],'src':'澎湃新闻','cat':'life','u':x['u']} for x in i]

def s14(): # 凤凰网（综合民生）
    i=lk(f_either('https://www.ifeng.com/'),r'<a[^>]*href="(https?://[^"]*ifeng\.com[^"]*)"[^>]*>([^<]{8,45})</a>',4)
    return [{'t':x['t'][:50],'src':'凤凰网','cat':'life','u':x['u']} for x in i if '\u67e5\u770b' not in x['t']]

def s15(): # 环球网（国际视野）
    i=lk(f_either('https://www.huanqiu.com/'),r'<a[^>]*href="(https?://[^"]*huanqiu\.com[^"]*)"[^>]*>([^<]{8,50})</a>',4)
    return [{'t':x['t'][:50],'src':'环球网','cat':'life','u':x['u']} for x in i]

def s16(): # 36氪（消费/科技生活）
    h=f_either('https://36kr.com/');i=pat(h,r'"title":"([^"]{6,50})"',3)
    if len(i)<2: i=pat(h,r'"widgetTitle":"([^"]{6,50})"',3)
    return [{'t':t[:45],'src':'36氪','cat':'life','u':'https://36kr.com/'} for t in i]

# ═══════════════════════════════════════════
# 模块四：🚗 行（出行·交通·城市）
# ═══════════════════════════════════════════

def s17(): # 快科技/IT之家（出行相关科技）
    h=f_either('https://www.ithome.com/');i=lk(h,r'<a[^>]*href="(https?://www\.ithome\.com/\d+[^"]+)"[^>]*>([^<]{8,50})</a>',5)
    return [{'t':x['t'][:50],'src':'IT之家','cat':'travel','u':x['u']} for x in i]

def s18(): # 观察者网（时政交通政策）
    i=lk(f_either('https://www.guancha.cn/'),r'<a[^>]*href="(https?://www\.guancha\.cn/[^"]+)"[^>]*>([^<]{8,50})</a>',4)
    return [{'t':x['t'][:50],'src':'观察者网','cat':'travel','u':x['u']} for x in i]

def s19(): # 第一财经
    h=f_either('https://www.yicai.com/');i=pat(h,r'"title":"([^"]{6,50})"',3)
    return [{'t':t[:45],'src':'第一财经','cat':'travel','u':'https://www.yicai.com/'} for t in i]

# ═══════════════════════════════════════════
# 模块五：🎮 玩（娱乐·体育·游戏·B站）
# ═══════════════════════════════════════════

def s20(): # 新浪体育
    i=lk(f_either('https://sports.sina.com.cn/'),r'<a[^>]*href="(https?://sports\.sina\.com\.cn[^"]+)"[^>]*>([^<]{8,50})</a>',4)
    return [{'t':x['t'][:50],'src':'新浪体育','cat':'play','u':x['u']} for x in i if '\u66f4\u591a' not in x['t']]

def s21(): # 新浪娱乐
    h=f_either('https://ent.sina.com.cn/');i=lk(h,r'<a[^>]*href="(https?://ent\.sina\.com\.cn[^"]+)"[^>]*>([^<]{8,50})</a>',4)
    return [{'t':x['t'][:50],'src':'新浪娱乐','cat':'play','u':x['u']} for x in i if '\u66f4\u591a' not in x['t']]

def s22(): # B站热门
    h=f_either('https://api.bilibili.com/x/web-interface/ranking/v2?rid=0&type=all')
    try: j=json.loads(h);items=[];s=set()
    except: return []
    for v in j.get('data',{}).get('list',[]):
        t=v.get('title','')
        if t and len(t)>=4 and t[:8] not in s: s.add(t[:8]);items.append({'t':t[:50],'src':'B站热门','cat':'play','u':'https://www.bilibili.com/video/'+str(v.get('aid',''))})
        if len(items)>=3:break
    return items

def s23(): # 知乎热门
    h=f_either('https://www.zhihu.com/hot')
    i=pat(h,r'"title":"([^"]{6,50})"',5)
    return [{'t':t,'src':'知乎热门','cat':'play','u':'https://www.zhihu.com/hot'} for t in i]

def s24(): # 知乎推荐（生活/消费）
    h=f_either('https://www.zhihu.com/');i=pat(h,r'"title":"([^"]{6,50})"',3)
    return [{'t':t,'src':'知乎','cat':'play','u':'https://www.zhihu.com/'} for t in i]

# ═══════════════════════════════════════════
# 模块六：🌐 全球视野（宽域国际）
# ═══════════════════════════════════════════

def s25(): # 热门速览
    h=f_either('https://news.163.com/');i=lk(h,r'<a[^>]*href="(https?://[^"]*163\.com[^"]+)"[^>]*>([^<]{8,45})</a>',5)
    return [{'t':x['t'][:50],'src':'网易速览','cat':'global','u':x['u']} for x in i]

def s26(): # 人民网（要闻）
    h=f_either('https://www.people.com.cn/');i=lk(h,r'<a[^>]*href="(http[^"]*people\.com\.[^"]+)"[^>]*>([^<]{8,50})</a>',4)
    return [{'t':x['t'][:50],'src':'人民网','cat':'global','u':x['u']} for x in i]

def s27(): # 雪球（投资/财经社区）
    h=f_either('https://www.xueqiu.com/');i=pat(h,r'"title":"([^"]{6,50})"',3)
    if len(i)<2: i=pat(h,r'"text":"([^"]{6,50})"',3)
    return [{'t':t[:45],'src':'雪球','cat':'global','u':'https://xueqiu.com/'} for t in i]

def s28(): # Donews（科技/商业）
    h=f_either('https://www.donews.com/');i=lk(h,r'<a[^>]*href="(https?://www\.donews\.com/[^"]+)"[^>]*>([^<]{8,50})</a>',4)
    return [{'t':x['t'][:50],'src':'DoNews','cat':'global','u':x['u']} for x in i]

def s29(): # 财联社电报（快讯）
    h=f_either('https://www.cls.cn/telegraph')
    i=pat(h,r'"content":"([^"]{8,60})"',5) or pat(h,r'"title":"([^"]{6,50})"',5)
    return [{'t':t,'src':'财联社电报','cat':'global','u':'https://www.cls.cn/telegraph'} for t in i]

def s30(): # 华尔街实时
    h=f_either('https://wallstreetcn.com/live/global')
    i=pat(h,r'"content_text":"([^"]{8,100})"',5) or pat(h,r'"title":"([^"]{6,50})"',5)
    return [{'t':t[:55],'src':'华尔街实时','cat':'global','u':'https://wallstreetcn.com/live/global'} for t in i]

def _run_src(fn):
    try:
        return fn() or []
    except:
        return []

def main():
    # 分类索引
    sources = [s1,s2,s3,s4,s5,s6,s7,s8,s9,s10,s11,s12,s13,s14,s15,s16,s17,s18,s19,s20,s21,s22,s23,s24,s25,s26,s27,s28,s29,s30]
    news = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as ex:
        futs = {ex.submit(_run_src, fn): i for i, fn in enumerate(sources)}
        try:
            for f in concurrent.futures.as_completed(futs, timeout=60):
                try:
                    items = f.result(timeout=3)
                    if items: news.extend(items)
                except: pass
        except concurrent.futures.TimeoutError:
            for f in futs: f.cancel()
            print('PARALLEL_TIMEOUT')
    
    seen=set();deduped=[]
    for n in news:
        k=n.get('t','')[:10]
        if k and k not in seen and len(n.get('t',''))>=4: seen.add(k);deduped.append(n)
    
    # 静态行情
    stocks=[{'n':'恒生指数','p':'20536.47','c':'-156.35','r':'-0.76%','cls':'down'},{'n':'上证指数','p':'3684.32','c':'13.45','r':'0.37%','cls':'up'},{'n':'深证成指','p':'11842.14','c':'55.82','r':'0.47%','cls':'up'},{'n':'创业板指','p':'2488.65','c':'8.23','r':'0.33%','cls':'up'},{'n':'道琴斯','p':'42918.72','c':'218.34','r':'0.51%','cls':'up'},{'n':'纳斯达克','p':'19217.94','c':'-46.21','r':'-0.24%','cls':'down'},{'n':'标普500','p':'5820.14','c':'14.23','r':'0.25%','cls':'up'},{'n':'日经225','p':'39245.31','c':'-124.56','r':'-0.32%','cls':'down'}]
    forex={'USD':'7.2420','EUR':'7.8321','JPY':'0.0450','GBP':'9.1250','HKD':'0.9280','KRW':'0.0052'}
    
    # 按分类组织（供 generate_site.py 读取）
    grouped = {'money':[],'live':[],'life':[],'travel':[],'play':[],'global':[]}
    for n in deduped:
        cat = n.get('cat','life')
        if cat not in grouped: cat = 'life'
        grouped[cat].append(n)
    
    output={'news':deduped,'groups':grouped,'stocks':stocks,'forex':forex,'labels':[]}
    with open('news_data.json','w',encoding='utf-8') as f:
        json.dump(output,f,ensure_ascii=False)
    
    for k,v in grouped.items():
        print(f'  {k}: {len(v)}')
    print('Done:', len(deduped), 'news')

if __name__ == '__main__':
    main()
