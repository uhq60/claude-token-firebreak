"""Dependency-free structural validator for the package."""
import json
import os
import sys


REQUIRED = [
    "README.md", "TOKEN-FIREBREAK.md", "docs/ARCHITECTURE.md", "docs/OFFICIAL-SOURCES.md",
    "docs/BENCHMARK.md", "docs/INSTALLATION.md", "config/firebreak.json",
    ".claude/settings.json", ".claude/statusline.py", ".claude/skills/token-firebreak/SKILL.md",
    ".claude/agents/audit-scanner.md", ".claude/agents/audit-worker.md",
    ".claude/agents/audit-verifier.md", ".claude/agents/audit-synthesizer.md",
    ".claude/workflows/token-firebreak-audit.js", ".claude/hooks/guard_large_reads.py",
    ".claude/hooks/filter_test_output.py", ".claude/hooks/pre_compact.py",
    ".claude/hooks/post_compact.py", "schemas/finding.schema.json",
    "scripts/inventory.py", "scripts/shard.py", "scripts/metrics.py", "scripts/benchmark.py"
]


def main(root):
    root = os.path.abspath(root)
    errors = []
    for relative in REQUIRED:
        if not os.path.isfile(os.path.join(root, relative)):
            errors.append(f"missing: {relative}")
    for relative in (".claude/settings.json", "config/firebreak.json", "schemas/finding.schema.json"):
        try:
            with open(os.path.join(root, relative), encoding="utf-8") as handle:
                json.load(handle)
        except (OSError, ValueError) as exc:
            errors.append(f"invalid json {relative}: {exc}")
    for base, _, files in os.walk(root):
        if ".firebreak" in base.split(os.sep) or "__pycache__" in base.split(os.sep):
            continue
        for name in files:
            path = os.path.join(base, name)
            if name.endswith(".py"):
                try:
                    compile(open(path, encoding="utf-8").read(), path, "exec")
                except (OSError, SyntaxError) as exc:
                    errors.append(f"python syntax {os.path.relpath(path, root)}: {exc}")
            if name.endswith((".md", ".json", ".js")):
                try:
                    text = open(path, encoding="utf-8").read()
                    if "TODO_PLACEHOLDER" in text:
                        errors.append(f"unfinished placeholder: {os.path.relpath(path, root)}")
                except OSError as exc:
                    errors.append(str(exc))
    skill = os.path.join(root, ".claude", "skills", "token-firebreak", "SKILL.md")
    if os.path.isfile(skill):
        content = open(skill, encoding="utf-8").read()
        if not content.startswith("---\n") or "name: token-firebreak" not in content[:800]:
            errors.append("invalid skill frontmatter")
    if errors:
        print("\n".join(errors))
        return 1
    print(f"package ok: {len(REQUIRED)} required files; JSON and Python syntax valid")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "."))
