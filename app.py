"""
Dashboard Warrior Scanner — Flask / Railway Cloud
Accessible depuis n'importe quel appareil (PC, mobile, tablette)
"""

from flask import Flask, jsonify, render_template_string, request
import csv
import os
import subprocess
import sys
from pathlib import Path
from datetime import datetime

app = Flask(__name__)

# Railway utilise la variable PORT
PORT     = int(os.environ.get("PORT", 5000))
CSV_PATH = Path("results.csv")

# Clés API depuis variables d'environnement (sécurisé pour le cloud)
FMP_KEY     = os.environ.get("FMP_KEY",     "U87EgtNaQOdshmSkc0IgEtCFcgqTDjvy")
FINNHUB_KEY = os.environ.get("FINNHUB_KEY", "d8cf7k9r01qidic7msv0d8cf7k9r01qidic7msvg")

HTML = """
<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>⚔️ Warrior Scanner</title>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@300;400;500&display=swap" rel="stylesheet">
<script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
<style>
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
:root {
  --bg: #0d0f14; --surface: #13161e; --border: #1e2533;
  --text: #e2e8f0; --muted: #4a5568; --mid: #a0aec0;
  --green: #4ade80; --red: #f87171; --blue: #60a5fa; --amber: #fbbf24;
}
body { background: var(--bg); color: var(--text); font-family: 'IBM Plex Sans', sans-serif; min-height: 100vh; }
.layout { display: flex; min-height: 100vh; }

/* SIDEBAR */
.sidebar {
  width: 220px; background: var(--surface); border-right: 1px solid var(--border);
  padding: 24px 16px; display: flex; flex-direction: column; gap: 16px;
  position: fixed; top: 0; left: 0; bottom: 0; overflow-y: auto;
}
.sidebar h2 { font-family: 'IBM Plex Mono', monospace; font-size: 13px; color: var(--text); padding-bottom: 12px; border-bottom: 1px solid var(--border); }
.sidebar label { font-family: 'IBM Plex Mono', monospace; font-size: 10px; color: var(--muted); letter-spacing: 0.1em; text-transform: uppercase; display: block; margin-bottom: 6px; }
.sidebar select { width: 100%; background: var(--bg); border: 1px solid var(--border); color: var(--text); font-family: 'IBM Plex Mono', monospace; font-size: 11px; padding: 6px 8px; border-radius: 4px; outline: none; }
.sidebar input[type=range] { width: 100%; cursor: pointer; accent-color: var(--blue); }
.btn { background: var(--bg); border: 1px solid var(--border); color: var(--text); font-family: 'IBM Plex Mono', monospace; font-size: 11px; padding: 8px 12px; border-radius: 4px; cursor: pointer; width: 100%; text-align: center; transition: border-color 0.2s, color 0.2s; text-decoration: none; display: block; }
.btn:hover { border-color: var(--blue); color: var(--blue); }
.btn.primary { border-color: var(--blue); color: var(--blue); }
.btn.scan { border-color: var(--green); color: var(--green); font-weight: 600; }
.btn.scan:hover { background: rgba(74,222,128,0.1); }
.sidebar-divider { border: none; border-top: 1px solid var(--border); }
.sidebar-note { font-family: 'IBM Plex Mono', monospace; font-size: 10px; color: var(--muted); line-height: 1.6; }

/* MAIN */
.main { margin-left: 220px; padding: 24px; flex: 1; }

/* Mobile */
@media (max-width: 768px) {
  .sidebar { width: 100%; position: relative; height: auto; }
  .main { margin-left: 0; padding: 16px; }
  .layout { flex-direction: column; }
  .metrics { grid-template-columns: repeat(2, 1fr) !important; }
  .charts-grid { grid-template-columns: 1fr !important; }
  .rank-main { grid-template-columns: 28px 60px 65px 65px 1fr !important; }
}

.header { display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 24px; flex-wrap: wrap; gap: 12px; }
.header h1 { font-family: 'IBM Plex Mono', monospace; font-size: 20px; font-weight: 600; }
.header-time { font-family: 'IBM Plex Mono', monospace; font-size: 11px; color: var(--muted); text-align: right; line-height: 1.6; }

/* METRICS */
.metrics { display: grid; grid-template-columns: repeat(5, 1fr); gap: 12px; margin-bottom: 24px; }
.metric { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 14px 16px; }
.metric-label { font-family: 'IBM Plex Mono', monospace; font-size: 10px; color: var(--muted); letter-spacing: 0.1em; text-transform: uppercase; margin-bottom: 6px; }
.metric-value { font-family: 'IBM Plex Mono', monospace; font-size: 22px; font-weight: 600; line-height: 1; }
.metric-sub { font-family: 'IBM Plex Mono', monospace; font-size: 11px; color: var(--muted); margin-top: 4px; }

/* TABS */
.tabs { display: flex; gap: 2px; margin-bottom: 20px; border-bottom: 1px solid var(--border); overflow-x: auto; }
.tab { font-family: 'IBM Plex Mono', monospace; font-size: 11px; color: var(--muted); padding: 8px 16px; cursor: pointer; border-bottom: 2px solid transparent; margin-bottom: -1px; white-space: nowrap; }
.tab.active { color: var(--blue); border-bottom-color: var(--blue); }

.tab-content { display: none; }
.tab-content.active { display: block; }

/* RANKING */
.rank-row { padding: 12px 0; border-bottom: 1px solid var(--border); }
.rank-main { display: grid; grid-template-columns: 32px 80px 85px 80px 100px 70px 70px 1fr 110px; align-items: center; gap: 8px; }
.rank-num { font-family: 'IBM Plex Mono', monospace; font-size: 18px; color: var(--border); font-weight: 700; }
.rank-sym { font-family: 'IBM Plex Mono', monospace; font-weight: 600; font-size: 15px; color: var(--text); }
.rank-price, .rank-rvol, .rank-float { font-family: 'IBM Plex Mono', monospace; font-size: 13px; }
.rank-chg { font-family: 'IBM Plex Mono', monospace; font-size: 14px; font-weight: 600; }
.rank-vol { font-family: 'IBM Plex Mono', monospace; font-size: 12px; color: var(--mid); }
.score-bar-wrap { background: var(--border); border-radius: 2px; height: 4px; margin-top: 4px; overflow: hidden; }
.score-bar-fill { height: 100%; border-radius: 2px; }
.score-val { font-family: 'IBM Plex Mono', monospace; font-size: 17px; font-weight: 600; }
.score-sub { font-family: 'IBM Plex Mono', monospace; font-size: 10px; color: var(--muted); margin-top: 3px; }
.badge { display: inline-block; padding: 2px 6px; border-radius: 3px; font-family: 'IBM Plex Mono', monospace; font-size: 10px; margin-right: 3px; margin-bottom: 2px; }
.badge-green { background: #0d2418; color: var(--green); }
.badge-red   { background: #2a0d0d; color: var(--red); }
.badge-blue  { background: #0d1a2a; color: var(--blue); }
.badge-amber { background: #2a1a0d; color: var(--amber); }
.rank-links { padding: 6px 0 2px 40px; display: flex; gap: 12px; flex-wrap: wrap; align-items: center; }
.tv-link { font-family: 'IBM Plex Mono', monospace; font-size: 11px; color: var(--blue); text-decoration: none; border: 1px solid var(--blue); padding: 2px 8px; border-radius: 3px; white-space: nowrap; }
.tv-link:hover { background: rgba(96,165,250,0.1); }
.news-link { font-family: 'IBM Plex Mono', monospace; font-size: 10px; color: var(--muted); text-decoration: none; overflow: hidden; text-overflow: ellipsis; max-width: 400px; display: block; }
.news-link:hover { color: var(--mid); }
.legend { font-family: 'IBM Plex Mono', monospace; font-size: 10px; color: var(--border); margin-top: 12px; }

/* CHARTS */
.charts-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.chart-box { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 16px; }

/* TABLE */
.data-table { width: 100%; border-collapse: collapse; font-family: 'IBM Plex Mono', monospace; font-size: 12px; }
.data-table th { text-align: left; color: var(--muted); font-size: 10px; letter-spacing: 0.1em; text-transform: uppercase; padding: 8px 12px; border-bottom: 1px solid var(--border); }
.data-table td { padding: 8px 12px; border-bottom: 1px solid var(--border); color: var(--mid); }
.data-table tr:hover td { background: rgba(255,255,255,0.02); }

.empty { font-family: 'IBM Plex Mono', monospace; font-size: 13px; color: var(--muted); padding: 40px 0; text-align: center; line-height: 2; }
.scanning { font-family: 'IBM Plex Mono', monospace; font-size: 13px; color: var(--amber); padding: 20px 0; text-align: center; }
.footer { font-family: 'IBM Plex Mono', monospace; font-size: 10px; color: var(--border); text-align: center; margin-top: 40px; padding-top: 16px; border-top: 1px solid var(--border); }
#score-min-val { font-family: 'IBM Plex Mono', monospace; font-size: 11px; color: var(--mid); }
</style>
</head>
<body>
<div class="layout">

<aside class="sidebar">
  <h2>⚔️ Warrior Scanner</h2>

  <button class="btn scan" onclick="lancerScan()">▶ Lancer le scan</button>
  <div id="scan-status" style="font-family:IBM Plex Mono,monospace;font-size:10px;color:var(--muted);text-align:center"></div>

  <hr class="sidebar-divider">

  <div>
    <label>Trier par</label>
    <select id="sort-by" onchange="applyFilters()">
      <option value="score">Score global</option>
      <option value="variation">Variation %</option>
      <option value="rvol">RVOL</option>
      <option value="float_m">Float</option>
    </select>
  </div>

  <div>
    <label>Score minimum — <span id="score-min-val">0</span></label>
    <input type="range" id="score-min" min="0" max="100" value="0"
      oninput="document.getElementById('score-min-val').textContent=this.value; applyFilters()">
  </div>

  <hr class="sidebar-divider">
  <button class="btn primary" onclick="location.reload()">🔄 Rafraîchir</button>

  <hr class="sidebar-divider">
  <div class="sidebar-note">
    <b>Filtres Warrior :</b><br>
    Prix : $1 – $20<br>
    Variation min : +10%<br>
    RVOL min : 5x<br>
    Float max : 20M titres<br><br>
    <b>Meilleure fenêtre :</b><br>
    9h30 – 11h00 ET<br>
    (15h30 – 17h00 MTL)
  </div>
</aside>

<main class="main">
  <div class="header">
    <h1>⚔️ Warrior Scanner</h1>
    <div class="header-time" id="scan-time">—</div>
  </div>

  <div class="metrics">
    <div class="metric"><div class="metric-label">Qualifiés</div><div class="metric-value" id="m-qualified">—</div><div class="metric-sub" id="m-excl"></div></div>
    <div class="metric"><div class="metric-label">Score moyen</div><div class="metric-value" id="m-avg">—</div></div>
    <div class="metric"><div class="metric-label">Meilleur RVOL</div><div class="metric-value" id="m-rvol">—</div><div class="metric-sub" id="m-rvol-sym"></div></div>
    <div class="metric"><div class="metric-label">Meilleure hausse</div><div class="metric-value" id="m-chg">—</div><div class="metric-sub" id="m-chg-sym"></div></div>
    <div class="metric"><div class="metric-label">Avec catalyst</div><div class="metric-value" id="m-news">—</div><div class="metric-sub">news dispo</div></div>
  </div>

  <div class="tabs">
    <div class="tab active" onclick="switchTab('ranking',this)">📊 Classement</div>
    <div class="tab" onclick="switchTab('charts',this)">📈 Graphiques</div>
    <div class="tab" onclick="switchTab('indicators',this)">🔬 Indicateurs</div>
    <div class="tab" onclick="switchTab('excluded',this)">❌ Exclus</div>
  </div>

  <div class="tab-content active" id="tab-ranking"><div id="ranking-list"></div><div class="legend">M=Momentum · V=Volume · T=Tendance · P=Proximité 52W · G=Gap</div></div>
  <div class="tab-content" id="tab-charts"><div class="charts-grid"><div class="chart-box"><div id="chart-score" style="height:280px"></div></div><div class="chart-box"><div id="chart-rvol" style="height:280px"></div></div><div class="chart-box"><div id="chart-chg" style="height:280px"></div></div><div class="chart-box"><div id="chart-radar" style="height:280px"></div></div></div></div>
  <div class="tab-content" id="tab-indicators"><div style="overflow-x:auto"><table class="data-table"><thead><tr id="ind-head"></tr></thead><tbody id="ind-body"></tbody></table></div></div>
  <div class="tab-content" id="tab-excluded"><div id="excluded-list"></div></div>

  <div class="footer">⚔️ Warrior Scanner Cloud · Yahoo Finance + FMP + Finnhub · Score /100</div>
</main>
</div>

<script>
let allData=[], valid=[], excl=[];
const PL={paper_bgcolor:'#0d0f14',plot_bgcolor:'#13161e',font:{color:'#718096',family:'IBM Plex Mono'},xaxis:{gridcolor:'#1e2533',linecolor:'#1e2533'},yaxis:{gridcolor:'#1e2533',linecolor:'#1e2533'},margin:{t:40,b:30,l:40,r:20}};
function sc(v){return v>=70?'#4ade80':v>=50?'#60a5fa':v>=30?'#fbbf24':'#4a5568';}
function fv(v){v=+v||0;return v>=1e9?(v/1e9).toFixed(1)+'G':v>=1e6?(v/1e6).toFixed(1)+'M':(v/1e3).toFixed(0)+'K';}
function n(v,d=2){return (+v||0).toFixed(d);}

function applyFilters(){
  const sb=document.getElementById('sort-by').value;
  const ms=+document.getElementById('score-min').value;
  valid=allData.filter(r=>!r.excluded).filter(r=>+r.score>=ms).sort((a,b)=>+b[sb]-+a[sb]);
  excl=allData.filter(r=>r.excluded);
  renderMetrics(); renderRanking(); renderIndicators(); renderExcluded();
}

function renderMetrics(){
  document.getElementById('m-qualified').textContent=valid.length;
  document.getElementById('m-excl').textContent=excl.length+' exclus';
  if(!valid.length)return;
  const avg=valid.reduce((s,r)=>s+(+r.score||0),0)/valid.length;
  document.getElementById('m-avg').textContent=avg.toFixed(1)+'/100';
  const topR=valid.reduce((a,b)=>(+a.rvol||0)>(+b.rvol||0)?a:b);
  document.getElementById('m-rvol').textContent=n(topR.rvol)+'x';
  document.getElementById('m-rvol-sym').textContent=topR.symbol;
  const topC=valid.reduce((a,b)=>(+a.variation||0)>(+b.variation||0)?a:b);
  document.getElementById('m-chg').textContent='+'+n(topC.variation)+'%';
  document.getElementById('m-chg-sym').textContent=topC.symbol;
  document.getElementById('m-news').textContent=valid.filter(r=>r.news).length;
}

function renderRanking(){
  const el=document.getElementById('ranking-list');
  if(!valid.length){el.innerHTML='<div class="empty">Aucune action ne passe les filtres Warrior.<br>Clique sur ▶ Lancer le scan<br>ou reviens entre 9h30–11h00 ET.</div>';return;}
  el.innerHTML=valid.map((r,i)=>{
    const s=+r.score||0,col=sc(s),chg=+r.variation||0,rvol=+r.rvol||0,fl=+r.float_m||0;
    const rvolCol=rvol>=10?'#4ade80':rvol>=5?'#60a5fa':'#fbbf24';
    const chgCol=chg>=20?'#4ade80':chg>=10?'#60a5fa':'#a0aec0';
    let badges='';
    if(chg>=20) badges+='<span class="badge badge-green">🔥 +20%</span>';
    if(rvol>=10) badges+='<span class="badge badge-green">⚡ RVOL 10x+</span>';
    if(fl<=5) badges+='<span class="badge badge-amber">🎯 Low Float</span>';
    if(r.news) badges+='<span class="badge badge-blue">📰 Catalyst</span>';
    if(+r['gap %']>5) badges+='<span class="badge badge-amber">GAP</span>';
    const newsHtml=r.news?r.news.split(' | ').map((t,idx)=>{
      const links=(r.news_links||'').split(' | ');
      return `<a class="news-link" href="${links[idx]||'#'}" target="_blank">📰 ${t.slice(0,70)}</a>`;
    }).join(''):'';
    const tvUrl=r.tradingview||`https://www.tradingview.com/chart/?symbol=${r.symbol}`;
    return `
    <div class="rank-row">
      <div class="rank-main">
        <div class="rank-num">${i+1}</div>
        <div><div class="rank-sym">${r.symbol}</div><div style="font-size:9px;color:var(--muted);font-family:IBM Plex Mono,monospace">${r.mode||''} ${r.heure||''}</div></div>
        <div class="rank-price">$${n(r.prix)}</div>
        <div class="rank-chg" style="color:${chgCol}">+${n(r.variation)}%</div>
        <div class="rank-vol">${fv(r.volume)}<br><span style="font-size:10px;color:var(--muted)">moy: ${fv(r['avg vol 10j']||0)}</span></div>
        <div style="color:${rvolCol};font-family:IBM Plex Mono,monospace;font-size:13px">${n(rvol)}x</div>
        <div style="color:${fl<=10?'#4ade80':fl<=20?'#fbbf24':'#a0aec0'};font-family:IBM Plex Mono,monospace;font-size:13px">${n(fl,1)}M</div>
        <div>
          <div class="score-val" style="color:${col}">${n(s,1)}<span style="font-size:11px;color:var(--muted)">/100</span></div>
          <div class="score-bar-wrap"><div class="score-bar-fill" style="width:${s}%;background:${col}"></div></div>
          <div class="score-sub">M:${r['s.momentum']||0} V:${r['s.volume']||0} T:${r['s.tendance']||0} P:${r['s.proximite']||0} G:${r['s.gap']||0}</div>
        </div>
        <div>${badges||'<span style="color:var(--border);font-size:11px">—</span>'}</div>
      </div>
      <div class="rank-links">
        <a class="tv-link" href="${tvUrl}" target="_blank">📈 TradingView</a>
        ${newsHtml}
      </div>
    </div>`;
  }).join('');
}

function renderCharts(){
  if(!valid.length)return;
  const syms=valid.map(r=>r.symbol),scores=valid.map(r=>+r.score||0),rvols=valid.map(r=>+r.rvol||0),chgs=valid.map(r=>+r.variation||0);
  Plotly.newPlot('chart-score',[{type:'bar',x:syms,y:scores,marker:{color:scores.map(sc)},text:scores.map(s=>s.toFixed(1)),textposition:'outside',textfont:{family:'IBM Plex Mono',size:11,color:'#a0aec0'}}],{...PL,title:{text:'Score /100',font:{size:13,color:'#a0aec0'}},yaxis:{...PL.yaxis,range:[0,110]}},{responsive:true,displayModeBar:false});
  Plotly.newPlot('chart-rvol',[{type:'bar',x:syms,y:rvols,marker:{color:rvols.map(v=>v>=10?'#4ade80':v>=5?'#60a5fa':'#4a5568')},text:rvols.map(v=>v.toFixed(1)+'x'),textposition:'outside',textfont:{family:'IBM Plex Mono',size:11,color:'#a0aec0'}}],{...PL,title:{text:'RVOL (seuil 5x)',font:{size:13,color:'#a0aec0'}},shapes:[{type:'line',x0:-0.5,x1:syms.length-0.5,y0:5,y1:5,line:{color:'#fbbf24',dash:'dash',width:1}}]},{responsive:true,displayModeBar:false});
  Plotly.newPlot('chart-chg',[{type:'bar',x:syms,y:chgs,marker:{color:chgs.map(v=>v>=20?'#4ade80':v>=10?'#60a5fa':'#a0aec0')},text:chgs.map(v=>'+'+v.toFixed(1)+'%'),textposition:'outside',textfont:{family:'IBM Plex Mono',size:11,color:'#a0aec0'}}],{...PL,title:{text:'Variation % (seuil 10%)',font:{size:13,color:'#a0aec0'}},shapes:[{type:'line',x0:-0.5,x1:syms.length-0.5,y0:10,y1:10,line:{color:'#fbbf24',dash:'dash',width:1}}]},{responsive:true,displayModeBar:false});
  const r=valid[0],maxes=[35,25,20,10,10],vals=[+r['s.momentum']||0,+r['s.volume']||0,+r['s.tendance']||0,+r['s.proximite']||0,+r['s.gap']||0],pcts=vals.map((v,i)=>v/maxes[i]*100),cats=['Momentum','Volume','Tendance','Proximité','Gap'];
  Plotly.newPlot('chart-radar',[{type:'scatterpolar',r:[...pcts,pcts[0]],theta:[...cats,cats[0]],fill:'toself',fillcolor:'rgba(96,165,250,0.15)',line:{color:'#60a5fa',width:2}}],{...PL,title:{text:`Profil ${r.symbol}`,font:{size:13,color:'#a0aec0'}},polar:{bgcolor:'#13161e',radialaxis:{range:[0,100],gridcolor:'#1e2533'},angularaxis:{gridcolor:'#1e2533',tickfont:{size:10,color:'#a0aec0'}}}},{responsive:true,displayModeBar:false});
}

function renderIndicators(){
  const cols=['symbol','prix','variation','gap %','volume','rvol','avg vol 10j','float m','sma50','sma200','52w high','dist 52w %'];
  const labels={'symbol':'Symbole','prix':'Prix','variation':'Var%','gap %':'Gap%','volume':'Volume','rvol':'RVOL','avg vol 10j':'AvgVol10j','float m':'Float M','sma50':'SMA50','sma200':'SMA200','52w high':'52W High','dist 52w %':'Dist 52W%'};
  const avail=cols.filter(c=>valid.some(r=>r[c]!==undefined));
  document.getElementById('ind-head').innerHTML=avail.map(c=>`<th>${labels[c]||c}</th>`).join('');
  document.getElementById('ind-body').innerHTML=valid.map(r=>`<tr>${avail.map(c=>{
    const v=r[c];
    if(c==='symbol')return`<td style="color:var(--text);font-weight:600"><a class="tv-link" style="font-size:11px" href="${r.tradingview||'#'}" target="_blank">${v}</a></td>`;
    if(c==='prix')return`<td>$${n(v)}</td>`;
    if(c==='rvol'){const rv=+v||0;return`<td style="color:${rv>=10?'#4ade80':rv>=5?'#60a5fa':'#fbbf24'}">${n(rv)}x</td>`;}
    if(c==='variation'){const cv=+v||0;return`<td style="color:${cv>=20?'#4ade80':'#60a5fa'}">+${n(cv)}%</td>`;}
    if(c==='float m'){const fv=+v||0;return`<td style="color:${fv<=10?'#4ade80':fv<=20?'#fbbf24':'#a0aec0'}">${n(fv,1)}M</td>`;}
    if(['gap %','dist 52w %'].includes(c))return`<td>${n(v)}%</td>`;
    if(['volume','avg vol 10j'].includes(c))return`<td>${fv(v)}</td>`;
    return`<td>${n(v)}</td>`;
  }).join('')}</tr>`).join('');
}

function renderExcluded(){
  const el=document.getElementById('excluded-list');
  if(!excl.length){el.innerHTML='<div class="empty">Aucune action exclue.</div>';return;}
  el.innerHTML=excl.map(r=>`<div style="display:grid;grid-template-columns:80px 80px 1fr;gap:8px;padding:8px 0;border-bottom:1px solid var(--border);align-items:center"><div style="font-family:IBM Plex Mono,monospace;font-weight:600;color:var(--mid)">${r.symbol}</div><div style="font-family:IBM Plex Mono,monospace;color:var(--muted)">$${n(r.prix||0)}</div><div><span class="badge badge-red">${r.reason||'Filtré'}</span></div></div>`).join('');
}

function switchTab(name,el){
  document.querySelectorAll('.tab').forEach(t=>t.classList.remove('active'));
  document.querySelectorAll('.tab-content').forEach(t=>t.classList.remove('active'));
  el.classList.add('active');
  document.getElementById('tab-'+name).classList.add('active');
  if(name==='charts')renderCharts();
}

function lancerScan(){
  const btn=document.querySelector('.btn.scan');
  const status=document.getElementById('scan-status');
  btn.textContent='⏳ Scan en cours...';
  btn.disabled=true;
  status.textContent='Peut prendre 30-60 secondes...';
  fetch('/scan',{method:'POST'}).then(r=>r.json()).then(d=>{
    btn.textContent='▶ Lancer le scan';
    btn.disabled=false;
    if(d.ok){status.textContent='✅ '+d.message;loadData();}
    else{status.textContent='❌ '+d.message;}
  }).catch(()=>{btn.textContent='▶ Lancer le scan';btn.disabled=false;status.textContent='❌ Erreur réseau';});
}

function loadData(){
  fetch('/data').then(r=>r.json()).then(d=>{
    allData=d.rows;
    document.getElementById('scan-time').innerHTML='Dernier scan<br>'+d.mtime;
    applyFilters();
  });
}

loadData();
setInterval(loadData, 60000); // Auto-refresh toutes les 60 secondes
</script>
</body>
</html>
"""

# ─────────────────────────────────────────────
# Mapping colonnes CSV Warrior
# ─────────────────────────────────────────────
RENAME = {
    "Symbol": "symbol", "Score": "score",
    "S.Momentum": "s.momentum", "S.Volume": "s.volume",
    "S.Tendance": "s.tendance", "S.Proximite": "s.proximite", "S.Gap": "s.gap",
    "Prix": "prix", "Variation %": "variation", "Gap %": "gap %",
    "Volume": "volume", "RVOL": "rvol",
    "Avg Vol 10j": "avg vol 10j", "Avg Vol 30j": "avg vol 30j",
    "Float M": "float_m", "Market Cap": "market_cap",
    "SMA50": "sma50", "SMA200": "sma200",
    "52W High": "52w high", "Dist 52W %": "dist 52w %",
    "TradingView": "tradingview", "News": "news", "News Links": "news_links",
    "Heure": "heure", "Mode": "mode",
}

def load_data():
    if not CSV_PATH.exists():
        return [], None
    mtime = datetime.fromtimestamp(CSV_PATH.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
    rows = []
    with open(CSV_PATH, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            clean   = {k.strip(): (v.strip() if isinstance(v, str) else v) for k, v in row.items()}
            renamed = {RENAME.get(k, k.lower()): v for k, v in clean.items()}
            renamed.setdefault("excluded", False)
            renamed.setdefault("news", "")
            renamed.setdefault("news_links", "")
            renamed.setdefault("mode", "")
            renamed.setdefault("tradingview",
                f"https://www.tradingview.com/chart/?symbol={renamed.get('symbol','')}")
            rows.append(renamed)
    return rows, mtime

@app.route("/")
def index():
    return render_template_string(HTML)

@app.route("/data")
def data():
    rows, mtime = load_data()
    return jsonify({"rows": rows, "mtime": mtime or "—"})

@app.route("/scan", methods=["POST"])
def run_scan():
    try:
        result = subprocess.run(
            [sys.executable, "scanner_warrior.py"],
            capture_output=True, text=True, timeout=120, cwd=os.getcwd()
        )
        if result.returncode == 0:
            return jsonify({"ok": True,  "message": "Scan terminé avec succès"})
        else:
            return jsonify({"ok": False, "message": result.stderr[-200:] or "Erreur scanner"})
    except subprocess.TimeoutExpired:
        return jsonify({"ok": False, "message": "Timeout — scan trop long"})
    except Exception as e:
        return jsonify({"ok": False, "message": str(e)})

if __name__ == "__main__":
    print("\n" + "="*50)
    print("  ⚔️  Warrior Scanner Dashboard")
    print(f"  http://localhost:{PORT}")
    print("="*50 + "\n")
    app.run(host="0.0.0.0", port=PORT, debug=False)
