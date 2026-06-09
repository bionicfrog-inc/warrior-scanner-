# =====================================================
# TEST LECTURE NASDAQLISTED.TXT
# =====================================================

symbols = []
total = 0

with open("nasdaqlisted.txt", "r", encoding="utf-8") as f:

    next(f)

    for line in f:

        total += 1

        parts = line.strip().split("|")

        if total <= 5:
            print(parts)

        if len(parts) < 1:
            continue

        symbol = parts[0].strip()

        if symbol:
            symbols.append(symbol)

with open("watchlist.txt", "w") as f:

    for symbol in symbols:
        f.write(symbol + "\n")

print("Total brut :", total)
print("Après nettoyage :", len(symbols))
print("Watchlist créée")
