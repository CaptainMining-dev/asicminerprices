# asicminerprices.com

Comparateur de rentabilité ASIC miners — site statique auto-généré avec données réseau live.

## Comment ça marche

- `fetch_data.py` — récupère les données live gratuites (mempool.space, 2miners, Blockchair, CoinGecko) → `data.json`
- `build.py` — génère le site complet dans `dist/` (30+ pages : accueil, fiches mineurs, hubs algo, calculateur, comparatifs, guides)
- `.github/workflows/deploy.yml` — GitHub Actions : fetch + build + déploiement Cloudflare Pages **toutes les 6h**, à chaque push, ou manuellement

## Modifier

- **Ajouter un mineur** : 1 ligne dans `MINERS` (build.py) → fiche + sitemap régénérés
- **Ajouter un comparatif** : 1 tuple dans `COMPARE_PAIRS`
- **Ajouter un guide** : 1 entrée dans `GUIDES`

## Déployer manuellement (local)

```bash
./refresh.sh        # fetch + build → dist/
```
