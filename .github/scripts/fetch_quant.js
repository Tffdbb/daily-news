#!/usr/bin/env node
const https = require('https');
const fs = require('fs');

function get(url) {
  return new Promise((resolve, reject) => {
    https.get(url, { timeout: 10000, headers: { 'User-Agent': 'Mozilla/5.0' } }, res => {
      let d = '';
      res.on('data', c => d += c);
      res.on('end', () => resolve(d));
    }).on('error', reject);
  });
}

const FIELDS = 'f2,f3,f4,f5,f6,f7,f8,f9,f10,f12,f14,f15,f16,f17,f18,f20,f21,f23,f25,f37,f38,f62,f115,f152,f168,f169,f170,f171';

async function fetchStocks(page, pz) {
  const url = 'https://push2.eastmoney.com/api/qt/clist/get?pn='+page+'&pz='+pz+'&po=1&np=1&ut=bd1d9ddb04089700cf9c27f6f7426281&fltt=2&invt=2&fid=f62&fs=m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23&fields='+FIELDS;
  try {
    const text = await get(url);
    const j = JSON.parse(text);
    return { stocks: j.data ? j.data.diff || [] : [], total: j.data ? j.data.total || 0 : 0 };
  } catch(e) { return { stocks: [], total: 0 }; }
}

function pick(stocks) {
  const candidates = [];
  for (const s of stocks) {
    const name = s.f14 || '';
    const code = s.f12 || '';
    if (name.indexOf('ST') >= 0 || name.indexOf('退') >= 0 || name.indexOf('N') >= 0) continue;
    const chg = s.f3 || 0;
    if (chg < 1.0 || chg > 18.0) continue;
    const volRatio = s.f23 || 0;
    if (volRatio < 0.8) continue;
    const turnover = s.f38 || 0;
    if (turnover < 0.5) continue;
    const pe = s.f115 || 0;
    if (pe && pe > 500) continue;
    const price = s.f2 || 0;
    const amt = (s.f62 || 0) / 1e8;
    const circCap = (s.f21 || 1) / 1e10;
    const realTurnover = turnover > 100 ? turnover / 1e8 : turnover;
    let score = 0;
    score += Math.min(chg / 5, 1.5) * 20;
    score += Math.min(volRatio / 3, 1.5) * 20;
    score += Math.min(realTurnover / 5, 1.0) * 15;
    score += Math.min(amt / 5, 1.0) * 15;
    score += Math.min(circCap / 30, 1.0) * 15;
    if (pe && pe > 10 && pe < 50) score += 15;
    const turnDisplay = turnover > 1e6 ? (turnover/1e8).toFixed(1) : turnover.toFixed(1);
    candidates.push({ name, code, price, chg, volRatio, turnover: turnDisplay, pe: Math.round(pe || 0), amt: Math.round(amt*10)/10, score: Math.round(score*10)/10 });
  }
  candidates.sort(function(a,b){ return b.score - a.score; });
  return candidates.slice(0, 10);
}

async function main() {
  let all = [];
  for (let page = 1; page <= 5; page++) {
    const { stocks } = await fetchStocks(page, 100);
    all = all.concat(stocks);
    if (stocks.length < 100) break;
  }
  const picks = pick(all);
  const result = { time: new Date().toLocaleString('zh-CN', {timeZone:'Asia/Shanghai'}), totalStocks: all.length, picks };
  fs.writeFileSync('quant_picks.json', JSON.stringify(result, null, 2), 'utf8');
  console.log('scan ' + all.length + ' picked ' + picks.length);
}

main().catch(function(e){ console.error(e+" "+e.stack); process.exit(1); });
