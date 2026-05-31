const fs = require('fs');
const https = require('https');

function fetch(url) {
  return new Promise(r => {
    const o = { hostname: url.match(/https?:\/\/([^\/]+)/)[1], path: url.replace(/https?:\/\/[^\/]+/, ''), method: 'GET', headers: { 'User-Agent': 'Mozilla/5.0' }, timeout: 8000 };
    const req = https.request(o, resp => { let d = ''; resp.on('data', c => d += c); resp.on('end', () => r(d)); });
    req.on('error', () => r('')); req.end();
  });
}

async function s1() {
  try { const h = await fetch('https://news.10jqka.com.cn/tapp/news/push/stock?type=all'); const j = JSON.parse(h); return j.data.list.map(i => ({ t: i.title.trim().substring(0,55), s: '同花顺快讯', src: '同花顺', u: 'https://www.10jqka.com.cn/' })).filter(i => i.t.length > 4).slice(0,15); } catch (e) { return []; }
}

async function s2() {
  try { const h = await fetch('https://api.wallstreetcn.com/apiv1/content/lives?channel=global-channel&limit=10'); const j = JSON.parse(h); return j.data.items.map(i => ({ t: (i.title || i.content_text || '').replace(/<em>/g,'').replace(/<\/em>/g,'').trim().substring(0,55), s: '见闻快讯', src: '华尔街见闻', u: 'https://wallstreetcn.com' + (i.uri || '/') })).filter(i => i.t.length > 4).slice(0,10); } catch (e) { return []; }
}

async function s3() {
  try {
    const h = await fetch('https://www.cls.cn/'); const items = []; const seen = new Set();
    let m; const re = /"title"\s*:\s*"([^"]+)"/g; while ((m = re.exec(h)) && items.length < 6) { const t = m[1].trim(); if (t.length > 5 && !seen.has(t.substring(0,8))) { seen.add(t.substring(0,8)); items.push(t); } }
    if (items.length < 3) { const re2 = /"content":"([^"]{8,60})"/g; while ((m = re2.exec(h)) && items.length < 6) { const t = m[1].trim(); if (!seen.has(t.substring(0,8))) { seen.add(t.substring(0,8)); items.push(t); } } }
    return items.map(t => ({ t, s: '电报快讯', src: '财联社', u: 'https://www.cls.cn/' }));
  } catch (e) { return []; }
}

async function s4() {
  try { const h = await fetch('https://www.yicai.com/'); const seen = new Set(), items = []; let m; const re = /<a[^>]*href="(https:\/\/www\.yicai\.com\/news\/[^"]+)"[^>]*>([^<]{8,55})<\/a>/g; while ((m = re.exec(h)) && items.length < 4) { const t = m[2].trim(); if (t.length > 7 && !seen.has(t.substring(0,8))) { seen.add(t.substring(0,8)); items.push({ t: t.substring(0,50), u: m[1] }); } } return items.map(i => ({ t: i.t, s: '一财', src: '第一财经', u: i.u })); } catch (e) { return []; }
}

async function s5() {
  try { const h = await fetch('https://news.163.com/'); const seen = new Set(), items = []; let m; const re = /<a[^>]*href="(https:\/\/news\.163\.com\/[^"]+)"[^>]*>([^<]{8,45})<\/a>/g; while ((m = re.exec(h)) && items.length < 4) { const t = m[2].trim(); if (t.length > 7 && !seen.has(t.substring(0,8))) { seen.add(t.substring(0,8)); items.push({ t: t.substring(0,50), u: m[1] }); } } return items.map(i => ({ t: i.t, s: '网易精选', src: '网易新闻', u: i.u })); } catch (e) { return []; }
}

async function s6() {
  try { const h = await fetch('https://finance.sina.com.cn/'); const seen = new Set(), items = []; let m; const re = /<a[^>]*href="(https:\/\/finance\.sina\.com\.cn[^"]*)"[^>]*>([^<]{8,45})<\/a>/g; while ((m = re.exec(h)) && items.length < 4) { const t = m[2].trim(); if (t.length > 7 && !seen.has(t.substring(0,8)) && !t.includes('更多') && !t.includes('客户端')) { seen.add(t.substring(0,8)); items.push({ t: t.substring(0,50), u: m[1] }); } } return items.map(i => ({ t: i.t, s: '财经资讯', src: '新浪财经', u: i.u })); } catch (e) { return []; }
}

async function s7() {
  try { const h = await fetch('https://www.xinhuanet.com/'); const seen = new Set(), items = []; let m; const re = /<a[^>]*href="([^"]+\.htm)"[^>]*>([^<]{8,45})<\/a>/g; while ((m = re.exec(h)) && items.length < 3) { const t = m[2].trim(); const u = m[1]; if (t.length > 7 && !seen.has(t.substring(0,8)) && !t.includes('English') && !t.includes('更多')) { seen.add(t.substring(0,8)); items.push({ t: t.substring(0,50), u: u.startsWith('http') ? u : 'https://www.xinhuanet.com' + u }); } } return items.map(i => ({ t: i.t, s: '官方发布', src: '新华网', u: i.u })); } catch (e) { return []; }
}

async function s8() {
  try { const h = await fetch('https://www.people.com.cn/'); const seen = new Set(), items = []; let m; const re = /<a[^>]*href="(https?:\/\/[^"]*people\.com\.cn[^"]*)"[^>]*>([^<]{8,45})<\/a>/g; while ((m = re.exec(h)) && items.length < 3) { const t = m[2].trim(); if (t.length > 7 && !seen.has(t.substring(0,8)) && !t.includes('许可证') && !t.includes('广告') && !t.includes('更多')) { seen.add(t.substring(0,8)); items.push({ t: t.substring(0,50), u: m[1] }); } } return items.map(i => ({ t: i.t, s: '人民网', src: '人民网', u: i.u })); } catch (e) { return []; }
}

async function s9() {
  try { const h = await fetch('https://www.chinanews.com.cn/'); const seen = new Set(), items = []; let m; const re = /<a[^>]*href="(https?:\/\/www\.chinanews\.com\.cn[^"]+)"[^>]*>([^<]{8,50})<\/a>/g; while ((m = re.exec(h)) && items.length < 4) { const t = m[2].trim(); if (t.length > 7 && !seen.has(t.substring(0,8))) { seen.add(t.substring(0,8)); items.push({ t: t.substring(0,50), u: m[1] }); } } return items.map(i => ({ t: i.t, s: '即时新闻', src: '中国新闻网', u: i.u })); } catch (e) { return []; }
}

async function s10() {
  try { const h = await fetch('https://news.cctv.com/'); const seen = new Set(), items = []; let m; const re = /<a[^>]*href="(https?:\/\/news\.cctv\.com[^"]+)"[^>]*>([^<]{8,50})<\/a>/g; while ((m = re.exec(h)) && items.length < 3) { const t = m[2].trim(); if (t.length > 7 && !seen.has(t.substring(0,8))) { seen.add(t.substring(0,8)); items.push({ t: t.substring(0,50), u: m[1] }); } } return items.map(i => ({ t: i.t, s: '央视报道', src: '央视新闻', u: i.u })); } catch (e) { return []; }
}

async function s11() {
  try { const h = await fetch('https://www.ifeng.com/'); const seen = new Set(), items = []; let m; const re = /<a[^>]*href="(https?:\/\/[^"]*ifeng\.com[^"]*)"[^>]*>([^<]{8,45})<\/a>/g; while ((m = re.exec(h)) && items.length < 4) { const t = m[2].trim(); if (t.length > 7 && !seen.has(t.substring(0,8)) && !t.includes('查看') && !t.includes('更多') && !t.includes('PHOENIX')) { seen.add(t.substring(0,8)); items.push({ t: t.substring(0,50), u: m[1] }); } } return items.map(i => ({ t: i.t, s: '凤凰网评', src: '凤凰网', u: i.u })); } catch (e) { return []; }
}

async function s12() {
  try { const h = await fetch('https://www.caixin.com/'); const seen = new Set(), items = []; let m; const re = /<a[^>]*href="(https?:\/\/www\.caixin\.com[^"]+)"[^>]*>([^<]{8,50})<\/a>/g; while ((m = re.exec(h)) && items.length < 3) { const t = m[2].trim(); if (t.length > 7 && !seen.has(t.substring(0,8))) { seen.add(t.substring(0,8)); items.push({ t: t.substring(0,50), u: m[1] }); } } return items.map(i => ({ t: i.t, s: '财新独家', src: '财新网', u: i.u })); } catch (e) { return []; }
}

async function s13() {
  try { const h = await fetch('https://www.nbd.com.cn/'); const seen = new Set(), items = []; let m; const re = /<a[^>]*href="(https?:\/\/www\.nbd\.com\.cn[^"]+)"[^>]*>([^<]{8,50})<\/a>/g; while ((m = re.exec(h)) && items.length < 4) { const t = m[2].trim(); if (t.length > 7 && !seen.has(t.substring(0,8))) { seen.add(t.substring(0,8)); items.push({ t: t.substring(0,50), u: m[1] }); } } return items.map(i => ({ t: i.t, s: '每经资讯', src: '每日经济新闻', u: i.u })); } catch (e) { return []; }
}

async function s14() {
  try { const h = await fetch('https://www.stcn.com/'); const seen = new Set(), items = []; let m; const re = /<a[^>]*href="(https?:\/\/www\.stcn\.com[^"]+)"[^>]*>([^<]{8,50})<\/a>/g; while ((m = re.exec(h)) && items.length < 4) { const t = m[2].trim(); if (t.length > 7 && !seen.has(t.substring(0,8))) { seen.add(t.substring(0,8)); items.push({ t: t.substring(0,50), u: m[1] }); } } return items.map(i => ({ t: i.t, s: '券商中国', src: '证券时报', u: i.u })); } catch (e) { return []; }
}

async function s15() {
  try { const h = await fetch('https://www.cs.com.cn/'); const seen = new Set(), items = []; let m; const re = /<a[^>]*href="(https?:\/\/www\.cs\.com\.cn[^"]+)"[^>]*>([^<]{8,50})<\/a>/g; while ((m = re.exec(h)) && items.length < 3) { const t = m[2].trim(); if (t.length > 7 && !seen.has(t.substring(0,8))) { seen.add(t.substring(0,8)); items.push({ t: t.substring(0,50), u: m[1] }); } } return items.map(i => ({ t: i.t, s: '中证报', src: '中国证券报', u: i.u })); } catch (e) { return []; }
}

async function s16() {
  try {
    const h = await fetch('https://www.ithome.com/rss/'); const items = []; const seen = new Set();
    let m; const re = /<title><!\[CDATA\[([^\]]+)\]\]><\/title>/g; while ((m = re.exec(h)) && items.length < 4) { const t = m[1].trim(); if (t.length > 4 && t !== 'IT之家' && !seen.has(t.substring(0,8))) { seen.add(t.substring(0,8)); items.push(t); } }
    if (items.length < 2) { const re2 = /<title>([^<]+)<\/title>/g; let first = true; while ((m = re2.exec(h)) && items.length < 4) { if (first) { first = false; continue; } const t = m[1].trim(); if (t.length > 4 && !seen.has(t.substring(0,8))) { seen.add(t.substring(0,8)); items.push(t); } } }
    return items.map(t => ({ t: t.substring(0,50), s: '科技资讯', src: 'IT之家', u: 'https://www.ithome.com/' }));
  } catch (e) { return []; }
}

async function s17() {
  try {
    const h = await fetch('https://top.baidu.com/board?tab=realtime'); const items = []; const seen = new Set();
    for (const pat of ['data-title="([^"]+)"', '"word":"([^"]+)"']) { let m; const re = new RegExp(pat, 'g'); while ((m = re.exec(h)) && items.length < 6) { const t = m[1].trim(); if (t.length > 3 && !seen.has(t.substring(0,6))) { seen.add(t.substring(0,6)); items.push(t); } } if (items.length >= 4) break; }
    return items.map(t => ({ t: t.substring(0,40), s: '热搜话题', src: '百度热搜', u: 'https://www.baidu.com/s?wd=' + encodeURIComponent(t) }));
  } catch (e) { return []; }
}

async function s18() {
  try { const h = await fetch('https://www.thepaper.cn/'); const seen = new Set(), items = []; let m; const re = /<a[^>]*href="(https?:\/\/www\.thepaper\.cn[^"]+)"[^>]*>([^<]{8,50})<\/a>/g; while ((m = re.exec(h)) && items.length < 4) { const t = m[2].trim(); if (t.length > 7 && !seen.has(t.substring(0,8))) { seen.add(t.substring(0,8)); items.push({ t: t.substring(0,50), u: m[1] }); } } return items.map(i => ({ t: i.t, s: '深度报道', src: '澎湃新闻', u: i.u })); } catch (e) { return []; }
}

async function s19() {
  try { const h = await fetch('https://36kr.com/'); const items = []; const seen = new Set(); let m; const re = /"title":"([^"]{6,50})"/g; while ((m = re.exec(h)) && items.length < 4) { const t = m[1].trim(); if (t.length > 5 && !seen.has(t.substring(0,6)) && !t.includes('{{')) { seen.add(t.substring(0,6)); items.push(t); } } if (items.length < 2) { const re2 = /"widgetTitle":"([^"]{6,50})"/g; while ((m = re2.exec(h)) && items.length < 4) { const t = m[1].trim(); if (t.length > 5 && !seen.has(t.substring(0,6))) { seen.add(t.substring(0,6)); items.push(t); } } } return items.map(t => ({ t: t.substring(0,45), s: '科技商业', src: '36氪', u: 'https://36kr.com/' })); } catch (e) { return []; }
}

async function s20() {
  try { const h = await fetch('https://www.donews.com/'); const seen = new Set(), items = []; let m; const re = /<a[^>]*href="(https?:\/\/www\.donews\.com[^"]+)"[^>]*>([^<]{8,50})<\/a>/g; while ((m = re.exec(h)) && items.length < 3) { const t = m[2].trim(); if (t.length > 7 && !seen.has(t.substring(0,8))) { seen.add(t.substring(0,8)); items.push({ t: t.substring(0,50), u: m[1] }); } } return items.map(i => ({ t: i.t, s: '互联网资讯', src: 'Donews', u: i.u })); } catch (e) { return []; }
}

async function s21() {
  try { const h = await fetch('https://sports.sina.com.cn/'); const seen = new Set(), items = []; let m; const re = /<a[^>]*href="(https?:\/\/sports\.sina\.com\.cn[^"]+)"[^>]*>([^<]{8,50})<\/a>/g; while ((m = re.exec(h)) && items.length < 4) { const t = m[2].trim(); if (t.length > 7 && !seen.has(t.substring(0,8)) && !t.includes('更多') && !t.includes('频道')) { seen.add(t.substring(0,8)); items.push({ t: t.substring(0,50), u: m[1] }); } } return items.map(i => ({ t: i.t, s: '体育资讯', src: '新浪体育', u: i.u })); } catch (e) { return []; }
}

async function s22() {
  try { const h = await fetch('https://www.huxiu.com/'); const seen = new Set(), items = []; let m; const re = /<h2[^>]*>([^<]+)<\/h2>/g; while ((m = re.exec(h)) && items.length < 3) { const t = m[1].trim(); if (t.length > 5 && !seen.has(t.substring(0,8))) { seen.add(t.substring(0,8)); items.push(t); } } return items.map(t => ({ t: t.substring(0,45), s: '深度商业', src: '虎嗅', u: 'https://www.huxiu.com/' })); } catch (e) { return []; }
}

async function s23() {
  try { const h = await fetch('https://health.people.com.cn/'); const seen = new Set(), items = []; let m; const re = /<a[^>]*href="(https?:\/\/health\.people\.com\.cn[^"]+)"[^>]*>([^<]{8,50})<\/a>/g; while ((m = re.exec(h)) && items.length < 3) { const t = m[2].trim(); if (t.length > 7 && !seen.has(t.substring(0,8)) && !t.includes('人民') && !t.includes('健康')) { seen.add(t.substring(0,8)); items.push({ t: t.substring(0,50), u: m[1] }); } } return items.map(i => ({ t: i.t, s: '健康资讯', src: '人民健康', u: i.u })); } catch (e) { return []; }
}

async function s24() {
  try { const h = await fetch('https://www.toutiao.com/'); const items = []; const seen = new Set(); for (const pat of ['"title":"([^"]{6,50})"', '"abstract":"([^"]{6,50})"', '"word":"([^"]{6,50})"']) { let m; const re = new RegExp(pat, 'g'); while ((m = re.exec(h)) && items.length < 5) { const t = m[1].trim(); if (t.length > 5 && !seen.has(t.substring(0,6)) && !t.includes('{{') && !t.includes('var')) { seen.add(t.substring(0,6)); items.push(t); } } if (items.length >= 3) break; } return items.map(t => ({ t: t.substring(0,40), s: '热点话题', src: '今日头条', u: 'https://www.toutiao.com/' })); } catch (e) { return []; }
}

async function s25() {
  try { const h = await fetch('https://www.eastmoney.com/'); const seen = new Set(), items = []; let m; const re = /<a[^>]*href="(https?:\/\/[^"]*eastmoney\.com[^"]*)"[^>]*>([^<]{6,50})<\/a>/g; while ((m = re.exec(h)) && items.length < 5) { const t = m[2].trim(); const keywords = ['股','涨','跌','亿','元','A股','市场','投资','基金','行情','板块']; if (t.length > 5 && !seen.has(t.substring(0,8)) && keywords.some(k => t.includes(k))) { seen.add(t.substring(0,8)); items.push({ t: t.substring(0,50), u: m[1] }); } } return items.map(i => ({ t: i.t, s: '财经资讯', src: '东方财富', u: i.u })); } catch (e) { return []; }
}

async function s26() {
  try { const h = await fetch('https://xueqiu.com/'); const seen = new Set(), items = []; let m; const re = /<a[^>]*href="(https?:\/\/xueqiu\.com\/\d+\/\d+[^"]*)"[^>]*>([^<]{6,50})<\/a>/g; while ((m = re.exec(h)) && items.length < 4) { const t = m[2].trim(); if (t.length > 5 && !seen.has(t.substring(0,8))) { seen.add(t.substring(0,8)); items.push({ t: t.substring(0,50), u: m[1] }); } } return items.map(i => ({ t: i.t, s: '投资者社区', src: '雪球', u: i.u })); } catch (e) { return []; }
}

async function s27() {
  try { const h = await fetch('https://www.huanqiu.com/'); const seen = new Set(), items = []; let m; const re = /<a[^>]*href="(https?:\/\/[^"]*huanqiu\.com[^"]*)"[^>]*>([^<]{8,50})<\/a>/g; while ((m = re.exec(h)) && items.length < 4) { const t = m[2].trim(); if (t.length > 7 && !seen.has(t.substring(0,8))) { seen.add(t.substring(0,8)); items.push({ t: t.substring(0,50), u: m[1] }); } } return items.map(i => ({ t: i.t, s: '国际视野', src: '环球网', u: i.u })); } catch (e) { return []; }
}

async function s28() {
  try { const h = await fetch('https://www.guancha.cn/'); const seen = new Set(), items = []; let m; const re = /<a[^>]*href="(https?:\/\/www\.guancha\.cn\/[^"]+)"[^>]*>([^<]{8,50})<\/a>/g; while ((m = re.exec(h)) && items.length < 4) { const t = m[2].trim(); if (t.length > 7 && !seen.has(t.substring(0,8))) { seen.add(t.substring(0,8)); items.push({ t: t.substring(0,50), u: m[1] }); } } return items.map(i => ({ t: i.t, s: '深度观察', src: '观察者网', u: i.u })); } catch (e) { return []; }
}

async function s29() {
  try { const h = await fetch('https://ent.sina.com.cn/'); const seen = new Set(), items = []; let m; const re = /<a[^>]*href="(https?:\/\/ent\.sina\.com\.cn[^"]+)"[^>]*>([^<]{8,50})<\/a>/g; while ((m = re.exec(h)) && items.length < 4) { const t = m[2].trim(); if (t.length > 7 && !seen.has(t.substring(0,8)) && !t.includes('更多') && !t.includes('频道')) { seen.add(t.substring(0,8)); items.push({ t: t.substring(0,50), u: m[1] }); } } return items.map(i => ({ t: i.t, s: '文娱资讯', src: '新浪娱乐', u: i.u })); } catch (e) { return []; }
}

async function s30() {
  try { const h = await fetch('https://sports.163.com/'); const seen = new Set(), items = []; let m; const re = /<a[^>]*href="(https?:\/\/sports\.163\.com[^"]+)"[^>]*>([^<]{8,50})<\/a>/g; while ((m = re.exec(h)) && items.length < 4) { const t = m[2].trim(); if (t.length > 7 && !seen.has(t.substring(0,8)) && !t.includes('更多') && !t.includes('直播')) { seen.add(t.substring(0,8)); items.push({ t: t.substring(0,50), u: m[1] }); } } return items.map(i => ({ t: i.t, s: '体育赛事', src: '网易体育', u: i.u })); } catch (e) { return []; }
}

async function s31() {
  try { const h = await fetch('https://api.bilibili.com/x/web-interface/ranking/v2?rid=0&type=all'); const j = JSON.parse(h); return j.data.list.slice(0,4).map(i => ({ t: (i.title || '').substring(0,50), s: '播放:' + Math.floor((i.stat?.view||0)/10000) + '万', src: 'B站热门', u: 'https://www.bilibili.com/video/' + i.bvid })).filter(i => i.t.length > 4); } catch (e) { return []; }
}

async function s32() {
  try { const h = await fetch('https://weibo.com/ajax/side/hotSearch'); const j = JSON.parse(h); return j.data.realtime.filter(i => i.word && i.word.length > 4).slice(0,8).map(i => ({ t: i.word.substring(0,40), s: '热搜#' + i.rank, src: '微博热搜', u: 'https://s.weibo.com/weibo?q=' + encodeURIComponent(i.word) })); } catch (e) { return []; }
}

async function s33() {
  try { const h = await fetch('https://www.jd.com/'); const seen = new Set(), items = []; let m; const re = /<a[^>]*href="(https?:\/\/item\.jd\.com\/[^"]+)"[^>]*title="([^"]{6,50})"/g; while ((m = re.exec(h)) && items.length < 4) { const t = m[2].trim(); if (t.length > 5 && !seen.has(t.substring(0,8)) && !t.includes('广告') && !t.includes('更多')) { seen.add(t.substring(0,8)); items.push({ t: t.substring(0,50), u: m[1] }); } } if (items.length < 2) { const re2 = /"title":"([^"]{6,50})"/g; while ((m = re2.exec(h)) && items.length < 4) { const t = m[1].trim(); if (t.length > 5 && !seen.has(t.substring(0,8)) && !t.includes('{{') && !t.includes('var ')) { seen.add(t.substring(0,8)); items.push({ t: t.substring(0,50), u: 'https://www.jd.com/' }); } } } return items.map(i => ({ t: i.t, s: '热卖商品', src: '京东', u: i.u })); } catch (e) { return []; }
}

async function s34() {
  try { const h = await fetch('https://www.douyin.com/'); const seen = new Set(), items = []; let m; const re = /"title":"([^"]{4,50})"/g; while ((m = re.exec(h)) && items.length < 4) { const t = m[1].trim(); if (t.length > 4 && !seen.has(t.substring(0,8)) && !t.includes('{{') && !t.includes('var') && !t.includes('\\x')) { seen.add(t.substring(0,8)); items.push(t); } } return items.map(t => ({ t: t.substring(0,40), s: '热门视频', src: '抖音', u: 'https://www.douyin.com/' })); } catch (e) { return []; }
}

async function s35() {
  try { const h = await fetch('https://music.163.com/discover/toplist'); const seen = new Set(), items = []; let m; const re = /<a[^>]*href="\/song[^"]*"[^>]*>([^<]{6,40})<\/a>/g; while ((m = re.exec(h)) && items.length < 3) { const t = m[1].trim(); if (t.length > 5 && !seen.has(t.substring(0,8))) { seen.add(t.substring(0,8)); items.push(t); } } return items.map(t => ({ t: t.substring(0,40), s: '热歌榜', src: '网易云音乐', u: 'https://music.163.com/' })); } catch (e) { return []; }
}

async function s36() {
  try { const h = await fetch('https://www.smzdm.com/'); const seen = new Set(), items = []; let m; const re = /<a[^>]*href="(https?:\/\/[^"]*smzdm\.com[^"]+)"[^>]*>([^<]{8,50})<\/a>/g; while ((m = re.exec(h)) && items.length < 4) { const t = m[2].trim(); if (t.length > 7 && !seen.has(t.substring(0,8))) { seen.add(t.substring(0,8)); items.push({ t: t.substring(0,50), u: m[1] }); } } return items.map(i => ({ t: i.t, s: '好价推荐', src: '什么值得买', u: i.u })); } catch (e) { return []; }
}

async function getStocks() {
  try { const h = await fetch('https://push2.eastmoney.com/api/qt/ulist.np/get?fltt=2&secids=1.000001,0.399001,0.399006,1.000688,1.000300,1.000016,1.000905,0.399001'); const j = JSON.parse(h); return j.data.diff.map(s => ({ n: s.f14 || '--', v: (s.f2 || 0).toFixed(2), c: (s.f3 || 0) >= 0 ? '+' + (s.f3 || 0).toFixed(2) + '%' : (s.f3 || 0).toFixed(2) + '%', cls: (s.f3 || 0) >= 0 ? 'up' : 'down' })); } catch (e) { return []; }
}

async function getForex() {
  try { const h = await fetch('https://api.exchangerate-api.com/v4/latest/CNY'); const j = JSON.parse(h); const r = j.rates; const symbols = ['USD','EUR','JPY','GBP','HKD','KRW']; const fx = {}; symbols.forEach(s => { if (r[s] && r[s] > 0) fx[s] = (1 / r[s]).toFixed(4); }); return fx; } catch (e) { return {}; }
}

function getDate() { const d = new Date(); d.setHours(d.getHours() + 8); const days = ['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday']; return d.getFullYear() + '年' + (d.getMonth()+1) + '月' + d.getDate() + '日 ' + days[d.getDay()]; }

function classify(items, categories) {
  const result = {}; Object.keys(categories).forEach(k => result[k] = []);
  const other = []; const used = new Set();
  items.forEach(item => {
    const tt = (item.t || item.title || '').toLowerCase();
    let placed = false;
    for (const [cat, keywords] of Object.entries(categories)) {
      const kws = keywords.split('|').filter(Boolean);
      if (kws.some(kw => tt.includes(kw.toLowerCase().trim()))) {
        result[cat].push(item); used.add(item); placed = true; break;
      }
    }
    if (!placed) other.push(item);
  });
  result['其他'] = other;
  return result;
}

function buildPage(opts) {
  const { stocks, forex, newsByCategory, categories, labels, allNews } = opts;
  const total = allNews.length;
  const activeSrcs = new Set(allNews.map(n => n.src)).size;
  
  const fxCny = forex && Object.keys(forex).length > 0 ? forex : { USD: '7.2420', EUR: '7.8321', JPY: '0.0450', GBP: '9.1250', HKD: '0.9280', KRW: '0.0052' };
  const fxKeys = ['USD','EUR','JPY','GBP','HKD','KRW'];
  const fxNames = {USD:'美元',EUR:'欧元',JPY:'日元',GBP:'英镑',HKD:'港币',KRW:'韩元'};
  
  const stockRows = stocks && stocks.length > 0 ? stocks.map(s => '<tr><td>' + s.n + '</td><td class="' + s.cls + '">' + s.v + '</td><td class="' + s.cls + '">' + s.c + '</td></tr>').join('\n') : '<tr><td colspan="3">暂无数据</td></tr>';
  
  const fxRows = fxKeys.map(k => '<tr><td>' + fxNames[k] + '(' + k + ')</td><td>' + fxCny[k] + '</td><td>1 CNY</td></tr>').join('\n');
  
  const catOrder = ['国际', '科技', 'A股民生', '财经', '体育', '文娱', '健康', '其他'];
  
  let newsHtml = '';
  catOrder.forEach(cat => {
    const items = newsByCategory[cat] || [];
    if (items.length === 0) return;
    const icon = {\n      '国际': '\uD83C\uDF0D', '科技': '\uD83D\uDD0C', 'A股民生': '\uD83D\uDCC8', '财经': '\uD83D\uDCB0',\n      '体育': '\u26BD', '文娱': '\uD83C\uDFAC', '健康': '\u2764\uFE0F', '其他': '\uD83D\uDCC5'\n    }[cat] || '\uD83D\uDCC5';
    const bg = {\n      '国际': '#e74c3c', '科技': '#3498db', 'A股民生': '#e67e22', '财经': '#1abc9c',\n      '体育': '#2ecc71', '文娱': '#9b59b6', '健康': '#e91e63', '其他': '#95a5a6'\n    }[cat] || '#95a5a6';
    newsHtml += '<div class="section"><h2 style="border-left:4px solid ' + bg + ';padding-left:12px">' + icon + ' ' + cat + ' <span class="badge">' + items.length + '</span></h2><div class="news-grid">' +\n      items.map(item => {
        const t = item.t || item.title || '';
        const s = item.s || '资讯';
        const src = item.src || '';
        const u = item.u || '#';
        const srcBadge = labels.includes(src) ? '<span class="src">' + src + '</span>' : '';
        return '<a href="' + u + '" class="news-card" target="_blank" rel="noopener">' + srcBadge + '<span class="title">' + t + '</span><span class="source">' + s + '</span></a>';\n      }).join('\n') + '</div></div>';
  });
  
  const labelHtml = labels.filter(l => activeSrcs >= labels.indexOf(l) + 1 || allNews.some(n => n.src === l)).join(' · ');
  
  const html = '<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>每日全球资讯</title><style>\
  *{margin:0;padding:0;box-sizing:border-box}\n  body{font-family:-apple-system,BlinkMacSystemFont,\\\"Segoe UI\\\",Roboto,Helvetica,Arial,sans-serif;background:#0d1117;color:#e6edf3;line-height:1.6;min-height:100vh}\n  .container{max-width:1200px;margin:0 auto;padding:16px 12px}\n  h1{font-size:1.5em;margin:16px 0 8px;background:linear-gradient(135deg,#58a6ff,#bc8cff);-webkit-background-clip:text;-webkit-text-fill-color:transparent}\n  .subtitle{color:#8b949e;font-size:0.85em;margin-bottom:16px;display:flex;flex-wrap:wrap;gap:4px 8px;align-items:baseline}\n  .subtitle .labels{font-size:0.78em;color:#58a6ff;width:100%;line-height:1.8}\n  .badge{display:inline-block;background:#30363d;color:#e6edf3;border-radius:10px;padding:0 8px;font-size:0.7em;vertical-align:middle;font-weight:400;margin-left:6px}\n  .section{margin-bottom:20px}\n  .section h2{font-size:1.05em;margin-bottom:8px;display:flex;align-items:center}\n  .news-grid{display:grid;grid-template-columns:1fr;gap:6px}\n  @media(min-width:640px){.news-grid{grid-template-columns:1fr 1fr}}.news-card{display:flex;flex-direction:column;padding:8px 10px;background:#161b22;border:1px solid #30363d;border-radius:6px;text-decoration:none;color:#e6edf3;transition:all 0.2s}.news-card:hover{background:#1c2128;border-color:#58a6ff;transform:translateX(2px)}.news-card .title{font-size:0.88em;line-height:1.4;margin-bottom:4px}.news-card .source{font-size:0.74em;color:#8b949e}.news-card .src{display:inline-block;font-size:0.65em;background:#1f6feb33;color:#58a6ff;padding:1px 6px;border-radius:3px;margin-bottom:3px;align-self:flex-start}\n  .stocks-section{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:12px;margin-bottom:20px}\n  .stocks-section h3{font-size:0.95em;margin-bottom:8px;color:#7ee787}\n  table{width:100%;border-collapse:collapse;font-size:0.84em}\n  th,td{text-align:left;padding:5px 8px;border-bottom:1px solid #30363d}\n  th{color:#8b949e;font-weight:400;font-size:0.8em}\n  .up{color:#3fb950;font-weight:500}.down{color:#f85149;font-weight:500}\n  footer{text-align:center;color:#484f58;font-size:0.75em;padding:24px 0 12px;border-top:1px solid #21262d;margin-top:16px}\n  a{color:#58a6ff;text-decoration:none}\n  .error{color:#f85149;font-size:0.8em;padding:6px 0}\n  .grid-2{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:16px}\n  @media(max-width:480px){.grid-2{grid-template-columns:1fr}}\\n</style></head><body><div class=\\\"container\\\"><h1>\uD83C\uDF0D 每日全球资讯</h1><div class=\\\"subtitle\\\"><span>' + getDate() + '</span><span style=\\\"color:#8b949e;background:#21262d;padding:0 8px;border-radius:4px;font-size:0.8em\\\">' + total + '条 \u00B7 ' + activeSrcs + '个来源</span><span class=\\\"labels\\\">' + labelHtml + '</span></div>' +\n    '<div class=\\\"grid-2\\\"><div class=\\\"stocks-section\\\"><h3>\uD83D\uDCCA 行情</h3><table><thead><tr><th>指数</th><th>最新</th><th>涨跌幅</th></tr></thead><tbody>' + stockRows + '</tbody></table></div>' +\n    '<div class=\\\"stocks-section\\\"><h3>\uD83D\uDCB1 汇率(1 CNY)</h3><table><thead><tr><th>货币</th><th>汇率</th><th>基准</th></tr></thead><tbody>' + fxRows + '</tbody></table></div></div>' +\n    newsHtml + '<footer>数据来源: 同花顺/华尔街见闻/财联社/第一财经/百度/新浪/新华/人民/央视/凤凰/网易/澎湃/36氪/IT之家/B站/微博/京东/抖音/网易云音乐/什么值得买等 \u00B7 每日自动更新 \u00B7 ' + getDate().split(' ')[0] + '</footer></div></body></html>';\n  return html;\n}

async function readPY(){
  try { return JSON.parse(fs.readFileSync('news_data.json','utf8')); } catch(e) { return null; }
}

async function main(){
  console.log('=== JS生成器 ===');\n  const pyData = await readPY();\n  let all = [];\n  let labels = ['同花顺','华尔街见闻','财联社','第一财经','网易','新浪财经','新华网','人民网','中国新闻网','央视新闻','凤凰网','财新网','每经','证券时报','中证报','IT之家','百度','澎湃新闻','36氪','Donews','新浪体育','虎嗅','人民健康','今日头条','东方财富','雪球','环球网','观察者网','新浪娱乐','网易体育','B站热门','微博热搜','京东','抖音','网易云音乐','什么值得买'];\n  \n  if(pyData && pyData.news && Array.isArray(pyData.news) && pyData.news.length > 0){\n    const srcFns = ['s1','s2','s3','s4','s5','s6','s7','s8','s9','s10','s11','s12','s13','s14','s15','s16','s17','s18','s19','s20','s21','s22','s23','s24','s25','s26','s27','s28','s29','s30','s31','s32','s33','s34','s35','s36'];\n    pyData.news.forEach((items, idx) => {\n      if(Array.isArray(items)){\n        items.forEach(item => { all.push(item); });\n        if(items.length > 0) console.log('PY:' + (pyData.labels?.[idx] || idx) + ':' + items.length);\n      }\n    });\n    if(pyData.stocks && pyData.stocks.length > 0) console.log('Stocks:live');\n    if(pyData.forex && Object.keys(pyData.forex).length > 0) console.log('Forex:live');\n  } else {\n    console.log('No PY data, fetching directly...');\n    const allFns = [s1,s2,s3,s4,s5,s6,s7,s8,s9,s10,s11,s12,s13,s14,s15,s16,s17,s18,s19,s20,s21,s22,s23,s24,s25,s26,s27,s28,s29,s30,s31,s32,s33,s34,s35,s36];\n    for(let i = 0; i < allFns.length; i++){\n      try {\n        const items = await allFns[i]();\n        if(Array.isArray(items) && items.length > 0){\n          items.forEach(item => all.push(item));\n          console.log(labels[i] + ':' + items.length);\n        }\n      } catch(e) {}\n    }\n  }\n  \n  const categories = {\n    '国际': '美国|特朗普|拜登|欧盟|北约|联合国|俄罗斯|乌克兰|伊朗|以色列|巴勒斯坦|中东|亚洲|欧洲|非洲|美洲|全球|国际|外交|制裁|关税|WTO|G7|G20|贸易战|地缘|冲突|战争|和平|难民|核武器|导弹|战机|军舰|大使|领事|访问|峰会|谈判|协议|退出|加入|世卫|气候|巴黎协定|人权',\n    '科技': 'AI|人工智能|芯片|半导体|华为|苹果|微软|谷歌|Meta|特斯拉|SpaceX|5G|6G|量子|算法|大模型|GPT|LLM|机器人|自动驾驶|云计算|区块链|NFT|元宇宙|VR|AR|激光雷达|传感器|操作系统|手机|iPhone|高通|英伟达|AMD|英特尔|台积电|三星|小米|OPPO|vivo|荣耀|蔚来|小鹏|理想|比亚迪|互联网|软件|数据|安全|黑客|漏洞|专利|创新|科技',\n    '体育': '金牌|银牌|铜牌|奥运|亚运|世界杯|欧冠|NBA|CBA|中超|英超|西甲|意甲|德甲|法甲|网球|F1|电竞|运动员|教练|选手|冠军|决赛|半决赛|资格赛|预选赛|世锦赛|马拉松|游泳|田径|体操|跳水|举重|乒乓球|羽毛球|足球|篮球|排球|中国足球|国足|联赛|赛事|竞技|球队|主场|客场',\n    '文娱': '电影|票房|音乐|演唱会|综艺|游戏|明星|导演|电视剧|Netflix|迪士尼|B站|抖音|快手|舞台|广告|视频|直播|演出',\n    '健康': '疫情|疫苗|新冠|病毒|疾病|诊断|治疗|患者|医院|医生|手术|药物|药品|药监|FDA|临床|疫苗|传染病|癌症|糖尿病|高血压|心脏|大脑|基因|干细胞|中医|中药|营养|健身|食品|安全|污染|环境',\n    'A股民生': 'A股|上证|深证|创业板|科创板|北交所|股市|股票|基金|理财|保险|银行|利率|降息|加息|存款|贷款|住房|公积金|房贷|房价|地产|土地|税收|个税|财政|财政|发改委|央企|国企|GDP|CPI|PPI|涨幅|跌幅|沪深|千亿|亿|万亿|证监会|交易所',\n    '财经': '美股|标普|纳斯达克|道指|期货|黄金|原油|大宗商品|数字货币|比特币|区块链|交易所|IPO|上市|融资|投资|资本|私募|风投|资产|估值|财报|营收|利润|市值|分红|回购|经济|消费|通胀|通缩|美联储|央行'\n  };\n  \n  const classified = classify(all, categories);\n  const html = buildPage({\n    stocks: pyData?.stocks || await getStocks(),\n    forex: pyData?.forex || await getForex(),\n    newsByCategory: classified,\n    categories: Object.keys(categories),\n    labels: labels,\n    allNews: all\n  });\n  \n  fs.writeFileSync('index.html', html, 'utf8');\n  console.log('\n=== 完成: ' + all.length + '条 \u00B7 ' + new Set(all.map(n => n.src)).size + '个来源 ===');\n}\n\nmain().catch(e => { console.log(e.message); process.exit(1); });