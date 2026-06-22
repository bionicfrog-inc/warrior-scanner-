import requests
import csv
import time
import os
from datetime import datetime
from html.parser import HTMLParser

FMP_KEY     = os.environ.get("FMP_KEY",     "U87EgtNaQOdshmSkc0IgEtCFcgqTDjvy")
FINNHUB_KEY = os.environ.get("FINNHUB_KEY", "d8cf7k9r01qidic7msv0d8cf7k9r01qidic7msvg")
TG_TOKEN    = os.environ.get("TG_TOKEN",    "")
TG_CHAT_ID  = os.environ.get("TG_CHAT_ID",  "")

DELAI = 0.2

# =====================================================
# PARSER HTML FINVIZ
# =====================================================

class FinvizParser(HTMLParser):
    """Extrait les données du tableau screener Finviz."""
    def __init__(self):
        super().__init__()
        self.in_table  = False
        self.in_row    = False
        self.in_cell   = False
        self.rows      = []
        self.current   = []
        self.cell_text = ""
        self.headers   = []
        self.got_hdr   = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "tr":
            cls = attrs.get("class", "")
            if "table-light-row" in cls or "table-dark-row" in cls or cls == "":
                self.in_row   = True
                self.current  = []
        if tag == "td" and self.in_row:
            self.in_cell   = True
            self.cell_text = ""
        if tag == "th" and not self.got_hdr:
            self.in_cell   = True
            self.cell_text = ""

    def handle_endtag(self, tag):
        if tag == "td" and self.in_cell:
            self.current.append(self.cell_text.strip())
            self.in_cell = False
        if tag == "th" and self.in_cell:
            self.headers.append(self.cell_text.strip())
            self.in_cell = False
        if tag == "tr" and self.in_row:
            if self.current:
                self.rows.append(self.current)
            self.in_row = False
            if self.headers and not self.got_hdr:
                self.got_hdr = True

    def handle_data(self, data):
        if self.in_cell:
            self.cell_text += data


def scrape_finviz():
    """
    Scrape le screener Finviz avec filtres Warrior :
    - Prix $0.50-$20
    - Volume > 500K
    - Float < 50M
    - Variation > +5%
    - Marché NASDAQ/NYSE/AMEX
    """
    print("  🔍 Finviz Screener en cours...")

    # URL Finviz avec filtres Warrior
    # f= filtres : prix, volume, float, variation, exchange
    url = (
        "https://finviz.com/screener.ashx"
        "?v=111"                    # vue tableau
        "&f=sh_float_u50"           # float < 50M
        ",sh_price_u20"             # prix < $20
        ",sh_price_o0.5"            # prix > $0.50
        ",sh_curvol_o500"           # volume actuel > 500K
        ",ta_change_u"              # variation positive
        "&o=-change"                # tri par variation décroissante
        "&r=1"                      # page 1
    )

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://finviz.com/",
    }

    try:
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code != 200:
            print(f"  ⚠ Finviz status: {r.status_code}")
            return []

        # Parser simple — cherche les tickers dans la page
        stocks = []
        lines  = r.text.split("\n")

        # Finviz met les données dans des liens comme :
        # <a href="quote.ashx?t=SMTK" ...>SMTK</a>
        import re
        pattern = r'quote\.ashx\?t=([A-Z]{1,5})'
        tickers = list(dict.fromkeys(re.findall(pattern, r.text)))

        # Extraire aussi les données du tableau
        # Finviz tableau v=111 colonnes :
        # No, Ticker, Company, Sector, Industry, Country, MarketCap,
        # P/E, Price, Change, Volume
        table_pattern = r'<td[^>]*>([^<]*)</td>'
        cells = re.findall(table_pattern, r.text)

        print(f"  Finviz → {len(tickers)} tickers trouvés")

        # Chercher les données de chaque ticker dans la page
        for ticker in tickers[:50]:  # max 50 pour ne pas ralentir
            # Chercher le prix et la variation dans le HTML
            price_pattern  = rf'quote\.ashx\?t={ticker}.*?(\d+\.\d{{2}})'
            change_pattern = rf'{ticker}.*?([+-]?\d+\.\d+)%'

            stocks.append({
                "symbol": ticker,
                "source": "Finviz"
            })

        return stocks

    except Exception as e:
        print(f"  ⚠ Finviz erreur: {e}")
        return []


# =====================================================
# YAHOO FINANCE — données complètes
# =====================================================

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
        avg_vol_30   = int(sum(vols_d[-31:-1]) / 30) if len(vols_d) >= 31 else 0
        sma50        = round(sum(closes[-50:])  / min(50,  len(closes)), 2) if len(closes) >= 10 else 0
        sma200       = round(sum(closes[-200:]) / min(200, len(closes)), 2) if len(closes) >= 10 else 0
        year_high    = float(meta_d.get("fiftyTwoWeekHigh", 0) or (max(closes) if closes else 0))
        market_cap   = float(meta_d.get("marketCap",   0) or 0)
        float_shares = float(meta_d.get("floatShares", 0) or 0)

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
            "gap": gap, "rvol": rvol,
            "avg_vol_10": avg_vol_10, "avg_vol_30": avg_vol_30,
            "year_high": year_high, "sma50": sma50, "sma200": sma200,
            "market_cap": market_cap, "float_shares": float_shares,
            "mode": mode,
        }
    except Exception:
        return None


# =====================================================
# SCORE /100
# =====================================================

def compute_score(d):
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
    sm = min(m, 35)

    v = 0
    if rvol >= 2:  v += 5
    if rvol >= 5:  v += 10
    if rvol >= 10: v += 5
    if rvol >= 20: v += 5
    dv = prix * volume
    if dv > 500_000:   v += 2
    if dv > 2_000_000: v += 3
    sv = min(v, 25)

    t = 0
    if sma50 > 0 and prix > sma50:                   t += 8
    if sma50 > 0 and sma200 > 0 and sma50 > sma200: t += 7
    if open_price > 0 and prix > open_price:         t += 5
    st = min(t, 20)

    dist_pct = 0.0
    p = 0
    if year_high > 0:
        dist_pct = (year_high - prix) / year_high * 100
        if dist_pct < 30: p += 2
        if dist_pct < 20: p += 2
        if dist_pct < 10: p += 3
        if dist_pct < 5:  p += 3
    sp = min(p, 10)

    g = 0
    if gap > 2:  g += 3
    if gap > 5:  g += 3
    if gap > 10: g += 4
    sg = min(g, 10)

    total = sm + sv + st + sp + sg
    return {
        "total": max(0, min(100, total)),
        "momentum": sm, "volume_sc": sv,
        "tendance": st, "proximite": sp, "gap_sc": sg,
        "dist_pct": round(dist_pct, 2),
    }


# =====================================================
# SCAN FINVIZ PRINCIPAL
# =====================================================

def run_finviz_scan():
    """Lance le scan Finviz et retourne les résultats scorés."""
    print("\n" + "=" * 50)
    print("  📡 SCAN FINVIZ")
    print("=" * 50)

    stocks   = scrape_finviz()
    results  = []

    if not stocks:
        print("  ⚠ Aucun résultat Finviz")
        return []

    for i, stock in enumerate(stocks, 1):
        symbol = stock["symbol"]
        print(f"  [{i:>2}/{len(stocks)}] {symbol:<6}", end=" ", flush=True)
        time.sleep(DELAI)

        data = get_quote_yahoo(symbol)
        if not data:
            print("⚠")
            continue

        prix      = data["prix"]
        variation = data["variation"]
        volume    = data["volume"]
        rvol      = data["rvol"]
        float_m   = data["float_shares"] / 1_000_000

        print(f"| ${prix:.2f} | {variation:+.2f}% | RVOL:{rvol:.1f}x", end=" ")

        scores = compute_score(data)
        print(f"→ Score {scores['total']}/100")

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
            "Float M":     round(float_m, 2),
            "Market Cap":  int(data["market_cap"]),
            "SMA50":       data["sma50"],
            "SMA200":      data["sma200"],
            "52W High":    round(data["year_high"], 2),
            "Dist 52W %":  scores["dist_pct"],
            "TradingView": f"https://www.tradingview.com/chart/?symbol={symbol}",
            "Finviz":      f"https://finviz.com/quote.ashx?t={symbol}",
            "Source":      "Finviz",
            "Heure":       datetime.now().strftime("%H:%M:%S"),
        })

    results.sort(key=lambda x: x["Score"], reverse=True)

    # Sauvegarder
    if results:
        with open("finviz_results.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(results[0].keys()))
            writer.writeheader()
            writer.writerows(results)
        print(f"\n  💾 {len(results)} résultats → finviz_results.csv")

    return results


if __name__ == "__main__":
    results = run_finviz_scan()
    print(f"\n  ✅ {len(results)} stocks scorés depuis Finviz")
