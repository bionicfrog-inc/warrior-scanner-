# =====================================================
# Génération automatique de watchlist.txt
# =====================================================

symbols = []

with open("nasdaqlisted.txt", "r", encoding="utf-8") as f:

    next(f)  # saute l'entête

    for line in f:

        parts = line.strip().split("|")

        if len(parts) < 8:
            continue

        symbol = parts[0].strip()
        security_name = parts[1].upper()
        etf = parts[6].strip()

        # ETF
        if etf == "Y":
            continue

        # Rights
        if "RIGHT" in security_name:
            continue

        # Units
        if "UNIT" in security_name:
            continue

        # Warrants
        if "WARRANT" in security_name:
            continue

        symbols.append(symbol)

symbols = sorted(set(symbols))

with open("watchlist.txt", "w") as f:

    for symbol in symbols:
        f.write(symbol + "\n")

print(f"Watchlist créée : {len(symbols)} symboles")# =====================================================
# Génération automatique de watchlist.txt
# à partir de nasdaqlisted.txt
# =====================================================

symbols = []

with open("nasdaqlisted.txt", "r", encoding="utf-8") as f:

    next(f)  # saute l'entête

    for line in f:

        parts = line.strip().split("|")

        if len(parts) < 8:
            continue

        symbol = parts[0].strip()
        security_name = parts[1].upper()
        etf = parts[6].strip()

        # Exclure ETF
        if etf == "Y":
            continue

        # Exclure Rights
        if "RIGHT" in security_name:
            continue

        # Exclure Units
        if "UNIT" in security_name:
            continue

        # Exclure Warrants
        if "WARRANT" in security_name:
            continue

        symbols.append(symbol)

symbols = sorted(set(symbols))

with open("watchlist.txt", "w") as f:

    for symbol in symbols:
        f.write(symbol + "\n")

print(f"Watchlist créée : {len(symbols)} symboles")import requests

FMP_KEY = "TA_CLE_FMP"

url = (
    f"https://financialmodelingprep.com/api/v3/stock/list"
    f"?apikey={FMP_KEY}"
)

data = requests.get(url, timeout=30).json()

symbols = []

if isinstance(data, list):

    for stock in data:

        symbol = stock.get("symbol")
        price = stock.get("price")

        if (
            symbol
            and isinstance(price, (int, float))
            and 0.25 <= price <= 20
        ):
            symbols.append(symbol.upper())

with open("watchlist.txt", "w") as f:

    for symbol in sorted(set(symbols)):
        f.write(symbol + "\n")

print("Watchlist créée")
print("Nombre de symboles :", len(symbols))
