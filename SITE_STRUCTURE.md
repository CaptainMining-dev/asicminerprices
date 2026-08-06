# Structure du site — asicminerprices.com

Générateur statique : `python3 build.py` → site complet dans `dist/` (30 URLs, 34 fichiers, zéro dépendance, hébergeable partout : Cloudflare Pages, Netlify, VPS…).

## Arborescence des pages (30 URLs)

```
/                                    Accueil — classement live des 14 mineurs, slider électricité, top 8 chart, top 3 cards
├── /sha-256/                        Hub Bitcoin (7 mineurs)
├── /kheavyhash/                     Hub Kaspa (4 mineurs)
├── /scrypt/                         Hub Litecoin+Dogecoin (3 mineurs)
├── /miners/<slug>/                  14 fiches mineurs (specs, profit vs tarif élec, ROI, FAQ, CTA affiliation)
├── /calculator/                     Calculateur (mineur + tarif + pool fee → net jour/mois/an, break-even, payback)
├── /compare/                        Index comparatifs
│   └── /<a>-vs-<b>/                 6 comparatifs head-to-head (S21 XP vs S21 Pro, L9 vs L7, etc.)
├── /guides/                         Index guides
│   └── /guides/<slug>/              3 guides SEO (choisir un ASIC, coût électricité, merged mining)
├── /sitemap.xml                     30 URLs pour Google
└── /robots.txt                      pointe vers le sitemap
```

## SEO intégré

- **Title/meta description uniques** par page, orientés requêtes ("Antminer S21 XP profitability, price & specs")
- **Schema.org JSON-LD** : Product + FAQPage + BreadcrumbList sur chaque fiche mineur, FAQPage sur l'accueil → rich snippets Google
- **Maillage interne** : accueil → hubs algo → fiches mineurs → comparatifs → calculateur (chaque fiche lie 3 mineurs du même algo)
- **URLs propres** en dossiers (`/miners/antminer-s21-xp/`) — extensibles à 500+ fiches sans changer la structure
- Canonical, OpenGraph, sitemap.xml, robots.txt

## Monétisation — emplacements prévus

- Slots AdSense balisés `<!-- pub -->` (classe `.ad-slot`) : leaderboard accueil, rectangle fiches mineurs, in-article guides, responsive calculateur
- **CTA affiliation** sur chaque fiche mineur : "Check price →" (vendeur) + "Get hosting quote" (hosting) avec `rel="sponsored nofollow"`

## Interactivité (vanilla JS, `assets/app.js`)

- Slider électricité $0.02–0.20/kWh → recalcule tous les profits de la page en direct, **persisté en localStorage** entre les pages
- Tableaux triables par colonne + auto-retri par profit quand le tarif change
- Filtres par algo (BTC / KAS / LTC+DOGE) sur l'accueil
- Calculateur autonome avec break-even électricité et payback

## Données live (déjà branché, 100% gratuit, sans clé API)

- `fetch_data.py` → `data.json` → `build.py` l'utilise automatiquement (fallback sur constantes si absent)
- Sources : **mempool.space** (hashrate + prix BTC), **2miners** (réseau Kaspa : hashrate, reward live), **Blockchair** (difficulté LTC + DOGE), **CoinGecko** (prix KAS/LTC/DOGE)
- Scrypt = revenu **LTC + DOGE merged mining** combiné
- `refresh.sh` = fetch + rebuild en une commande (cron-ready)
- Antpool/F2Pool/Minerstat : testés mais **clé API requise** (compte gratuit possible, pas nécessaire aujourd'hui)

## Pour passer en production (prochaines étapes)

1. **Prix réels des machines** : brancher les fiches sur les vendeurs (liens affiliation)
2. **Scale** : ajouter un mineur = 1 ligne dans `MINERS` → fiche + sitemap régénérés
3. **Contenu SEO** : étoffer les guides (longue traîne : "antminer s21 xp profitability", "kaspa mining still profitable 2026"…)
4. **Déploiement** : `dist/` sur Cloudflare Pages + cron `refresh.sh` toutes les 6h + redirection 301 d'asiccharts.com

## Fichiers

- `build.py` — générateur (dataset + templates + pages)
- `assets/style.css` — thème dashboard dark
- `assets/app.js` — interactions
- `dist/` — site généré (à déployer)
- `shot-*.png` — captures d'écran de vérification
