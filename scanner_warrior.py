import requests
import csv
import time
from datetime import datetime

print("################################")
print("SCANNER VERSION DEBUG V999")
print("################################")

# =====================================================
# CLÉS API
# =====================================================

FMP_KEY     = "U87EgtNaQOdshmSkc0IgEtCFcgqTDjvy"
FINNHUB_KEY = "d8cf7k9r01qidic7msv0d8cf7k9r01qidic7msvg"

# =====================================================
# CONFIG WARRIOR STYLE (Ross Cameron / Warrior Trading)
# =====================================================

MAX_PRIX      = 1000.0
MIN_PRIX      = 0.01
MIN_VOLUME    = 0
MIN_VARIATION = -100.0
MIN_RVOL      = 0.0
MAX_FLOAT_M   = 999999
TOP_N         = 10
DELAI         = 0.1

print("DEBUG CONFIG")
print("MIN_PRIX =", MIN_PRIX)
print("MAX_PRIX =", MAX_PRIX)
print("MIN_VOLUME =", MIN_VOLUME)
print("MIN_VARIATION =", MIN_VARIATION)
print("MIN_RVOL =", MIN_RVOL)
print("MAX_FLOAT_M =", MAX_FLOAT_M)
print("\n" + "═"*62)
print("  ⚔️   WARRIOR STYLE SCANNER  —  Small Cap Momentum")
print("  Critères : Ross Cameron / Warrior Trading")
print("  MODE DEBUG — Tous les filtres désactivés")
print("═"*62 + "\n")
print("MIN_PRIX =", MIN_PRIX)
print("MAX_PRIX =", MAX_PRIX)
print("MIN_VARIATION =", MIN_VARIATION)
print("MIN_RVOL =", MIN_RVOL)

# =====================================================
# Charger les symboles
# =====================================================

# =====================================================
# Charger les symboles
# =====================================================

try:
    with open("watchlist.txt", "r") as f:
        symbols = [
            line.strip().upper()
            for line in f
            if line.strip() and not line.startswith("#")
        ]

    print(f"NB SYMBOLS = {len(symbols)}")

    symbols = symbols[:5]

    print("MODE TEST : seulement 5 symboles")

except Exception as e:
    print(f"❌ watchlist.txt introuvable : {e}")
    exit()
    

results = []
excluded = []

# =====================================================
# Données Yahoo Finance — DEUX appels séparés
# daily pour historique/RVOL + intraday pour prix RT
# =====================================================

def get_quote_yahoo(symbol):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}

        # ── 1. Historique 60j daily pour volumes moyens et SMA ──
        url_daily = (
            f"https://query1.finance.yahoo.com/v8/finance/chart/"
            f"{symbol}?interval=1d&range=60d"
        )

        r_daily = requests.get(
            url_daily,
            headers=headers,
            timeout=5
        ).json()

        res_daily = r_daily.get("chart", {}).get("result", [])

        if not res_daily:
            return None

        meta_d = res_daily[0].get("meta", {})
        q_daily = res_daily[0].get("indicators", {}).get("quote", [{}])[0]

        closes = [c for c in q_daily.get("close", []) if c is not None]
        vols_d = [v for v in q_daily.get("volume", []) if v is not None]
        # Volumes moyens sur données daily (CORRECT pour RVOL)
        avg_vol_10 = int(sum(vols_d[-11:-1]) / 10) if len(vols_d) >= 11 else 0
        avg_vol_30 = int(sum(vols_d[-31:-1]) / 30) if len(vols_d) >= 31 else 0

        # SMA depuis daily
        sma50  = round(sum(closes[-50:])  / min(50,  len(closes)), 2) if len(closes) >= 10 else 0
        sma200 = round(sum(closes[-200:]) / min(200, len(closes)), 2) if len(closes) >= 10 else 0

        # 52W
        year_high = float(meta_d.get("fiftyTwoWeekHigh", 0) or (max(closes) if closes else 0))
        year_low  = float(meta_d.get("fiftyTwoWeekLow",  0) or (min(closes) if closes else 0))
        market_cap   = float(meta_d.get( "marketCap",    0) or 0)
        float_shares = float(meta_d.get("floatShares",  0) or 0)

        # ── 2. Données intraday pour prix temps réel + volume du jour ──
        url_rt = (
            f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
            f"?interval=1m&range=1d&includePrePost=true"
        )
        r_rt   = requests.get(url_rt, headers=headers, timeout=5).json()
        res_rt = r_rt.get("chart", {}).get("result", [])

        if not res_rt:
            return None

        meta_rt = res_rt[0].get("meta", {})

        print("\n==============================")
        print(f"META_RT RAW {symbol}")
        print("==============================")
        print(meta_rt)
        print("==============================\n")
       
        print(f"META_RT {symbol}")
        
        # Prix et variation
        prix = float(meta_rt.get("regularMarketPrice", 0) or 0)

        prev_close = float(
            meta_rt.get("chartPreviousClose", 0) or 0
        )

        variation = (
            round((prix - prev_close) / prev_close * 100, 2)
            if prev_close > 0
            else 0
        )

        volume = int(
            meta_rt.get("regularMarketVolume", 0) or 0
        )

        q_rt = res_rt[0].get("indicators", {}).get("quote", [{}])[0]

        opens = q_rt.get("open", [])

        open_px = 0.0

        for o in opens:
            if o is not None:
                open_px = float(o)
                break

        if open_px > 0 and prev_close > 0:
            gap = round(
                (open_px - prev_close) / prev_close * 100,
                2
            )
        else:
            gap = 0.0
        # After-hours / Pre-market
        mode    = "Marché"
        post_px = float(meta_rt.get("postMarketPrice", 0) or 0)
        pre_px  = float(meta_rt.get("preMarketPrice",  0) or 0)

        if post_px and abs(post_px - prix) > 0.01:
            prix      = post_px
            variation = round((post_px - prev_close) / prev_close * 100, 2) if prev_close else variation
            mode      = "After-Hours"
        elif pre_px and abs(pre_px - prix) > 0.01:
            prix      = pre_px
            variation = round((pre_px - prev_close) / prev_close * 100, 2) if prev_close else variation
            mode      = "Pre-Market"

        # RVOL = volume du jour / moyenne daily des 10 derniers jours (CORRECT)
        rvol = round(volume / avg_vol_10, 2) if avg_vol_10 > 0 else 0.0

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
            "market_cap":   market_cap,
            "float_shares": float_shares,
            "mode":         mode,
        }
    except Exception as e:
      print(f"ERREUR {symbol}: {e}")
      return None


# =====================================================
# Float depuis FMP (plus fiable que Yahoo)
# =====================================================

def get_float_fmp(symbol):

    print(f"FMP FLOAT -> {symbol}")

    try:
        url = (
            f"https://financialmodelingprep.com/api/v3/"
            f"shares_float?symbol={symbol}&apikey={FMP_KEY}"
        )

        r = requests.get(url, timeout=3).json()

        print("FMP RESPONSE:")
        print(r)

        if isinstance(r, list) and r:
            return float(r[0].get("floatShares", 0) or 0)

    except Exception as e:
        print("FMP ERROR:", e)

    return 0.0


# =====================================================
# News — Finnhub > FMP > Yahoo
# =====================================================

def get_news(symbol):
    if FINNHUB_KEY:
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            url = f"https://finnhub.io/api/v1/company-news?symbol={symbol}&from={today}&to={today}&token={FINNHUB_KEY}"
            r = requests.get(url, timeout=5).json()
            if isinstance(r, list) and r:
                return [{"title": n.get("headline", ""), "link": n.get("url", "")} for n in r[:3]]
        except Exception:
            pass
    try:
        url = f"https://financialmodelingprep.com/stable/news/stock?symbols={symbol}&limit=3&apikey={FMP_KEY}"
        r = requests.get(url, timeout=3).json()
        if isinstance(r, list) and r:
            return [{"title": n.get("title", ""), "link": n.get("url", "")} for n in r[:3]]
    except Exception:
        pass
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
    variation  = d["variation"]
    volume     = d["volume"]
    rvol       = d["rvol"]
    prix       = d["prix"]
    sma50      = d["sma50"]
    sma200     = d["sma200"]
    year_high  = d["year_high"]
    gap        = d["gap"]
    open_price = d["open_price"]

    # Momentum /35
    m = 0
    if variation > 0:   m += 5
    if variation > 5:   m += 5
    if variation > 10:  m += 10
    if variation > 20:  m += 10
    if variation > 30:  m += 5
    score_momentum = min(m, 35)

    # Volume /25
    v = 0
    if rvol >= 5:    v += 10
    if rvol >= 10:   v += 5
    if rvol >= 20:   v += 5
    dollar_vol = prix * volume
    if dollar_vol > 500_000:    v += 2
    if dollar_vol > 2_000_000:  v += 3
    score_volume = min(v, 25)

    # Tendance /20
    t = 0
    if sma50  > 0 and prix > sma50:                   t += 8
    if sma50  > 0 and sma200 > 0 and sma50 > sma200: t += 7
    if open_price > 0 and prix > open_price:          t += 5
    score_tendance = min(t, 20)

    # Proximité 52W /10
    dist_pct = 0.0
    p = 0
    if year_high > 0:
        dist_pct = ((year_high - prix) / year_high) * 100
        if dist_pct < 30: p += 2
        if dist_pct < 20: p += 2
        if dist_pct < 10: p += 3
        if dist_pct < 5:  p += 3
    score_proximity = min(p, 10)

    # Gap /10
    g = 0
    if gap > 2:   g += 3
    if gap > 5:   g += 3
    if gap > 10:  g += 4
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
    print(f"SCAN -> {symbol}")
    print(f"  [{i:>2}/{len(symbols)}] {symbol:<6}", end=" ", flush=True)
    time.sleep(DELAI)

    data = get_quote_yahoo(symbol)
    print(f"DATA -> {data}")
    if not data:
        print("⚠  données indisponibles")
        excluded.append({"Symbol": symbol, "Raison": "Données indisponibles"})
        continue

    prix      = data["prix"]
    variation = data["variation"]
    volume    = data["volume"]
    rvol      = data["rvol"]

    print(f"| ${prix:.2f} | {variation:+.2f}% | Vol:{volume:,} | RVOL:{rvol:.2f}x", end=" ")

    # ── Filtres Warrior ──
    if not (MIN_PRIX <= prix <= MAX_PRIX):
        reason = f"Prix hors plage (${prix:.2f})"
        print(f"✗ {reason}")
        excluded.append({"Symbol": symbol, "Raison": reason})
        continue

    if volume < MIN_VOLUME:
        reason = f"Volume faible ({volume:,})"
        print(f"✗ {reason}")
        excluded.append({"Symbol": symbol, "Raison": reason})
        continue

    if variation < MIN_VARIATION:
        reason = f"Variation < +{MIN_VARIATION}% ({variation:+.2f}%)"
        print(f"✗ {reason}")
        excluded.append({"Symbol": symbol, "Raison": reason})
        continue

    if rvol < MIN_RVOL:
        reason = f"RVOL < {MIN_RVOL}x ({rvol:.2f}x)"
        print(f"✗ {reason}")
        excluded.append({"Symbol": symbol, "Raison": reason})
        continue

    # Float
    float_shares = get_float_fmp(symbol) or data.get("float_shares", 0)
    float_m = float_shares / 1_000_000

    if float_m > MAX_FLOAT_M and float_m > 0:
        reason = f"Float trop élevé ({float_m:.1f}M)"
        print(f"✗ {reason}")
        excluded.append({"Symbol": symbol, "Raison": reason})
        continue

    # Score
    scores = compute_warrior_score(data)
    news   = get_news(symbol) if scores["total"] >= 50 else []

    has_news    = "✅" if news else "—"
    news_titles = " | ".join(n["title"] for n in news) if news else ""
    news_links  = " | ".join(n["link"]  for n in news) if news else ""

    print(f"✓ Score {scores['total']}/100 Float:{float_m:.1f}M News:{has_news}")

    tv_link = f"https://www.tradingview.com/chart/?symbol={symbol}"

    print(f"QUALIFIÉ -> {symbol}")

    results.append({
        "Symbol":      symbol, 
        "Score":       scores["total"],
        "S.Momentum":  scores["momentum"],
        "S.Volume":    scores["volume_sc"],
        "S.Tendance":  scores["tendance"],
        "S.Proximite": scores["proximite"],
        "S.Gap":       scores["gap_sc"],
        "Prix":        round(prix, 2),
        "Variation %": round(variation, 2),
        "Gap %":       round(data["gap"], 2),
        "Volume":      volume,
        "RVOL":        rvol,
        "Avg Vol 10j": data["avg_vol_10"],
        "Avg Vol 30j": data["avg_vol_30"],
        "Float M":     round(float_m, 2),
        "Market Cap":  int(data["market_cap"]),
        "SMA50":       data["sma50"],
        "SMA200":      data["sma200"],
        "52W High":    round(data["year_high"], 2),
        "Dist 52W %":  scores["dist_pct"],
        "TradingView": tv_link,
        "News":        news_titles,
        "News Links":  news_links,
        "Mode":        data.get("mode", ""),
        "Heure":       datetime.now().strftime("%H:%M:%S"),
    })

# =====================================================
# Classement & Affichage
# =====================================================

results.sort(key=lambda x: x["Score"], reverse=True)

print("\n" + "═"*62)
print(f"  ⚔️   RÉSULTATS — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
print("═"*62)

if not results:
    print("\n  Aucune action ne passe les filtres Warrior Style.")
    print("  → Relance entre 9h30 et 11h00 ET (15h30-17h00 MTL).\n")
else:
    for i, s in enumerate(results[:TOP_N], 1):
        bar   = "█" * int(s["Score"] / 5) + "░" * (20 - int(s["Score"] / 5))
        emoji = "🔥" if s["Score"] >= 80 else "✅" if s["Score"] >= 60 else "📊"
        print(f"\n  {i}. {s['Symbol']} {emoji} Score {s['Score']}/100")
        print(f"     {bar}")
        print(f"     Var:{s['Variation %']:+.1f}% | RVOL:{s['RVOL']:.1f}x | Float:{s['Float M']:.1f}M | Gap:{s['Gap %']:+.1f}%")
        print(f"     M:{s['S.Momentum']} V:{s['S.Volume']} T:{s['S.Tendance']} P:{s['S.Proximite']} G:{s['S.Gap']}")
        print(f"     📈 {s['TradingView']}")
        if s["News"]:
            print(f"     📰 {s['News'].split(' | ')[0][:65]}")

print(f"\n  ✅ {len(results)} qualifiés / ✗ {len(excluded)} exclus\n")

# =====================================================
# Export CSV
# =====================================================

print(f"DEBUG RESULTS = {len(results)}")

if results:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")

    with open(f"warrior_{timestamp}.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(results[0].keys()))
        writer.writeheader()
        writer.writerows(results)

    with open("resultats.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(results[0].keys()))
        writer.writeheader()
        writer.writerows(results)

    print(f"  💾 Exporté → warrior_{timestamp}.csv + resultats.csv")

else:
    print("⚠ Aucun résultat qualifié")
    print("⚠ resultats.csv non mis à jour")

print("═"*62 + "\n")
