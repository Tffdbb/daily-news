#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""每日价值资讯 - 投资·工作·宏观·生活"""
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
# 📈 钱 - 股市/基金/投资/宏观
# ═══════════════════════════════════════════

def s1():
    h=f_either('https://news.10jqka.com.cn/tapp/news/push/stock?type=all')
    try: return [{'t':i['title'].strip()[:55],'src':'同花顺','cat':'finance','u':'https://www.10jqka.com.cn/'} for i in json.loads(h).get('data',{}).get('list',json.loads(h).get('data',[])) if i.get('title','')][:12]
    except: return []

def s2():
    h=f_either('https://api.wallstreetcn.com/apiv1/content/lives?channel=global-channel&limit=15')
    try: return [{'t':(i.get('title') or i.get('content_text','')).replace('<em>','').replace('</em>','').strip()[:55],'src':'华尔街见闻','cat':'finance','u':'https://wallstreetcn.com/live/global'} for i in json.loads(h).get('data',{}).get('items',[]) if (i.get('title') or i.get('content_text',''))][:8]
    except: return []

def s3():
    i=pat(f_either('https://www.cls.cn/'),r'"title"\s*:\s*"([^"]+)"',8)
    if len(i)<3: i=pat(f_either('https://www.cls.cn/'),r'"content":"([^"]{8,60})"',8)
    return [{'t':t,'src':'财联社','cat':'finance','u':'https://www.cls.cn/'} for t in i]

def s4():
    i=lk(f_either('https://www.eastmoney.com/'),r'<a[^>]*href="(https?://[^"]*eastmoney\.com[^"]*)"[^>]*>([^<]{8,50})</a>',6)
    return [{'t':x['t'][:50],'src':'东方财富','cat':'finance','u':x['u']} for x in i]

def s5():
    h=f_either('https://www.nbd.com.cn/');i=pat(h,r'"title":"([^"]{6,50})"',4)
    if len(i)<2: i=lk(h,r'<a[^>]*href="(https?://www\.nbd\.com\.cn/[^"]+)"[^>]*>([^<]{8,50})</a>',4)
    return [{'t':t[:45],'src':'每经新闻','cat':'finance','u':'https://www.nbd.com.cn/'} for t in i]

def s6():
    i=lk(f_either('https://finance.sina.com.cn/'),r'<a[^>]*href="(https://finance\.sina\.com\.cn[^"]*)"[^>]*>([^<]{8,45})</a>',5)
    return [{'t':x['t'][:50],'src':'新浪财经','cat':'finance','u':x['u']} for x in i if '\u66f4\u591a' not in x['t']]

def s7():
    h=f_either('https://www.yicai.com/');i=pat(h,r'"title":"([^"]{6,50})"',5)
    return [{'t':t[:45],'src':'第一财经','cat':'finance','u':'https://www.yicai.com/'} for t in i]

def s8():
    i=lk(f_either('https://money.163.com/'),r'<a[^>]*href="(https?://money\.163\.com/[^"]+)"[^>]*>([^<]{8,50})</a>',5)
    return [{'t':x['t'][:50],'src':'网易财经','cat':'finance','u':x['u']} for x in i]

def s9():
    h=f_either('https://www.xueqiu.com/');i=pat(h,r'"title":"([^"]{6,50})"',5)
    if len(i)<2: i=pat(h,r'"text":"([^"]{6,50})"',5)
    return [{'t':t[:45],'src':'雪球','cat':'finance','u':'https://xueqiu.com/'} for t in i]

# ═══════════════════════════════════════════
# 🌐 宏观 - 国际局势/经济/政策
# ═══════════════════════════════════════════

def s10():
    i=lk(f_either('https://news.cctv.com/'),r'<a[^>]*href="(https?://news\.cctv\.com[^"]+)"[^>]*>([^<]{8,50})</a>',6)
    return [{'t':x['t'][:50],'src':'央视新闻','cat':'macro','u':x['u']} for x in i]

def s11():
    i=lk(f_either('https://www.xinhuanet.com/'),r'<a[^>]*href="([^"]+\.htm)"[^>]*>([^<]{8,45})</a>',4)
    return [{'t':x['t'][:50],'src':'新华网','cat':'macro','u':x['u'] if x['u'].startswith('http') else 'https://www.xinhuanet.com'+x['u']} for x in i]

def s12():
    i=lk(f_either('https://www.chinanews.com.cn/'),r'<a[^>]*href="(https?://www\.chinanews\.com\.cn[^"]+)"[^>]*>([^<]{8,50})</a>',5)
    return [{'t':x['t'][:50],'src':'中国新闻网','cat':'macro','u':x['u']} for x in i]

def s13():
    i=lk(f_either('https://www.huanqiu.com/'),r'<a[^>]*href="(https?://[^"]*huanqiu\.com[^"]*)"[^>]*>([^<]{8,50})</a>',5)
    return [{'t':x['t'][:50],'src':'环球网','cat':'macro','u':x['u']} for x in i]

def s14():
    i=lk(f_either('https://www.people.com.cn/'),r'<a[^>]*href="(http[^"]*people\.com\.[^"]+)"[^>]*>([^<]{8,50})</a>',5)
    return [{'t':x['t'][:50],'src':'人民网','cat':'macro','u':x['u']} for x in i]

# ═══════════════════════════════════════════
# 📰 热点 - 社会/民生/热搜
# ═══════════════════════════════════════════

def s15():
    h=f_either('https://top.baidu.com/board?tab=realtime');i=[];s=set()
    for p in [r'data-title="([^"]+)"',r'"word":"([^"]+)"']:
        for m in re.finditer(p,h):
            if len(i)>=8:break
            t=m.group(1).strip()
            if len(t)>=4 and t[:8] not in s: s.add(t[:8]);i.append({'t':t[:50],'src':'百度热搜','cat':'hot','u':'https://top.baidu.com/'})
    return i

def s16():
    h=f_either('https://weibo.com/ajax/side/hotSearch')
    try: j=json.loads(h);items=[];s=set()
    except: return []
    for item in j.get('data',{}).get('realtime',[]):
        t=item.get('word','')
        if t and t[:8] not in s: s.add(t[:8]);items.append({'t':t[:50],'src':'微博热搜','cat':'hot','u':'https://weibo.com/'})
        if len(items)>=8:break
    return items

def s17():
    i=lk(f_either('https://news.163.com/'),r'<a[^>]*href="(https://news\.163\.com/[^"]+)"[^>]*>([^<]{8,45})</a>',5)
    return [{'t':x['t'][:50],'src':'网易新闻','cat':'hot','u':x['u']} for x in i]

def s18():
    i=lk(f_either('https://www.thepaper.cn/'),r'<a[^>]*href="(https?://www\.thepaper\.cn[^"]+)"[^>]*>([^<]{8,50})</a>',5)
    return [{'t':x['t'][:50],'src':'澎湃新闻','cat':'hot','u':x['u']} for x in i]

def s19():
    i=lk(f_either('https://www.ifeng.com/'),r'<a[^>]*href="(https?://[^"]*ifeng\.com[^"]*)"[^>]*>([^<]{8,45})</a>',5)
    return [{'t':x['t'][:50],'src':'凤凰网','cat':'hot','u':x['u']} for x in i if '\u67e5\u770b' not in x['t']]

def s20():
    i=lk(f_either('https://www.guancha.cn/'),r'<a[^>]*href="(https?://www\.guancha\.cn/[^"]+)"[^>]*>([^<]{8,50})</a>',5)
    return [{'t':x['t'][:50],'src':'观察者网','cat':'hot','u':x['u']} for x in i]

# ═══════════════════════════════════════════
# 💡 科技商业
# ═══════════════════════════════════════════

def s21():
    h=f_either('https://36kr.com/');i=pat(h,r'"title":"([^"]{6,50})"',5)
    if len(i)<2: i=pat(h,r'"widgetTitle":"([^"]{6,50})"',5)
    return [{'t':t[:45],'src':'36氪','cat':'tech','u':'https://36kr.com/'} for t in i]

def s22():
    h=f_either('https://www.ithome.com/');i=lk(h,r'<a[^>]*href="(https?://www\.ithome\.com/\d+[^"]+)"[^>]*>([^<]{8,50})</a>',6)
    return [{'t':x['t'][:50],'src':'IT之家','cat':'tech','u':x['u']} for x in i]

def s23():
    h=f_either('https://www.donews.com/');i=lk(h,r'<a[^>]*href="(https?://www\.donews\.com/[^"]+)"[^>]*>([^<]{8,50})</a>',5)
    return [{'t':x['t'][:50],'src':'DoNews','cat':'tech','u':x['u']} for x in i]

def s24():
    h=f_either('https://api.bilibili.com/x/web-interface/ranking/v2?rid=0&type=all')
    try: j=json.loads(h);items=[];s=set()
    except: return []
    for v in j.get('data',{}).get('list',[]):
        t=v.get('title','')
        if t and len(t)>=4 and t[:8] not in s: s.add(t[:8]);items.append({'t':t[:50],'src':'B站热门','cat':'tech','u':'https://www.bilibili.com/video/'+str(v.get('aid',''))})
        if len(items)>=5:break
    return items

# ═══════════════════════════════════════════
# 🎯 机会 - 新兴行业/风口/值得关注
# ═══════════════════════════════════════════

def s25():
    h=f_either('https://www.zhihu.com/hot')
    i=pat(h,r'"title":"([^"]{6,50})"',8)
    return [{'t':t,'src':'知乎热门','cat':'oppo','u':'https://www.zhihu.com/hot'} for t in i]

def s26():
    h=f_either('https://sports.sina.com.cn/');i=lk(h,r'<a[^>]*href="(https?://sports\.sina\.com\.cn[^"]+)"[^>]*>([^<]{8,50})</a>',5)
    return [{'t':x['t'][:50],'src':'新浪体育','cat':'oppo','u':x['u']} for x in i if '\u66f4\u591a' not in x['t']]

def s27():
    h=f_either('https://ent.sina.com.cn/');i=lk(h,r'<a[^>]*href="(https?://ent\.sina\.com\.cn[^"]+)"[^>]*>([^<]{8,50})</a>',5)
    return [{'t':x['t'][:50],'src':'新浪娱乐','cat':'oppo','u':x['u']} for x in i if '\u66f4\u591a' not in x['t']]

def s28():
    h=f_either('https://www.cls.cn/telegraph')
    i=pat(h,r'"content":"([^"]{8,60})"',6) or pat(h,r'"title":"([^"]{6,50})"',6)
    return [{'t':t,'src':'财联社电报','cat':'oppo','u':'https://www.cls.cn/telegraph'} for t in i]

def s29():
    h=f_either('https://wallstreetcn.com/live/global')
    i=pat(h,r'"content_text":"([^"]{8,100})"',6) or pat(h,r'"title":"([^"]{6,50})"',6)
    return [{'t':t[:55],'src':'华尔街实时','cat':'oppo','u':'https://wallstreetcn.com/live/global'} for t in i]

def _run_src(fn):
    try: return fn() or []
    except: return []

def main():
    sources = [s1,s2,s3,s4,s5,s6,s7,s8,s9,s10,s11,s12,s13,s14,s15,s16,s17,s18,s19,s20,s21,s22,s23,s24,s25,s26,s27,s28,s29]
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
    
    seen=set();deduped=[]
    for n in news:
        k=n.get('t','')[:10]
        if k and k not in seen and len(n.get('t',''))>=4: seen.add(k);deduped.append(n)
    
    grouped = {'finance':[],'macro':[],'hot':[],'tech':[],'oppo':[]}
    for n in deduped:
        cat = n.get('cat','hot')
        if cat not in grouped: cat = 'hot'
        grouped[cat].append(n)
    
    stocks=[{'n':'恒生指数','p':'20536.47','c':'-156.35','r':'-0.76%','cls':'down'},{'n':'上证指数','p':'3684.32','c':'13.45','r':'0.37%','cls':'up'},{'n':'深证成指','p':'11842.14','c':'55.82','r':'0.47%','cls':'up'},{'n':'创业板指','p':'2488.65','c':'8.23','r':'0.33%','cls':'up'},{'n':'道琴斯','p':'42918.72','c':'218.34','r':'0.51%','cls':'up'},{'n':'纳斯达克','p':'19217.94','c':'-46.21','r':'-0.24%','cls':'down'},{'n':'标普500','p':'5820.14','c':'14.23','r':'0.25%','cls':'up'},{'n':'日经225','p':'39245.31','c':'-124.56','r':'-0.32%','cls':'down'}]
    forex={'USD':'7.2420','EUR':'7.8321','JPY':'0.0450','GBP':'9.1250','HKD':'0.9280','KRW':'0.0052'}
    
    with open('news_data.json','w',encoding='utf-8') as f:
        json.dump({'news':deduped,'groups':grouped,'stocks':stocks,'forex':forex},f,ensure_ascii=False)
    
    for k,v in grouped.items():
        print(f'  {k}: {len(v)}')
    print('Done:', len(deduped), 'news')

if __name__ == '__main__':
    main()
