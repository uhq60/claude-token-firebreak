# Installation Windows

## 1. Prérequis

```powershell
claude --version
python --version
```

Dynamic workflows : Claude Code 2.1.154 ou version ultérieure. Python 3.9+ est requis pour les scripts et hooks, sans paquet additionnel.

## 2. Sauvegarde

Si le dépôt cible possède déjà `.claude/settings.json`, en faire une copie avant installation. Ne pas écraser ses hooks, permissions ou variables : fusionner uniquement `statusLine` et les quatre groupes de hooks du package.

```powershell
Copy-Item -LiteralPath 'C:\mon-projet\.claude\settings.json' -Destination 'C:\mon-projet\.claude\settings.before-firebreak.json' -ErrorAction SilentlyContinue
```

## 3. Copie

Depuis `C:\codex\skill\coding\claude-token-firebreak`, copier dans la racine du dépôt audité :

- `.claude\agents`
- `.claude\hooks`
- `.claude\skills\token-firebreak`
- `.claude\workflows\token-firebreak-audit.js`
- `.claude\statusline.py`
- `config`, `schemas`, `scripts`
- `TOKEN-FIREBREAK.md`

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

Ajouter `.firebreak/` à `.gitignore` lorsque les preuves, sorties ou chemins ne doivent pas être versionnés. Vérifier la politique interne avant d’activer OpenTelemetry : l’export est optionnel et dirigé vers votre propre backend.

## Désinstallation

Restaurer `settings.before-firebreak.json`, puis retirer uniquement les fichiers copiés ci-dessus. Les résultats d’audit sous `.firebreak/` ne sont pas supprimés automatiquement.
