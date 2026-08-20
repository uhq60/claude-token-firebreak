# Claude Token Firebreak

Un package Claude Code pour auditer de très grands dépôts sans transformer la conversation principale en entrepôt de code, logs et résultats intermédiaires. Il applique une barrière de contexte (« firebreak ») : l'inventaire est mécanique, le périmètre est découpé, les analyses sont isolées, les constats sont vérifiés, puis seule une synthèse bornée remonte à l'orchestrateur.

> Objectif : rendre les audits volumineux plus prévisibles et vérifiables. Les seuils du package sont des politiques locales, pas des limites ou garanties Anthropic.

## Ce que le package met en place

- inventaire local avant tout appel LLM, avec exclusions configurables ;
- sharding logique et limitation du nombre de shards traités ;
- rôles séparés : `audit-scanner`, `audit-worker`, `audit-verifier` et `audit-synthesizer` ;
- findings JSON validables, preuves localisées et sorties strictement bornées ;
- artefacts intermédiaires stockés sous `.firebreak/`, hors de la conversation principale ;
- hooks de filtrage des logs/tests, garde de grosses lectures et pré/post-compaction ;
- Token Governor, télémétrie et benchmark A/B pour calibrer les seuils ;
- mode non destructif : le dépôt audité n'est jamais modifié.

## Architecture de l'audit

```text
REPOSITORY
  -> inventory (mécanique)
  -> exclusions + shards
  -> workers isolés
  -> findings JSON + evidence sous .firebreak/
  -> vérification indépendante
  -> déduplication + synthèse bornée
```

Cette architecture suit les capacités documentées de Claude Code : les subagents disposent d'un contexte isolé, les workflows JavaScript conservent les résultats intermédiaires dans le script plutôt que dans la conversation, et les hooks peuvent contrôler les outils ou filtrer leurs sorties.

## Prérequis

- Windows PowerShell ;
- Python 3.9+ sans dépendance externe ;
- Claude Code 2.1.154+ pour les dynamic workflows ;
- accès Claude Code compatible avec les workflows.

## Démarrage

Après installation à la racine du dépôt audité :

```powershell
python scripts/validate_package.py .
python scripts/inventory.py . --config config/firebreak.json --out .firebreak/manifest.json
python scripts/shard.py .firebreak/manifest.json --config config/firebreak.json --out .firebreak/shards
```

Dans Claude Code, lancer :

```text
/token-firebreak auditer le dépôt pour les défauts de sécurité et de fiabilité
```

Le skill peut ensuite lancer le workflow réutilisable `/token-firebreak-audit`. Le workflow accepte un objet contenant `objective` et `maxShards`; la valeur par défaut est 10 shards afin de borner le coût.

## Utilisation responsable

- Lancez d'abord le benchmark A/B sur un dépôt représentatif : aucune économie de tokens n'est présumée sans mesure.
- Révisez les exclusions et les plafonds dans `config/firebreak.json` avant un audit de production.
- N'incluez jamais de secrets dans les prompts, findings ou artefacts exportés.
- Exécutez Claude Code dans un environnement où le dépôt cible et `.firebreak/` peuvent être écrits ; les données intermédiaires restent locales au dépôt cible.

## Livrables d’un audit

```text
.firebreak/
├── manifest.json
├── shards/
├── raw-findings/
├── verified-findings/
├── rejected/
├── evidence/
├── tool-output/
├── reports/audit-report.md
├── runtime.json
└── metrics.json
```

Les seuils de [config/firebreak.json](config/firebreak.json) sont une politique locale, pas des limites Anthropic. Ils doivent être calibrés par un benchmark A/B.

## Fondations officielles Anthropic

Le package s'appuie exclusivement sur la documentation Anthropic ci-dessous :

- [Gestion des coûts Claude Code](https://code.claude.com/docs/en/costs) : coût du contexte, `/usage`, compaction, filtres de sorties et subagents ;
- [Fenêtre de contexte](https://code.claude.com/docs/en/context-window) : effet des lectures sur le contexte et isolation des subagents ;
- [Dynamic workflows](https://code.claude.com/docs/en/workflows) : orchestration JavaScript, fan-out et conservation d'états hors conversation ;
- [Subagents](https://code.claude.com/docs/en/sub-agents) : délégation et contextes séparés ;
- [Hooks](https://code.claude.com/docs/en/hooks) et [guide des hooks](https://code.claude.com/docs/en/hooks-guide) : interception des outils, filtrage et cycle de compaction ;
- [Prompt caching](https://code.claude.com/docs/en/prompt-caching) : cache reads/writes et structure de préfixe ;
- [Mémoire CLAUDE.md](https://code.claude.com/docs/en/memory), [status line](https://code.claude.com/docs/en/statusline) et [monitoring d'usage](https://code.claude.com/docs/en/monitoring-usage).

La liste annotée, avec le lien entre chaque source et son implémentation, est dans [docs/OFFICIAL-SOURCES.md](docs/OFFICIAL-SOURCES.md).

## Documentation

- [Runbook complet](TOKEN-FIREBREAK.md)
- [Guide de fonctionnement détaillé](GUIDE-FONCTIONNEMENT.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Installation](docs/INSTALLATION.md)
- [Benchmark A/B](docs/BENCHMARK.md)
- [Sources Anthropic officielles](docs/OFFICIAL-SOURCES.md)

Le package n’autorise aucune modification du code audité. Les agents écrivent uniquement sous `.firebreak/`.
