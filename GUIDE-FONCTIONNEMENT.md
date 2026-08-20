# Guide de fonctionnement — Claude Token Firebreak

## Objectif

Claude Token Firebreak est un package Claude Code conçu pour auditer de très gros dépôts sans remplir inutilement la conversation principale.

Son principe est simple : les fichiers bruts, les longs journaux et les preuves détaillées restent sur disque ou dans les contextes isolés des agents. La conversation principale reçoit seulement les informations nécessaires pour décider et présenter le résultat.

```text
Dépôt brut
  → inventaire mécanique
  → exclusions
  → découpage en shards
  → audit par agents isolés
  → vérification indépendante
  → déduplication et synthèse
  → rapport final concis
```

## 1. Inventaire mécanique

Avant toute analyse par un modèle, le script `scripts/inventory.py` parcourt le dépôt de façon déterministe.

Il relève notamment :

- les chemins et tailles des fichiers ;
- les extensions ;
- les répertoires principaux ;
- les fichiers exceptionnellement volumineux ;
- les manifests de dépendances ;
- les indices de fichiers générés ;
- les noms pouvant contenir des données sensibles ;
- les exclusions appliquées.

Il ne réalise pas d’audit sémantique et ne transmet pas le contenu du dépôt à Claude. Le résultat est enregistré dans :

```text
.firebreak/manifest.json
```

Commande :

```powershell
python scripts/inventory.py . --config config/firebreak.json --out .firebreak/manifest.json
```

## 2. Exclusions configurables

Le fichier `config/firebreak.json` évite d’envoyer au modèle les éléments généralement inutiles :

- `.git`, `node_modules`, `dist`, `build`, `coverage` ;
- caches et environnements virtuels ;
- fichiers minifiés et source maps ;
- archives, images et binaires ;
- fichiers générés ou trop volumineux.

Les listes `exclude_dirs` et `exclude_globs` peuvent être adaptées au dépôt. Un nom marqué comme potentiellement sensible reste une simple alerte : le système n’en lit pas automatiquement le contenu.

## 3. Découpage logique

Le script `scripts/shard.py` transforme le manifeste en unités d’audit bornées appelées shards.

Il tente d’abord de regrouper les fichiers par fonction :

- authentification ;
- API et routes ;
- base de données ;
- frontend ;
- infrastructure ;
- tests ;
- configuration.

Chaque shard respecte une limite de fichiers et une limite d’octets. Les résultats sont enregistrés dans :

```text
.firebreak/shards/
```

Commande :

```powershell
python scripts/shard.py .firebreak/manifest.json --config config/firebreak.json --out .firebreak/shards
```

## 4. Agents spécialisés

Le package fournit quatre agents sous `.claude/agents/`.

### audit-scanner

Il lance l’inventaire et le sharding. Il travaille avec un effort faible et ne produit aucun finding.

### audit-worker

Chaque worker reçoit un seul shard et un objectif précis. Il ne peut auditer que les fichiers listés dans ce shard.

Ses constats sont enregistrés au format JSONL dans :

```text
.firebreak/raw-findings/
```

Les preuves longues sont externalisées dans `.firebreak/evidence/` au lieu d’être recopiées dans la conversation.

### audit-verifier

Le verifier est séparé de l’auditeur. Il relit uniquement les plages de code citées et classe chaque finding :

- `confirmed` : problème suffisamment démontré ;
- `rejected` : assertion fausse, non prouvée ou dupliquée ;
- `uncertain` : preuve insuffisante nécessitant une vérification humaine.

Les résultats sont répartis entre :

```text
.firebreak/verified-findings/
.firebreak/rejected/
```

### audit-synthesizer

Il lit les findings vérifiés et les métriques, déduplique les problèmes, les classe par priorité et écrit :

```text
.firebreak/reports/audit-report.md
```

Il ne reparcourt pas tout le dépôt.

## 5. Workflow hors contexte

Le fichier `.claude/workflows/token-firebreak-audit.js` orchestre automatiquement les phases précédentes.

Le runtime du workflow conserve les résultats intermédiaires dans ses variables JavaScript. Cela évite de faire remonter chaque réponse de worker dans le contexte principal.

Le workflow applique :

1. un inventaire mécanique ;
2. un fan-out d’auditeurs ;
3. un fan-out de vérificateurs indépendants ;
4. une synthèse des findings confirmés ou incertains.

Par défaut, il traite au maximum 10 shards et 20 findings par shard. Ces plafonds empêchent un lancement incontrôlé. Ils sont configurables, mais il est recommandé de tester d’abord un petit périmètre.

## 6. Token Governor

Le Token Governor surveille le remplissage du contexte grâce à `.claude/statusline.py`.

La statusline reçoit les compteurs Claude Code, puis écrit l’état courant dans :

```text
.firebreak/runtime.json
```

Les états par défaut sont :

| État | Contexte utilisé | Comportement |
|---|---:|---|
| `NORMAL` | moins de 20 % | fonctionnement normal |
| `WATCH` | 20 à 29 % | surveillance et externalisation renforcée |
| `BLOCK` | 30 à 49 % | recherches globales bloquées ou bornées |
| `COMPACT` | 50 % et plus | nouvelles lectures du dépôt bloquées jusqu’à compaction ou nouvelle session |

Ces seuils sont locaux au package. Ils ne représentent pas des limites officielles Anthropic.

## 7. Hooks de protection

Les hooks se trouvent dans `.claude/hooks/` et sont activés par `.claude/settings.json`.

### Protection des grosses lectures

`guard_large_reads.py` intervient avant `Read`, `Grep`, `Glob`, `Bash` ou `PowerShell`.

Il peut :

- bloquer la lecture complète d’un fichier trop volumineux ;
- imposer une limite à une recherche Grep ;
- refuser un parcours global lorsque le contexte est trop chargé ;
- bloquer une commande susceptible d’imprimer une sortie illimitée.

### Filtrage des tests et journaux

`filter_test_output.py` intervient après une commande.

Lorsqu’une sortie dépasse la limite :

1. Claude reçoit seulement un extrait borné ;
2. pour les tests et logs, les lignes `FAIL`, `ERROR`, `WARN`, exceptions et traces sont privilégiées ;
3. l’intégralité n’est sauvegardée dans `.firebreak/tool-output/` que si `store_full_tool_output` est explicitement activé après revue de sécurité.

### Hooks de compaction

`pre_compact.py` écrit un checkpoint indiquant les artefacts à reprendre après compaction.

`post_compact.py` journalise l’événement et l’empreinte du résumé sans recopier son contenu complet.

## 8. Findings structurés

Chaque finding doit respecter `schemas/finding.schema.json`.

Exemple simplifié :

```json
{
  "id": "SEC-AUTH-014",
  "status": "confirmed",
  "severity": "HIGH",
  "confidence": 0.93,
  "category": "authentication",
  "file": "src/auth/session.ts",
  "lines": "141-168",
  "finding": "Description concise",
  "evidence": "Preuve bornée",
  "impact": "Conséquence possible",
  "recommended_action": "Correction recommandée"
}
```

Le schéma limite la longueur des descriptions, preuves et recommandations. Cela empêche les agents de retourner de longues dissertations.

## 9. Raisonnement gradué

Le package adapte le coût de raisonnement à la difficulté :

- inventaire et classification : faible ;
- audit standard : moyen ;
- vérification : moyen ;
- synthèse critique ambiguë : élevé.

Les opérations mécaniques ne consomment donc pas un niveau de raisonnement inutilement élevé.

## 10. Métriques et benchmark

Le script `scripts/metrics.py` agrège :

- tokens d’entrée et de sortie ;
- tokens de création et de lecture du cache ;
- pic de contexte ;
- findings confirmés, rejetés et incertains ;
- sévérités ;
- durée.

Le script `scripts/benchmark.py` compare ensuite :

- une session Claude Code classique ;
- une session utilisant Token Firebreak.

Il calcule notamment l’économie de tokens, le cache hit ratio, les tokens par finding confirmé, le taux de faux positifs et le pic de contexte.

Une réduction de tokens accompagnée d’une perte de couverture ou de findings confirmés n’est pas considérée comme une amélioration.

## 11. Utilisation complète

Depuis la racine du dépôt dans lequel le package est installé :

```powershell
python scripts/validate_package.py .
python scripts/inventory.py . --config config/firebreak.json --out .firebreak/manifest.json
python scripts/shard.py .firebreak/manifest.json --config config/firebreak.json --out .firebreak/shards
```

Puis dans Claude Code :

```text
/token-firebreak auditer le dépôt pour les défauts de sécurité, de fiabilité et de logique
```

À la fin :

```powershell
python scripts/metrics.py .firebreak --out .firebreak/metrics.json
```

## Résumé

Token Firebreak ne cherche pas seulement à demander à Claude d’utiliser moins de tokens. Il impose une architecture dans laquelle le gaspillage devient difficile :

- inventaire sans LLM ;
- exclusion avant analyse ;
- périmètres isolés ;
- sorties bornées ;
- preuves hors contexte ;
- vérification indépendante ;
- limites déterministes ;
- télémétrie mesurable.

La conversation principale reste ainsi centrée sur les décisions et le rapport final, même lorsque le dépôt audité est très volumineux.
