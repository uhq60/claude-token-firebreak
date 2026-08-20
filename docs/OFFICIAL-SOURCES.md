# Sources officielles Anthropic

Sources consultées le 19 août 2026. Aucun lien tiers n’est utilisé dans la documentation technique du package.

- [Manage costs effectively](https://code.claude.com/docs/en/costs) — coût proportionnel au contexte, `/usage`, `/clear`, `/compact`, filtrage de logs par hooks, délégation des sorties verbeuses, effort et coût des agent teams.
- [Explore the context window](https://code.claude.com/docs/en/context-window) — contenu du contexte, coût des lectures, comportement après compaction et isolation des subagents.
- [Orchestrate subagents at scale with dynamic workflows](https://code.claude.com/docs/en/workflows) — audits de codebase, variables de script hors contexte, fan-out, vérification adversariale, limites, coût, cache partagé et version minimale 2.1.154.
- [Create custom subagents](https://code.claude.com/docs/en/sub-agents) — contexte frais, outils, permissions, modèles, effort et limites de tours.
- [Hooks reference](https://code.claude.com/docs/en/hooks) — `PreToolUse`, `PostToolUse.updatedToolOutput`, `PreCompact`, `PostCompact` et formats JSON.
- [Automate workflows with hooks](https://code.claude.com/docs/en/hooks-guide) — choix des hooks déterministes et cycle de vie.
- [How Claude Code uses prompt caching](https://code.claude.com/docs/en/prompt-caching) — cache par préfixe, invalidations, compteurs de cache et comportement des subagents.
- [How Claude remembers your project](https://code.claude.com/docs/en/memory) — chargement de `CLAUDE.md`, objectif inférieur à 200 lignes et limite de chargement de `MEMORY.md`.
- [Extend Claude Code](https://code.claude.com/docs/en/features-overview) — coût de contexte comparé des skills, hooks, subagents et plugins.
- [Customize your status line](https://code.claude.com/docs/en/statusline) — `used_percentage`, tokens de contexte et compteurs cache lus sur stdin.
- [Monitoring](https://code.claude.com/docs/en/monitoring-usage) — métriques OpenTelemetry de tokens, coûts, agents, skills et cache.
- [Get structured output from agents](https://code.claude.com/docs/en/agent-sdk/structured-outputs) — validation de sorties par JSON Schema.
- [Claude Platform pricing](https://platform.claude.com/docs/en/about-claude/pricing) — tarification officielle du prompt caching ; le taux exact dépend du modèle et de la durée du cache.

## Distinction importante

Anthropic documente les mécanismes et certaines limites du runtime. Les seuils `20/30/50 %`, `200 000` octets, `12 000` caractères, `10` shards et `20` findings sont des choix conservateurs de ce package. Ils doivent être ajustés par mesure, sans être présentés comme des recommandations officielles Anthropic.
