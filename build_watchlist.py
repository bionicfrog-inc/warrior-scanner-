import requests

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
