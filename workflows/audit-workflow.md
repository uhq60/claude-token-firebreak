# Orchestration hors contexte

Le workflow installable est `.claude/workflows/token-firebreak-audit.js`. Il utilise `agent()` et `pipeline()` pour exécuter quatre phases : inventaire, fan-out d’auditeurs, fan-out de vérificateurs, synthèse.

Les résultats intermédiaires restent dans les variables JavaScript du runtime et dans `.firebreak/`. Le workflow retourne uniquement le chemin du manifeste, le nombre de shards traités et le résumé final borné.

Arguments pris en charge :

```json
{
  "objective": "auditer les contrôles d'authentification",
  "maxShards": 10
}
```

Commencer sur une tranche réduite. Le cap local est 20 shards, indépendamment de la limite supérieure du runtime Claude Code.
