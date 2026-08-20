# Claude Token Firebreak

A Claude Code package for very large repository audits. It prevents the main conversation from becoming a repository, log, and intermediate-result store.

## Installable package

Download [claude-token-firebreak.zip](./claude-token-firebreak.zip), extract it at the root of the repository to audit, then follow the included installation and operating guides.

## How it works

```text
Repository -> mechanical inventory -> exclusions -> logical shards
           -> isolated audit workers -> independent verification
           -> deduplicated, bounded synthesis
```

The main context receives only compact status, verified findings, coverage limitations, and artifact paths. Raw inventory, tool output, full evidence, and intermediate findings remain under `.firebreak/`.

## Core controls

- Mechanical inventory before LLM source analysis
- Configurable directory/glob exclusions and secret-name protection
- Logical sharding with file and byte limits
- Separate scanner, worker, verifier, and synthesizer roles
- JSON findings with bounded fields and externalized evidence
- Guard hooks for oversized reads, broad listings, logs, and test output
- Pre/Post compact checkpoints and a Token Governor
- Telemetry, cache metrics, and A/B benchmark tooling
- Non-destructive audit policy

## Official Anthropic documentation

The package is designed only from official Anthropic documentation:

- [Claude Code costs](https://code.claude.com/docs/en/costs): context cost, usage, compaction, output filtering, and subagents.
- [Context window](https://code.claude.com/docs/en/context-window): contextual growth from reads and isolated subagent contexts.
- [Dynamic workflows](https://code.claude.com/docs/en/workflows): JavaScript orchestration, fan-out, and intermediate state outside the conversation.
- [Subagents](https://code.claude.com/docs/en/sub-agents): delegated work with independent contexts.
- [Hooks](https://code.claude.com/docs/en/hooks) and [hooks guide](https://code.claude.com/docs/en/hooks-guide): tool interception, output controls, and compaction lifecycle.
- [Prompt caching](https://code.claude.com/docs/en/prompt-caching): cache reads/writes and reusable prompt prefixes.
- [Memory / CLAUDE.md](https://code.claude.com/docs/en/memory), [status line](https://code.claude.com/docs/en/statusline), and [usage monitoring](https://code.claude.com/docs/en/monitoring-usage).

All local thresholds are package policies, not Anthropic limits or savings guarantees. Run the included A/B benchmark on a representative repository before relying on token or quality outcomes.
