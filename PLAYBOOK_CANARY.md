# Playbook Canary - Optimisations GPT + Scrapers

## Objectif
Réduire coût OpenAI rapidement en déployant optimisations sur 10% du trafic.

## Étapes
1. Branch: `optimize/gpt-scraper`
2. Déployer sur un environnement staging identique à prod.
3. Activer variables d'env:
   - GPT_MODEL=gpt-4o
   - GPT_MINI=gpt-4o-mini
   - MAX_WORKERS=6
4. Lancer canary: router 10% du trafic vers la nouvelle version.
5. Mesures à collecter (24-72h):
   - tokens/request
   - coût OpenAI / jour
   - latence mediane
   - % cache hits
6. Si gain >= 50%: rollout progressif 25% -> 50% -> 100%.
7. Rollback si erreurs > 5% ou latence > 2x.

## Notes
- Ajuster selectors du scraper Ticketmaster avant production.
- Ajouter monitoring (Prometheus/Grafana) pour métriques clés.
