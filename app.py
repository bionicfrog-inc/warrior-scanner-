"""
Dashboard Warrior Scanner — Flask / Railway Cloud
Avec onglet Finviz séparé
"""

from flask import Flask, jsonify, render_template_string
import csv
import os
import subprocess
import sys
from pathlib import Path
from datetime import datetime

print("APP VERSION FINVIZ 1.0")

app      = Flask(__name__)
PORT     = int(os.environ.get("PORT", 5000))
CSV_PATH = Path("resultats.csv")
FVZ_PATH = Path("finviz_results.csv")

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
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{--bg:#0d0f14;--surface:#13161e;--border:#1e2533;--text:#e2e8f0;--muted:#4a5568;--mid:#a0aec0;--green:#4ade80;--red:#f87171;--blue:#60a5fa;--amber:#fbbf24;--purple:#a78bfa}
body{background:var(--bg);color:var(--text);font-family:'IBM Plex Sans',sans-serif;min-height:100vh}
.layout{display:flex;min-height:100vh}
.sidebar{width:220px;background:var(--surface);border-right:1px solid var(--border);padding:24px 16px;display:flex;flex-direction:column;gap:16px;position:fixed;top:0;left:0;bottom:0;overflow-y:auto}
.sidebar h2{font-family:'IBM Plex Mono',monospace;font-size:13px;color:var(--text);padding-bottom:12px;border-bottom:1px solid var(--border)}
.sidebar label{font-family:'IBM Plex Mono',monospace;font-size:10px;color:var(--muted);letter-spacing:.1em;text-transform:uppercase;display:block;margin-bottom:6px}
.sidebar select{width:100%;background:var(--bg);border:1px solid var(--border);color:var(--text);font-family:'IBM Plex Mono',monospace;font-size:11px;padding:6px 8px;border-radius:4px;outline:none}
.sidebar input[type=range]{width:100%;cursor:pointer;accent-color:var(--blue)}
.btn{background:var(--bg);border:1px solid var(--border);color:var(--text);font-family:'IBM Plex Mono',monospace;font-size:11px;padding:8px 12px;border-radius:4px;cursor:pointer;width:100%;text-align:center;transition:border-color .2s,color .2s;text-decoration:none;display:block}
.btn:hover{border-color:var(--blue);color:var(--blue)}
.btn.primary{border-color:var(--blue);color:var(--blue)}
.btn.scan{border-color:var(--green);color:var(--green);font-weight:600}
.btn.scan:hover{background:rgba(74,222,128,.1)}
.btn.fvz{border-color:var(--purple);color:var(--purple);font-weight:600}
.btn.fvz:hover{background:rgba(167,139,250,.1)}
.sidebar-divider{border:none;border-top:1px solid var(--border)}
.sidebar-note{font-family:'IBM Plex Mono',monospace;font-size:10px;color:var(--muted);line-height:1.6}
.main{margin-left:220px;padding:24px;flex:1}
@media(max-width:768px){.sidebar{width:100%;position:relative;height:auto}.main{margin-left:0;padding:16px}.layout{flex-direction:column}.metrics{grid-template-columns:repeat(2,1fr)!important}.charts-grid{grid-template-columns:1fr!important}}
.header{display:flex;justify-content:space-between;align-items:flex-end;margin-bottom:24px;flex-wrap:wrap;gap:12px}
.header h1{font-family:'IBM Plex Mono',monospace;font-size:20px;font-weight:600}
.header-time{font-family:'IBM Plex Mono',monospace;font-size:11px;color:var(--muted);text-align:right;line-height:1.6}
.metrics{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;margin-bottom:24px}
.metric{background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:14px 16px}
.metric-label{font-family:'IBM Plex Mono',monospace;font-size:10px;color:var(--muted);letter-spacing:.1em;text-transform:uppercase;margin-bottom:6px}
.metric-value{font-family:'IBM Plex Mono',monospace;font-size:22px;font-weight:600;line-height:1}
.metric-sub{font-family:'IBM Plex Mono',monospace;font-size:11px;color:var(--muted);margin-top:4px}
.section-tabs{display:flex;gap:4px;margin-bottom:20px}
.section-tab{font-family:'IBM Plex Mono',monospace;font-size:12px;padding:8px 16px;border-radius:6px;cursor:pointer;border:1px solid var(--border);color:var(--muted);transition:all .2s}
.section-tab.active-warrior{border-color:var(--blue);color:var(--blue);background:rgba(96,165,250,.08)}
.section-tab.active-finviz{border-color:var(--purple);color:var(--purple);background:rgba(167,139,250,.08)}
.section-content{display:none}
.section-content.active{display:block}
.tabs{display:flex;gap:2px;margin-bottom:20px;border-bottom:1px solid var(--border);overflow-x:auto}
.tab{font-family:'IBM Plex Mono',monospace;font-size:11px;color:var(--muted);padding:8px 16px;cursor:pointer;border-bottom:2px solid transparent;margin-bottom:-1px;white-space:nowrap}
.tab.active{color:var(--blue);border-bottom-color:var(--blue)}
.tab-content{display:none}
.tab-content.active{display:block}
.fvz-tabs .tab.active{color:var(--purple);border-bottom-color:var(--purple)}
.rank-row{padding:12px 0;border-bottom:1px solid var(--border)}
.rank-main{display:grid;grid-template-columns:32px 90px 80px 80px 90px 70px 70px 1fr 100px;align-items:center;gap:8px}
.rank-num{font-family:'IBM Plex Mono',monospace;font-size:18px;color:var(--border);font-weight:700}
.rank-sym{font-family:'IBM Plex Mono',monospace;font-weight:600;font-size:15px;color:var(--text)}
.score-bar-wrap{background:var(--border);border-radius:2px;height:4px;margin-top:4px;overflow:hidden}
.score-bar-fill{height:100%;border-radius:2px}
.score-val{font-family:'IBM Plex Mono',monospace;font-size:17px;font-weight:600}
.score-sub{font-family:'IBM Plex Mono',monospace;font-size:10px;color:var(--muted);margin-top:3px}
.badge{display:inline-block;padding:2px 6px;border-radius:3px;font-family:'IBM Plex Mono',monospace;font-size:10px;margin-right:3px;margin-bottom:2px}
.badge-green{background:#0d2418;color:var(--green)}
.badge-blue{background:#0d1a2a;color:var(--blue)}
.badge-amber{background:#2a1a0d;color:var(--amber)}
.badge-purple{background:#1a0d2a;color:var(--purple)}
.rank-links{padding:6px 0 2px 40px;display:flex;gap:12px;flex-wrap:wrap;align-items:center}
.tv-link{font-family:'IBM Plex Mono',monospace;font-size:11px;color:var(--blue);text-decoration:none;border:1px solid var(--blue);padding:2px 8px;border-radius:3px;white-space:nowrap}
.tv-link:hover{background:rgba(96,165,250,.1)}
.fvz-link{font-family:'IBM Plex Mono',monospace;font-size:11px;color:var(--purple);text-decoration:none;border:1px solid var(--purple);padding:2px 8px;border-radius:3px;white-space:nowrap}
.fvz-link:hover{background:rgba(167,139,250,.1)}
.charts-grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.chart-box{background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:16px}
.data-table{width:100%;border-collapse:collapse;font-family:'IBM Plex Mono',monospace;font-size:12px}
.data-table th{text-align:left;color:var(--muted);font-size:10px;letter-spacing:.1em;text-transform:uppercase;padding:8px 12px;border-bottom:1px solid var(--border)}
.data-table td{padding:8px 12px;border-bottom:1px solid var(--border);color:var(--mid)}
.data-table tr:hover td{background:rgba(255,255,255,.02)}
.empty{font-family:'IBM Plex Mono',monospace;font-size:13px;color:var(--muted);padding:40px 0;text-align:center;line-height:2}
.footer{font-family:'IBM Plex Mono',monospace;font-size:10px;color:var(--border);text-align:center;margin-top:40px;padding-top:16px;border-top:1px solid var(--border)}
.finviz-header{background:rgba(167,139,250,.06);border:1px solid rgba(167,139,250,.2);border-radius:8px;padding:12px 16px;margin-bottom:16px;font-family:'IBM Plex Mono',monospace;font-size:11px;color:var(--purple)}
.mode-badge{display:inline-block;padding:3px 8px;border-radius:4px;font-family:'IBM Plex Mono',monospace;font-size:10px;font-weight:600;margin-left:8px}
</style>
</head>
<body>
<div class="layout">
<aside class="sidebar">
  <h2>⚔️ Warrior Scanner</h2>

  <button class="btn scan" onclick="lancerScan()">▶ Warrior Scan</button>
  <div id="scan-status" style="font-family:IBM Plex Mono,monospace;font-size:10px;color:var(--muted);text-align:center;margin-top:4px"></div>

  <!-- Tickers manuels Warrior -->
  <div>
    <label>📸 Screenshot ou tickers</label>
    <div style="background:var(--bg);border:1px dashed var(--green);border-radius:4px;padding:6px;text-align:center;cursor:pointer;margin-bottom:6px;font-family:IBM Plex Mono,monospace;font-size:10px;color:var(--green)" onclick="document.getElementById('warrior-file').click()">
      📷 Upload screenshot
      <input type="file" id="warrior-file" accept="image/*" style="display:none" onchange="handleWarriorScreenshot(this)">
    </div>
    <div id="warrior-img-status" style="font-family:IBM Plex Mono,monospace;font-size:10px;color:var(--muted);text-align:center;margin-bottom:4px"></div>
    <textarea id="warrior-tickers" oninput="countWarriorTickers()" placeholder="TNON JAGX NXTS..." style="width:100%;height:55px;background:var(--bg);border:1px solid var(--border);color:var(--text);font-family:IBM Plex Mono,monospace;font-size:11px;padding:6px;border-radius:4px;resize:none;outline:none"></textarea>
    <div style="font-family:IBM Plex Mono,monospace;font-size:10px;color:var(--muted)" id="warrior-ticker-count">0 tickers</div>
    <button onclick="lancerScanTickers()" style="width:100%;background:var(--bg);border:1px solid var(--green);color:var(--green);font-family:IBM Plex Mono,monospace;font-size:11px;padding:6px;border-radius:4px;cursor:pointer;margin-top:4px">▶ Scanner ces tickers</button>
    <div id="warrior-ticker-status" style="font-family:IBM Plex Mono,monospace;font-size:10px;color:var(--muted);text-align:center;margin-top:4px"></div>
  </div>

  <hr class="sidebar-divider">

  <button class="btn fvz" onclick="lancerFinviz()">📡 Finviz Scan</button>
  <div id="fvz-status" style="font-family:IBM Plex Mono,monospace;font-size:10px;color:var(--muted);text-align:center;margin-top:4px"></div>

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
    <input type="range" id="score-min" min="0" max="100" value="0" oninput="document.getElementById('score-min-val').textContent=this.value;applyFilters()">
  </div>

  <hr class="sidebar-divider">
  <button class="btn primary" onclick="location.reload()">🔄 Rafraîchir</button>

  <hr class="sidebar-divider">
  <div class="sidebar-note">
    <b>Warrior :</b><br>
    Prix $0.50–$20<br>
    Variation +10%<br>
    RVOL 5x+<br>
    Float &lt;20M<br><br>
    <b>Finviz :</b><br>
    Float &lt;50M<br>
    Volume 500K+<br>
    Tous les movers<br><br>
    <b>Fenêtre :</b><br>
    9h30–11h ET<br>
    15h30–17h MTL
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
    <div class="metric"><div class="metric-label">Finviz trouvés</div><div class="metric-value" id="m-fvz">—</div><div class="metric-sub">stocks scorés</div></div>
  </div>

  <!-- SECTIONS PRINCIPALES -->
  <div class="section-tabs">
    <div class="section-tab active-warrior" onclick="switchSection('warrior',this)">⚔️ Warrior Scanner</div>
    <div class="section-tab" onclick="switchSection('finviz',this)" id="fvz-tab-btn">📡 Finviz Scanner</div>
  </div>

  <!-- WARRIOR SECTION -->
  <div class="section-content active" id="section-warrior">
    <div class="tabs">
      <div class="tab active" onclick="switchTab('ranking',this)">📊 Classement</div>
      <div class="tab" onclick="switchTab('charts',this)">📈 Graphiques</div>
      <div class="tab" onclick="switchTab('indicators',this)">🔬 Indicateurs</div>
      <div class="tab" onclick="switchTab('excluded',this)">❌ Exclus</div>
    </div>
    <div class="tab-content active" id="tab-ranking"><div id="ranking-list"></div></div>
    <div class="tab-content" id="tab-charts"><div class="charts-grid"><div class="chart-box"><div id="chart-score" style="height:280px"></div></div><div class="chart-box"><div id="chart-rvol" style="height:280px"></div></div><div class="chart-box"><div id="chart-chg" style="height:280px"></div></div><div class="chart-box"><div id="chart-radar" style="height:280px"></div></div></div></div>
    <div class="tab-content" id="tab-indicators"><div style="overflow-x:auto"><table class="data-table"><thead><tr id="ind-head"></tr></thead><tbody id="ind-body"></tbody></table></div></div>
    <div class="tab-content" id="tab-excluded"><div id="excluded-list"></div></div>
  </div>

  <!-- FINVIZ SECTION -->
  <div class="section-content" id="section-finviz">
    <div class="finviz-header">
      📡 <b>Finviz Scanner</b> — Envoie un screenshot Finviz ou colle des tickers, le scanner analyse et score chaque stock /100
    </div>

    <!-- INPUT ZONE -->
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:20px" id="fvz-input-grid">

      <!-- Screenshot upload -->
      <div style="background:var(--surface);border:2px dashed var(--purple);border-radius:8px;padding:20px;text-align:center;cursor:pointer" onclick="document.getElementById('fvz-file').click()" id="fvz-drop-zone">
        <div style="font-size:32px;margin-bottom:8px">📸</div>
        <div style="font-family:IBM Plex Mono,monospace;font-size:12px;color:var(--purple)">Upload screenshot Finviz</div>
        <div style="font-family:IBM Plex Mono,monospace;font-size:10px;color:var(--muted);margin-top:4px">PNG · JPG · depuis ton téléphone</div>
        <input type="file" id="fvz-file" accept="image/*" style="display:none" onchange="handleScreenshot(this)">
        <div id="fvz-preview" style="margin-top:12px"></div>
      </div>

      <!-- Ticker manuel -->
      <div style="background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:20px">
        <div style="font-family:IBM Plex Mono,monospace;font-size:11px;color:var(--purple);margin-bottom:8px">✏️ OU colle les tickers manuellement</div>
        <textarea id="fvz-tickers" oninput="countFvzTickers()" placeholder="TNON JAGX NXTS EHGO ADTX&#10;(séparés par espace, virgule ou nouvelle ligne)" style="width:100%;height:90px;background:var(--bg);border:1px solid var(--border);color:var(--text);font-family:IBM Plex Mono,monospace;font-size:12px;padding:8px;border-radius:4px;resize:none;outline:none"></textarea>
        <div style="font-family:IBM Plex Mono,monospace;font-size:10px;color:var(--muted);margin-top:4px" id="fvz-ticker-count">0 tickers détectés</div>
      </div>
    </div>

    <!-- Bouton analyser -->
    <button onclick="analyserFinviz()" style="width:100%;background:var(--bg);border:2px solid var(--purple);color:var(--purple);font-family:IBM Plex Mono,monospace;font-size:13px;font-weight:600;padding:12px;border-radius:6px;cursor:pointer;margin-bottom:20px;transition:background .2s" onmouseover="this.style.background='rgba(167,139,250,.1)'" onmouseout="this.style.background='var(--bg)'" id="fvz-analyze-btn">
      📡 Analyser avec Warrior Scanner
    </button>
    <div id="fvz-analyze-status" style="font-family:IBM Plex Mono,monospace;font-size:11px;color:var(--muted);text-align:center;margin-bottom:16px"></div>

    <!-- Résultats -->
    <div class="tabs fvz-tabs">
      <div class="tab active" onclick="switchFvzTab('fvz-ranking',this)">📊 Classement</div>
      <div class="tab" onclick="switchFvzTab('fvz-charts',this)">📈 Graphiques</div>
      <div class="tab" onclick="switchFvzTab('fvz-table',this)">🔬 Tableau</div>
    </div>
    <div class="tab-content active" id="fvz-ranking"><div id="fvz-ranking-list"><div class="empty">Upload un screenshot Finviz ou colle des tickers pour commencer.</div></div></div>
    <div class="tab-content" id="fvz-charts"><div class="charts-grid"><div class="chart-box"><div id="fvz-chart-score" style="height:280px"></div></div><div class="chart-box"><div id="fvz-chart-rvol" style="height:280px"></div></div></div></div>
    <div class="tab-content" id="fvz-table"><div style="overflow-x:auto"><table class="data-table"><thead><tr id="fvz-head"></tr></thead><tbody id="fvz-body"></tbody></table></div></div>
  </div>

  <div class="footer">⚔️ Warrior Scanner · Yahoo Finance + FMP + Finviz · Score /100</div>
</main>
</div>

<script>
let allData=[], valid=[], excl=[], fvzData=[];
const PL={paper_bgcolor:'#0d0f14',plot_bgcolor:'#13161e',font:{color:'#718096',family:'IBM Plex Mono'},xaxis:{gridcolor:'#1e2533',linecolor:'#1e2533'},yaxis:{gridcolor:'#1e2533',linecolor:'#1e2533'},margin:{t:40,b:30,l:40,r:20}};
function sc(v){return v>=70?'#4ade80':v>=50?'#60a5fa':v>=30?'#fbbf24':'#4a5568'}
function fv(v){v=+v||0;return v>=1e9?(v/1e9).toFixed(1)+'G':v>=1e6?(v/1e6).toFixed(1)+'M':(v/1e3).toFixed(0)+'K'}
function n(v,d=2){return (+v||0).toFixed(d)}

// Section switch
function switchSection(name, el){
  document.querySelectorAll('.section-tab').forEach(t=>{t.classList.remove('active-warrior','active-finviz')});
  document.querySelectorAll('.section-content').forEach(t=>t.classList.remove('active'));
  el.classList.add(name==='finviz'?'active-finviz':'active-warrior');
  document.getElementById('section-'+name).classList.add('active');
  if(name==='finviz') renderFvzRanking();
}

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
  document.getElementById('m-fvz').textContent=fvzData.length;
  if(!valid.length)return;
  const avg=valid.reduce((s,r)=>s+(+r.score||0),0)/valid.length;
  document.getElementById('m-avg').textContent=avg.toFixed(1)+'/100';
  const topR=valid.reduce((a,b)=>(+a.rvol||0)>(+b.rvol||0)?a:b);
  document.getElementById('m-rvol').textContent=n(topR.rvol)+'x';
  document.getElementById('m-rvol-sym').textContent=topR.symbol;
  const topC=valid.reduce((a,b)=>(+a.variation||0)>(+b.variation||0)?a:b);
  document.getElementById('m-chg').textContent='+'+n(topC.variation)+'%';
  document.getElementById('m-chg-sym').textContent=topC.symbol;
}

function renderRow(r, i, showFvzLink=false){
  const s=+r.score||0,col=sc(s),chg=+r.variation||0,rvol=+r.rvol||0,fl=+(r.float_m||r['float m'])||0;
  const rvolCol=rvol>=10?'#4ade80':rvol>=5?'#60a5fa':'#fbbf24';
  const chgCol=chg>=20?'#4ade80':chg>=10?'#60a5fa':'#a0aec0';
  let badges='';
  if(chg>=20) badges+='<span class="badge badge-green">🔥 +20%</span>';
  if(rvol>=10) badges+='<span class="badge badge-green">⚡ RVOL 10x+</span>';
  if(fl>0 && fl<=5) badges+='<span class="badge badge-amber">🎯 Low Float</span>';
  if(r.news) badges+='<span class="badge badge-blue">📰 Catalyst</span>';
  if(showFvzLink) badges+='<span class="badge badge-purple">📡 Finviz</span>';
  const tvUrl=r.tradingview||`https://www.tradingview.com/chart/?symbol=${r.symbol}`;
  const fvzUrl=r.finviz||`https://finviz.com/quote.ashx?t=${r.symbol}`;
  return `
  <div class="rank-row">
    <div class="rank-main">
      <div class="rank-num">${i+1}</div>
      <div><div class="rank-sym">${r.symbol}</div><div style="font-size:9px;color:var(--muted);font-family:IBM Plex Mono,monospace">${r.mode||''} ${r.heure||''}</div></div>
      <div style="font-family:IBM Plex Mono,monospace;font-size:13px">$${n(r.prix||r.price||0)}</div>
      <div style="font-family:IBM Plex Mono,monospace;font-size:14px;font-weight:600;color:${chgCol}">+${n(r.variation||r.change||0)}%</div>
      <div style="font-family:IBM Plex Mono,monospace;font-size:12px;color:var(--mid)">${fv(r.volume)}<br><span style="font-size:10px;color:var(--muted)">moy:${fv(r['avg vol 10j']||r['avg_vol_10j']||0)}</span></div>
      <div style="color:${rvolCol};font-family:IBM Plex Mono,monospace;font-size:13px">${n(rvol)}x</div>
      <div style="color:${fl>0&&fl<=10?'#4ade80':fl<=20?'#fbbf24':'#a0aec0'};font-family:IBM Plex Mono,monospace;font-size:13px">${fl>0?n(fl,1)+'M':'—'}</div>
      <div>
        <div class="score-val" style="color:${col}">${n(s,1)}<span style="font-size:11px;color:var(--muted)">/100</span></div>
        <div class="score-bar-wrap"><div class="score-bar-fill" style="width:${s}%;background:${col}"></div></div>
        <div class="score-sub">M:${r['s.momentum']||r.s_momentum||0} V:${r['s.volume']||r.s_volume||0} T:${r['s.tendance']||r.s_tendance||0} P:${r['s.proximite']||r.s_proximite||0} G:${r['s.gap']||r.s_gap||0}</div>
      </div>
      <div>${badges||'<span style="color:var(--border);font-size:11px">—</span>'}</div>
    </div>
    <div class="rank-links">
      <a class="tv-link" href="${tvUrl}" target="_blank">📈 TradingView</a>
      ${showFvzLink?`<a class="fvz-link" href="${fvzUrl}" target="_blank">📡 Finviz</a>`:''}
    </div>
  </div>`;
}

function renderRanking(){
  const el=document.getElementById('ranking-list');
  if(!valid.length){el.innerHTML='<div class="empty">Aucune action ne passe les filtres Warrior.<br>Clique sur ▶ Warrior Scan<br>ou reviens entre 9h30–11h00 ET.</div>';return;}
  el.innerHTML=valid.map((r,i)=>renderRow(r,i,false)).join('');
}

function renderFvzRanking(){
  const el=document.getElementById('fvz-ranking-list');
  if(!fvzData.length){el.innerHTML='<div class="empty">Aucun résultat Finviz.<br>Clique sur 📡 Finviz Scan pour lancer le scan.</div>';return;}
  el.innerHTML=fvzData.map((r,i)=>renderRow(r,i,true)).join('');
  renderFvzCharts();
  renderFvzTable();
}

function renderFvzCharts(){
  if(!fvzData.length)return;
  const syms=fvzData.slice(0,15).map(r=>r.symbol);
  const scores=fvzData.slice(0,15).map(r=>+r.score||0);
  const rvols=fvzData.slice(0,15).map(r=>+r.rvol||0);
  Plotly.newPlot('fvz-chart-score',[{type:'bar',x:syms,y:scores,marker:{color:scores.map(sc)},text:scores.map(s=>s.toFixed(0)),textposition:'outside'}],{...PL,title:{text:'Score Finviz /100',font:{size:13,color:'#a78bfa'}}},{responsive:true,displayModeBar:false});
  Plotly.newPlot('fvz-chart-rvol',[{type:'bar',x:syms,y:rvols,marker:{color:rvols.map(v=>v>=10?'#4ade80':v>=5?'#60a5fa':'#a78bfa')},text:rvols.map(v=>v.toFixed(1)+'x'),textposition:'outside'}],{...PL,title:{text:'RVOL Finviz',font:{size:13,color:'#a78bfa'}}},{responsive:true,displayModeBar:false});
}

function renderFvzTable(){
  const cols=['symbol','prix','variation','gap %','volume','rvol','float m','sma50','sma200'];
  const labels={'symbol':'Symbole','prix':'Prix','variation':'Var%','gap %':'Gap%','volume':'Volume','rvol':'RVOL','float m':'Float M','sma50':'SMA50','sma200':'SMA200'};
  document.getElementById('fvz-head').innerHTML=cols.map(c=>`<th>${labels[c]||c}</th>`).join('');
  document.getElementById('fvz-body').innerHTML=fvzData.map(r=>`<tr>${cols.map(c=>{
    const v=r[c];
    if(c==='symbol')return`<td style="color:var(--purple);font-weight:600"><a class="fvz-link" style="font-size:11px" href="${r.finviz||'#'}" target="_blank">${v}</a></td>`;
    if(c==='prix')return`<td>$${n(v)}</td>`;
    if(c==='rvol'){const rv=+v||0;return`<td style="color:${rv>=10?'#4ade80':rv>=5?'#60a5fa':'#a78bfa'}">${n(rv)}x</td>`;}
    if(c==='variation'){const cv=+v||0;return`<td style="color:${cv>=20?'#4ade80':'#60a5fa'}">+${n(cv)}%</td>`;}
    if(['gap %'].includes(c))return`<td>${n(v)}%</td>`;
    if(['volume'].includes(c))return`<td>${fv(v)}</td>`;
    return`<td>${n(v)}</td>`;
  }).join('')}</tr>`).join('');
}

function renderCharts(){
  if(!valid.length)return;
  const syms=valid.map(r=>r.symbol),scores=valid.map(r=>+r.score||0),rvols=valid.map(r=>+r.rvol||0),chgs=valid.map(r=>+r.variation||0);
  Plotly.newPlot('chart-score',[{type:'bar',x:syms,y:scores,marker:{color:scores.map(sc)},text:scores.map(s=>s.toFixed(1)),textposition:'outside'}],{...PL,title:{text:'Score /100',font:{size:13,color:'#a0aec0'}},yaxis:{...PL.yaxis,range:[0,110]}},{responsive:true,displayModeBar:false});
  Plotly.newPlot('chart-rvol',[{type:'bar',x:syms,y:rvols,marker:{color:rvols.map(v=>v>=10?'#4ade80':v>=5?'#60a5fa':'#4a5568')},text:rvols.map(v=>v.toFixed(1)+'x'),textposition:'outside'}],{...PL,title:{text:'RVOL',font:{size:13,color:'#a0aec0'}},shapes:[{type:'line',x0:-0.5,x1:syms.length-0.5,y0:5,y1:5,line:{color:'#fbbf24',dash:'dash',width:1}}]},{responsive:true,displayModeBar:false});
  Plotly.newPlot('chart-chg',[{type:'bar',x:syms,y:chgs,marker:{color:chgs.map(v=>v>=20?'#4ade80':v>=10?'#60a5fa':'#a0aec0')},text:chgs.map(v=>'+'+v.toFixed(1)+'%'),textposition:'outside'}],{...PL,title:{text:'Variation %',font:{size:13,color:'#a0aec0'}}},{responsive:true,displayModeBar:false});
  const r=valid[0],maxes=[35,25,20,10,10],vals=[+r['s.momentum']||0,+r['s.volume']||0,+r['s.tendance']||0,+r['s.proximite']||0,+r['s.gap']||0],pcts=vals.map((v,i)=>v/maxes[i]*100),cats=['Momentum','Volume','Tendance','Proximité','Gap'];
  Plotly.newPlot('chart-radar',[{type:'scatterpolar',r:[...pcts,pcts[0]],theta:[...cats,cats[0]],fill:'toself',fillcolor:'rgba(96,165,250,0.15)',line:{color:'#60a5fa',width:2}}],{...PL,title:{text:`Profil ${r.symbol}`,font:{size:13,color:'#a0aec0'}},polar:{bgcolor:'#13161e',radialaxis:{range:[0,100],gridcolor:'#1e2533'},angularaxis:{gridcolor:'#1e2533',tickfont:{size:10,color:'#a0aec0'}}}},{responsive:true,displayModeBar:false});
}

function renderIndicators(){
  const cols=['symbol','prix','variation','gap %','volume','rvol','avg vol 10j','float m','sma50','sma200'];
  const labels={'symbol':'Symbole','prix':'Prix','variation':'Var%','gap %':'Gap%','volume':'Volume','rvol':'RVOL','avg vol 10j':'AvgVol10j','float m':'Float M','sma50':'SMA50','sma200':'SMA200'};
  const avail=cols.filter(c=>valid.some(r=>r[c]!==undefined));
  document.getElementById('ind-head').innerHTML=avail.map(c=>`<th>${labels[c]||c}</th>`).join('');
  document.getElementById('ind-body').innerHTML=valid.map(r=>`<tr>${avail.map(c=>{
    const v=r[c];
    if(c==='symbol')return`<td style="color:var(--text);font-weight:600"><a class="tv-link" style="font-size:11px" href="${r.tradingview||'#'}" target="_blank">${v}</a></td>`;
    if(c==='prix')return`<td>$${n(v)}</td>`;
    if(c==='rvol'){const rv=+v||0;return`<td style="color:${rv>=10?'#4ade80':rv>=5?'#60a5fa':'#fbbf24'}">${n(rv)}x</td>`;}
    if(c==='variation'){const cv=+v||0;return`<td style="color:${cv>=20?'#4ade80':'#60a5fa'}">+${n(cv)}%</td>`;}
    if(c==='float m'){const fv2=+v||0;return`<td style="color:${fv2<=10?'#4ade80':fv2<=20?'#fbbf24':'#a0aec0'}">${n(fv2,1)}M</td>`;}
    if(['gap %'].includes(c))return`<td>${n(v)}%</td>`;
    if(['volume','avg vol 10j'].includes(c))return`<td>${fv(v)}</td>`;
    return`<td>${n(v)}</td>`;
  }).join('')}</tr>`).join('');
}

function renderExcluded(){
  const el=document.getElementById('excluded-list');
  if(!excl.length){el.innerHTML='<div class="empty">Aucune action exclue.</div>';return;}
  el.innerHTML=excl.map(r=>`<div style="display:grid;grid-template-columns:80px 1fr;gap:8px;padding:8px 0;border-bottom:1px solid var(--border)"><div style="font-family:IBM Plex Mono,monospace;font-weight:600;color:var(--mid)">${r.symbol}</div><div style="font-family:IBM Plex Mono,monospace;font-size:11px;color:var(--muted)">${r.reason||'Filtré'}</div></div>`).join('');
}

function switchTab(name,el){
  document.querySelectorAll('#section-warrior .tab').forEach(t=>t.classList.remove('active'));
  document.querySelectorAll('#section-warrior .tab-content').forEach(t=>t.classList.remove('active'));
  el.classList.add('active');
  document.getElementById('tab-'+name).classList.add('active');
  if(name==='charts')renderCharts();
}

function switchFvzTab(name,el){
  document.querySelectorAll('#section-finviz .tab').forEach(t=>t.classList.remove('active'));
  document.querySelectorAll('#section-finviz .tab-content').forEach(t=>t.classList.remove('active'));
  el.classList.add('active');
  document.getElementById(name).classList.add('active');
  if(name==='fvz-charts')renderFvzCharts();
  if(name==='fvz-table')renderFvzTable();
}

function lancerScan(){
  const btn=document.querySelector('.btn.scan');
  const status=document.getElementById('scan-status');
  btn.textContent='⏳ En cours...';
  btn.disabled=true;
  status.textContent='30-120 secondes...';
  fetch('/scan',{method:'POST'}).then(r=>r.json()).then(d=>{
    btn.textContent='▶ Warrior Scan';
    btn.disabled=false;
    if(d.ok){status.textContent='✅ Terminé';loadData();}
    else{status.textContent='❌ '+d.message.slice(0,50);}
  }).catch(()=>{btn.textContent='▶ Warrior Scan';btn.disabled=false;status.textContent='❌ Erreur réseau';});
}

function lancerFinviz(){
  const btn=document.querySelector('.btn.fvz');
  const status=document.getElementById('fvz-status');
  btn.textContent='⏳ En cours...';
  btn.disabled=true;
  status.textContent='30-60 secondes...';
  fetch('/scan-finviz',{method:'POST'}).then(r=>r.json()).then(d=>{
    btn.textContent='📡 Finviz Scan';
    btn.disabled=false;
    if(d.ok){status.textContent='✅ '+d.count+' trouvés';loadFvzData();}
    else{status.textContent='❌ '+d.message.slice(0,50);}
  }).catch(()=>{btn.textContent='📡 Finviz Scan';btn.disabled=false;status.textContent='❌ Erreur réseau';});
}

// ─── WARRIOR — Screenshot + Tickers manuels ───

let warriorImage64 = null;

function handleWarriorScreenshot(input) {
  const file = input.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = e => {
    warriorImage64 = e.target.result.split(',')[1];
    document.getElementById('warrior-img-status').textContent = '✓ Image chargée — clique Scanner ces tickers';
    document.getElementById('warrior-img-status').style.color = 'var(--green)';
  };
  reader.readAsDataURL(file);
}

function countWarriorTickers() {
  const ta = document.getElementById('warrior-tickers');
  if (!ta) return;
  const t = extractTickers(ta.value);
  document.getElementById('warrior-ticker-count').textContent = t.length + ' tickers';
}
async function lancerScanTickers() {
  const status = document.getElementById('warrior-ticker-status');
  const manual = document.getElementById('warrior-tickers').value;
  let tickers  = [];

  // Screenshot via Claude AI
  if (warriorImage64) {
    status.textContent = '🤖 Claude lit le screenshot...';
    status.style.color = 'var(--amber)';
    try {
      const resp = await fetch('https://api.anthropic.com/v1/messages', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
          model: 'claude-sonnet-4-6',
          max_tokens: 500,
          messages: [{
            role: 'user',
            content: [
              {type: 'image', source: {type: 'base64', media_type: 'image/jpeg', data: warriorImage64}},
              {type: 'text', text: 'Extract ALL stock ticker symbols from this image (1-5 uppercase letters). Return ONLY tickers separated by spaces. Example: TNON JAGX NXTS'}
            ]
          }]
        })
      });
      const data = await resp.json();
      if (data.content && data.content[0]) {
        tickers = extractTickers(data.content[0].text);
        document.getElementById('warrior-tickers').value = tickers.join(' ');
        document.getElementById('warrior-ticker-count').textContent = tickers.length + ' tickers';
        status.textContent = `✅ ${tickers.length} tickers extraits`;
        status.style.color = 'var(--green)';
      }
    } catch(e) {
      status.textContent = '⚠ Erreur Claude — utilise les tickers manuels';
      status.style.color = 'var(--amber)';
    }
  }

  // Tickers manuels
  if (manual.trim()) {
    tickers = [...new Set([...tickers, ...extractTickers(manual)])];
  }

  if (tickers.length === 0) {
    status.textContent = '⚠ Aucun ticker détecté';
    status.style.color = 'var(--red)';
    return;
  }

  status.textContent = `⏳ Analyse de ${tickers.length} stocks...`;
  status.style.color = 'var(--amber)';

  try {
    const r = await fetch('/scan-warrior-tickers', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({tickers: tickers})
    });
    const d = await r.json();
    if (d.ok) {
      status.textContent = `✅ ${d.count} qualifiés`;
      status.style.color = 'var(--green)';
      loadData();
    } else {
      status.textContent = '❌ ' + d.message.slice(0,40);
      status.style.color = 'var(--red)';
    }
  } catch(e) {
    status.textContent = '❌ Erreur réseau';
    status.style.color = 'var(--red)';
  }
}

// ─── FINVIZ — Screenshot + Tickers manuels ───

let fvzImage64 = null;

function handleScreenshot(input) {
  const file = input.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = e => {
    fvzImage64 = e.target.result.split(',')[1]; // base64
    document.getElementById('fvz-preview').innerHTML =
      `<img src="${e.target.result}" style="max-width:100%;max-height:120px;border-radius:4px;margin-top:8px">
       <div style="font-family:IBM Plex Mono,monospace;font-size:10px;color:var(--green);margin-top:4px">✓ Image chargée</div>`;
  };
  reader.readAsDataURL(file);
}

function countFvzTickers() {
  const ta = document.getElementById('fvz-tickers');
  if (!ta) return;
  const tickers = extractTickers(ta.value);
  document.getElementById('fvz-ticker-count').textContent = tickers.length + ' tickers détectés';
}

function extractTickers(text) {
  const raw = text.toUpperCase().match(/\b[A-Z]{1,5}\b/g) || [];
  const exclude = ['THE','AND','FOR','NOT','ARE','BUT','FROM','WITH','THIS','THAT','HAVE','WILL','BEEN','PNG','JPG','USD','ETF','NYSE','AMEX'];
  return [...new Set(raw.filter(t => t.length >= 2 && !exclude.includes(t)))];
}

async function analyserFinviz() {
  const btn    = document.getElementById('fvz-analyze-btn');
  const status = document.getElementById('fvz-analyze-status');
  const manual = document.getElementById('fvz-tickers').value;

  let tickers = [];

  // 1. Si screenshot → analyser avec Claude API
  if (fvzImage64) {
    btn.textContent = '🤖 Claude analyse le screenshot...';
    btn.disabled = true;
    status.textContent = 'Extraction des tickers en cours...';
    status.style.color = 'var(--amber)';

    try {
      const resp = await fetch('https://api.anthropic.com/v1/messages', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
          model: 'claude-sonnet-4-6',
          max_tokens: 500,
          messages: [{
            role: 'user',
            content: [
              {
                type: 'image',
                source: {type: 'base64', media_type: 'image/jpeg', data: fvzImage64}
              },
              {
                type: 'text',
                text: 'This is a Finviz stock screener screenshot. Extract ALL stock ticker symbols visible (1-5 uppercase letters). Return ONLY the tickers separated by spaces, nothing else. Example: TNON JAGX NXTS EHGO'
              }
            ]
          }]
        })
      });

      const data = await resp.json();
      if (data.content && data.content[0]) {
        const extracted = data.content[0].text.trim();
        tickers = extractTickers(extracted);
        status.textContent = `✅ Claude a trouvé ${tickers.length} tickers : ${tickers.join(' ')}`;
        status.style.color = 'var(--green)';
        // Mettre dans la zone texte aussi
        document.getElementById('fvz-tickers').value = tickers.join(' ');
        document.getElementById('fvz-ticker-count').textContent = tickers.length + ' tickers détectés';
      }
    } catch(e) {
      status.textContent = '⚠ Erreur Claude API — utilise les tickers manuels';
      status.style.color = 'var(--red)';
    }
  }

  // 2. Si tickers manuels (ou en plus du screenshot)
  if (manual.trim()) {
    const manualTickers = extractTickers(manual);
    tickers = [...new Set([...tickers, ...manualTickers])];
  }

  if (tickers.length === 0) {
    status.textContent = '⚠ Aucun ticker trouvé — upload un screenshot ou colle des tickers';
    status.style.color = 'var(--red)';
    btn.textContent = '📡 Analyser avec Warrior Scanner';
    btn.disabled = false;
    return;
  }

  // 3. Envoyer au scanner
  btn.textContent = `⏳ Analyse de ${tickers.length} stocks...`;
  status.textContent = `Envoi de ${tickers.join(', ')} au scanner...`;
  status.style.color = 'var(--amber)';

  try {
    const r = await fetch('/scan-tickers', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({tickers: tickers})
    });
    const d = await r.json();
    btn.textContent = '📡 Analyser avec Warrior Scanner';
    btn.disabled = false;
    if (d.ok) {
      status.textContent = `✅ ${d.count} stocks scorés`;
      status.style.color = 'var(--green)';
      loadFvzData();
      document.getElementById('m-fvz').textContent = d.count;
    } else {
      status.textContent = '❌ ' + d.message;
      status.style.color = 'var(--red)';
    }
  } catch(e) {
    btn.textContent = '📡 Analyser avec Warrior Scanner';
    btn.disabled = false;
    status.textContent = '❌ Erreur réseau';
    status.style.color = 'var(--red)';
  }
}


  fetch('/data').then(r=>r.json()).then(d=>{
    allData=d.rows;
    document.getElementById('scan-time').innerHTML='Dernier scan<br>'+d.mtime;
    applyFilters();
  });
}

function loadFvzData(){
  fetch('/data-finviz').then(r=>r.json()).then(d=>{
    fvzData=d.rows;
    document.getElementById('m-fvz').textContent=fvzData.length;
    renderFvzRanking();
  });
}

loadData();
loadFvzData();
setInterval(loadData, 60000);
setInterval(loadFvzData, 120000);
</script>
</body>
</html>
"""

# ─────────────────────────────────────────────
# Mapping colonnes CSV
# ─────────────────────────────────────────────
RENAME = {
    "Symbol":"symbol","Score":"score",
    "S.Momentum":"s.momentum","S.Volume":"s.volume",
    "S.Tendance":"s.tendance","S.Proximite":"s.proximite","S.Gap":"s.gap",
    "Prix":"prix","Variation %":"variation","Gap %":"gap %",
    "Volume":"volume","RVOL":"rvol",
    "Avg Vol 10j":"avg vol 10j","Avg Vol 30j":"avg vol 30j",
    "Float M":"float_m","Market Cap":"market_cap",
    "SMA50":"sma50","SMA200":"sma200",
    "52W High":"52w high","Dist 52W %":"dist 52w %",
    "TradingView":"tradingview","News":"news","News Links":"news_links",
    "Heure":"heure","Mode":"mode","Source":"source","Finviz":"finviz",
}

def load_csv(path):
    if not path.exists():
        return [], None
    if path.stat().st_size == 0:
        return [], datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
    mtime = datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
    rows  = []
    try:
        with open(path, newline="", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                clean   = {k.strip(): (v.strip() if isinstance(v, str) else v) for k, v in row.items()}
                renamed = {RENAME.get(k, k.lower()): v for k, v in clean.items()}
                renamed.setdefault("excluded",    False)
                renamed.setdefault("news",        "")
                renamed.setdefault("news_links",  "")
                renamed.setdefault("mode",        "")
                renamed.setdefault("source",      "")
                renamed.setdefault("finviz",      f"https://finviz.com/quote.ashx?t={renamed.get('symbol','')}")
                renamed.setdefault("tradingview", f"https://www.tradingview.com/chart/?symbol={renamed.get('symbol','')}")
                rows.append(renamed)
    except Exception as e:
        print(f"CSV read error: {e}")
    return rows, mtime

@app.route("/")
def index():
    return render_template_string(HTML)

@app.route("/data")
def data():
    rows, mtime = load_csv(CSV_PATH)
    return jsonify({"rows": rows, "mtime": mtime or "—"})

@app.route("/data-finviz")
def data_finviz():
    rows, mtime = load_csv(FVZ_PATH)
    return jsonify({"rows": rows, "mtime": mtime or "—", "count": len(rows)})

@app.route("/scan", methods=["POST"])
def run_scan():
    try:
        result = subprocess.run(
            [sys.executable, "scanner_warrior.py"],
            capture_output=True, text=True, timeout=600, cwd=os.getcwd()
        )
        if result.returncode == 0:
            return jsonify({"ok": True,  "message": "Scan terminé"})
        return jsonify({"ok": False, "message": result.stderr[-300:] or "Erreur scanner"})
    except subprocess.TimeoutExpired:
        return jsonify({"ok": False, "message": "Timeout"})
    except Exception as e:
        return jsonify({"ok": False, "message": str(e)})

@app.route("/scan-warrior-tickers", methods=["POST"])
def scan_warrior_tickers():
    """Lance le scanner Warrior sur une liste de tickers spécifiques."""
    try:
        from flask import request as req
        data    = req.get_json()
        tickers = data.get("tickers", [])
        if not tickers:
            return jsonify({"ok": False, "message": "Aucun ticker reçu"})

        env = os.environ.copy()
        env["MANUAL_TICKERS"] = " ".join(tickers[:50])

        result = subprocess.run(
            [sys.executable, "scanner_warrior.py"],
            capture_output=True, text=True, timeout=600,
            cwd=os.getcwd(), env=env
        )
        rows, _ = load_csv(CSV_PATH)
        if result.returncode == 0:
            return jsonify({"ok": True, "message": "Scan terminé", "count": len(rows)})
        return jsonify({"ok": False, "message": result.stderr[-200:] or "Erreur"})
    except subprocess.TimeoutExpired:
        return jsonify({"ok": False, "message": "Timeout"})
    except Exception as e:
        return jsonify({"ok": False, "message": str(e)})

@app.route("/scan-tickers", methods=["POST"])
def scan_tickers():
    """Analyse une liste de tickers fournis par l'utilisateur."""
    try:
        data    = request.get_json()
        tickers = data.get("tickers", [])
        if not tickers:
            return jsonify({"ok": False, "message": "Aucun ticker reçu"})

        # Passer les tickers au finviz_scanner via variable d'env
        tickers_str = " ".join(tickers[:50])
        env = os.environ.copy()
        env["MANUAL_TICKERS"] = tickers_str

        result = subprocess.run(
            [sys.executable, "finviz_scanner.py"],
            capture_output=True, text=True, timeout=300,
            cwd=os.getcwd(), env=env
        )
        rows, _ = load_csv(FVZ_PATH)
        if result.returncode == 0:
            return jsonify({"ok": True, "message": "Analyse terminée", "count": len(rows)})
        return jsonify({"ok": False, "message": result.stderr[-200:] or "Erreur"})
    except subprocess.TimeoutExpired:
        return jsonify({"ok": False, "message": "Timeout"})
    except Exception as e:
        return jsonify({"ok": False, "message": str(e)})

@app.route("/scan-finviz", methods=["POST"])
def run_finviz():
    try:
        result = subprocess.run(
            [sys.executable, "finviz_scanner.py"],
            capture_output=True, text=True, timeout=300, cwd=os.getcwd()
        )
        rows, _ = load_csv(FVZ_PATH)
        if result.returncode == 0:
            return jsonify({"ok": True,  "message": "Finviz scan terminé", "count": len(rows)})
        return jsonify({"ok": False, "message": result.stderr[-300:] or "Erreur Finviz"})
    except subprocess.TimeoutExpired:
        return jsonify({"ok": False, "message": "Timeout Finviz"})
    except Exception as e:
        return jsonify({"ok": False, "message": str(e)})

if __name__ == "__main__":
    print(f"\n{'='*50}")
    print("  ⚔️  Warrior Scanner Dashboard + Finviz")
    print(f"  http://localhost:{PORT}")
    print(f"{'='*50}\n")
    app.run(host="0.0.0.0", port=PORT, debug=False, threaded=True)
