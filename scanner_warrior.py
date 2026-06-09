import requests
import csv
import time
from datetime import datetime

print("=" * 62)
print("  WARRIOR SCANNER — NASDAQ DYNAMIQUE")
print("  Étape 1 : FMP Screener (filtre rapide)")
print("  Étape 2 : Yahoo Finance (analyse complète)")
print("=" * 62 + "\n")

# =====================================================
# CLÉS API
# =====================================================
FMP_KEY     = "U87EgtNaQOdshmSkc0IgEtCFcgqTDjvy"
FINNHUB_KEY = "d8cf7k9r01qidic7msv0d8cf7k9r01qidic7msvg"

# =====================================================
# CONFIG WARRIOR
# =====================================================
MAX_PRIX      = 20.0
MIN_PRIX      = 0.50
MIN_VOLUME    = 500_000
MIN_VARIATION = 5.0    # Seuil bas pour pré-filtre FMP
MIN_RVOL      = 1.5    # Seuil bas pour pré-filtre FMP
MAX_FLOAT_M   = 100.0
MIN_VARIATION_FINAL = 10.0  # Seuil strict pour le score final
MIN_RVOL_FINAL      = 5.0   # Seuil strict pour le score final
TOP_N         = 15
DELAI         = 0.15

# =====================================================
# ÉTAPE 1 — FMP Screener (filtre rapide sur tout le NASDAQ)
# Retourne les candidats sans analyser stock par stock
# =====================================================

def get_fmp_candidates():
    """
    Utilise le screener FMP pour filtrer tout le NASDAQ
    en UN SEUL appel API — beaucoup plus rapide que Yahoo stock par stock.
    """
    print("  Étape 1 — FMP Screener en cours...")

    candidates = []

    try:
        # Screener FMP : stocks $0.50-$20, variation > 5%, volume > 500K
        url = (
            f"https://financialmodelingprep.com/api/v3/stock-screener"
            f"?marketCapMoreThan=1000000"
            f"&marketCapLessThan=5000000000"
            f"&priceMoreThan={MIN_PRIX}"
            f"&priceLessThan={MAX_PRIX}"
            f"&volumeMoreThan={MIN_VOLUME}"
            f"&exchange=NASDAQ,NYSE,AMEX"
            f"&limit=200"
            f"&apikey={FMP_KEY}"
        )

        r = requests.get(url, timeout=10)
        data = r.json()

        if not isinstance(data, list):
            print(f"  ⚠ FMP Screener erreur: {data}")
            return []

        print(f"  FMP Screener → {len(data)} résultats bruts")

        # Filtrer par variation et volume
        for stock in data:
            symbol = stock.get("symbol", "")
            if not symbol:
                continue

            # Ignorer ETFs, fonds, warrants (symboles avec W, U, R à la fin)
            if len(symbol) > 5 or any(symbol.endswith(x) for x in ["W", "U", "R", "Z", "L"]):
                continue

            candidates.append(symbol)

        print(f"  Candidats après nettoyage : {len(candidates)}\n")
        return candidates

    except Exception as e:
        print(f"  ⚠ Erreur FMP Screener: {e}")
        return []


def get_fmp_movers():
    """
    Récupère les plus grosses hausses du jour via FMP.
    Complément au screener pour ne pas rater les gros movers.
    """
    candidates = []
    try:
        url = f"https://financialmodelingprep.com/api/v3/stock_market/gainers?apikey={FMP_KEY}"
        r = requests.get(url, timeout=8)
        data = r.json()

        if isinstance(data, list):
            for stock in data:
                symbol = stock.get("symbol", "")
                price  = float(stock.get("price", 0) or 0)
                change = float(stock.get("changesPercentage", 0) or 0)

                if not symbol or len(symbol) > 5:
                    continue
                if MIN_PRIX <= price <= MAX_PRIX and change >= MIN_VARIATION:
                    candidates.append(symbol)

            print(f"  FMP Gainers → {len(candidates)} candidats supplémentaires")

    except Exception as e:
        print(f"  ⚠ Erreur FMP Gainers: {e}")

    return candidates


# =====================================================
# ÉTAPE 2 — Yahoo Finance (analyse complète)
# =====================================================

def get_quote_yahoo(symbol):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}

        # Historique daily pour RVOL et SMA
        url_daily = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=60d"
        r_daily   = requests.get(url_daily, headers=headers, timeout=5).json()
        res_daily = r_daily.get("chart", {}).get("result", [])
        if not res_daily:
            return None

        meta_d  = res_daily[0].get("meta", {})
        q_daily = res_daily[0].get("indicators", {}).get("quote", [{}])[0]
        closes  = [c for c in q_daily.get("close",  []) if c is not None]
        vols_d  = [v for v in q_daily.get("volume", []) if v is not None]

        avg_vol_10 = int(sum(vols_d[-11:-1]) / 10) if len(vols_d) >= 11 else 0
        avg_vol_30 = int(sum(vols_d[-31:-1]) / 30) if len(vols_d) >= 31 else 0
        sma50  = round(sum(closes[-50:])  / min(50,  len(closes)), 2) if len(closes) >= 10 else 0
        sma200 = round(sum(closes[-200:]) / min(200, len(closes)), 2) if len(closes) >= 10 else 0
        year_high    = float(meta_d.get("fiftyTwoWeekHigh", 0) or (max(closes) if closes else 0))
        year_low     = float(meta_d.get("fiftyTwoWeekLow",  0) or (min(closes) if closes else 0))
        market_cap   = float(meta_d.get("marketCap",   0) or 0)
        float_shares = float(meta_d.get("floatShares", 0) or 0)

        # Données intraday temps réel
        url_rt = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1m&range=1d&includePrePost=true"
        r_rt   = requests.get(url_rt, headers=headers, timeout=5).json()
        res_rt = r_rt.get("chart", {}).get("result", [])
        if not res_rt:
            return None

        meta_rt    = res_rt[0].get("meta", {})
        prix       = float(meta_rt.get("regularMarketPrice", 0) or 0)
        prev_close = float(meta_rt.get("chartPreviousClose", 0) or 0)
        variation  = round((prix - prev_close) / prev_close * 100, 2) if prev_close > 0 else 0
        volume     = int(meta_rt.get("regularMarketVolume", 0) or 0)

        # Open price
        q_rt   = res_rt[0].get("indicators", {}).get("quote", [{}])[0]
        opens  = [o for o in q_rt.get("open", []) if o is not None]
        open_px = float(opens[0]) if opens else 0.0

        gap  = round((open_px - prev_close) / prev_close * 100, 2) if (open_px > 0 and prev_close > 0) else 0.0
        rvol = round(volume / avg_vol_10, 2) if avg_vol_10 > 0 else 0.0

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

        return {
            "prix": prix, "variation": variation, "volume": volume,
            "open_price": open_px, "prev_close": prev_close,
            "gap": gap, "rvol": rvol,
            "avg_vol_10": avg_vol_10, "avg_vol_30": avg_vol_30,
            "year_high": year_high, "year_low": year_low,
            "sma50": sma50, "sma200": sma200,
            "market_cap": market_cap, "float_shares": float_shares,
            "mode": mode,
        }
    except Exception:
        return None


# =====================================================
# News
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
    return []


# =====================================================
# Score Warrior /100
# =====================================================

def compute_warrior_score(d):
    variation  = d["variation"]
    rvol       = d["rvol"]
    prix       = d["prix"]
    volume     = d["volume"]
    sma50      = d["sma50"]
    sma200     = d["sma200"]
    year_high  = d["year_high"]
    gap        = d["gap"]
    open_price = d["open_price"]

    m = 0
    if variation > 0:   m += 5
    if variation > 5:   m += 5
    if variation > 10:  m += 10
    if variation > 20:  m += 10
    if variation > 30:  m += 5
    score_momentum = min(m, 35)

    v = 0
    if rvol >= 5:  v += 10
    if rvol >= 10: v += 5
    if rvol >= 20: v += 5
    dv = prix * volume
    if dv > 500_000:   v += 2
    if dv > 2_000_000: v += 3
    score_volume = min(v, 25)

    t = 0
    if sma50 > 0 and prix > sma50:                   t += 8
    if sma50 > 0 and sma200 > 0 and sma50 > sma200: t += 7
    if open_price > 0 and prix > open_price:         t += 5
    score_tendance = min(t, 20)

    dist_pct = 0.0
    p = 0
    if year_high > 0:
        dist_pct = (year_high - prix) / year_high * 100
        if dist_pct < 30: p += 2
        if dist_pct < 20: p += 2
        if dist_pct < 10: p += 3
        if dist_pct < 5:  p += 3
    score_proximity = min(p, 10)

    g = 0
    if gap > 2:  g += 3
    if gap > 5:  g += 3
    if gap > 10: g += 4
    score_gap = min(g, 10)

    total = score_momentum + score_volume + score_tendance + score_proximity + score_gap

    return {
        "total":     max(0, min(100, total)),
        "momentum":  score_momentum,
        "volume_sc": score_volume,
        "tendance":  score_tendance,
        "proximite": score_proximity,
        "gap_sc":    score_gap,
        "dist_pct":  round(dist_pct, 2),
    }


# =====================================================
# PIPELINE PRINCIPAL
# =====================================================

results  = []
excluded = []

# Étape 1 : Obtenir les candidats via FMP (rapide)
candidates_screener = get_fmp_candidates()
candidates_movers   = get_fmp_movers()

# Combiner et dédupliquer
all_candidates = list(set(candidates_screener + candidates_movers))

# Fallback : lire watchlist.txt si FMP ne donne rien
if not all_candidates:
    print("  ⚠ FMP sans résultats → fallback watchlist.txt")
    try:
        with open("watchlist.txt", "r") as f:
            all_candidates = [l.strip().upper() for l in f if l.strip() and not l.startswith("#")]
    except Exception:
        print("  ❌ watchlist.txt introuvable")
        exit()

print(f"  Total candidats à analyser : {len(all_candidates)}")
print(f"  Analyse Yahoo en cours...\n")

# Étape 2 : Analyser chaque candidat avec Yahoo
for i, symbol in enumerate(all_candidates, 1):
    print(f"  [{i:>3}/{len(all_candidates)}] {symbol:<6}", end=" ", flush=True)
    time.sleep(DELAI)

    data = get_quote_yahoo(symbol)
    if not data:
        print("⚠ données indisponibles")
        excluded.append({"Symbol": symbol, "Raison": "Données indisponibles"})
        continue

    prix      = data["prix"]
    variation = data["variation"]
    volume    = data["volume"]
    rvol      = data["rvol"]
    float_m   = data["float_shares"] / 1_000_000

    print(f"| ${prix:.2f} | {variation:+.2f}% | RVOL:{rvol:.2f}x | Float:{float_m:.1f}M", end=" ")

    # Filtres stricts
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

    if variation < MIN_VARIATION_FINAL:
        reason = f"Variation < +{MIN_VARIATION_FINAL}% ({variation:+.2f}%)"
        print(f"✗ {reason}")
        excluded.append({"Symbol": symbol, "Raison": reason})
        continue

    if rvol < MIN_RVOL_FINAL:
        reason = f"RVOL < {MIN_RVOL_FINAL}x ({rvol:.2f}x)"
        print(f"✗ {reason}")
        excluded.append({"Symbol": symbol, "Raison": reason})
        continue

    if float_m > 0 and float_m > MAX_FLOAT_M:
        reason = f"Float trop élevé ({float_m:.1f}M)"
        print(f"✗ {reason}")
        excluded.append({"Symbol": symbol, "Raison": reason})
        continue

    scores = compute_warrior_score(data)
    news   = get_news(symbol) if scores["total"] >= 40 else []

    news_titles = " | ".join(n["title"] for n in news) if news else ""
    news_links  = " | ".join(n["link"]  for n in news) if news else ""
    has_news    = "✅" if news else "—"

    print(f"✓ Score {scores['total']}/100 News:{has_news}")

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
        "TradingView": f"https://www.tradingview.com/chart/?symbol={symbol}",
        "News":        news_titles,
        "News Links":  news_links,
        "Mode":        data.get("mode", ""),
        "Heure":       datetime.now().strftime("%H:%M:%S"),
    })

# =====================================================
# Résultats
# =====================================================

results.sort(key=lambda x: x["Score"], reverse=True)

print("\n" + "=" * 62)
print(f"  RÉSULTATS WARRIOR — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
print("=" * 62)

if not results:
    print("\n  Aucune action qualifiée.")
    print("  Relance entre 9h30 et 11h00 ET (15h30-17h00 MTL).\n")
else:
    for i, s in enumerate(results[:TOP_N], 1):
        emoji = "🔥" if s["Score"] >= 80 else "✅" if s["Score"] >= 60 else "📊"
        bar   = "█" * int(s["Score"] / 5) + "░" * (20 - int(s["Score"] / 5))
        print(f"\n  {i}. {s['Symbol']} {emoji}  Score {s['Score']}/100")
        print(f"     {bar}")
        print(f"     Var:{s['Variation %']:+.1f}% | RVOL:{s['RVOL']:.1f}x | Float:{s['Float M']:.1f}M | Gap:{s['Gap %']:+.1f}%")
        print(f"     M:{s['S.Momentum']} V:{s['S.Volume']} T:{s['S.Tendance']} P:{s['S.Proximite']} G:{s['S.Gap']}")
        print(f"     📈 {s['TradingView']}")
        if s["News"]:
            print(f"     📰 {s['News'].split(' | ')[0][:65]}")

print(f"\n  ✅ {len(results)} qualifiés / ✗ {len(excluded)} exclus")
print(f"  Candidats analysés : {len(all_candidates)}")

# Export CSV
if results:
    ts = datetime.now().strftime("%Y%m%d_%H%M")
    for fname in [f"warrior_{ts}.csv", "resultats.csv"]:
        with open(fname, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(results[0].keys()))
            writer.writeheader()
            writer.writerows(results)
    print(f"  💾 Exporté → warrior_{ts}.csv + resultats.csv")
else:
    print("  ⚠ Aucun résultat — nettoyage du CSV")
    # Vider le CSV pour ne pas afficher d'anciennes données
    with open("resultats.csv", "w", newline="", encoding="utf-8") as f:
        f.write("")

print("=" * 62 + "\n")
