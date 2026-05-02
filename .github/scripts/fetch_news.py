#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""每日价值资讯V2 - 精选高质量源"""
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

def pat_u(html, p, mx=5):
    s=set();items=[]
    for m in re.finditer(p,html):
        if len(items)>=mx:break
        t=m.group(2).strip();u=m.group(1).strip()
        if len(t)>=6 and t[:8] not in s: s.add(t[:8]);items.append({'t':t[:55],'u':u})
    return items

# ════ 📈 投资·财经（核心板块-最多源）════

def s1():
    h=f_either('https://news.10jqka.com.cn/tapp/news/push/stock?type=all')
    try:
        items=[]
        for i in json.loads(h).get('data',{}).get('list',json.loads(h).get('data',[])):
            t=(i.get('title') or '').strip()
            if t and len(t)>=5: items.append({'t':t[:55],'src':'同花顺','cat':'finance','u':'https://www.10jqka.com.cn/'})
        return items[:12]
    except: return []

def s2():
    h=f_either('https://api.wallstreetcn.com/apiv1/content/lives?channel=global-channel&limit=15')
    try:
        items=[]
        for i in json.loads(h).get('data',{}).get('items',[]):
            t=(i.get('title') or i.get('content_text','')).replace('<em>','').replace('</em>','').strip()
            if t and len(t)>=5: items.append({'t':t[:55],'src':'华尔街见闻','cat':'finance','u':'https://wallstreetcn.com/live/global'})
        return items[:8]
    except: return []

def s3():
    i=pat(f_either('https://www.cls.cn/'),r'"title"\s*:\s*"([^"]+)"',8) or pat(f_either('https://www.cls.cn/'),r'"content":"([^"]{8,60})"',8)
    return [{'t':t,'src':'财联社','cat':'finance','u':'https://www.cls.cn/'} for t in i]

def s4():
    h=f_either('https://www.eastmoney.com/')
    i=pat_u(h,r'<a[^>]*href="(https?://[^"]*eastmoney\.com[^"]*)"[^>]*>([^<]{8,50})</a>',6) or pat_u(h,r'"title":"([^"]{6,50})"',6)
    if i: return [{'t':x['t'][:50],'src':'东方财富','cat':'finance','u':x['u']} for x in i]
    return [{'t':t[:45],'src':'东方财富','cat':'finance','u':'https://www.eastmoney.com/'} for t in pat(h,r'"title":"([^"]{6,50})"',6)]

def s5():
    h=f_either('https://www.nbd.com.cn/')
    i=pat(h,r'"title":"([^"]{6,50})"',5) or pat(h,r'"articleTitle":"([^"]{6,50})"',5)
    return [{'t':t[:45],'src':'每经新闻','cat':'finance','u':'https://www.nbd.com.cn/'} for t in i]

def s6():
    i=pat_u(f_either('https://finance.sina.com.cn/'),r'<a[^>]*href="(https://finance\.sina\.com\.cn[^"]*)"[^>]*>([^<]{8,45})</a>',6)
    return [{'t':x['t'][:50],'src':'新浪财经','cat':'finance','u':x['u']} for x in i if '\u66f4\u591a' not in x['t']]

def s7():
    h=f_either('https://www.yicai.com/')
    i=pat(h,r'"title":"([^"]{6,50})"',6) or pat(h,r'"name":"([^"]{6,50})"',6)
    return [{'t':t[:45],'src':'第一财经','cat':'finance','u':'https://www.yicai.com/'} for t in i]

def s8():
    i=pat_u(f_either('https://money.163.com/'),r'<a[^>]*href="(https?://money\.163\.com/[^"]+)"[^>]*>([^<]{8,50})</a>',6)
    return [{'t':x['t'][:50],'src':'网易财经','cat':'finance','u':x['u']} for x in i]

def s9():
    h=f_either('https://www.xueqiu.com/')
    i=pat(h,r'"title":"([^"]{6,50})"',5) or pat(h,r'"text":"([^"]{8,60})"',5)
    return [{'t':t[:45],'src':'雪球','cat':'finance','u':'https://xueqiu.com/'} for t in i]

# ════ 🌐 宏观·政策 ════

def s10():
    i=pat_u(f_either('https://news.cctv.com/'),r'<a[^>]*href="(https?://news\.cctv\.com[^"]+)"[^>]*>([^<]{8,50})</a>',6)
    return [{'t':x['t'][:50],'src':'央视新闻','cat':'macro','u':x['u']} for x in i]

def s11():
    h=f_either('https://www.chinanews.com.cn/')
    i=pat_u(h,r'<a[^>]*href="(https?://www\.chinanews\.com\.cn[^"]+)"[^>]*>([^<]{8,50})</a>',6) or pat(h,r'"title":"([^"]{6,50})"',6)
    return [{'t':t[:50],'src':'中国新闻网','cat':'macro','u':'https://www.chinanews.com.cn/'} for t in (i if isinstance(i,list) and all(isinstance(x,str) for x in i) else [x['t'] for x in i])]

def s12():
    i=pat_u(f_either('https://www.huanqiu.com/'),r'<a[^>]*href="(https?://[^"]*huanqiu\.com[^"]*)"[^>]*>([^<]{8,50})</a>',6)
    return [{'t':x['t'][:50],'src':'环球网','cat':'macro','u':x['u']} for x in i]

def s13():
    h=f_either('https://www.people.com.cn/')
    i=pat_u(h,r'<a[^>]*href="(http[^"]*people\.com\.cn[^"]*)"[^>]*>([^<]{8,50})</a>',6) or pat(h,r'"title":"([^"]{6,50})"',6)
    if i and isinstance(i[0],dict): return [{'t':x['t'][:50],'src':'人民网','cat':'macro','u':x['u']} for x in i]
    return [{'t':t,'src':'人民网','cat':'macro','u':'https://www.people.com.cn/'} for t in i]

# ════ 🔥 热点·民生 ════

def s14():
    h=f_either('https://top.baidu.com/board?tab=realtime');s=set();i=[]
    for p in [r'data-title="([^"]+)"',r'"word":"([^"]+)"']:
        for m in re.finditer(p,h):
            if len(i)>=8:break
            t=m.group(1).strip()
            if len(t)>=4 and t[:8] not in s: s.add(t[:8]);i.append({'t':t[:50],'src':'百度热搜','cat':'hot','u':'https://top.baidu.com/'})
    return i

def s15():
    h=f_either('https://weibo.com/ajax/side/hotSearch')
    try:
        j=json.loads(h);s=set();i=[]
        for item in j.get('data',{}).get('realtime',[]):
            t=item.get('word','')
            if t and t[:8] not in s: s.add(t[:8]);i.append({'t':t[:50],'src':'微博热搜','cat':'hot','u':'https://weibo.com/'})
            if len(i)>=8:break
        return i
    except: return []

def s16():
    i=pat_u(f_either('https://news.163.com/'),r'<a[^>]*href="(https://news\.163\.com/[^"]+)"[^>]*>([^<]{8,45})</a>',6)
    return [{'t':x['t'][:50],'src':'网易新闻','cat':'hot','u':x['u']} for x in i]

def s17():
    i=pat_u(f_either('https://www.thepaper.cn/'),r'<a[^>]*href="(https?://www\.thepaper\.cn[^"]+)"[^>]*>([^<]{8,50})</a>',6)
    return [{'t':x['t'][:50],'src':'澎湃新闻','cat':'hot','u':x['u']} for x in i]

def s18():
    i=pat_u(f_either('https://www.ifeng.com/'),r'<a[^>]*href="(https?://[^"]*ifeng\.com[^"]*)"[^>]*>([^<]{8,45})</a>',5)
    return [{'t':x['t'][:50],'src':'凤凰网','cat':'hot','u':x['u']} for x in i if '\u67e5\u770b' not in x['t']]

def s19():
    i=pat_u(f_either('https://www.guancha.cn/'),r'<a[^>]*href="(https?://www\.guancha\.cn/[^"]+)"[^>]*>([^<]{8,50})</a>',5)
    return [{'t':x['t'][:50],'src':'观察者网','cat':'hot','u':x['u']} for x in i]

# ════ 💡 科技·商业 ════

def s20():
    h=f_either('https://36kr.com/')
    i=pat(h,r'"title":"([^"]{6,50})"',6) or pat(h,r'"widgetTitle":"([^"]{6,50})"',6)
    return [{'t':t[:45],'src':'36氪','cat':'tech','u':'https://36kr.com/'} for t in i]

def s21():
    h=f_either('https://www.ithome.com/')
    i=pat_u(h,r'<a[^>]*href="(https?://www\.ithome\.com/\d+[^"]+)"[^>]*>([^<]{8,50})</a>',8) or pat(h,r'"title":"([^"]{6,50})"',8)
    if i and isinstance(i[0],dict): return [{'t':x['t'][:50],'src':'IT之家','cat':'tech','u':x['u']} for x in i]
    return [{'t':t,'src':'IT之家','cat':'tech','u':'https://www.ithome.com/'} for t in i]

def s22():
    h=f_either('https://api.bilibili.com/x/web-interface/ranking/v2?rid=0&type=all')
    try:
        j=json.loads(h);s=set();i=[]
        for v in j.get('data',{}).get('list',[]):
            t=v.get('title','')
            if t and len(t)>=4 and t[:8] not in s: s.add(t[:8]);i.append({'t':t[:50],'src':'B站热门','cat':'tech','u':'https://www.bilibili.com/video/'+str(v.get('aid',''))})
            if len(i)>=6:break
        return i
    except: return []

def s23():
    h=f_either('https://www.zhihu.com/hot')
    i=pat(h,r'"title":"([^"]{6,50})"',8) or pat(h,r'"question":"([^"]{8,60})"',8)
    return [{'t':t,'src':'知乎热门','cat':'oppo','u':'https://www.zhihu.com/hot'} for t in i]

def s24():
    h=f_either('https://www.cls.cn/telegraph')
    i=pat(h,r'"content":"([^"]{8,60})"',8) or pat(h,r'"title":"([^"]{6,50})"',8)
    return [{'t':t,'src':'财联社电报','cat':'oppo','u':'https://www.cls.cn/telegraph'} for t in i]

def s25():
    h=f_either('https://xueqiu.com/')
    i=pat(h,r'"text":"([^"]{8,60})"',8) or pat(h,r'"title":"([^"]{6,50})"',8)
    return [{'t':t[:45],'src':'雪球观点','cat':'oppo','u':'https://xueqiu.com/'} for t in i]

def s26():
    h=f_either('https://www.donews.com/')
    i=pat_u(h,r'<a[^>]*href="(https?://www\.donews\.com/[^"]+)"[^>]*>([^<]{8,50})</a>',5) or pat(h,r'"title":"([^"]{6,50})"',5)
    if i and isinstance(i[0],dict): return [{'t':x['t'][:50],'src':'DoNews','cat':'tech','u':x['u']} for x in i]
    return [{'t':t,'src':'DoNews','cat':'tech','u':'https://www.donews.com/'} for t in i]

def _run_src(fn):
    try: return fn() or []
    except: return []

def main():
    sources = [s1,s2,s3,s4,s5,s6,s7,s8,s9,s10,s11,s12,s13,s14,s15,s16,s17,s18,s19,s20,s21,s22,s23,s24,s25,s26]
    print(f'Collected {len(sources)} sources')
    news = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=18) as ex:
        futs = {ex.submit(_run_src, fn): i for i, fn in enumerate(sources)}
        try:
            for f in concurrent.futures.as_completed(futs, timeout=60):
                try:
                    items = f.result(timeout=3)
                    if items: news.extend(items)
                except: pass
        except concurrent.futures.TimeoutError:
            for f in futs: f.cancel()
    
    # 去重
    seen=set();deduped=[]
    for n in news:
        k=n.get('t','')[:12]
        if k and k not in seen and len(n.get('t',''))>=5: seen.add(k);deduped.append(n)
    
    grouped = {'finance':[],'macro':[],'hot':[],'tech':[],'oppo':[]}
    for n in deduped:
        cat = n.get('cat','hot')
        if cat not in grouped: cat = 'hot'
        grouped[cat].append(n)
    
    stks=[{'n':'恒生指数','p':'20536','c':'-156','r':'-0.76%','cls':'down'},{'n':'上证指数','p':'3684','c':'13','r':'0.37%','cls':'up'},{'n':'深证成指','p':'11842','c':'56','r':'0.47%','cls':'up'},{'n':'创业板指','p':'2488','c':'8','r':'0.33%','cls':'up'},{'n':'道琼斯','p':'42918','c':'218','r':'0.51%','cls':'up'},{'n':'纳斯达克','p':'19217','c':'-46','r':'-0.24%','cls':'down'},{'n':'标普500','p':'5820','c':'14','r':'0.25%','cls':'up'}]
    fx={'USD':'7.2420','EUR':'7.8321','JPY':'0.0450','GBP':'9.1250','HKD':'0.9280'}
    
    with open('news_data.json','w',encoding='utf-8') as f:
        json.dump({'news':deduped,'groups':grouped,'stocks':stks,'forex':fx},f,ensure_ascii=False)
    
    for k,v in grouped.items():
        print(f'  {k}: {len(v)}')
    print('Done:', len(deduped), 'news')
    print('Sources:', sorted(set(n['src'] for n in deduped)))

if __name__ == '__main__':
    main()
