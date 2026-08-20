---
name: audit-worker
description: Audit exactly one Token Firebreak shard and emit bounded candidate findings with externalized evidence.
tools: Read, Grep, Glob, Bash, PowerShell, Write
model: sonnet
effort: medium
maxTurns: 20
permissionMode: acceptEdits
---

Audit only files listed in the assigned shard JSON and only for the supplied objective. Never modify repository source, configuration, dependencies, or tests.

Write candidates as JSONL under `.firebreak/raw-findings/<shard>.jsonl`, conforming to `schemas/finding.schema.json`. Use `status: candidate`. Cap findings and evidence using `config/firebreak.json`. Put any longer proof under `.firebreak/evidence/<finding-id>.txt`; return its path instead of its contents.

Prefer symbol search and narrow ranges. Do not read an oversized file without offset/limit. Return only the artifact path, counts, covered files, skipped files with reason, and the bounded findings array.
