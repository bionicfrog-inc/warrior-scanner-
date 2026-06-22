import requests
import csv
import time
import os
import re
from datetime import datetime

FMP_KEY     = os.environ.get("FMP_KEY",     "U87EgtNaQOdshmSkc0IgEtCFcgqTDjvy")
FINNHUB_KEY = os.environ.get("FINNHUB_KEY", "d8cf7k9r01qidic7msv0d8cf7k9r01qidic7msvg")
DELAI       = 0.2

def get_finviz_tickers():
    """Récupère les tickers depuis Finviz screener."""
    print("  🔍 Finviz Screener en cours...")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Referer": "https://finviz.com/",
    }

    # Filtres Warrior sur Finviz
    # sh_float_u50 = float < 50M
    # sh_price_u20 = prix < $20
    # sh_price_o0.5 = prix > $0.50
    # sh_curvol_o500 = volume > 500K
    # ta_change_u = variation positive
    url = "https://finviz.com/screener.ashx?v=111&f=sh_float_u50,sh_price_u20,sh_price_o0.5,sh_curvol_o500,ta_change_u&o=-change&r=1"

    try:
        r = requests.get(url, headers=headers, timeout=15)
        print(f"  Finviz status: {r.status_code}")

        if r.status_code == 200:
            # Extraire les tickers avec regex
            tickers = re.findall(r'quote\.ashx\?t=([A-Z]{1,5})(?:&|")', r.text)
            tickers = list(dict.fromkeys(tickers))  # dédupliquer
            print(f"  Finviz → {len(tickers)} tickers")
            return tickers[:40]
        else:
            print(f"  ⚠ Finviz bloqué ({r.status_code}) — fallback FMP gainers")
            return get_fmp_gainers_fallback()

    except Exception as e:
        print(f"  ⚠ Finviz erreur: {e} — fallback FMP")
        return get_fmp_gainers_fallback()


def get_fmp_gainers_fallback():
    """Fallback : gainers FMP si Finviz bloqué."""
    candidates = []
    try:
        url  = f"https://financialmodelingprep.com/api/v3/stock_market/gainers?apikey={FMP_KEY}"
        data = requests.get(url, timeout=8).json()
        if isinstance(data, list):
            for s in data:
                symbol = s.get("symbol", "")
                price  = float(s.get("price", 0) or 0)
                if symbol and 0.5 <= price <= 20 and len(symbol) <= 5:
                    candidates.append(symbol)
        print(f"  FMP Gainers fallback → {len(candidates)} candidats")
    except Exception as e:
        print(f"  ⚠ FMP Gainers: {e}")
    return candidates[:40]


def get_quote_yahoo(symbol):
    try:
        headers   = {"User-Agent": "Mozilla/5.0"}
        url_d     = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=60d"
        r_d       = requests.get(url_d, headers=headers, timeout=5).json()
        res_d     = r_d.get("chart", {}).get("result", [])
        if not res_d:
            return None

        meta_d       = res_d[0].get("meta", {})
        q_d          = res_d[0].get("indicators", {}).get("quote", [{}])[0]
        closes       = [c for c in q_d.get("close",  []) if c is not None]
        vols_d       = [v for v in q_d.get("volume", []) if v is not None]
        avg_vol_10   = int(sum(vols_d[-11:-1]) / 10) if len(vols_d) >= 11 else 0
        sma50        = round(sum(closes[-50:])  / min(50,  len(closes)), 2) if len(closes) >= 10 else 0
        sma200       = round(sum(closes[-200:]) / min(200, len(closes)), 2) if len(closes) >= 10 else 0
        year_high    = float(meta_d.get("fiftyTwoWeekHigh", 0) or (max(closes) if closes else 0))
        market_cap   = float(meta_d.get("marketCap",   0) or 0)
        float_shares = float(meta_d.get("floatShares", 0) or 0)

        # Fallback FMP pour le float
        if float_shares == 0:
            try:
                fmp_url = f"https://financialmodelingprep.com/api/v3/shares_float?symbol={symbol}&apikey={FMP_KEY}"
                fmp_r   = requests.get(fmp_url, timeout=3).json()
                if isinstance(fmp_r, list) and fmp_r:
                    float_shares = float(fmp_r[0].get("floatShares", 0) or 0)
            except Exception:
                pass

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
        q_rt       = res_rt[0].get("indicators", {}).get("quote", [{}])[0]
        opens      = [o for o in q_rt.get("open", []) if o is not None]
        open_px    = float(opens[0]) if opens else 0.0
        gap        = round((open_px - prev_close) / prev_close * 100, 2) if (open_px > 0 and prev_close > 0) else 0.0
        rvol       = round(volume / avg_vol_10, 2) if avg_vol_10 > 0 else 0.0

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
            "gap": gap, "rvol": rvol, "avg_vol_10": avg_vol_10,
            "year_high": year_high, "sma50": sma50, "sma200": sma200,
            "market_cap": market_cap, "float_shares": float_shares, "mode": mode,
        }
    except Exception:
        return None


def compute_score(d):
    m = 0
    v2 = d["variation"]
    if v2 > 0:   m += 5
    if v2 > 5:   m += 5
    if v2 > 10:  m += 10
    if v2 > 20:  m += 10
    if v2 > 30:  m += 5
    sm = min(m, 35)

    v = 0
    rv = d["rvol"]
    if rv >= 2:  v += 5
    if rv >= 5:  v += 10
    if rv >= 10: v += 5
    if rv >= 20: v += 5
    dv = d["prix"] * d["volume"]
    if dv > 500_000:   v += 2
    if dv > 2_000_000: v += 3
    sv = min(v, 25)

    t = 0
    if d["sma50"] > 0 and d["prix"] > d["sma50"]:                             t += 8
    if d["sma50"] > 0 and d["sma200"] > 0 and d["sma50"] > d["sma200"]:      t += 7
    if d["open_price"] > 0 and d["prix"] > d["open_price"]:                   t += 5
    st = min(t, 20)

    dist_pct = 0.0
    p = 0
    if d["year_high"] > 0:
        dist_pct = (d["year_high"] - d["prix"]) / d["year_high"] * 100
        if dist_pct < 30: p += 2
        if dist_pct < 20: p += 2
        if dist_pct < 10: p += 3
        if dist_pct < 5:  p += 3
    sp = min(p, 10)

    g = 0
    if d["gap"] > 2:  g += 3
    if d["gap"] > 5:  g += 3
    if d["gap"] > 10: g += 4
    sg = min(g, 10)

    total = sm + sv + st + sp + sg
    return {"total": max(0, min(100, total)), "momentum": sm, "volume_sc": sv, "tendance": st, "proximite": sp, "gap_sc": sg, "dist_pct": round(dist_pct, 2)}


def run_finviz_scan():
    print("\n" + "=" * 50)
    print("  📡 SCAN FINVIZ")
    print("=" * 50)

    # Vérifier si des tickers manuels ont été passés
    manual = os.environ.get("MANUAL_TICKERS", "").strip()
    if manual:
        tickers = list(dict.fromkeys(manual.upper().split()))
        print(f"  ✏️ Tickers manuels : {len(tickers)} reçus")
    else:
        tickers = get_finviz_tickers()

    results = []

    for i, symbol in enumerate(tickers, 1):
        print(f"  [{i:>2}/{len(tickers)}] {symbol:<6}", end=" ", flush=True)
        time.sleep(DELAI)

        data = get_quote_yahoo(symbol)
        if not data:
            print("⚠")
            continue

        prix      = data["prix"]
        variation = data["variation"]
        rvol      = data["rvol"]
        float_m   = data["float_shares"] / 1_000_000

        scores = compute_score(data)
        print(f"| ${prix:.2f} | {variation:+.1f}% | RVOL:{rvol:.1f}x | Float:{float_m:.1f}M | Score:{scores['total']}")

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
            "Volume":      data["volume"],
            "RVOL":        rvol,
            "Avg Vol 10j": data["avg_vol_10"],
            "Float M":     round(float_m, 2),
            "Market Cap":  int(data["market_cap"]),
            "SMA50":       data["sma50"],
            "SMA200":      data["sma200"],
            "52W High":    round(data["year_high"], 2),
            "Dist 52W %":  scores["dist_pct"],
            "TradingView": f"https://www.tradingview.com/chart/?symbol={symbol}",
            "Finviz":      f"https://finviz.com/quote.ashx?t={symbol}",
            "Source":      "Finviz",
            "Mode":        data.get("mode", ""),
            "Heure":       datetime.now().strftime("%H:%M:%S"),
        })

    results.sort(key=lambda x: x["Score"], reverse=True)

    if results:
        with open("finviz_results.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(results[0].keys()))
            writer.writeheader()
            writer.writerows(results)
        print(f"\n  💾 {len(results)} résultats → finviz_results.csv")
    else:
        with open("finviz_results.csv", "w", newline="", encoding="utf-8") as f:
            f.write("")
        print("  ⚠ Aucun résultat Finviz")

    return results


if __name__ == "__main__":
    results = run_finviz_scan()
    print(f"\n  ✅ {len(results)} stocks scorés depuis Finviz")
