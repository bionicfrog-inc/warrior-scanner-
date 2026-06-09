# =====================================================
# Génération automatique de watchlist.txt
# =====================================================

symbols = []
total = 0

with open("nasdaqlisted.txt", "r", encoding="utf-8") as f:

    next(f)  # saute l'entête

    for line in f:

        total += 1

        parts = line.strip().split("|")
        
        if total <= 5:
            print(parts)

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

        # Symboles spéciaux
        if symbol.endswith(("W", "U", "R")):
            continue

        symbols.append(symbol)

symbols = sorted(set(symbols))

with open("watchlist.txt", "w") as f:

    for symbol in symbols:
        f.write(symbol + "\n")

print("Total brut :", total)
print("Après nettoyage :", len(symbols))
print("Watchlist créée")
