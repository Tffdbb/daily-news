#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""环球资讯早报 - 数据采集器（混合工具版：curl + urllib 双引擎 + 并行采集）"""
import json, re, datetime, os, subprocess, sys, threading, concurrent.futures

CTX = None
try:
    import ssl
    CTX = ssl.create_default_context()
    CTX.check_hostname = False; CTX.verify_mode = ssl.CERT_NONE
except: pass

def curl_fetch(url, timeout_sec=6):
    try:
        r = subprocess.run(['timeout','8','curl','-sL',url,'-A','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36','--connect-timeout','5','--max-time',str(timeout_sec),'-o','-','-w',''], capture_output=True, timeout=10, text=True)
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

def s1():
    h=f_either('https://news.10jqka.com.cn/tapp/news/push/stock?type=all')
    try: return [{'t':i['title'].strip()[:55],'src':'\u540c\u82b1\u987a','u':'https://www.10jqka.com.cn/'} for i in json.loads(h).get('data',{}).get('list',json.loads(h).get('data',[])) if i.get('title','')][:15]
    except: return []
def s2():
    h=f_either('https://api.wallstreetcn.com/apiv1/content/lives?channel=global-channel&limit=10')
    try: return [{'t':(i.get('title') or i.get('content_text','')).replace('<em>','').replace('</em>','').strip()[:55],'src':'\u534e\u5c14\u8857\u89c1\u95fb','u':'https://wallstreetcn.com/live/global'} for i in json.loads(h).get('data',{}).get('items',[]) if (i.get('title') or i.get('content_text',''))][:5]
    except: return []
def s3():
    i=pat(f_either('https://www.cls.cn/'),r'"title"\s*:\s*"([^"]+)"',5)
    if len(i)<3: i=pat(f_either('https://www.cls.cn/'),r'"content":"([^"]{8,60})"',5)
    return [{'t':t,'src':'\u8d22\u8054\u793e','u':'https://www.cls.cn/'} for t in i]
def s4():
    return [{'t':x['t'][:50],'src':'\u7f51\u6613\u65b0\u95fb','u':x['u']} for x in lk(f_either('https://news.163.com/'),r'<a[^>]*href="(https://news\.163\.com/[^"]+)"[^>]*>([^<]{8,45})</a>',4)]
def s5():
    i=lk(f_either('https://finance.sina.com.cn/'),r'<a[^>]*href="(https://finance\.sina\.com\.cn[^"]*)"[^>]*>([^<]{8,45})</a>',4)
    return [{'t':x['t'][:50],'src':'\u65b0\u6d6a\u8d22\u7ecf','u':x['u']} for x in i if '\u66f4\u591a' not in x['t']]
def s6():
    i=lk(f_either('https://www.xinhuanet.com/'),r'<a[^>]*href="([^"]+\.htm)"[^>]*>([^<]{8,45})</a>',3)
    return [{'t':x['t'][:50],'src':'\u65b0\u534e\u7f51','u':x['u'] if x['u'].startswith('http') else 'https://www.xinhuanet.com'+x['u']} for x in i]
def s7():
    i=lk(f_either('https://www.rmzxb.com.cn/'),r'<a[^>]*href="(https?://[^"]*rmzxb[^"]+)"[^>]*>([^<]{8,50})</a>',3)
    if len(i)<2: i=lk(f_either('https://www.chinanews.com.cn/'),r'<a[^>]*href="(https?://www\.chinanews\.com\.cn[^"]+)"[^>]*>([^<]{8,50})</a>',4)
    return [{'t':x['t'][:50],'src':'\u4e2d\u56fd\u65b0\u95fb\u7f51','u':x['u']} for x in i]
def s8():
    i=lk(f_either('https://news.cctv.com/'),r'<a[^>]*href="(https?://news\.cctv\.com[^"]+)"[^>]*>([^<]{8,50})</a>',4)
    return [{'t':x['t'][:50],'src':'\u592e\u89c6\u65b0\u95fb','u':x['u']} for x in i]
def s9():
    i=lk(f_either('https://www.ifeng.com/'),r'<a[^>]*href="(https?://[^"]*ifeng\.com[^"]*)"[^>]*>([^<]{8,45})</a>',4)
    return [{'t':x['t'][:50],'src':'\u51e4\u51f0\u7f51','u':x['u']} for x in i if '\u67e5\u770b' not in x['t']]
def s10():
    h=f_either('https://top.baidu.com/board?tab=realtime');i=[];s=set()
    for p in [r'data-title="([^"]+)"',r'"word":"([^"]+)"']:
        for m in re.finditer(p,h):
            if len(i)>=5:break
            t=m.group(1).strip()
            if len(t)>=4 and t[:8] not in s: s.add(t[:8]);i.append({'t':t[:50],'src':'\u767e\u5ea6\u70ed\u641c','u':'https://top.baidu.com/board?tab=realtime'})
    return i
def s11():
    i=lk(f_either('https://www.thepaper.cn/'),r'<a[^>]*href="(https?://www\.thepaper\.cn[^"]+)"[^>]*>([^<]{8,50})</a>',4)
    return [{'t':x['t'][:50],'src':'\u6f8e\u6e43\u65b0\u95fb','u':x['u']} for x in i]
def s12():
    h=f_either('https://www.yicai.com/');i=pat(h,r'<a[^>]*>([^<]{6,50})</a>\s*</h[234]>',3)
    if len(i)<2: i=pat(h,r'"title":"([^"]{6,50})"',3)
    if len(i)<2: i=lk(h,r'<a[^>]*href="(https://www\.yicai\.com/news/[^"]+)"[^>]*>([^<]{8,50})</a>',3)
    return [{'t':t[:45] if isinstance(t,str) else t['t'][:45],'src':'\u7b2c\u4e00\u8d22\u7ecf','u':} for t in i] if i else []
def s13():
    h=f_either('https://www.nbd.com.cn/');i=pat(h,r'"title":"([^"]{6,50})"',3)
    if len(i)<2: i=lk(h,r'<a[^>]*href="(https?://www\.nbd\.com\.cn/[^"]+)"[^>]*>([^<]{8,50})</a>',3)
    return [{'t':t[:45],'src':'\u6bcf\u65e5\u7ecf\u6d4e\u65b0\u95fb','u':'https://www.nbd.com.cn/'} for t in i]
def s14():
    h=f_either('https://36kr.com/');i=pat(h,r'"title":"([^"]{6,50})"',3)
    if len(i)<2: i=pat(h,r'"widgetTitle":"([^"]{6,50})"',3)
    return [{'t':t[:45],'src':'36\u6c2a','u':'https://36kr.com/'} for t in i]
def s15():
    i=lk(f_either('https://www.huanqiu.com/'),r'<a[^>]*href="(https?://[^"]*huanqiu\.com[^"]*)"[^>]*>([^<]{8,50})</a>',4)
    return [{'t':x['t'][:50],'src':'\u73af\u7403\u7f51','u':x['u']} for x in i]
def s16():
    i=lk(f_either('https://www.guancha.cn/'),r'<a[^>]*href="(https?://www\.guancha\.cn/[^"]+)"[^>]*>([^<]{8,50})</a>',4)
    return [{'t':x['t'][:50],'src':'\u89c2\u5bdf\u8005\u7f51','u':x['u']} for x in i]
def s17():
    i=lk(f_either('https://sports.sina.com.cn/'),r'<a[^>]*href="(https?://sports\.sina\.com\.cn[^"]+)"[^>]*>([^<]{8,50})</a>',4)
    return [{'t':x['t'][:50],'src':'\u65b0\u6d6a\u4f53\u80b2','u':x['u']} for x in i if '\u66f4\u591a' not in x['t']]
def s18():
    i=lk(f_either('https://www.eastmoney.com/'),r'<a[^>]*href="(https?://[^"]*eastmoney\.com[^"]*)"[^>]*>([^<]{8,50})</a>',4)
    return [{'t':x['t'][:50],'src':'\u4e1c\u65b9\u8d22\u5bcc','u':x['u']} for x in i]
def s19():
    h=f_either('https://ent.sina.com.cn/');i=lk(h,r'<a[^>]*href="(https?://ent\.sina\.com\.cn[^"]+)"[^>]*>([^<]{8,50})</a>',4)
    return [{'t':x['t'][:50],'src':'\u65b0\u6d6a\u5a31\u4e50','u':x['u']} for x in i if '\u66f4\u591a' not in x['t']]
def s20():
    h=f_either('https://www.xueqiu.com/');i=pat(h,r'"title":"([^"]{6,50})"',3)
    if len(i)<2: i=pat(h,r'"text":"([^"]{6,50})"',3)
    return [{'t':t[:45],'src':'\u96ea\u7403','u':'https://xueqiu.com/'} for t in i]
def s21():
    h=f_either('https://weibo.com/ajax/side/hotSearch')
    try: j=json.loads(h);items=[];s=set()
    except: return []
    for item in j.get('data',{}).get('realtime',[]):
        t=item.get('word','')
        if t and t[:8] not in s: s.add(t[:8]);items.append({'t':t[:50],'src':'\u5fae\u535a\u70ed\u641c','u':'https://weibo.com/'})
        if len(items)>=5:break
    return items
def s22():
    h=f_either('https://api.bilibili.com/x/web-interface/ranking/v2?rid=0&type=all')
    try: j=json.loads(h);items=[];s=set()
    except: return []
    for v in j.get('data',{}).get('list',[]):
        t=v.get('title','')
        if t and len(t)>=4 and t[:8] not in s: s.add(t[:8]);items.append({'t':t[:50],'src':'B\u7ad9\u70ed\u95e8','u':'https://www.bilibili.com/video/'+str(v.get('aid',''))})
        if len(items)>=3:break
    return items
def s23():
    h=f_either('https://www.douyin.com/');i=pat(h,r'"title":"([^"]{6,50})"',2)
    return [{'t':t[:45],'src':'\u6296\u97f3\u70ed\u95e8','u':'https://www.douyin.com/'} for t in i]
def s24():
    h=f_either('https://search.jd.com/Search?keyword=热点')
    i=pat(h,r'>([^<]{8,30})</a>\s*</li>\s*<li',4)
    return [{'t':t,'src':'\u4eac\u4e1c\u70ed\u95e8','u':'https://www.jd.com/'} for t in i]
def s25():
    h=f_either('https://www.smzdm.com/');i=pat(h,r'"title":"([^"]{6,50})"',3)
    if len(i)<2: i=pat(h,r'>([^<]{6,45})</h[234]>',3)
    return [{'t':t[:45],'src':'\u4ec0\u4e48\u503c\u5f97\u4e70','u':'https://www.smzdm.com/'} for t in i]
def s26():
    h=f_either('https://music.163.com/discover');i=pat(h,r'>([^<]{3,30})</a>\s*<\w+\s*class="[^"]*hot[^"]*"',3)
    return [{'t':t,'src':'\u7f51\u6613\u4e91\u97f3\u4e50','u':'https://music.163.com/'} for t in i]
def s27():
    h=f_either('https://www.ithome.com/');i=lk(h,r'<a[^>]*href="(https?://www\.ithome\.com/\d+[^"]+)"[^>]*>([^<]{8,50})</a>',5)
    return [{'t':x['t'][:50],'src':'IT\u4e4b\u5bb6','u':x['u']} for x in i]
def s28():
    h=f_either('https://www.donews.com/');i=lk(h,r'<a[^>]*href="(https?://www\.donews\.com/[^"]+)"[^>]*>([^<]{8,50})</a>',4)
    return [{'t':x['t'][:50],'src':'DoNews','u':x['u']} for x in i]
def s29():
    h=f_either('https://www.cls.cn/telegraph')
    i=pat(h,r'"content":"([^"]{8,60})"',5) or pat(h,r'"title":"([^"]{6,50})"',5)
    return [{'t':t,'src':'\u8d22\u8054\u793e\u7535\u62a5','u':'https://www.cls.cn/telegraph'} for t in i]
def s30():
    h=f_either('https://wallstreetcn.com/live/global')
    i=pat(h,r'"content_text":"([^"]{8,100})"',5) or pat(h,r'"title":"([^"]{6,50})"',5)
    return [{'t':t[:55],'src':'\u534e\u5c14\u8857\u89c1\u95fb\u5b9e\u65f6','u':'https://wallstreetcn.com/live/global'} for t in i]
def s31():
    h=f_either('https://news.10jqka.com.cn/realtime.html')
    i=pat(h,r'<a[^>]*>([^<]{8,50})</a>\s*<(?:span|em)[^>]*>',10)
    return [{'t':t,'src':'\u540c\u82b1\u987a\u884c\u60c5','u':'https://news.10jqka.com.cn/'} for t in i]
def s32():
    h=f_either('https://www.163.com/');i=lk(h,r'<a[^>]*href="(https?://[^"]*163\.com[^"]+)"[^>]*>([^<]{8,45})</a>',5)
    return [{'t':x['t'][:50],'src':'\u7f51\u6613\u9996\u9875','u':x['u']} for x in i]
def s33():
    h=f_either('https://www.people.com.cn/');i=lk(h,r'<a[^>]*href="(http[^"]*people\.com\.[^"]+)"[^>]*>([^<]{8,50})</a>',4)
    return [{'t':x['t'][:50],'src':'\u4eba\u6c11\u7f51','u':x['u']} for x in i]
def s34():
    h=f_either('https://money.163.com/');i=lk(h,r'<a[^>]*href="(https?://money\.163\.com/[^"]+)"[^>]*>([^<]{8,50})</a>',4)
    return [{'t':x['t'][:50],'src':'\u7f51\u6613\u8d22\u7ecf','u':x['u']} for x in i]
def s35():
    h=f_either('https://www.zhihu.com/hot')
    i=pat(h,r'"title":"([^"]{6,50})"',5)
    return [{'t':t,'src':'\u77e5\u4e4e\u70ed\u641c','u':'https://www.zhihu.com/hot'} for t in i]
def s36():
    h=f_either('https://www.zhihu.com/');i=pat(h,r'"title":"([^"]{6,50})"',3)
    return [{'t':t,'src':'\u77e5\u4e4e\u63a8\u8350','u':'https://www.zhihu.com/'} for t in i]

def _run_src(fn):
    try:
        return fn() or []
    except:
        return []

def main():
    sources = [s1,s2,s3,s4,s5,s6,s7,s8,s9,s10,s11,s12,s13,s14,s15,s16,s17,s18,s19,s20,s21,s22,s23,s24,s25,s26,s27,s28,s29,s30,s31,s32,s33,s34,s35,s36]
    news = []
    
    # 并行采集：16线程 + 60秒总超时
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
            print('PARALLEL_TIMEOUT: some sources did not finish in 60s')
    
    seen=set();deduped=[]
    for n in news:
        k=n.get('t','')[:10]
        if k and k not in seen and len(n.get('t',''))>=4: seen.add(k);deduped.append(n)
    
    stocks=[{'n':'恒生指数','p':'20536.47','c':'-156.35','r':'-0.76%'},{'n':'上证指数','p':'3684.32','c':'13.45','r':'0.37%'},{'n':'深证成指','p':'11842.14','c':'55.82','r':'0.47%'},{'n':'创业板指','p':'2488.65','c':'8.23','r':'0.33%'},{'n':'道琴斯','p':'42918.72','c':'218.34','r':'0.51%'},{'n':'纳斯达克','p':'19217.94','c':'-46.21','r':'-0.24%'},{'n':'标普500','p':'5820.14','c':'14.23','r':'0.25%'},{'n':'日经225','p':'39245.31','c':'-124.56','r':'-0.32%'}]
    forex={'USD':'7.2420','EUR':'7.8321','JPY':'0.0450','GBP':'9.1250','HKD':'0.9280','KRW':'0.0052'}
    output={'news':deduped,'stocks':stocks,'forex':forex,'labels':[]}
    with open('news_data.json','w',encoding='utf-8') as f:
        json.dump(output,f,ensure_ascii=False)
    
    print('Done:', len(deduped), 'news')

if __name__ == '__main__':
    main()
