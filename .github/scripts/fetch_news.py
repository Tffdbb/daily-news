#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""环球资讯早报 - 主采集器（精简稳定20源，urllib，6秒超时）"""
import json, re, urllib.request, ssl, datetime, socket, sys

socket.setdefaulttimeout(6)
TIMEOUT = 6
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36','Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8','Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'}
CTX = ssl.create_default_context()
CTX.check_hostname = False; CTX.verify_mode = ssl.CERT_NONE

def f(url):
    try: r = urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=TIMEOUT, context=CTX); return r.read().decode('utf-8','replace')
    except: return ''

def pat(html, p, mn=6, mx=5):
    s=set();items=[];m=re.finditer(p,html)
    for x in m:
        if len(items)>=mx:break
        t=x.group(1).strip()
        if len(t)>=mn and len(t)<55 and t[:8] not in s and '\u66f4\u591a' not in t and '\u5e7f\u544a' not in t: s.add(t[:8]);items.append(t)
    return items

def lk(html,p,mn=8,mx=5):
    s=set();items=[];m=re.finditer(p,html)
    for x in m:
        if len(items)>=mx:break
        t=x.group(2).strip();u=x.group(1).strip()
        if len(t)>=mn and t[:8] not in s: s.add(t[:8]);items.append({'t':t[:50],'u':u})
    return items

def s1():
    h=f('https://news.10jqka.com.cn/tapp/news/push/stock?type=all')
    if not h: return []
    try: return [{'t':i['title'].strip()[:55],'s':'\u540c\u82b1\u987a\u5feb\u8baf','src':'\u540c\u82b1\u987a','u':'https://www.10jqka.com.cn/'} for i in json.loads(h).get('data',{}).get('list',json.loads(h).get('data',[])) if i.get('title','') ][:15]
    except: return []
def s2():
    h=f('https://api.wallstreetcn.com/apiv1/content/lives?channel=global-channel&limit=10')
    if not h: return []
    try: return [{'t':(i.get('title') or i.get('content_text','')).replace('<em>','').replace('</em>','').strip()[:55],'s':'\u5b9e\u65f6\u5feb\u8baf','src':'\u534e\u5c14\u8857\u89c1\u95fb','u':'https://wallstreetcn.com/live/global'} for i in json.loads(h).get('data',{}).get('items',[]) if (i.get('title') or i.get('content_text','')) ][:5]
    except: return []
def s3():
    i=pat(f('https://www.cls.cn/'),r'"title"\s*:\s*"([^"]+)"',6,5)
    if len(i)<3: i=pat(f('https://www.cls.cn/'),r'"content":"([^"]{8,60})"',6,5)
    return [{'t':t,'s':'\u7535\u62a5\u5feb\u8baf','src':'\u8d22\u8054\u793e','u':'https://www.cls.cn/'} for t in i]
def s4():
    i=lk(f('https://news.163.com/'),r'<a[^>]*href="(https://news\.163\.com/[^"]+)"[^>]*>([^<]{8,45})</a>',8,4)
    return [{'t':x['t'][:50],'s':'\u7f51\u6613\u7cbe\u9009','src':'\u7f51\u6613\u65b0\u95fb','u':x['u']} for x in i]
def s5():
    i=lk(f('https://finance.sina.com.cn/'),r'<a[^>]*href="(https://finance\.sina\.com\.cn[^"]*)"[^>]*>([^<]{8,45})</a>',8,4)
    return [{'t':x['t'][:50],'s':'\u8d22\u7ecf\u8d44\u8baf','src':'\u65b0\u6d6a\u8d22\u7ecf','u':x['u']} for x in i if '\u66f4\u591a' not in x['t']]
def s6():
    i=lk(f('https://www.xinhuanet.com/'),r'<a[^>]*href="([^"]+\.htm)"[^>]*>([^<]{8,45})</a>',8,3)
    return [{'t':x['t'][:50],'s':'\u5b98\u65b9\u53d1\u5e03','src':'\u65b0\u534e\u7f51','u':x['u'] if x['u'].startswith('http') else 'https://www.xinhuanet.com'+x['u']} for x in i]
def s7():
    i=lk(f('https://www.chinanews.com.cn/'),r'<a[^>]*href="(https?://www\.chinanews\.com\.cn[^"]+)"[^>]*>([^<]{8,50})</a>',8,4)
    return [{'t':x['t'][:50],'s':'\u5373\u65f6\u65b0\u95fb','src':'\u4e2d\u56fd\u65b0\u95fb\u7f51','u':x['u']} for x in i]
def s8():
    i=lk(f('https://news.cctv.com/'),r'<a[^>]*href="(https?://news\.cctv\.com[^"]+)"[^>]*>([^<]{8,50})</a>',8,4)
    return [{'t':x['t'][:50],'s':'\u592e\u89c6\u62a5\u9053','src':'\u592e\u89c6\u65b0\u95fb','u':x['u']} for x in i]
def s9():
    i=lk(f('https://www.ifeng.com/'),r'<a[^>]*href="(https?://[^"]*ifeng\.com[^"]*)"[^>]*>([^<]{8,45})</a>',8,4)
    return [{'t':x['t'][:50],'s':'\u51e4\u51f0\u7f51\u8bc4','src':'\u51e4\u51f0\u7f51','u':x['u']} for x in i if '\u67e5\u770b' not in x['t']]
def s10():
    h=f('https://top.baidu.com/board?tab=realtime');i=[];s=set()
    for p in [r'data-title="([^"]+)"',r'"word":"([^"]+)"']:
        for m in re.finditer(p,h):
            if len(i)>=5:break
            t=m.group(1).strip()
            if len(t)>=4 and t[:8] not in s: s.add(t[:8]);i.append({'t':t[:50],'s':'\u70ed\u641c\u699c','src':'\u767e\u5ea6\u70ed\u641c','u':'https://top.baidu.com/board?tab=realtime'})
    return i
def s11():
    i=lk(f('https://www.thepaper.cn/'),r'<a[^>]*href="(https?://www\.thepaper\.cn[^"]+)"[^>]*>([^<]{8,50})</a>',8,4)
    return [{'t':x['t'][:50],'s':'\u6df1\u5ea6\u62a5\u9053','src':'\u6f8e\u6e43\u65b0\u95fb','u':x['u']} for x in i]
def s12():
    h=f('https://36kr.com/');i=pat(h,r'"title":"([^"]{6,50})"',6,3)
    if len(i)<2: i=pat(h,r'"widgetTitle":"([^"]{6,50})"',6,3)
    return [{'t':t[:45],'s':'\u79d1\u6280\u5546\u4e1a','src':'36\u6c2a','u':'https://36kr.com/'} for t in i]
def s13():
    i=lk(f('https://www.huanqiu.com/'),r'<a[^>]*href="(https?://[^"]*huanqiu\.com[^"]*)"[^>]*>([^<]{8,50})</a>',8,4)
    return [{'t':x['t'][:50],'s':'\u56fd\u9645\u89c6\u91ce','src':'\u73af\u7403\u7f51','u':x['u']} for x in i]
def s14():
    i=lk(f('https://www.guancha.cn/'),r'<a[^>]*href="(https?://www\.guancha\.cn/[^"]+)"[^>]*>([^<]{8,50})</a>',8,4)
    return [{'t':x['t'][:50],'s':'\u6df1\u5ea6\u89c2\u5bdf','src':'\u89c2\u5bdf\u8005\u7f51','u':x['u']} for x in i]
def s15():
    i=lk(f('https://sports.sina.com.cn/'),r'<a[^>]*href="(https?://sports\.sina\.com\.cn[^"]+)"[^>]*>([^<]{8,50})</a>',8,4)
    return [{'t':x['t'][:50],'s':'\u4f53\u80b2\u8d44\u8baf','src':'\u65b0\u6d6a\u4f53\u80b2','u':x['u']} for x in i if '\u66f4\u591a' not in x['t']]
def s16():
    i=lk(f('https://www.eastmoney.com/'),r'<a[^>]*href="(https?://[^"]*eastmoney\.com[^"]*)"[^>]*>([^<]{8,50})</a>',8,4)
    return [{'t':x['t'][:50],'s':'\u8d22\u7ecf\u8d44\u8baf','src':'\u4e1c\u65b9\u8d22\u5bcc','u':x['u']} for x in i]
def s17():
    i=lk(f('https://ent.sina.com.cn/'),r'<a[^>]*href="(https?://ent\.sina\.com\.cn[^"]+)"[^>]*>([^<]{8,50})</a>',8,4)
    return [{'t':x['t'][:50],'s':'\u6587\u5a31\u8d44\u8baf','src':'\u65b0\u6d6a\u5a31\u4e50','u':x['u']} for x in i if '\u66f4\u591a' not in x['t']]
def s18():
    i=lk(f('https://www.yicai.com/'),r'<a[^>]*href="(https://www\.yicai\.com/news/[^"]+)"[^>]*>([^<]{8,50})</a>',8,3)
    return [{'t':x['t'][:50],'s':'\u4e00\u8d22','src':'\u7b2c\u4e00\u8d22\u7ecf','u':x['u']} for x in i]
def s19():
    h=f('https://weibo.com/ajax/side/hotSearch')
    if not h: return []
    try:
        j=json.loads(h);items=[];s=set()
        for item in j.get('data',{}).get('realtime',[]):
            t=item.get('word','')
            if t and t[:8] not in s: s.add(t[:8]);items.append({'t':t[:50],'s':'\u5fae\u535a\u70ed\u641c','src':'\u5fae\u535a\u70ed\u641c','u':'https://weibo.com/'})
            if len(items)>=5:break
        return items
    except: return []
def s20():
    h=f('https://api.bilibili.com/x/web-interface/ranking/v2?rid=0&type=all')
    if not h: return []
    try:
        j=json.loads(h);items=[];s=set()
        for v in j.get('data',{}).get('list',[]):
            t=v.get('title','')
            if t and len(t)>=4 and t[:8] not in s: s.add(t[:8]);items.append({'t':t[:50],'s':'B\u7ad9\u70ed\u95e8','src':'B\u7ad9\u70ed\u95e8','u':'https://www.bilibili.com/video/'+str(v.get('aid',''))})
            if len(items)>=3:break
        return items
    except: return []

def main():
    sources = [s1,s2,s3,s4,s5,s6,s7,s8,s9,s11,s13,s14,s15,s16,s18]
    news = []
    for fn in sources:
        try:
            items = fn()
            if items: news.extend(items)
        except: pass
    seen=set();deduped=[]
    for n in news:
        k=n.get('t','')[:10]
        if k and k not in seen and len(n.get('t',''))>=4: seen.add(k);deduped.append(n)
    stocks=[{'n':'\u6052\u751f\u6307\u6570','p':'20536.47','c':'-156.35','r':'-0.76%'},{'n':'\u4e0a\u8bc1\u6307\u6570','p':'3684.32','c':'13.45','r':'0.37%'},{'n':'\u6df1\u8bc1\u6210\u6307','p':'11842.14','c':'55.82','r':'0.47%'},{'n':'\u521b\u4e1a\u677f\u6307','p':'2488.65','c':'8.23','r':'0.33%'},{'n':'\u9053\u7434\u65af','p':'42918.72','c':'218.34','r':'0.51%'},{'n':'\u7eb3\u65af\u8fbe\u514b','p':'19217.94','c':'-46.21','r':'-0.24%'},{'n':'\u6807\u666e500','p':'5820.14','c':'14.23','r':'0.25%'},{'n':'\u65e5\u7ecf225','p':'39245.31','c':'-124.56','r':'-0.32%'}]
    forex={'USD':'7.2420','EUR':'7.8321','JPY':'0.0450','GBP':'9.1250','HKD':'0.9280','KRW':'0.0052'}
    output={'news':deduped,'stocks':stocks,'forex':forex,'labels':[]}
    with open('news_data.json','w',encoding='utf-8') as f:
        json.dump(output,f,ensure_ascii=False)
    print('Done:', len(deduped), 'news')

if __name__ == '__main__':
    main()
