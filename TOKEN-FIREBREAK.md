# Runbook Token Firebreak

## Flux obligatoire

```text
RAW REPOSITORY
  -> MECHANICAL INVENTORY
  -> EXCLUSIONS
  -> LOGICAL SHARDS
  -> ISOLATED AUDITORS
  -> INDEPENDENT VERIFIERS
  -> DEDUPLICATED SYNTHESIS
  -> MAIN CONTEXT
```

Le dépôt brut, les logs complets et les preuves longues ne franchissent pas la barrière. Le contexte principal reçoit le manifeste résumé, les compteurs, les findings vérifiés et un chemin de rapport.

## 1. Reconnaissance sans LLM

Exécuter `scripts/inventory.py` avant toute lecture de source. Le script collecte uniquement chemins, tailles, extensions, indices de fichier généré, noms potentiellement sensibles, manifests de dépendances et plus gros fichiers. Il exclut les répertoires, globs et binaires configurés.

Inspecter `summary`, `excluded_sample`, `oversize_files` et `sensitive_name_hints`. Un indice sensible n’accorde jamais l’autorisation de lire un secret.

## 2. Sharding logique

`scripts/shard.py` applique d’abord les catégories de `logical_shards`, puis utilise le premier répertoire comme repli. Chaque shard respecte simultanément `max_files_per_shard` et `max_bytes_per_shard`. Un fichier dépassant seul la borne reste visible avec `oversize: true` et doit être lu par plages ciblées.

## 3. Audit isolé

Chaque `audit-worker` reçoit un objectif, un seul fichier de shard et le schéma. Il utilise recherche symbolique/Grep avant Read, ne modifie jamais les sources, écrit ses candidats dans `.firebreak/raw-findings/` et externalise les preuves longues.

Le workflow `.claude/workflows/token-firebreak-audit.js` conserve les retours intermédiaires dans ses variables. Il borne par défaut le fan-out à 10 shards et 20 findings par shard. Augmenter `maxShards` seulement après un essai sur une tranche réduite.

## 4. Vérification indépendante

Un verifier distinct revalide chaque candidat sur les seules plages citées. Il contrôle atteignabilité, préconditions, impact, mitigations et doublons. Les décisions sont :

- `confirmed` : preuve suffisante et impact établi ;
- `rejected` : assertion fausse, dupliquée ou non soutenue ;
- `uncertain` : preuve incomplète, à escalader explicitement.

Seuls `confirmed` et `uncertain` atteignent le synthétiseur.

## 5. Token Governor

La statusline lit les compteurs live de Claude Code et écrit `.firebreak/runtime.json`. Le hook de pré-lecture applique les seuils :

| État | Seuil par défaut | Action |
|---|---:|---|
| NORMAL | <20 % | limites ordinaires |
| WATCH | 20–29 % | surveiller et privilégier les artefacts |
| BLOCK | 30–49 % | bloquer les recherches globales et borner Grep |
| COMPACT | ≥50 % | bloquer de nouvelles lectures du dépôt ; checkpoint puis `/compact` ou nouvelle session |

Les fichiers directs de plus de 200 000 octets sont refusés sans limite de lignes. Les sorties de commandes dépassant 12 000 caractères sont sauvegardées sous `.firebreak/tool-output/` puis remplacées par un extrait. Les tests et logs privilégient les lignes FAIL/ERROR/WARN.

## 6. Raisonnement gradué

- inventaire et classification : `low` / Haiku ;
- audit : `medium` / Sonnet ;
- vérification : `medium` / Sonnet ;
- synthèse : `medium`, puis `high` uniquement si un finding critique survit.

Ne pas utiliser un effort maximal pour lister, compter, filtrer ou classifier.

## 7. Compaction et reprise

`PreCompact` écrit un checkpoint de reprise sous `.firebreak/state/pre-compact.json`. `PostCompact` journalise le déclencheur, la longueur et l’empreinte du résumé sans dupliquer son contenu. Après compaction, reprendre depuis les artefacts, pas depuis une nouvelle lecture globale.

## 8. Mesure

Générer les métriques :

```powershell
python scripts/metrics.py .firebreak --usage usage.json --duration-seconds 900 --out .firebreak/metrics.json
```

Comparer ensuite deux sessions réellement équivalentes avec `scripts/benchmark.py`. Un gain de tokens accompagné d’une baisse des findings confirmés ou de la couverture n’est pas un succès.
