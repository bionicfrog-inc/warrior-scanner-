# ⚔️ Warrior Scanner

Scanner momentum boursier inspiré de la méthodologie **Ross Cameron / Warrior Trading**.

Déployé sur Railway — accessible depuis n'importe quel appareil (PC, mobile, tablette) sans que l'ordinateur soit allumé.

---

## Critères Warrior Style

| Critère | Seuil |
|---|---|
| Prix | $1.00 – $20.00 |
| Variation minimum | +10% |
| Relative Volume (RVOL) | 5x minimum |
| Float maximum | 20 millions de titres |

---

## Score /100

| Composante | Poids | Description |
|---|---|---|
| Momentum | 35 pts | Variation % du jour |
| Volume | 25 pts | RVOL + dollar volume |
| Tendance | 20 pts | SMA50/200 + prix > open |
| Proximité 52W | 10 pts | Distance au plus haut 52 semaines |
| Gap | 10 pts | Gap overnight positif |

---

## Sources de données

- **Yahoo Finance** — prix, volume, historique (gratuit)
- **FMP** — float, news (clé API requise)
- **Finnhub** — news temps réel (clé API optionnelle)

---

## Déploiement Railway

1. Fork ce repo
2. Connecte-le sur [railway.app](https://railway.app)
3. Ajoute les variables d'environnement :
   - `FMP_KEY` — ta clé Financial Modeling Prep
   - `FINNHUB_KEY` — ta clé Finnhub (optionnel)
4. Railway déploie automatiquement

---

## Utilisation locale

```bash
pip install -r requirements.txt
python scanner_warrior.py   # génère resultats.csv
python app.py               # lance le dashboard sur http://localhost:5000
```

---

## Fenêtre optimale

**9h30 – 11h00 ET** (15h30 – 17h00 heure de Montréal)

C'est pendant cette fenêtre que le momentum small cap est le plus fort et que les filtres Warrior donnent les meilleurs résultats.

---

*Disclaimer : Cet outil est à des fins éducatives uniquement. Les résultats passés ne garantissent pas les performances futures.*
