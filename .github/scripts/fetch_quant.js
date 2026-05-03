#!/usr/bin/env node
var https = require('https');
var fs = require('fs');

function get(url) {
  return new Promise(function(resolve, reject){
    var req = https.request(url, {
      timeout: 15000,
      headers: {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    }, function(res){
      var d = '';
      res.on('data', function(c){ d += c; });
      res.on('end', function(){ resolve(d); });
    });
    req.on('error', reject);
    req.end();
  });
}

function fetchStocks(page, pz) {
  var url = 'https://push2.eastmoney.com/api/qt/clist/get?pn='+page+'&pz='+pz+'&po=1&np=1&ut=bd1d9ddb04089700cf9c27f6f7426281&fltt=2&invt=2&fid=f62&fs=m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23&fields=f2,f3,f4,f5,f6,f7,f8,f9,f10,f12,f14,f15,f16,f17,f18,f20,f21,f23,f25,f37,f38,f62,f115,f152,f168,f169,f170,f171';
  return get(url).then(function(text){
    var j = JSON.parse(text);
    return { stocks: (j.data && j.data.diff) || [], total: (j.data && j.data.total) || 0 };
  }).catch(function(){ return { stocks: [], total: 0 }; });
}

function pick(stocks) {
  var candidates = [];
  for (var i = 0; i < stocks.length; i++) {
    var s = stocks[i];
    var name = s.f14 || '';
    var code = s.f12 || '';
    if (name.indexOf('ST') >= 0 || name.indexOf('退') >= 0) continue;
    var chg = s.f3 || 0;
    if (chg < 1.0 || chg > 18.0) continue;
    var volRatio = s.f23 || 0;
    if (volRatio < 0.8) continue;
    var turnover = s.f38 || 0;
    if (turnover < 0.5) continue;
    var pe = s.f115 || 0;
    if (pe > 500) continue;
    var amt = (s.f62 || 0) / 1e8;
    var circCap = (s.f21 || 1) / 1e10;
    var realTurnover = turnover > 100 ? turnover / 1e8 : turnover;
    var score = 0;
    score += Math.min(chg / 5, 1.5) * 20;
    score += Math.min(volRatio / 3, 1.5) * 20;
    score += Math.min(realTurnover / 5, 1.0) * 15;
    score += Math.min(amt / 5, 1.0) * 15;
    score += Math.min(circCap / 30, 1.0) * 15;
    if (pe > 10 && pe < 50) score += 15;
    candidates.push({name:name, code:code, chg:chg, volRatio:volRatio, turnover:realTurnover.toFixed(1), pe:Math.round(pe), amt:Math.round(amt*10)/10, score:Math.round(score*10)/10});
  }
  candidates.sort(function(a,b){ return b.score - a.score; });
  return candidates.slice(0, 10);
}

function main() {
  var all = [];
  var pages = [1, 2, 3, 4, 5];
  var p = Promise.resolve();
  pages.forEach(function(page){
    p = p.then(function(){
      return fetchStocks(page, 100).then(function(r){
        all = all.concat(r.stocks);
      });
    });
  });
  p.then(function(){
    var picks = pick(all);
    var result = { picks: picks };
    fs.writeFileSync('quant_picks.json', JSON.stringify(result, null, 2), 'utf8');
    console.log('scan ' + all.length + ' picked ' + picks.length);
  }).catch(function(e){
    console.error(e.message);
    process.exit(1);
  });
}

main();
