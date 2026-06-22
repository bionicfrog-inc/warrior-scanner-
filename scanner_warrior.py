import requests
import csv
import time
import os
from datetime import datetime
import pytz

print("=" * 62)
print("  WARRIOR SCANNER — INTELLIGENT + ALERTES TELEGRAM")
print("=" * 62 + "\n")

# =====================================================
# CLÉS API
# =====================================================
FMP_KEY     = os.environ.get("FMP_KEY",     "U87EgtNaQOdshmSkc0IgEtCFcgqTDjvy")
FINNHUB_KEY = os.environ.get("FINNHUB_KEY", "d8cf7k9r01qidic7msv0d8cf7k9r01qidic7msvg")
TG_TOKEN    = os.environ.get("TG_TOKEN",    "")
TG_CHAT_ID  = os.environ.get("TG_CHAT_ID",  "")

# =====================================================
# DÉTECTION DU MODE SELON L'HEURE ET
# =====================================================
ET = pytz.timezone("America/New_York")
now_et = datetime.now(ET)
heure  = now_et.hour + now_et.minute / 60
jour   = now_et.weekday()  # 0=Lundi, 6=Dimanche

# Weekend — pas de marché
if jour >= 5:
    print("  ⚠ Weekend — marché fermé")
    print("  ℹ Le scanner tourne du lundi au vendredi")
    # Vider le CSV
    with open("resultats.csv", "w", newline="", encoding="utf-8") as f:
        f.write("")
    exit(0)

# Déterminer le mode
if 4.0 <= heure < 9.5:
    MODE         = "PRE-MARKET"
    MIN_VAR      = 2.0
    MIN_RVOL     = 0.5
    MIN_VOL      = 25_000
    MAX_FLOAT    = 100.0
    MODE_EMOJI   = "🌅"
    MODE_DESC    = "Gappers pre-market (4h-9h30 ET)"

elif 9.5 <= heure < 11.0:
    MODE         = "OUVERTURE"
    MIN_VAR      = 10.0
    MIN_RVOL     = 5.0
    MIN_VOL      = 500_000
    MAX_FLOAT    = 20.0
    MODE_EMOJI   = "🔥"
    MODE_DESC    = "Critères Warrior stricts (9h30-11h ET)"

elif 11.0 <= heure < 14.0:
    MODE         = "MILIEU"
    MIN_VAR      = 8.0
    MIN_RVOL     = 3.0
    MIN_VOL      = 300_000
    MAX_FLOAT    = 30.0
    MODE_EMOJI   = "📊"
    MODE_DESC    = "Surveillance mid-day (11h-14h ET)"

elif 14.0 <= heure < 16.0:
    MODE         = "FERMETURE"
    MIN_VAR      = 8.0
    MIN_RVOL     = 3.0
    MIN_VOL      = 300_000
    MAX_FLOAT    = 30.0
    MODE_EMOJI   = "🌆"
    MODE_DESC    = "Surveillance fin de journée (14h-16h ET)"

elif 16.0 <= heure < 20.0:
    MODE         = "AFTER-HOURS"
    MIN_VAR      = 5.0
    MIN_RVOL     = 1.5
    MIN_VOL      = 100_000
    MAX_FLOAT    = 50.0
    MODE_EMOJI   = "🌙"
    MODE_DESC    = "After-hours (16h-20h ET)"

else:
    print(f"  ⚠ Hors heures de marché ({now_et.strftime('%H:%M')} ET)")
    print("  ℹ Marché actif : lun-ven 4h00-20h00 ET")
    with open("resultats.csv", "w", newline="", encoding="utf-8") as f:
        f.write("")
    exit(0)

MIN_PRIX  = 0.50
MAX_PRIX  = 20.0
TOP_N     = 15
DELAI     = 0.15

print(f"  {MODE_EMOJI} MODE : {MODE}")
print(f"  {MODE_DESC}")
print(f"  Heure ET : {now_et.strftime('%H:%M')}")
print(f"  Variation min : +{MIN_VAR}%")
print(f"  RVOL min      : {MIN_RVOL}x")
print(f"  Volume min    : {MIN_VOL:,}")
print(f"  Float max     : {MAX_FLOAT}M\n")

# =====================================================
# TELEGRAM
# =====================================================

def send_telegram(message):
    if not TG_TOKEN or not TG_CHAT_ID:
        return
    try:
        url  = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
        data = {"chat_id": TG_CHAT_ID, "text": message, "parse_mode": "HTML"}
        r    = requests.post(url, data=data, timeout=10)
        if r.status_code == 200:
            print("  ✅ Alerte Telegram envoyée")
        else:
            print(f"  ⚠ Telegram erreur {r.status_code}")
    except Exception as e:
        print(f"  ⚠ Telegram: {e}")


def send_telegram_alert(stock):
    score   = stock["Score"]
    symbol  = stock["Symbol"]
    prix    = stock["Prix"]
    var     = stock["Variation %"]
    rvol    = stock["RVOL"]
    float_m = stock["Float M"]
    gap     = stock["Gap %"]
    news    = stock["News"].split(" | ")[0][:80] if stock["News"] else ""
    tv_link = stock["TradingView"]

    emoji     = "🔥" if score >= 80 else "✅" if score >= 60 else "📊"
    news_line = f"\n📰 <b>Catalyst :</b> {news}" if news else ""
    mode_line = f"\n⏱ <b>Mode :</b> {MODE_EMOJI} {MODE}"

    msg = (
        f"⚔️ <b>WARRIOR ALERT</b>\n"
        f"{'═' * 28}\n"
        f"{emoji} <b>{symbol}</b> — Score <b>{score}/100</b>\n\n"
        f"💰 <b>Prix :</b> ${prix:.2f}\n"
        f"📈 <b>Variation :</b> +{var:.1f}%\n"
        f"⚡ <b>RVOL :</b> {rvol:.1f}x\n"
        f"📊 <b>Gap :</b> +{gap:.1f}%\n"
        f"🎯 <b>Float :</b> {float_m:.1f}M"
        f"{news_line}"
        f"{mode_line}\n\n"
        f"📈 <a href='{tv_link}'>Voir sur TradingView</a>\n"
        f"⏰ {now_et.strftime('%H:%M')} ET"
    )
    send_telegram(msg)


# =====================================================
# FMP SCREENER
# =====================================================

def get_fmp_candidates():
    print("  Étape 1 — FMP Screener...")
    candidates = []
    try:
        url = (
            f"https://financialmodelingprep.com/api/v3/stock-screener"
            f"?marketCapMoreThan=500000"
            f"&marketCapLessThan=5000000000"
            f"&priceMoreThan={MIN_PRIX}"
            f"&priceLessThan={MAX_PRIX}"
            f"&volumeMoreThan={MIN_VOL}"
            f"&exchange=NASDAQ,NYSE,AMEX"
            f"&limit=300"
            f"&apikey={FMP_KEY}"
        )
        data = requests.get(url, timeout=10).json()
        if not isinstance(data, list):
            print(f"  ⚠ FMP Screener: {str(data)[:100]}")
            return []
        print(f"  FMP Screener → {len(data)} résultats bruts")
        for stock in data:
            symbol = stock.get("symbol", "")
            if not symbol or len(symbol) > 5:
                continue
            if any(symbol.endswith(x) for x in ["W", "U", "R", "Z", "L"]):
                continue
            candidates.append(symbol)
        print(f"  Après nettoyage : {len(candidates)}")
    except Exception as e:
        print(f"  ⚠ FMP Screener erreur: {e}")
    return candidates


def get_fmp_gainers():
    candidates = []
    try:
        url  = f"https://financialmodelingprep.com/api/v3/stock_market/gainers?apikey={FMP_KEY}"
        data = requests.get(url, timeout=8).json()
        if isinstance(data, list):
            for s in data:
                symbol = s.get("symbol", "")
                price  = float(s.get("price", 0) or 0)
                change = float(s.get("changesPercentage", 0) or 0)
                if not symbol or len(symbol) > 5:
                    continue
                if any(symbol.endswith(x) for x in ["W", "U", "R", "Z"]):
                    continue
                if MIN_PRIX <= price <= MAX_PRIX and change >= MIN_VAR:
                    candidates.append(symbol)
        print(f"  FMP Gainers → {len(candidates)} candidats")
    except Exception as e:
        print(f"  ⚠ FMP Gainers: {e}")
    return candidates


def get_fmp_premarket():
    """Gappers pre-market via FMP."""
    candidates = []
    if MODE not in ["PRE-MARKET", "OUVERTURE"]:
        return candidates
    try:
        url  = f"https://financialmodelingprep.com/api/v3/pre-market-stocks?apikey={FMP_KEY}"
        data = requests.get(url, timeout=8).json()
        if isinstance(data, list):
            for s in data:
                symbol = s.get("symbol", "")
                price  = float(s.get("price", 0) or 0)
                change = float(s.get("changesPercentage", 0) or 0)
                if not symbol or len(symbol) > 5:
                    continue
                if MIN_PRIX <= price <= MAX_PRIX and change >= MIN_VAR:
                    candidates.append(symbol)
            print(f"  FMP Pre-Market → {len(candidates)} gappers")
    except Exception as e:
        print(f"  ⚠ FMP Pre-Market: {e}")
    return candidates


# =====================================================
# YAHOO FINANCE
# =====================================================

def get_quote_yahoo(symbol):
    try:
        headers   = {"User-Agent": "Mozilla/5.0"}

        # Daily pour RVOL
        url_d  = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=60d"
        r_d    = requests.get(url_d, headers=headers, timeout=5).json()
        res_d  = r_d.get("chart", {}).get("result", [])
        if not res_d:
            return None

        meta_d  = res_d[0].get("meta", {})
        q_d     = res_d[0].get("indicators", {}).get("quote", [{}])[0]
        closes  = [c for c in q_d.get("close",  []) if c is not None]
        vols_d  = [v for v in q_d.get("volume", []) if v is not None]

        avg_vol_10   = int(sum(vols_d[-11:-1]) / 10) if len(vols_d) >= 11 else 0
        avg_vol_30   = int(sum(vols_d[-31:-1]) / 30) if len(vols_d) >= 31 else 0
        sma50        = round(sum(closes[-50:])  / min(50,  len(closes)), 2) if len(closes) >= 10 else 0
        sma200       = round(sum(closes[-200:]) / min(200, len(closes)), 2) if len(closes) >= 10 else 0
        year_high    = float(meta_d.get("fiftyTwoWeekHigh", 0) or (max(closes) if closes else 0))
        year_low     = float(meta_d.get("fiftyTwoWeekLow",  0) or (min(closes) if closes else 0))
        market_cap   = float(meta_d.get("marketCap",   0) or 0)
        float_shares = float(meta_d.get("floatShares", 0) or 0)
        # Fallback FMP si Yahoo ne retourne pas le float
        if float_shares == 0:
            try:
                fmp_url = f"https://financialmodelingprep.com/api/v3/shares_float?symbol={symbol}&apikey={FMP_KEY}"
                fmp_r = requests.get(fmp_url, timeout=3).json()
                if isinstance(fmp_r, list) and fmp_r:
                    float_shares = float(fmp_r[0].get("floatShares", 0) or 0)
            except Exception:
                pass
        # Intraday temps réel
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

        q_rt    = res_rt[0].get("indicators", {}).get("quote", [{}])[0]
        opens   = [o for o in q_rt.get("open", []) if o is not None]
        open_px = float(opens[0]) if opens else 0.0
        gap     = round((open_px - prev_close) / prev_close * 100, 2) if (open_px > 0 and prev_close > 0) else 0.0
        rvol    = round(volume / avg_vol_10, 2) if avg_vol_10 > 0 else 0.0

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
# NEWS
# =====================================================

def get_news(symbol):
    if FINNHUB_KEY:
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            url   = f"https://finnhub.io/api/v1/company-news?symbol={symbol}&from={today}&to={today}&token={FINNHUB_KEY}"
            r     = requests.get(url, timeout=5).json()
            if isinstance(r, list) and r:
                return [{"title": n.get("headline", ""), "link": n.get("url", "")} for n in r[:3]]
        except Exception:
            pass
    try:
        url  = f"https://financialmodelingprep.com/stable/news/stock?symbols={symbol}&limit=3&apikey={FMP_KEY}"
        r    = requests.get(url, timeout=3).json()
        if isinstance(r, list) and r:
            return [{"title": n.get("title", ""), "link": n.get("url", "")} for n in r[:3]]
    except Exception:
        pass
    return []


# =====================================================
# SCORE /100
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
    if rvol >= 2:  v += 5
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

# Collecter les candidats selon le mode
c_screener  = get_fmp_candidates()
c_gainers   = get_fmp_gainers()
c_premarket = get_fmp_premarket()

all_candidates = list(set(c_screener + c_gainers + c_premarket))

# Fallback watchlist
if not all_candidates:
    print("  ⚠ FMP sans résultats → fallback watchlist.txt")
    try:
        with open("watchlist.txt", "r") as f:
            all_candidates = [l.strip().upper() for l in f if l.strip() and not l.startswith("#")]
    except Exception:
        print("  ❌ watchlist.txt introuvable")
        exit()

print(f"\n  Total candidats à analyser : {len(all_candidates)}")
print(f"  Analyse Yahoo en cours...\n")

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

    # Filtres selon le mode
    if not (MIN_PRIX <= prix <= MAX_PRIX):
        print(f"✗ Prix (${prix:.2f})")
        excluded.append({"Symbol": symbol, "Raison": f"Prix (${prix:.2f})"})
        continue

    if volume < MIN_VOL:
        print(f"✗ Volume ({volume:,})")
        excluded.append({"Symbol": symbol, "Raison": f"Volume ({volume:,})"})
        continue

    if variation < MIN_VAR:
        print(f"✗ Var ({variation:+.2f}%)")
        excluded.append({"Symbol": symbol, "Raison": f"Var ({variation:+.2f}%)"})
        continue

    if rvol < MIN_RVOL:
        print(f"✗ RVOL ({rvol:.2f}x)")
        excluded.append({"Symbol": symbol, "Raison": f"RVOL ({rvol:.2f}x)"})
        continue

    if float_m > 0 and float_m > MAX_FLOAT:
        print(f"✗ Float ({float_m:.1f}M)")
        excluded.append({"Symbol": symbol, "Raison": f"Float ({float_m:.1f}M)"})
        continue

    scores = compute_warrior_score(data)
    news   = get_news(symbol) if scores["total"] >= 40 else []

    news_titles = " | ".join(n["title"] for n in news) if news else ""
    news_links  = " | ".join(n["link"]  for n in news) if news else ""
    has_news    = "✅" if news else "—"

    print(f"✓ Score {scores['total']}/100 News:{has_news}")

    result = {
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
        "Heure":       now_et.strftime("%H:%M:%S"),
    }
    results.append(result)
    send_telegram_alert(result)

# =====================================================
# RÉSULTATS
# =====================================================

results.sort(key=lambda x: x["Score"], reverse=True)

print("\n" + "=" * 62)
print(f"  {MODE_EMOJI} {MODE} — {now_et.strftime('%Y-%m-%d %H:%M')} ET")
print("=" * 62)

if not results:
    print(f"\n  Aucune action qualifiée en mode {MODE}.")
    if MODE == "OUVERTURE":
        print("  → Journée calme ou marché sans momentum aujourd'hui.")
    elif MODE == "PRE-MARKET":
        print("  → Pas de gappers significatifs ce matin.")
    else:
        print("  → Reviens en mode OUVERTURE (9h30-11h ET).")
    # Vider le CSV
    with open("resultats.csv", "w", newline="", encoding="utf-8") as f:
        f.write("")
else:
    for i, s in enumerate(results[:TOP_N], 1):
        emoji = "🔥" if s["Score"] >= 80 else "✅" if s["Score"] >= 60 else "📊"
        bar   = "█" * int(s["Score"] / 5) + "░" * (20 - int(s["Score"] / 5))
        print(f"\n  {i}. {s['Symbol']} {emoji}  Score {s['Score']}/100")
        print(f"     {bar}")
        print(f"     Var:{s['Variation %']:+.1f}% | RVOL:{s['RVOL']:.1f}x | Float:{s['Float M']:.1f}M | Gap:{s['Gap %']:+.1f}%")
        if s["News"]:
            print(f"     📰 {s['News'].split(' | ')[0][:65]}")

    print(f"\n  ✅ {len(results)} qualifiés / ✗ {len(excluded)} exclus")

    # Résumé Telegram
    summary = f"{MODE_EMOJI} <b>SCAN {MODE} TERMINÉ</b>\n{'═'*28}\n✅ <b>{len(results)} qualifiés</b>\n⏰ {now_et.strftime('%H:%M')} ET\n\n"
    for s in results[:5]:
        emoji = "🔥" if s["Score"] >= 80 else "✅"
        summary += f"{emoji} <b>{s['Symbol']}</b> {s['Score']}/100 | +{s['Variation %']:.1f}% | RVOL {s['RVOL']:.1f}x\n"
    send_telegram(summary)

    # Export CSV
    ts = now_et.strftime("%Y%m%d_%H%M")
    for fname in [f"warrior_{ts}.csv", "resultats.csv"]:
        with open(fname, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(results[0].keys()))
            writer.writeheader()
            writer.writerows(results)
    print(f"  💾 Exporté → warrior_{ts}.csv + resultats.csv")

print("=" * 62 + "\n")
