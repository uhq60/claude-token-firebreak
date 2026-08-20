---
name: token-firebreak
description: Run a very large codebase audit through mechanical inventory, logical shards, isolated auditors, independent verification, bounded findings, and off-context artifacts.
argument-hint: "<audit objective> [target path]"
disable-model-invocation: true
---

# Token Firebreak

Run this only when the user invokes `/token-firebreak`. Keep the main conversation as an orchestrator, never as the repository reader.

## Invariants

1. Before source analysis, run `python scripts/inventory.py . --config config/firebreak.json --out .firebreak/manifest.json`, then `python scripts/shard.py .firebreak/manifest.json --config config/firebreak.json --out .firebreak/shards`.
2. Review manifest counts and exclusion hints. Do not expose secret-file contents; a sensitive filename is metadata, not authorization to read it.
3. For large scope, launch `.claude/workflows/token-firebreak-audit.js`. Pass only the audit objective and bounded shard metadata.
4. Workers may read only their assigned shard and must write JSONL candidates under `.firebreak/raw-findings/`. Evidence excerpts obey `max_evidence_chars`; full evidence stays under `.firebreak/evidence/`.
5. An auditor never verifies its own findings. `audit-verifier` independently marks each item `confirmed`, `rejected`, or `uncertain` before synthesis.
6. The main context receives only counts, verified findings, unresolved critical uncertainties, and the report path.
7. Honor the live Token Governor state in `.firebreak/runtime.json`. At `BLOCK`, refuse broad reads; at `COMPACT`, checkpoint artifacts and compact or start a fresh session.
8. Use low effort for inventory/classification, medium for audit/verification, and high only for ambiguous critical synthesis.

## Completion

Run `python scripts/metrics.py .firebreak --out .firebreak/metrics.json`. Return the report path, severity counts, confirmed/rejected/uncertain counts, coverage limits, and metric path. Do not paste raw logs or evidence.

For operating details read [TOKEN-FIREBREAK.md](../../../TOKEN-FIREBREAK.md). For the schema read [finding.schema.json](../../../schemas/finding.schema.json). For source-backed design constraints read [OFFICIAL-SOURCES.md](../../../docs/OFFICIAL-SOURCES.md).
