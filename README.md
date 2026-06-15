# Warrior Scanner

Scanner momentum boursier inspire de la methodologie Ross Cameron / Warrior Trading.

Deploye sur Railway et utilisable aussi en local.

## Criteres Warrior Style

| Critere | Seuil |
|---|---|
| Prix | $0.50 - $20.00 |
| Volume minimum | 500 000 actions |
| Variation minimum finale | +10% |
| Relative Volume (RVOL) final | 5x minimum |
| Float ideal | moins de 100 millions de titres |

## Score /100

| Composante | Poids | Description |
|---|---|---|
| Momentum | 35 pts | Variation % du jour ou pre-market |
| Volume | 25 pts | RVOL + dollar volume |
| Tendance | 20 pts | SMA50/200 + prix > open |
| Proximite 52W | 10 pts | Distance au plus haut 52 semaines |
| Gap | 10 pts | Gap overnight ou pre-market positif |

## Sources de donnees

- Yahoo Finance : prix, volume, historique, pre-market et after-hours
- FMP : screener rapide, top gainers et news
- Finnhub : news temps reel optionnelles

## Variables d'environnement

Ne pas mettre les cles API directement dans le code.

- `FMP_KEY` : cle Financial Modeling Prep
- `FINNHUB_KEY` : cle Finnhub optionnelle

## Utilisation locale

```bash
pip install -r requirements.txt
python scanner_warrior.py
python app.py
```

Le scanner genere `resultats.csv`, puis le dashboard lit ce fichier.

## Fenetre optimale

Pre-market et ouverture du marche US, surtout entre 9h30 et 11h00 ET.

## Note

Cet outil est a des fins educatives uniquement. Ce n'est pas un conseil financier.# ⚔️ Warrior Scanner

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
