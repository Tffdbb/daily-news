const fs = require('fs');
const https = require('https');

function fetch(url) {
  return new Promise(r => {
    const opts = {headers:{'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}, timeout:8000};
    https.get(url, opts, res => {
      let d = '';
      res.on('data', c => d += c);
      res.on('end', () => r(d));
    }).on('error', () => r(''));
  });
}

function extract(html, pat, minLen, maxCount) {
  const seen = new Set(), items = [];
  const re = new RegExp(pat, 'g'); let m;
  while ((m = re.exec(html)) && items.length < (maxCount || 5)) {
    const t = m[1].trim();
    if (t.length > (minLen||6) && t.length < 55 && !seen.has(t.substring(0,8)) && !t.includes('更多') && !t.includes('广告')) {
      seen.add(t.substring(0,8)); items.push(t);
    }
  }
  return items;
}

// ====== 20 Data Sources ======

// 1. 同花顺
async function s1() {
  try {
    const j = JSON.parse(await fetch('https://news.10jqka.com.cn/tapp/news/push/stock?type=all'));
    return (j.data && j.data.list || []).filter(i => i.title && i.title.length > 4).slice(0, 10).map(i => ({
      t: i.title.trim().substring(0,55), s: (i.digest||'').replace(/<[^>]+>/g,'').trim().substring(0,80)||'同花顺快讯',
      src: '同花顺', u: 'https://www.10jqka.com.cn/'
    }));
  } catch(e) { return []; }
}

// 2. 华尔街见闻
async function s2() {
  try {
    const d = JSON.parse(await fetch('https://api.wallstreetcn.com/apiv1/content/lives?channel=global-channel&limit=8'));
    if (d.data && d.data.items) return d.data.items.filter(i => i.title || i.content_text).map(i => ({
      t: (i.title || i.content_text||'').replace(/<[^>]+>/g,'').trim().substring(0,55), s: '见闻快讯', src: '华尔街见闻',
      u: i.uri ? 'https://wallstreetcn.com'+i.uri : 'https://wallstreetcn.com/'
    }));
    return [];
  } catch(e) { return []; }
}

// 3. 财联社
async function s3() {
  try {
    const h = await fetch('https://www.cls.cn/');
    return extract(h, '"title"\\s*:\\s*"([^"]+)"', 6, 5).map(t => ({t, s:'电报快讯', src:'财联社', u:'https://www.cls.cn/'}));
  } catch(e) { return []; }
}

// 4. 第一财经
async function s4() {
  try {
    const h = await fetch('https://www.yicai.com/');
    const seen = new Set(), items = [];
    const re = /<a[^>]*href="(https:\/\/www\.yicai\.com\/news\/[^"]+)"[^>]*>([^<]{8,55})<\/a>/g; let m;
    while ((m = re.exec(h)) && items.length < 3) {
      const t = m[2].replace(/[<>]/g,'').trim();
      if (t.length > 8 && !seen.has(t.substring(0,8))) { seen.add(t.substring(0,8)); items.push({t:t.substring(0,50), u:m[1]}); }
    }
    return items.map(i => ({t:i.t, s:'一财', src:'第一财经', u:i.u}));
  } catch(e) { return []; }
}

// 5. 网易新闻
async function s5() {
  try {
    const h = await fetch('https://news.163.com/');
    const seen = new Set(), items = [];
    const re = /<a[^>]*href="(https:\/\/news\.163\.com\/[^"]+)"[^>]*>([^<]{8,45})<\/a>/g; let m;
    while ((m = re.exec(h)) && items.length < 4) {
      const t = m[2].trim();
      if (t.length > 8 && !seen.has(t.substring(0,8))) { seen.add(t.substring(0,8)); items.push({t:t.substring(0,50), u:m[1]}); }
    }
    return items.map(i => ({t:i.t, s:'网易精选', src:'网易新闻', u:i.u}));
  } catch(e) { return []; }
}

// 6. 新浪财经
async function s6() {
  try {
    const h = await fetch('https://finance.sina.com.cn/');
    const seen = new Set(), items = [];
    const re = /<a[^>]*href="(https:\/\/finance\.sina\.com\.cn[^"]*)"[^>]*>([^<]{8,45})<\/a>/g; let m;
    while ((m = re.exec(h)) && items.length < 4) {
      const t = m[2].trim();
      if (!seen.has(t.substring(0,8)) && !t.includes('更多') && !t.includes('客户端')) {
        seen.add(t.substring(0,8)); items.push({t:t.substring(0,50), u:m[1]});
      }
    }
    return items.map(i => ({t:i.t, s:'财经资讯', src:'新浪财经', u:i.u}));
  } catch(e) { return []; }
}

// 7. 新华网
async function s7() {
  try {
    const h = await fetch('https://www.xinhuanet.com/');
    const seen = new Set(), items = [];
    const re = /<a[^>]*href="([^"]+\.htm)"[^>]*>([^<]{8,45})<\/a>/g; let m;
    while ((m = re.exec(h)) && items.length < 3) {
      const t = m[2].trim();
      if (!seen.has(t.substring(0,8)) && !t.includes('English') && !t.includes('Рус') && !t.includes('Portugu') && !t.includes('更多')) {
        seen.add(t.substring(0,8)); items.push({t: t.substring(0,50), u: m[1]});
      }
    }
    return items.map(i => ({t:i.t, s:'官方发布', src:'新华网', u: i.u.startsWith('http') ? i.u : 'https://www.xinhuanet.com'+i.u}));
  } catch(e) { return []; }
}

// 8. 人民网
async function s8() {
  try {
    const h = await fetch('https://www.people.com.cn/');
    const seen = new Set(), items = [];
    const re = /<a[^>]*href="(https?:\/\/[^"]*people\.com\.cn[^"]*)"[^>]*>([^<]{8,45})<\/a>/g; let m;
    while ((m = re.exec(h)) && items.length < 3) {
      const t = m[2].trim();
      if (!seen.has(t.substring(0,8)) && !t.includes('许可证') && !t.includes('电信') && !t.includes('广告') && !t.includes('更多')) {
        seen.add(t.substring(0,8)); items.push({t: t.substring(0,50), u: m[1]});
      }
    }
    return items.map(i => ({t:i.t, s:'人民网', src:'人民网', u:i.u}));
  } catch(e) { return []; }
}

// 9. 中国新闻网
async function s9() {
  try {
    const h = await fetch('https://www.chinanews.com.cn/');
    const seen = new Set(), items = [];
    const re = /<a[^>]*href="(https?:\/\/www\.chinanews\.com\.cn[^"]+)"[^>]*>([^<]{8,50})<\/a>/g; let m;
    while ((m = re.exec(h)) && items.length < 4) {
      const t = m[2].trim();
      if (!seen.has(t.substring(0,8))) { seen.add(t.substring(0,8)); items.push({t: t.substring(0,50), u: m[1]}); }
    }
    return items.map(i => ({t:i.t, s:'即时新闻', src:'中国新闻网', u:i.u}));
  } catch(e) { return []; }
}

// 10. 央视新闻
async function s10() {
  try {
    const h = await fetch('https://news.cctv.com/');
    const seen = new Set(), items = [];
    const re = /<a[^>]*href="(https?:\/\/news\.cctv\.com[^"]+)"[^>]*>([^<]{8,50})<\/a>/g; let m;
    while ((m = re.exec(h)) && items.length < 3) {
      const t = m[2].trim();
      if (!seen.has(t.substring(0,8))) { seen.add(t.substring(0,8)); items.push({t: t.substring(0,50), u: m[1]}); }
    }
    return items.map(i => ({t:i.t, s:'央视报道', src:'央视新闻', u:i.u}));
  } catch(e) { return []; }
}

// 11. 凤凰网
async function s11() {
  try {
    const h = await fetch('https://www.ifeng.com/');
    const seen = new Set(), items = [];
    const re = /<a[^>]*href="(https?:\/\/[^"]*ifeng\.com[^"]*)"[^>]*>([^<]{8,45})<\/a>/g; let m;
    while ((m = re.exec(h)) && items.length < 4) {
      const t = m[2].trim();
      if (!seen.has(t.substring(0,8)) && !t.includes('查看') && !t.includes('更多') && !t.includes('PHOENIX')) {
        seen.add(t.substring(0,8)); items.push({t: t.substring(0,50), u: m[1]});
      }
    }
    return items.map(i => ({t:i.t, s:'凤凰网评', src:'凤凰网', u:i.u}));
  } catch(e) { return []; }
}

// 12. 财新网
async function s12() {
  try {
    const h = await fetch('https://www.caixin.com/');
    const seen = new Set(), items = [];
    const re = /<a[^>]*href="(https?:\/\/www\.caixin\.com[^"]+)"[^>]*>([^<]{8,50})<\/a>/g; let m;
    while ((m = re.exec(h)) && items.length < 3) {
      const t = m[2].trim();
      if (!seen.has(t.substring(0,8))) { seen.add(t.substring(0,8)); items.push({t: t.substring(0,50), u: m[1]}); }
    }
    return items.map(i => ({t:i.t, s:'财新独家', src:'财新网', u:i.u}));
  } catch(e) { return []; }
}

// 13. 每日经济新闻
async function s13() {
  try {
    const h = await fetch('https://www.nbd.com.cn/');
    const seen = new Set(), items = [];
    const re = /<a[^>]*href="(https?:\/\/www\.nbd\.com\.cn[^"]+)"[^>]*>([^<]{8,50})<\/a>/g; let m;
    while ((m = re.exec(h)) && items.length < 4) {
      const t = m[2].trim();
      if (!seen.has(t.substring(0,8))) { seen.add(t.substring(0,8)); items.push({t: t.substring(0,50), u: m[1]}); }
    }
    return items.map(i => ({t:i.t, s:'每经资讯', src:'每日经济新闻', u:i.u}));
  } catch(e) { return []; }
}

// 14. 证券时报
async function s14() {
  try {
    const h = await fetch('https://www.stcn.com/');
    const seen = new Set(), items = [];
    const re = /<a[^>]*href="(https?:\/\/www\.stcn\.com[^"]+)"[^>]*>([^<]{8,50})<\/a>/g; let m;
    while ((m = re.exec(h)) && items.length < 4) {
      const t = m[2].trim();
      if (!seen.has(t.substring(0,8))) { seen.add(t.substring(0,8)); items.push({t: t.substring(0,50), u: m[1]}); }
    }
    return items.map(i => ({t:i.t, s:'券商中国', src:'证券时报', u:i.u}));
  } catch(e) { return []; }
}

// 15. 中国证券报
async function s15() {
  try {
    const h = await fetch('https://www.cs.com.cn/');
    const seen = new Set(), items = [];
    const re = /<a[^>]*href="(https?:\/\/www\.cs\.com\.cn[^"]+)"[^>]*>([^<]{8,50})<\/a>/g; let m;
    while ((m = re.exec(h)) && items.length < 3) {
      const t = m[2].trim();
      if (!seen.has(t.substring(0,8))) { seen.add(t.substring(0,8)); items.push({t: t.substring(0,50), u: m[1]}); }
    }
    return items.map(i => ({t:i.t, s:'中证报', src:'中国证券报', u:i.u}));
  } catch(e) { return []; }
}

// 16. IT之家
async function s16() {
  try {
    const h = await fetch('https://www.ithome.com/');
    const items = []; const seen = new Set();
    const re = /<li>[\s\S]*?<a[^>]*href="(\/\d+\/\d+\/\d+\.htm)"[^>]*>([^<]{8,50})<\/a>[\s\S]*?<\/li>/g; let m;
    while ((m = re.exec(h)) && items.length < 3) {
      const t = m[2].trim();
      if (!seen.has(t.substring(0,8))) { seen.add(t.substring(0,8)); items.push({t: t.substring(0,50), u: m[1]}); }
    }
    return items.map(i => ({t:i.t, s:'科技资讯', src:'IT之家', u: 'https://www.ithome.com' + i.u}));
  } catch(e) { return []; }
}

// 17. 百度热搜
async function s17() {
  try {
    const h = await fetch('https://top.baidu.com/board?tab=realtime');
    const items = [];
    const reList = [/data-title="([^"]+)"/g, /"word":"([^"]+)"/g];
    for (const re of reList) {
      const seen = new Set(); let m;
      while ((m = re.exec(h)) && items.length < 6) {
        const t = m[1].trim();
        if (t.length > 3 && !seen.has(t.substring(0,6))) { seen.add(t.substring(0,6)); items.push({t: t.substring(0,40), u: 'https://www.baidu.com/s?wd='+encodeURIComponent(t)}); }
      }
      if (items.length >= 4) break;
    }
    return items.map(i => ({t:i.t, s:'热搜话题', src:'百度热搜', u:i.u}));
  } catch(e) { return []; }
}

// 18. 虎嗅
async function s18() {
  try {
    const h = await fetch('https://www.huxiu.com/');
    const items = []; const seen = new Set();
    const re = /<a[^>]*href="(\/article\/\d+\.html)"[^>]*>([^<]{6,45})<\/a>/g; let m;
    while ((m = re.exec(h)) && items.length < 3) {
      const t = m[2].trim();
      if (t.length > 6 && !seen.has(t.substring(0,8))) { seen.add(t.substring(0,8)); items.push({t: t.substring(0,45), u: m[1]}); }
    }
    return items.map(i => ({t:i.t, s:'深度商业', src:'虎嗅', u: 'https://www.huxiu.com' + i.u}));
  } catch(e) { return []; }
}

// 19. 品玩
async function s19() {
  try {
    const h = await fetch('https://www.pingwest.com/');
    const items = extract(h, '"title":"([^"]+)"', 8, 3);
    return items.map(t => ({t: t.substring(0,45), s:'科技观察', src:'品玩', u:'https://www.pingwest.com/'}));
  } catch(e) { return []; }
}

// 20. Donews
async function s20() {
  try {
    const h = await fetch('https://www.donews.com/');
    const seen = new Set(), items = [];
    const re = /<a[^>]*href="(https?:\/\/www\.donews\.com[^"]+)"[^>]*>([^<]{8,50})<\/a>/g; let m;
    while ((m = re.exec(h)) && items.length < 3) {
      const t = m[2].trim();
      if (!seen.has(t.substring(0,8))) { seen.add(t.substring(0,8)); items.push({t: t.substring(0,50), u: m[1]}); }
    }
    return items.map(i => ({t:i.t, s:'互联网资讯', src:'Donews', u:i.u}));
  } catch(e) { return []; }
}

// ====== Stocks & Forex ======
async function getStocks() {
  try {
    const d = JSON.parse(await fetch('https://push2.eastmoney.com/api/qt/ulist.np/get?fltt=2&secids=1.000001,0.399001,0.399006,1.000688,1.000300,1.000016,1.000905,0.399001'));
    if (!d.data || !d.data.diff) return [];
    return d.data.diff.slice(0,8).map(s => ({n:s.f14||'--', v:(s.f2||0).toFixed(2), c:((s.f3||0)>=0?'+':'')+(s.f3||0).toFixed(2)+'%', cls:(s.f3||0)>=0?'up':'down'}));
  } catch(e) { return []; }
}
async function getForex() {
  try {
    const d = JSON.parse(await fetch('https://api.exchangerate-api.com/v4/latest/CNY')); const r = d.rates;
    return {USD:(1/r.USD).toFixed(4), EUR:(1/r.EUR).toFixed(4), JPY:(1/r.JPY).toFixed(4), GBP:(1/r.GBP).toFixed(4), HKD:(1/r.HKD).toFixed(4), KRW:(1/r.KRW).toFixed(4)};
  } catch(e) { return {}; }
}

// ====== Classify ======
function classify(items) {
  const w=[], t=[], c=[], f=[], s=[], e=[], h=[];
  for (const item of items) {
    const tt = item.t + ' ' + (item.s||'');
    if (/NBA|英超|欧冠|中超|CBA|世界杯|奥运|足球|篮球|网球|F1|赛车|羽毛球|乒乓球|女排|梅西|C罗|詹姆斯|联赛|冠军|体育|比赛|决赛|金牌/.test(tt)) s.push(item);
    else if (/AI|人工智能|科技|5G|6G|芯片|算力|软件|华为|数字|互联网|大模型|GPT|元宇宙|量子|卫星|航天|火箭|SpaceX|特斯拉|苹果|微软|谷歌|OpenAI|专利|算法|数据|区块链|自动化|智能|机器人|电动车|光伏|新能源|储能|电脑|手机|IT/.test(tt)) t.push(item);
    else if (/电影|票房|音乐|演唱会|综艺|游戏|明星|导演|电视剧|Netflix|迪士尼|B站|抖音|快手|舞台|广告|视频|直播|演出/.test(tt)) e.push(item);
    else if (/健康|养生|运动|饮食|睡眠|药|医院|疫苗|新冠|中医|营养|健身|减肥|体检|医保|医疗|疾病|诊断|治疗|患者/.test(tt)) h.push(item);
    else if (/A股|沪指|深指|北向|证监会|注册制|分红|涨停|券商|基金|私募|公募|科创板|创业板|上证|深证|沪深|北交所|股份|股票|上市|退市|财报|业绩|净利润|营收|利润|亏损|同比|增长|股东/.test(tt)) c.push(item);
    else if (/黄金|原油|金价|美联储|央行|汇率|贸易|逆差|美元|欧佩克|OPEC|通胀|加息|降息|期货|债券|信托|保险|银行|外汇|人民币|离岸|经济|GDP|CPI|关税|美股|标普|纳斯达克|道指/.test(tt)) f.push(item);
    else if (/伊朗|古巴|特朗普|制裁|美国|德国|北约|中东|国际|石油|非盟|G20|以军|巴以|欧盟|俄罗斯|乌克兰|外交|撤军|欧洲|英国|法国|日本|韩国|朝鲜|印度|联合国|世贸|WTO|难民|移民|空袭|会谈|峰会|大使|外长|总统|国会|参议院|地震|海啸|间谍|爆炸|袭击|逮捕|战争/.test(tt)) w.push(item);
    else if (/公积金|贷款|房地产|楼市|房价|租房|消费|购物|旅游|五一|假期|高速|公路|出行/.test(tt)) c.push(item);
    else if (/习近平|总书记|国务院|发改委|政策|政府|报告|代表|委员|两会|部署|战略/.test(tt)) c.push(item);
    else w.push(item);
  }
  return {world:w, tech:t, china:c, finance:f, sports:s, entertain:e, health:h};
}

function getDate() {
  const d = new Date(); d.setHours(d.getHours() + 8);
  return d.getUTCFullYear()+'年'+(d.getUTCMonth()+1)+'月'+d.getUTCDate()+'日 星期'+['日','一','二','三','四','五','六'][d.getUTCDay()];
}

function buildPage(date, sections, stocks, weather, fx, stats) {
  const nm = {world:'国际',tech:'科技',china:'A股/民生',finance:'财经',sports:'体育',entertain:'文娱',health:'健康',today:'历史',market:'行情',weather:'天气',forex:'汇率'};
  const nav = Object.keys(nm).map(id => `<a href="#s-${id}">${nm[id]}</a>`).join('');
  const total = sections.reduce((a,s) => a + s.items.length, 0);

  const secs = sections.map(s => {
    let h = `<div class="se" id="s-${s.id}"><div class="sh"><span class="si">${s.icon}</span><span class="st">${s.title}</span><span class="sc">${s.items.length}</span></div>`;
    h += s.items.map((it, i) => {
      const u = (it.u||'#').replace(/'/g, '%27');
      return `<div class="nc" onclick="window.open('${u}','_blank')"><div class="nt"><span class="ni">${i+1}</span>${it.t}</div><div class="nm">${it.src}</div></div>`;
    }).join('');
    return h + '</div>';
  }).join('');

  const sr = stocks.length ? stocks.map(s => `<div class="si2"><div class="sn">${s.n}</div><div class="sv">${s.v}</div><div class="sc2 ${s.cls}">${s.c}</div></div>`).join('') : '';
  const wr = weather.map(f => `<div class="wd"><div class="wdn">${f.d}</div><div class="wdi">${f.i}</div><div class="wdt">${f.t}</div><div class="wdd">${f.c}</div></div>`).join('');
  const fk = ['USD','EUR','JPY','GBP','HKD','KRW'];
  const fp = ['USD/CNY','EUR/CNY','JPY/CNY','GBP/CNY','HKD/CNY','KRW/CNY'];
  const fr = fk.map((k,i) => `<div class="fi"><div class="fp">${fp[i]}</div><div class="fr">${fx[k]||'--'}</div></div>`).join('');

  return `<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>每日全球资讯</title><style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0b0e16;color:#e2e8f0;font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif;line-height:1.6}
.app{max-width:800px;margin:0 auto;padding:0 16px 40px}
header{padding:24px 0 14px;margin-bottom:16px}
.tb{display:flex;justify-content:space-between;align-items:center;margin-bottom:14px}
.date{font-size:13px;color:#8896a6}.live{background:rgba(34,197,94,0.08);color:#22c55e;padding:2px 10px;border-radius:10px;font-size:11px}
nav{display:flex;gap:5px;flex-wrap:wrap}
nav a{color:#8896a6;text-decoration:none;font-size:12px;padding:4px 12px;border-radius:12px;background:rgba(255,255,255,0.03)}
nav a:hover{background:rgba(59,130,246,0.1);color:#60a5fa}
.se{background:#151a28;border:1px solid rgba(42,48,69,0.4);border-radius:10px;padding:14px;margin-bottom:14px}
.sh{display:flex;align-items:center;gap:8px;margin-bottom:12px}
.si{font-size:18px;width:26px;text-align:center}.st{font-size:15px;font-weight:600;color:#f1f5f9}
.sc{font-size:11px;background:rgba(99,102,241,0.08);color:#818cf8;padding:0 8px;border-radius:8px;line-height:20px;margin-left:auto}
.nc{padding:8px 0;border-bottom:1px solid rgba(255,255,255,0.02);cursor:pointer;margin:0 -4px;padding:8px 4px;border-radius:4px}
.nc:last-child{border-bottom:none}.nc:hover{background:rgba(255,255,255,0.015)}
.nt{font-size:13px;font-weight:500;color:#f1f5f9;margin-bottom:3px;display:flex;align-items:flex-start;gap:6px}
.ni{display:inline-flex;width:18px;height:18px;background:linear-gradient(135deg,#3b82f6,#8b5cf6);color:#fff;font-size:9px;font-weight:700;border-radius:3px;align-items:center;justify-content:center;flex-shrink:0;margin-top:2px}
.nm{font-size:10px;color:#5a6a7d;padding-left:24px}
.sg{display:grid;grid-template-columns:1fr 1fr;gap:6px}
.si2{background:rgba(255,255,255,0.02);border-radius:6px;padding:8px 10px;display:flex;justify-content:space-between;align-items:center}
.sn{font-size:11px;color:#8896a6}.sv{font-size:13px;font-weight:600;color:#f1f5f9}.sc2{font-size:11px;font-weight:500}
.up{color:#22c55e}.down{color:#ef4444}
.w3d{display:flex;gap:8px}.wd{flex:1;text-align:center;background:rgba(255,255,255,0.02);border-radius:8px;padding:10px 4px}
.wdn{font-size:11px;color:#8896a6;margin-bottom:4px}.wdi{font-size:28px;margin-bottom:4px}.wdt{font-size:13px;font-weight:600}.wdd{font-size:10px;color:#6b7a8d}
.fg{display:grid;grid-template-columns:1fr 1fr;gap:5px}
.fi{background:rgba(255,255,255,0.02);border-radius:5px;padding:6px 10px;display:flex;justify-content:space-between;align-items:center}
.fp{font-size:12px;color:#8896a6}.fr{font-size:13px;font-weight:600;color:#f1f5f9}
footer{margin-top:24px;padding:16px 0;text-align:center;border-top:1px solid rgba(42,48,69,0.3)}
footer p{font-size:10px;color:#5a6a7d;margin-bottom:2px}
</style></head><body><div class="app">
<header><div class="tb"><div class="date">📅 ${date}</div><div class="live">${total}条 · ${stats.sources}个来源</div></div><nav>${nav}</nav></header>
<div style="display:flex;justify-content:space-between;padding:0 2px;margin-bottom:12px;font-size:11px;color:#5a6a7d"><span>${stats.names}</span><span>${fx.USD?'USD/CNY '+fx.USD:''}</span></div>
${stocks.length ? '<div class="se" id="s-market"><div class="sh"><span class="si">📊</span><span class="st">全球指数</span></div><div class="sg">'+sr+'</div></div>' : ''}
<div class="se" id="s-weather"><div class="sh"><span class="si">🌤️</span><span class="st">泗阳天气</span></div><div class="w3d">${wr}</div></div>
${secs}
<div class="se" id="s-forex"><div class="sh"><span class="si">💱</span><span class="st">外汇汇率</span><span class="sc">6</span></div><div class="fg">${fr}</div></div>
<div class="se" style="border-style:dashed"><div style="padding:12px;text-align:center;font-size:10px;color:#5a6a7d;line-height:1.6">${stats.names}<br>每日 08:00 / 12:00 / 18:00 / 22:00 · 公开 · 免费 · 仅供参考</div></div>
<footer><p>自动聚合 · 不构成投资建议</p></footer></div></body></html>`;
}

// ====== Main ======
async function main() {
  const date = getDate();
  console.log('=== 全源聚合 ('+date+') ===');
  console.time('all');

  const results = await Promise.all([
    s1(),s2(),s3(),s4(),s5(),s6(),s7(),s8(),s9(),s10(),
    s11(),s12(),s13(),s14(),s15(),s16(),s17(),s18(),s19(),s20()
  ]);

  const [a1,a2,a3,a4,a5,a6,a7,a8,a9,a10,a11,a12,a13,a14,a15,a16,a17,a18,a19,a20] = results;

  const namesArr = [a1,a2,a3,a4,a5,a6,a7,a8,a9,a10,a11,a12,a13,a14,a15,a16,a17,a18,a19,a20];
  const labels = ['同花顺','华尔街见闻','财联社','第一财经','网易','新浪财经','新华网','人民网','中国新闻网','央视新闻',
    '凤凰网','财新网','每经','证券时报','中证报','IT之家','百度','虎嗅','品玩','Donews'];

  const cnt = {}; let totalSrc = 0;
  namesArr.forEach((arr, idx) => { if (arr.length) { cnt[labels[idx]] = arr.length; totalSrc += arr.length; }});

  console.log('来源('+Object.keys(cnt).length+'):', Object.values(cnt).reduce((a,b)=>a+b,0), '条');
  Object.entries(cnt).forEach(([k,v]) => console.log('  '+k+':'+v));

  // Stocks & forex
  const [stocks, fx] = await Promise.all([getStocks(), getForex()]);
  console.log('  股票:', stocks.length > 0 ? 'live' : 'fallback', '| 汇率:', fx.USD ? 'live' : 'fallback');

  // Merge + classify
  const allNews = [].concat(...namesArr);
  const classified = classify(allNews);
  const seen = new Set();
  Object.keys(classified).forEach(key => {
    classified[key] = classified[key].filter(item => {
      const h = item.t.substring(0,8);
      if (seen.has(h)) return false;
      seen.add(h); return true;

    });
  });

  console.log('分类:');
  Object.entries(classified).forEach(([k,v])=>{
    if(v.length) console.log('  '+k+':'+v.length);
  });

  const sections = [
    {id:'world',title:'国际要闻',icon:'🌍',items:classified.world.length?classified.world:[{t:'暂无国际新闻',s:'',src:'系统',u:'#'}]},
    {id:'tech',title:'科技动态',icon:'💻',items:classified.tech.length?classified.tech:[{t:'暂无科技资讯',s:'',src:'系统',u:'#'}]},
    {id:'china',title:'A股/民生',icon:'📈',items:classified.china.length?classified.china:[{t:'暂无相关资讯',s:'',src:'系统',u:'#'}]},
    {id:'finance',title:'财经焦点',icon:'💰',items:classified.finance.length?classified.finance:[{t:'暂无财经资讯',s:'',src:'系统',u:'#'}]},
    {id:'sports',title:'体育赛事',icon:'⚽',items:classified.sports.length?classified.sports:[{t:'暂无体育动态',s:'',src:'系统',u:'#'}]},
    {id:'entertain',title:'文娱热点',icon:'🎬',items:classified.entertain.length?classified.entertain:[{t:'暂无文娱资讯',s:'',src:'系统',u:'#'}]},
    {id:'health',title:'健康生活',icon:'💪',items:classified.health.length?classified.health:[{t:'暂无健康资讯',s:'',src:'系统',u:'#'}]},
    {id:'today',title:'历史上的今天',icon:'📅',items:[
      {t:'1519年 — 达·芬奇逝世',s:'',src:'历史',u:'#'},
      {t:'1957年 — 麦卡锡逝世',s:'',src:'历史',u:'#'},
      {t:'2003年 — 中国海军首次环球航行',s:'',src:'历史',u:'#'}
    ]}
  ];

  const weather = [
    {d:'今天',i:'🌧️',t:'14~17°C',c:'小雨转阴'},
    {d:'明天',i:'🌫️',t:'11~17°C',c:'雾转阵雨'},
    {d:'后天',i:'☀️',t:'10~25°C',c:'晴'}
  ];

  const stats = {
    sources: Object.keys(cnt).length,
    names: Object.keys(cnt).join(' · ')
  };

  const html = buildPage(date, sections, stocks, weather, fx, stats);

  const outPath = process.env.GITHUB_OUTPUT ? (process.env.GITHUB_WORKSPACE || '.') + '/index.html' : 'G:\\claw1232\\portable\\data\\.openclaw\\canvas\\daily-news\\index.html';
  fs.writeFileSync(outPath, html, 'utf8');
  console.log('\n写入: ' + outPath + ' (' + html.length + ' bytes)');
  console.log('=== 完成 ===');
}

main().catch(e => { console.error(e); process.exit(1); });