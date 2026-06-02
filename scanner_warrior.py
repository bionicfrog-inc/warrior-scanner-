import requests
import csv
import time
from datetime import datetime

# =====================================================
# CLÉS API
# =====================================================

FMP_KEY     = "U87EgtNaQOdshmSkc0IgEtCFcgqTDjvy"
FINNHUB_KEY = "d8cf7k9r01qidic7msv0d8cf7k9r01qidic7msvg"  # Optionnel — mets ta clé ici

# =====================================================
# CONFIG WARRIOR STYLE (Ross Cameron / Warrior Trading)
# =====================================================

MAX_PRIX      = 20.0    # $1 à $20 — sweet spot small cap
MIN_PRIX      = 0.10
MIN_VOLUME    = 500_000
MIN_VARIATION = 10.0    # Already up +10% minimum
MIN_RVOL      = 5.0     # Relative Volume 5x minimum
MAX_FLOAT_M   = 20.0    # Float max 20 millions de titres
TOP_N         = 10
DELAI         = 0.25    # délai entre requêtes (secondes)

print("\n" + "═"*62)
print("  ⚔️   WARRIOR STYLE SCANNER  —  Small Cap Momentum")
print("  Critères : Ross Cameron / Warrior Trading")
print("  Prix $1-$20 | +10% | RVOL 5x+ | Float <20M")
print("═"*62 + "\n")

# =====================================================
# Charger les symboles
# =====================================================

try:
    with open("watchlist.txt", "r") as f:
        symbols = [line.strip().upper() for line in f if line.strip() and not line.startswith("#")]
    print(f"  {len(symbols)} symboles chargés depuis watchlist.txt\n")
except Exception:
    print("  ❌  watchlist.txt introuvable")
    exit()

results  = []
excluded = []

# =====================================================
# Données Yahoo Finance (gratuit, sans clé)
# =====================================================

def get_quote_yahoo(symbol):
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1m&range=1d&includePrePost=true"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=10).json()
        result = r.get("chart", {}).get("result", [])
        if not result:
            return None

        meta       = result[0].get("meta", {})
        indicators = result[0].get("indicators", {})
        quotes     = indicators.get("quote", [{}])[0]
        closes     = [c for c in quotes.get("close",  []) if c is not None]
        volumes    = [v for v in quotes.get("volume", []) if v is not None]

        prix       = float(meta.get("regularMarketPrice", 0) or 0)
        variation  = float(meta.get("regularMarketChangePercent", 0) or 0)
        volume     = int(meta.get("regularMarketVolume", 0) or 0)
        open_px    = float(meta.get("regularMarketOpen", 0) or 0)
        prev_close = float(meta.get("chartPreviousClose", 0) or 0)

        # Volumes moyens calculés sur l'historique réel
        avg_vol_10 = int(sum(volumes[-11:-1]) / 10) if len(volumes) >= 11 else 0
        avg_vol_30 = int(sum(volumes[-31:-1]) / 30) if len(volumes) >= 31 else 0
        rvol       = round(volume / avg_vol_10, 2) if avg_vol_10 > 0 else 0.0

        # Gap overnight
        gap = round((open_px - prev_close) / prev_close * 100, 2) if prev_close else 0.0

        # 52W high/low
        year_high = float(meta.get("fiftyTwoWeekHigh", 0) or (max(closes) if closes else 0))
        year_low  = float(meta.get("fiftyTwoWeekLow",  0) or (min(closes) if closes else 0))

        # SMA calculées depuis l'historique
        sma50  = round(sum(closes[-50:])  / min(50,  len(closes)), 2) if len(closes) >= 10 else 0
        sma200 = round(sum(closes[-200:]) / min(200, len(closes)), 2) if len(closes) >= 10 else 0

        return {
            "prix":         prix,
            "variation":    variation,
            "volume":       volume,
            "open_price":   open_px,
            "prev_close":   prev_close,
            "gap":          gap,
            "rvol":         rvol,
            "avg_vol_10":   avg_vol_10,
            "avg_vol_30":   avg_vol_30,
            "year_high":    year_high,
            "year_low":     year_low,
            "sma50":        sma50,
            "sma200":       sma200,
            "market_cap":   float(meta.get("marketCap", 0) or 0),
            "float_shares": float(meta.get("floatShares", 0) or 0),
        }
    except Exception:
        return None


# =====================================================
# Float depuis FMP (plus fiable que Yahoo)
# =====================================================

def get_float_fmp(symbol):
    try:
        url = f"https://financialmodelingprep.com/api/v3/shares_float?symbol={symbol}&apikey={FMP_KEY}"
        r = requests.get(url, timeout=5).json()
        if isinstance(r, list) and r:
            return float(r[0].get("floatShares", 0) or 0)
    except Exception:
        pass
    return 0.0


# =====================================================
# News — Finnhub > FMP > Yahoo
# =====================================================

def get_news(symbol):
    # 1. Finnhub (le plus rapide si dispo)
    if FINNHUB_KEY:
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            url = f"https://finnhub.io/api/v1/company-news?symbol={symbol}&from={today}&to={today}&token={FINNHUB_KEY}"
            r = requests.get(url, timeout=5).json()
            if isinstance(r, list) and r:
                return [{"title": n.get("headline", ""), "link": n.get("url", "")} for n in r[:3]]
        except Exception:
            pass

    # 2. FMP
    try:
        url = f"https://financialmodelingprep.com/stable/news/stock?symbols={symbol}&limit=3&apikey={FMP_KEY}"
        r = requests.get(url, timeout=5).json()
        if isinstance(r, list) and r:
            return [{"title": n.get("title", ""), "link": n.get("url", "")} for n in r[:3]]
    except Exception:
        pass

    # 3. Yahoo fallback
    try:
        url = f"https://query1.finance.yahoo.com/v1/finance/search?q={symbol}&newsCount=3&quotesCount=0"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=5).json()
        news = r.get("news", [])
        return [{"title": n.get("title", ""), "link": n.get("link", "")} for n in news[:3]]
    except Exception:
        pass

    return []


# =====================================================
# Score Warrior Style /100
# =====================================================

def compute_warrior_score(d):
    """
    Score /100 calqué sur la philosophie Ross Cameron.

    Momentum    /35  — variation % du jour (seuils : 10%, 20%, 30%)
    Volume      /25  — RVOL (roi chez Warrior) + dollar volume
    Tendance    /20  — SMA50/200 + prix au-dessus de l'open
    Proximité   /10  — distance au 52W high (breakout imminent)
    Gap         /10  — gap overnight positif = catalyst fort
    """
    variation  = d["variation"]
    volume     = d["volume"]
    rvol       = d["rvol"]
    prix       = d["prix"]
    sma50      = d["sma50"]
    sma200     = d["sma200"]
    year_high  = d["year_high"]
    gap        = d["gap"]
    open_price = d["open_price"]

    # ── Momentum /35 ─────────────────────────────
    m = 0
    if variation > 0:   m += 5
    if variation > 5:   m += 5
    if variation > 10:  m += 10   # Seuil Warrior minimum
    if variation > 20:  m += 10   # Squeeze fort
    if variation > 30:  m += 5    # Squeeze exceptionnel
    score_momentum = min(m, 35)

    # ── Volume /25 ───────────────────────────────
    v = 0
    if rvol >= 5:    v += 10   # Seuil Warrior minimum
    if rvol >= 10:   v += 5    # Fort
    if rvol >= 20:   v += 5    # Exceptionnel
    dollar_vol = prix * volume
    if dollar_vol > 500_000:    v += 2
    if dollar_vol > 2_000_000:  v += 3
    score_volume = min(v, 25)

    # ── Tendance /20 ─────────────────────────────
    t = 0
    if sma50  > 0 and prix > sma50:                   t += 8
    if sma50  > 0 and sma200 > 0 and sma50 > sma200: t += 7
    if open_price > 0 and prix > open_price:          t += 5
    score_tendance = min(t, 20)

    # ── Proximité 52W high /10 ───────────────────
    dist_pct = 0.0
    p = 0
    if year_high > 0:
        dist_pct = ((year_high - prix) / year_high) * 100
        if dist_pct < 30: p += 2
        if dist_pct < 20: p += 2
        if dist_pct < 10: p += 3
        if dist_pct < 5:  p += 3   # Quasi-breakout = signal fort
    score_proximity = min(p, 10)

    # ── Gap /10 ──────────────────────────────────
    g = 0
    if gap > 2:   g += 3
    if gap > 5:   g += 3
    if gap > 10:  g += 4   # Gap énorme = catalyst évident
    score_gap = min(g, 10)

    total = score_momentum + score_volume + score_tendance + score_proximity + score_gap

    return {
        "total":      max(0, min(100, total)),
        "momentum":   score_momentum,
        "volume_sc":  score_volume,
        "tendance":   score_tendance,
        "proximite":  score_proximity,
        "gap_sc":     score_gap,
        "dist_pct":   round(dist_pct, 2),
    }


# =====================================================
# Scanner principal
# =====================================================

for i, symbol in enumerate(symbols, 1):
    print(f"  [{i:>2}/{len(symbols)}] {symbol:<6}", end=" ", flush=True)
    time.sleep(DELAI)

    data = get_quote_yahoo(symbol)
    if not data:
        print("⚠  données indisponibles")
        excluded.append({"Symbol": symbol, "Raison": "Données indisponibles"})
        continue

    prix      = data["prix"]
    variation = data["variation"]
    volume    = data["volume"]
    rvol      = data["rvol"]

    # ── Filtres Warrior (dans l'ordre de Ross Cameron) ──

    if not (MIN_PRIX <= prix <= MAX_PRIX):
        reason = f"Prix hors plage ${MIN_PRIX}-${MAX_PRIX} (${prix:.2f})"
        print(f"✗  {reason}")
        excluded.append({"Symbol": symbol, "Raison": reason})
        continue

    if volume < MIN_VOLUME:
        reason = f"Volume faible ({volume:,})"
        print(f"✗  {reason}")
        excluded.append({"Symbol": symbol, "Raison": reason})
        continue

    if variation < MIN_VARIATION:
        reason = f"Variation < +{MIN_VARIATION}% ({variation:+.2f}%)"
        print(f"✗  {reason}")
        excluded.append({"Symbol": symbol, "Raison": reason})
        continue

    if rvol < MIN_RVOL:
        reason = f"RVOL < {MIN_RVOL}x ({rvol:.2f}x)"
        print(f"✗  {reason}")
        excluded.append({"Symbol": symbol, "Raison": reason})
        continue

    # Float — FMP d'abord, Yahoo en fallback
    float_shares = get_float_fmp(symbol) or data.get("float_shares", 0)
    float_m = float_shares / 1_000_000

    if float_m > MAX_FLOAT_M and float_m > 0:
        reason = f"Float trop élevé ({float_m:.1f}M > {MAX_FLOAT_M}M)"
        print(f"✗  {reason}")
        excluded.append({"Symbol": symbol, "Raison": reason})
        continue

   # ── Calcul du score ──────────────────────────
    scores = compute_warrior_score(data)

    news = []

    if scores["total"] >= 60:
        news = get_news(symbol)

    has_news    = "✅" if news else "—"
    news_titles = " | ".join(n["title"] for n in news) if news else ""
    news_links  = " | ".join(n["link"]  for n in news) if news else ""

    print(
        f"✓  Score {scores['total']:>3}/100  |  "
        f"Var {variation:>+6.1f}%  |  "
        f"RVOL {rvol:>5.1f}x  |  "
        f"Float {float_m:>5.1f}M  |  "
        f"News {has_news}"
    )

    tv_link = f"https://www.tradingview.com/chart/?symbol={symbol}"

    results.append({
        "Symbol":        symbol,
        "Score":         scores["total"],
        "S.Momentum":    scores["momentum"],
        "S.Volume":      scores["volume_sc"],
        "S.Tendance":    scores["tendance"],
        "S.Proximite":   scores["proximite"],
        "S.Gap":         scores["gap_sc"],
        "Prix":          round(prix, 2),
        "Variation %":   round(variation, 2),
        "Gap %":         round(data["gap"], 2),
        "Volume":        volume,
        "RVOL":          rvol,
        "Avg Vol 10j":   data["avg_vol_10"],
        "Avg Vol 30j":   data["avg_vol_30"],
        "Float M":       round(float_m, 2),
        "Market Cap":    int(data["market_cap"]),
        "SMA50":         data["sma50"],
        "SMA200":        data["sma200"],
        "52W High":      round(data["year_high"], 2),
        "Dist 52W %":    scores["dist_pct"],
        "TradingView":   tv_link,
        "News":          news_titles,
        "News Links":    news_links,
        "Heure":         datetime.now().strftime("%H:%M:%S"),
    })

# =====================================================
# Classement & Affichage final
# =====================================================

results.sort(key=lambda x: x["Score"], reverse=True)

print("\n" + "═"*62)
print(f"  ⚔️   RÉSULTATS WARRIOR — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
print("═"*62)

if not results:
    print("\n  Aucune action ne passe les filtres Warrior Style.")
    print("  → Marchés fermés ou journée calme.")
    print("  → Relance en semaine entre 9h30 et 11h00 ET.\n")
else:
    print(f"\n  {'#':<3} {'Sym':<6} {'Score':>5}  {'Var%':>7}  {'RVOL':>6}  {'Float':>6}  {'Gap%':>6}  Scores détail")
    print("  " + "─"*70)
    for i, s in enumerate(results[:TOP_N], 1):
        bar   = "█" * int(s["Score"] / 5) + "░" * (20 - int(s["Score"] / 5))
        emoji = "🔥" if s["Score"] >= 80 else "✅" if s["Score"] >= 60 else "📊"
        print(
            f"  {i:<3} {s['Symbol']:<6} {s['Score']:>3}/100  "
            f"{s['Variation %']:>+6.1f}%  "
            f"{s['RVOL']:>5.1f}x  "
            f"{s['Float M']:>5.1f}M  "
            f"{s['Gap %']:>+5.1f}%  "
            f"{emoji}"
        )
        print(f"      {bar}")
        print(
            f"      M:{s['S.Momentum']}/35  "
            f"V:{s['S.Volume']}/25  "
            f"T:{s['S.Tendance']}/20  "
            f"P:{s['S.Proximite']}/10  "
            f"G:{s['S.Gap']}/10"
        )
        print(f"      📈 {s['TradingView']}")
        if s["News"]:
            titre = s["News"].split(" | ")[0][:65]
            print(f"      📰 {titre}")
        print()

print(f"  ✅ {len(results)} qualifiés  /  ✗ {len(excluded)} exclus\n")

if excluded:
    print("  Exclus :")
    for e in excluded:
        print(f"  • {e['Symbol']:<6}  {e['Raison']}")
    print()

# =====================================================
# Export CSV
# =====================================================

if results:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    filename  = f"warrior_{timestamp}.csv"

    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(results[0].keys()))
        writer.writeheader()
        writer.writerows(results)

    # Aussi écraser results.csv pour le dashboard Streamlit
    with open("results.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(results[0].keys()))
        writer.writeheader()
        writer.writerows(results)

    print(f"  💾 Exporté → {filename}  +  results.csv\n")

print("═"*62 + "\n")
