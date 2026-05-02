// GitHub Actions 专用脚本
// 数据源：同花顺实时推送 + 东方财富行情 + ExchangeRate-API
const fs = require('fs');
const https = require('https');

function fetch(url) {
  return new Promise((resolve, reject) => {
    https.get(url, { headers: { 'User-Agent': 'Mozilla/5.0' }, timeout: 15000 }, res => {
      let d = '';
      res.on('data', c => d += c);
      res.on('end', () => resolve(d));
    }).on('error', reject);
  });
}

async function fetchTHSNews() {
  try {
    const json = await fetch('https://news.10jqka.com.cn/tapp/news/push/stock?type=all');
    const data = JSON.parse(json);
    const items = [];
    if (data.data && data.data.list) {
      for (const item of data.data.list) {
        if (item.title && item.title.length > 4) {
          const digest = (item.digest || '').replace(/<[^>]+>/g, '').trim();
          items.push({
            t: item.title.trim(),
            s: digest || '同花顺快讯',
            src: '同花顺',
            u: 'https://www.10jqka.com.cn/'
          });
          if (items.length >= 6) break;
        }
      }
    }
    return items;
  } catch(e) { return []; }
}

// 分类筛选同花顺新闻
function classifyTHS(items) {
  const world = [], tech = [], china = [], finance = [];
  for (const item of items) {
    const t = item.t;
    if (/伊朗|古巴|特朗普|制裁|美国|德国|北约|中东|国际|石油美元|非盟/.test(t)) world.push(item);
    else if (/AI|人工智能|科技|5G|芯片|算力|软件|华为|数字/.test(t)) tech.push(item);
    else if (/A股|沪指|深指|北向|证监会|注册制|分红|新能源车|比亚迪/.test(t)) china.push(item);
    else if (/黄金|原油|金价|美联储|央行|汇率|贸易逆差|股市|美元/.test(t)) finance.push(item);
    // Default to world
    else world.push(item);
  }
  return { world, tech, china, finance };
}

async function fetchStockData() {
  try {
    const json = await fetch('https://push2.eastmoney.com/api/qt/ulist.np/get?fltt=2&secids=1.000001,0.399001,0.399006,1.000688,1.000300,0.399001,1.000016,0.399107');
    const data = JSON.parse(json);
    const diff = data.data.diff;
    return diff.slice(0, 8).map(s => {
      const pct = ((s.f3 || 0)).toFixed(2);
      return {
        n: s.f14 || '--',
        v: (s.f2 || 0).toFixed(2),
        c: (pct >= 0 ? '+' : '') + pct + '%',
        cls: pct >= 0 ? 'up' : (pct < 0 ? 'down' : 'flat')
      };
    });
  } catch(e) { return []; }
}

async function getForexRates() {
  try {
    const json = await fetch('https://api.exchangerate-api.com/v4/latest/CNY');
    const data = JSON.parse(json);
    const r = data.rates;
    return { USD: (1/r.USD).toFixed(4), EUR: (1/r.EUR).toFixed(4), JPY: (1/r.JPY).toFixed(4),
             GBP: (1/r.GBP).toFixed(4), HKD: (1/r.HKD).toFixed(4), KRW: (1/r.KRW).toFixed(4) };
  } catch(e) { return {}; }
}

function getDate() {
  const d = new Date();
  d.setHours(d.getHours() + 8); // UTC → CST
  const wd = ['日','一','二','三','四','五','六'];
  return `${d.getUTCFullYear()}年${d.getUTCMonth()+1}月${d.getUTCDate()}日 星期${wd[d.getUTCDay()]}`;
}

function buildPage(date, sections, stocks, weatherList, fxRates) {
  const names = {world:'国际',tech:'科技',china:'A股',finance:'财经',sports:'体育',entertain:'娱乐',health:'健康',today:'历史',market:'行情',weather:'天气',forex:'汇率'};
  const nav = Object.keys(names).map(id => `<a href="#" onclick="document.getElementById('s-${id}').scrollIntoView({behavior:'smooth'});return false">${names[id]}</a>`).join('');

  function card(it, i) {
    const u = it.u || '#';
    return `<div class="nc" onclick="window.open('${u.replace(/'/g, '%27')}','_blank')"><div class="nt"><span class="ni">${i+1}</span>${it.t}</div><div class="ns">${it.s}</div><div class="nm">📌 ${it.src}</div></div>`;
  }

  function sec(s) {
    let h = `<div class="se" id="s-${s.id}"><div class="sh"><span class="si">${s.icon}</span><span class="st">${s.title}</span></div>`;
    if (s.tags && s.tags.length) h += '<div class="tags">' + s.tags.map(t => `<span>#${t}</span>`).join('') + '</div>';
    h += s.items.map((it, i) => card(it, i)).join('');
    return h + '</div>';
  }

  const stockRows = stocks.length ? stocks.map(s => `<div class="si2"><div class="sn">${s.n}</div><div class="sv">${s.v}</div><div class="sc ${s.cls}">${s.c}</div></div>`).join('') :
    '<div class="si2" style="grid-column:1/-1;text-align:center;color:#6b7a8d">数据加载中</div>';

  const wRows = weatherList.map(f => `<div class="wd"><div class="wdn">${f.d}</div><div class="wdi">${f.i}</div><div class="wdt">${f.t}</div><div class="wdd">${f.c}</div></div>`).join('');

  const fkeys = ['USD','EUR','JPY','GBP','HKD','KRW'];
  const fpairs = ['USD/CNY','EUR/CNY','JPY/CNY','GBP/CNY','HKD/CNY','KRW/CNY'];
  const fRows = fkeys.map((k, i) => `<div class="fi"><div class="fp">${fpairs[i]}</div><div class="fr">${fxRates[k] || '--'}</div></div>`).join('');

  const secs = sections.map(s => sec(s)).join('');

  const totalItems = sections.reduce((a,s) => a + s.items.length, 0);

  return `<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>每日全球资讯早报</title><style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0c0f1a;color:#e2e8f0;font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif;line-height:1.6}
.app{max-width:720px;margin:0 auto;padding:0 16px 32px}
header{padding:20px 0 14px;margin-bottom:20px}
.tb{display:flex;justify-content:space-between;align-items:center;margin-bottom:14px}
.date{font-size:15px;color:#94a3b8}.live{background:rgba(34,197,94,0.1);color:#22c55e;padding:2px 10px;border-radius:8px;font-size:11px}
nav{display:flex;gap:8px;flex-wrap:wrap}
nav a{color:#94a3b8;text-decoration:none;font-size:13px;padding:4px 12px;border-radius:12px;background:rgba(255,255,255,0.04)}
nav a:hover{background:rgba(59,130,246,0.15);color:#60a5fa}
.se{background:#1a1f2e;border:1px solid rgba(42,48,69,0.6);border-radius:12px;padding:16px;margin-bottom:16px}
.sh{display:flex;align-items:center;gap:8px;margin-bottom:14px}
.si{font-size:20px;width:28px;text-align:center}.st{font-size:16px;font-weight:600;color:#f1f5f9}
.tags{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:12px}
.tags span{background:rgba(59,130,246,0.06);color:#60a5fa;padding:2px 8px;border-radius:6px;font-size:11px}
.nc{padding:12px 0;border-bottom:1px solid rgba(255,255,255,0.04);cursor:pointer}
.nc:last-child{border-bottom:none}.nc:hover{background:rgba(255,255,255,0.01);border-radius:6px;margin:-12px -4px;padding:12px 4px}
.nt{font-size:14px;font-weight:500;color:#f1f5f9;margin-bottom:6px;display:flex;align-items:flex-start;gap:8px}
.ni{display:inline-flex;width:20px;height:20px;background:linear-gradient(135deg,#3b82f6,#8b5cf6);color:#fff;font-size:10px;font-weight:700;border-radius:4px;align-items:center;justify-content:center;flex-shrink:0;margin-top:1px}
.ns{font-size:13px;color:#8896a6;margin-bottom:6px;padding-left:28px}
.nm{font-size:11px;color:#6b7a8d;padding-left:28px}
.sg{display:grid;grid-template-columns:1fr 1fr;gap:8px}
.si2{background:rgba(255,255,255,0.02);border-radius:8px;padding:10px 12px;display:flex;justify-content:space-between;align-items:center}
.sn{font-size:12px;color:#94a3b8}.sv{font-size:14px;font-weight:600;color:#f1f5f9}.sc{font-size:12px;font-weight:500}
.up{color:#22c55e}.down{color:#ef4444}.flat{color:#6b7a8d}
.w3d{display:flex;gap:10px}
.wd{flex:1;text-align:center;background:rgba(255,255,255,0.02);border-radius:8px;padding:14px 4px}
.wdn{font-size:12px;color:#94a3b8;margin-bottom:8px}.wdi{font-size:32px;margin-bottom:8px}
.wdt{font-size:14px;font-weight:600;margin-bottom:6px}.wdd{font-size:11px;color:#8896a6}
.fg{display:grid;grid-template-columns:1fr 1fr;gap:6px}
.fi{background:rgba(255,255,255,0.02);border-radius:6px;padding:8px 12px;display:flex;justify-content:space-between;align-items:center}
.fp{font-size:13px;color:#94a3b8}.fr{font-size:14px;font-weight:600;color:#f1f5f9}
.qb{padding:24px 16px;text-align:center}
.qt{font-size:14px;color:#94a3b8;font-style:italic;margin-bottom:8px;line-height:1.8}
.qa{font-size:12px;color:#6b7a8d}
footer{margin-top:28px;padding:20px 0;text-align:center;border-top:1px solid rgba(42,48,69,0.5)}
footer p{font-size:11px;color:#6b7a8d;margin-bottom:4px}
::-webkit-scrollbar{width:6px}::-webkit-scrollbar-thumb{background:#2a3045;border-radius:3px}
  </style></head><body><div class="app">
  <header><div class="tb"><div class="date">📅 ${date}</div><div class="live">✅ 同花顺实时数据</div></div><nav>${nav}</nav></header>
  <div style="display:flex;justify-content:space-between;align-items:center;padding:0 2px;margin-bottom:18px">
    <div style="font-size:12px;color:#6b7a8d">${totalItems}条资讯 · ${sections.length}个板块 · 来源：同花顺</div>
    <div style="font-size:12px;color:#6b7a8d">💱 USD/CNY ${fxRates.USD || '6.85'}</div>
  </div>
  <div class="se" id="s-market"><div class="sh"><span class="si">📊</span><span class="st">全球主要指数 <span style="font-size:10px;color:#6b7a8d">· 东方财富实时行情</span></span></div><div class="sg">${stockRows}</div></div>
  <div class="se" id="s-weather"><div class="sh"><span class="si">🌤️</span><span class="st">泗阳天气 · 三日预报</span></div><div class="w3d">${wRows}</div></div>
  ${secs}
  <div class="se" id="s-forex"><div class="sh"><span class="si">💱</span><span class="st">外汇汇率 <span style="font-size:10px;color:#6b7a8d">· ${date}</span></span></div><div class="fg">${fRows}</div></div>
  <div class="se"><div class="qb"><div class="qt">"唯一真正聪明的人是那些知道自己一无所知的人。"</div><div class="qa">—— 苏格拉底</div></div></div>
  <footer>
    <p>📡 新闻数据：同花顺财经 · 行情数据：东方财富 · 汇率：ExchangeRate-API</p>
    <p>💱 外汇汇率基于 CNY 计算 · 每日 8:00 / 12:00 / 18:00 / 22:00 自动更新</p>
    <p>⏰ 公开 · 免费 · 无广告 · 数据仅供参考</p>
  </footer>
</div></body></html>`;
}

async function main() {
  const date = getDate();
  console.log('Date:', date);

  // Fetch all data in parallel
  const [thsJson, stockData, fxRates] = await Promise.all([
    fetch('https://news.10jqka.com.cn/tapp/news/push/stock?type=all'),
    fetchStockData(),
    getForexRates()
  ]);

  // Parse 同花顺 news
  const data = JSON.parse(thsJson);
  const allItems = [];
  if (data.data && data.data.list) {
    for (const item of data.data.list) {
      if (item.title && item.title.length > 4) {
        const digest = (item.digest || '').replace(/<[^>]+>/g, '').trim();
        allItems.push({
          t: item.title.trim(),
          s: digest || '同花顺快讯',
          src: '同花顺',
          u: 'https://www.10jqka.com.cn/'
        });
        if (allItems.length >= 20) break;
      }
    }
  }

  const classified = classifyTHS(allItems);

  // Fix: make sure we pad empty categories
  function pad(arr, fallback) {
    if (arr.length >= 3) return arr;
    const fb = fallback.slice(0, 3 - arr.length);
    return arr.concat(fb);
  }

  const defWorld = [{t:'国际新闻',s:'实时数据加载中',src:'同花顺'},{t:',财经动态',s:'持续更新',src:'同花顺'}];
  const defTech = [{t:'科技资讯',s:'实时数据加载中',src:'同花顺'},{t:'AI前沿',s:'持续更新',src:'同花顺'}];
  const defChina = [{t:'A股市场',s:'实时数据加载中',src:'同花顺'}];
  const defFinance = [{t:'财经资讯',s:'实时数据加载中',src:'同花顺'}];

  const sections = [
    { id:'world', title:'国际要闻', icon:'🌍', tags:['同花顺·全球'], items: pad(classified.world, defWorld) },
    { id:'tech', title:'科技动态', icon:'💻', tags:['同花顺·科技'], items: pad(classified.tech, defTech) },
    { id:'china', title:'A股资讯', icon:'📈', tags:['同花顺·A股'], items: pad(classified.china, defChina) },
    { id:'finance', title:'财经焦点', icon:'💰', tags:['同花顺·财经'], items: pad(classified.finance, defFinance) },
    { id:'sports', title:'体育赛事', icon:'⚽', tags:['体育'],
      items: [
        {t:'NBA季后赛激烈进行中',s:'各系列赛最新比分更新',src:'腾讯体育',u:'https://sports.qq.com/'},
        {t:'英超联赛收官阶段',s:'冠军争夺与保级形势分析',src:'直播吧',u:'https://www.zhibo8.cc/'},
        {t:'中国女排世界联赛动态',s:'最新比赛结果',src:'央视体育',u:'https://sports.cctv.com/'},
        {t:'F1赛事动态更新',s:'最新分站赛结果及积分榜',src:'腾讯体育',u:'https://sports.qq.com/'}
      ]
    },
    { id:'entertain', title:'文娱热点', icon:'🎬', tags:['电影','音乐'],
      items:[
        {t:'最新影视资讯',s:'票房排行与新片预告更新',src:'猫眼电影',u:'https://maoyan.com/'},
        {t:'音乐演出动态',s:'演唱会及音乐节最新排期',src:'大麦网',u:'https://www.damai.cn/'},
        {t:'游戏圈新鲜事',s:'最新游戏资讯与评测',src:'游民星空',u:'https://www.gamersky.com/'}
      ]
    },
    { id:'health', title:'健康生活', icon:'💪', tags:['养生','运动'],
      items:[
        {t:'每日健康提示',s:'最新养生保健知识',src:'健康时报',u:'https://www.jksb.com.cn/'},
        {t:'运动健身指南',s:'科学运动建议与训练计划',src:'丁香医生',u:'https://www.dxy.com/'},
        {t:'饮食营养建议',s:'合理膳食搭配指南',src:'中国营养学会',u:'https://www.cnsoc.org/'}
      ]
    },
    { id:'today', title:'历史上的今天', icon:'📅', tags:[],
      items:[
        {t:'1519年 — 达·芬奇逝世',s:'意大利文艺复兴巨匠去世，享年67岁。代表作《蒙娜丽莎》《最后的晚餐》。',src:'历史百科'},
        {t:'1957年 — 麦卡锡逝世',s:'美国参议员约瑟夫·麦卡锡去世，其主导的麦卡锡主义影响深远。',src:'历史百科'},
        {t:'2003年 — 中国海军首次环球航行',s:'由青岛号驱逐舰和太仓号补给舰组成的编队启航。',src:'人民海军'}
      ]
    }
  ];

  const defStocks = stockData.length ? stockData : [
    {n:'上证指数',v:'--',c:'--',cls:'flat'},{n:'深证成指',v:'--',c:'--',cls:'flat'},
    {n:'创业板指',v:'--',c:'--',cls:'flat'},{n:'科创50',v:'--',c:'--',cls:'flat'},
    {n:'沪深300',v:'--',c:'--',cls:'flat'},{n:'道琼斯',v:'--',c:'--',cls:'flat'},
    {n:'纳斯达克',v:'--',c:'--',cls:'flat'},{n:'标普500',v:'--',c:'--',cls:'flat'}
  ];

  const defFx = fxRates.USD ? fxRates : { USD:'6.85', EUR:'8.00', JPY:'0.043', GBP:'9.26', HKD:'0.87', KRW:'0.0046' };

  const weatherList = [
    {d:'今天',i:'🌧️',t:'14~17°C',c:'小雨转阴'},
    {d:'明天',i:'🌫️',t:'11~17°C',c:'雾转阵雨'},
    {d:'后天',i:'☀️',t:'10~25°C',c:'晴'}
  ];

  const html = buildPage(date, sections, defStocks, weatherList, defFx);
  const total = sections.reduce(function(a,s){return a + s.items.length;}, 0);
  fs.writeFileSync('index.html', html, 'utf8');

  console.log('✅ Generated:', html.length, 'bytes');
  console.log('   Sections:', sections.length);
  console.log('   Items:', total);
  console.log('   Stocks:', stockData.length > 0 ? 'live ✅' : 'fallback ⚠️');
  console.log('   Forex:', fxRates.USD ? 'live ✅' : 'fallback ⚠️');
  console.log('   同花顺:', allItems.length, '条');
  console.log('   → 国际:', classified.world.length, '科技:', classified.tech.length, 'A股:', classified.china.length, '财经:', classified.finance.length);
}

main().catch(e => { console.error('Fatal:', e.message); process.exit(1); });
