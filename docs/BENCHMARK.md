# Benchmark A/B

## But

Mesurer si le Firebreak réduit la pollution du contexte et les tokens par finding confirmé sans dégrader la couverture ou la précision.

## Protocole

1. Geler le même commit et le même objectif d’audit.
2. Utiliser le même modèle principal, le même budget temps et des niveaux d’effort documentés.
3. Session A : audit Claude Code classique, sans package.
4. Session B : audit Token Firebreak, avec les exclusions et caps conservés.
5. Relever pour chaque session : input, output, cache creation/read, pic de contexte, durée, confirmed/rejected/uncertain et couverture.
6. Ne pas réutiliser l’historique de A dans B. Ne pas modifier `CLAUDE.md`, les MCP ou le modèle entre les deux.

## Captures

La statusline écrit automatiquement le dernier usage et le contexte dans `.firebreak/runtime.json`. Pour une mesure cumulative fiable, exporter les métriques Claude Code via OpenTelemetry ou enregistrer les objets `usage` de résultats SDK, puis les fournir à :

```powershell
python scripts/metrics.py .firebreak --usage .firebreak/usage-export.json --duration-seconds 900 --out .firebreak/firebreak-metrics.json
```

Créer de la même façon `baseline-metrics.json`, puis comparer :

```powershell
python scripts/benchmark.py --baseline .firebreak/baseline-metrics.json --firebreak .firebreak/firebreak-metrics.json --out .firebreak/benchmark.json
```

## Indicateurs

- économie brute de tokens ;
- cache hit ratio ;
- tokens par finding confirmé ;
- faux positifs parmi les décisions vérifiées ;
- pic de contexte principal ;
- delta de findings confirmés ;
- durée et couverture de fichiers.

Une économie avec moins de findings confirmés ou une couverture moindre doit être signalée comme non concluante, pas comme une victoire.
