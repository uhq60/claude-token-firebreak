import json
import os
import re
import sys


def load_json(path, default):
    try:
        with open(path, encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError):
        return default


def deny(reason):
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": reason}}))


def update(tool_input, reason):
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "ask", "permissionDecisionReason": reason, "updatedInput": tool_input}}))


def resolve(root, raw):
    if not raw:
        return None
    path = os.path.expandvars(os.path.expanduser(str(raw)))
    return os.path.abspath(path if os.path.isabs(path) else os.path.join(root, path))


def main():
    try:
        event = json.load(sys.stdin)
    except (ValueError, TypeError):
        return 0
    root = os.environ.get("CLAUDE_PROJECT_DIR") or event.get("cwd") or os.getcwd()
    cfg = load_json(os.path.join(root, "config", "firebreak.json"), {})
    runtime = load_json(os.path.join(root, ".firebreak", "runtime.json"), {})
    tool = str(event.get("tool_name") or "")
    tool_input = dict(event.get("tool_input") or {})
    max_bytes = int(cfg.get("max_file_bytes", 200000))
    max_lines = int(cfg.get("max_direct_read_lines", 400))
    pct = float(runtime.get("context_percent") or 0)
    block_pct = float(cfg.get("context_block_percent", 30))
    compact_pct = float(cfg.get("context_compact_percent", 50))

    if tool == "Read":
        path = resolve(root, tool_input.get("file_path"))
        requested_lines = int(tool_input.get("limit") or 0)
        try:
            is_artifact = bool(path and os.path.commonpath([os.path.abspath(root), path]) == os.path.abspath(root) and ".firebreak" in path.split(os.sep))
        except ValueError:
            is_artifact = False
        if pct >= compact_pct and not is_artifact:
            deny(f"Token Governor: context at {pct:.0f}%. Compact or start a fresh session before more repository reads.")
            return 0
        if path and os.path.isfile(path):
            size = os.path.getsize(path)
            if size > max_bytes and (requested_lines == 0 or requested_lines > max_lines):
                deny(f"Large read blocked ({size} bytes). Read at most {max_lines} lines, use Grep, or delegate the shard.")
                return 0

    if tool == "Grep" and pct >= block_pct:
        if tool_input.get("output_mode", "files_with_matches") == "content" and not tool_input.get("head_limit"):
            tool_input["head_limit"] = max_lines
            update(tool_input, f"Token Governor capped Grep output at {max_lines} matches.")
            return 0

    if tool == "Glob" and pct >= block_pct and str(tool_input.get("pattern", "")) in ("**/*", "**/**"):
        deny("Repository-wide Glob blocked at the current context level. Use the mechanical manifest or a narrower path.")
        return 0

    if tool in ("Bash", "PowerShell"):
        command = str(tool_input.get("command") or "")
        full_dump = re.search(r"(^|[;&|]\s*)(cat|type|Get-Content|gc)\s+[^|;]+$", command, re.I)
        broad_listing = re.search(r"(^|[;&|]\s*)(tree|find\s+\.|Get-ChildItem\s+.*-Recurse)(\s|$)", command, re.I)
        bounded = re.search(r"head|tail|Select-Object|Out-File|Set-Content|--max-count|-m\s+\d+", command, re.I)
        if (full_dump or broad_listing) and not bounded:
            deny("Unbounded command output blocked. Add a line/result limit or write raw output under .firebreak/ and return a summary.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
