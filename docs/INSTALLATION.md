# Installation Windows

## 1. Prérequis

```powershell
claude --version
python --version
```

Dynamic workflows : Claude Code 2.1.154 ou version ultérieure. Python 3.9+ est requis pour les scripts et hooks, sans paquet additionnel.

## 2. Sauvegarde

Si le dépôt cible possède déjà `.claude/settings.json`, en faire une copie hors du dépôt avant installation. Ne pas écraser ses hooks, permissions ou variables : fusionner uniquement `statusLine` et les quatre groupes de hooks du package.

```powershell
Copy-Item -LiteralPath 'C:\mon-projet\.claude\settings.json' -Destination 'C:\sauvegardes-firebreak\settings.json' -ErrorAction SilentlyContinue
```

## 3. Copie

Copier le package téléchargé dans la racine du dépôt audité. Conserver au minimum :

- `.claude\agents`
- `.claude\hooks`
- `.claude\skills\token-firebreak`
- `.claude\workflows\token-firebreak-audit.js`
- `.claude\statusline.py`
- `config`, `schemas`, `scripts`
- `TOKEN-FIREBREAK.md`
- `README.md`, `GUIDE-FONCTIONNEMENT.md`, `docs`
- `.gitignore` (ou fusionner ses exclusions avec le fichier existant)

Copier `.claude/settings.json` seulement si le dépôt n’en possède pas. Sinon fusionner sa configuration avec le fichier existant.

## 4. Validation

Depuis la racine cible :

```powershell
python scripts/validate_package.py .
python scripts/inventory.py . --config config/firebreak.json --out .firebreak/manifest.json
python scripts/shard.py .firebreak/manifest.json --config config/firebreak.json --out .firebreak/shards
```

Puis ouvrir Claude Code, accepter la confiance du projet et lancer `/token-firebreak <objectif>`. Sur un plan Pro, activer Dynamic workflows dans `/config` si nécessaire.

## 5. Données locales

Exclure obligatoirement `.firebreak/`, les sauvegardes de configuration, les caches Python et les exports locaux d’usage/benchmark. Le `.gitignore` fourni couvre ces chemins ; fusionner ses règles si le dépôt cible possède déjà ce fichier. Vérifier la politique interne avant d’activer OpenTelemetry : l’export est optionnel et dirigé vers votre propre backend.

## Désinstallation

Restaurer la sauvegarde externe de `settings.json`, puis retirer uniquement les fichiers copiés ci-dessus. Les résultats d’audit sous `.firebreak/` ne sont pas supprimés automatiquement.
