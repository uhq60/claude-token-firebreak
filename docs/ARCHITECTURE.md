# Architecture

## Composants

```text
Main Claude (objectif + décisions)
        |
        v
Dynamic workflow (plan en JavaScript, variables hors contexte)
   | scanner -> manifest + shard index
   | workers -> candidate JSONL + evidence paths
   | verifiers -> confirmed / rejected / uncertain
   ` synthesizer -> report + bounded summary
        |
        v
.firebreak/ (état durable et preuves)
```

Le runtime des workflows n’accède pas directement au système de fichiers : les agents exécutent les scripts et écrivent les artefacts. Les résultats intermédiaires restent dans les variables du workflow et seuls le résultat final et les chemins utiles rejoignent la conversation principale.

## Barrières de contexte

- `audit-scanner` : inventaire mécanique, effort faible, aucune conclusion ;
- `audit-worker` : un shard, un objectif, sortie JSON bornée ;
- `audit-verifier` : contexte séparé, contrôle adversarial ;
- `audit-synthesizer` : lit uniquement les survivants et la couverture.

Les subagents n’utilisent pas de mémoire persistante : cela évite de recharger des notes historiques et de contaminer des audits indépendants. Le package ne grossit pas `CLAUDE.md`; sa procédure spécialisée réside dans un skill à invocation manuelle.

## Garde-fous

`PreToolUse` bloque ou borne les lectures et recherches. `PostToolUse` remplace les grosses sorties avant leur transmission au modèle et conserve l’original sur disque. `PreCompact` et `PostCompact` maintiennent une trace de reprise. La statusline fournit le pourcentage de contexte au Token Governor.

## Cache

Le skill, les agents et leurs schémas restent stables pendant un run. Les workers d’un même fan-out utilisent des modèles, efforts, outils, schémas et répertoires cohérents afin de favoriser le partage du préfixe mis en cache. Éviter de modifier `CLAUDE.md`, les outils ou le modèle en cours de phase.

## Limites

- Les seuils locaux ne sont pas des limites Anthropic.
- Un workflow multi-agent peut consommer plus de tokens qu’un audit étroit mono-agent.
- Les hooks ne remplacent ni les permissions Claude Code ni une sandbox.
- Le benchmark doit être exécuté sur le même commit, objectif, modèle, effort et budget temps.
