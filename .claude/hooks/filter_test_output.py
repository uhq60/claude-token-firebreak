import json
import os
import re
import sys
import time


SIGNAL = re.compile(r"FAIL|FAILED|ERROR|WARN|Traceback|Exception|panic|fatal|✗|×", re.I)


def load_config(root):
    try:
        with open(os.path.join(root, "config", "firebreak.json"), encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError):
        return {}


def bounded(text, max_chars, max_lines, signal_only):
    lines = str(text or "").splitlines()
    selected = [line for line in lines if SIGNAL.search(line)] if signal_only else lines
    if signal_only and not selected:
        selected = lines[-min(40, max_lines):]
    result = "\n".join(selected[:max_lines])
    return result[:max_chars], len(lines), len(selected)


def main():
    try:
        event = json.load(sys.stdin)
    except (ValueError, TypeError):
        return 0
    response = event.get("tool_response")
    if not isinstance(response, dict):
        return 0
    stdout, stderr = str(response.get("stdout") or ""), str(response.get("stderr") or "")
    root = os.environ.get("CLAUDE_PROJECT_DIR") or event.get("cwd") or os.getcwd()
    cfg = load_config(root)
    max_chars, max_lines = int(cfg.get("max_command_output_chars", 12000)), int(cfg.get("max_output_lines", 160))
    command = str((event.get("tool_input") or {}).get("command") or "")
    is_test_or_log = bool(re.search(r"pytest|npm\s+(test|run\s+test)|pnpm\s+test|yarn\s+test|go\s+test|cargo\s+test|dotnet\s+test|mvn\s+test|gradle.*test|\.log\b", command, re.I))
    if len(stdout) + len(stderr) <= max_chars and not (is_test_or_log and stdout.count("\n") > max_lines):
        return 0
    output_dir = os.path.join(root, ".firebreak", "tool-output")
    os.makedirs(output_dir, exist_ok=True)
    token = re.sub(r"[^A-Za-z0-9_.-]", "-", str(event.get("tool_use_id") or int(time.time() * 1000)))
    artifact = os.path.join(output_dir, token + ".json")
    with open(artifact, "w", encoding="utf-8") as handle:
        json.dump({"command": command, "stdout": stdout, "stderr": stderr}, handle, ensure_ascii=False)
    out, out_lines, kept_out = bounded(stdout, max_chars * 3 // 4, max_lines, is_test_or_log)
    err, err_lines, kept_err = bounded(stderr, max_chars // 4, max_lines // 2, is_test_or_log)
    note = f"\n[Token Firebreak: full output saved to {os.path.relpath(artifact, root)}; stdout lines {out_lines}, stderr lines {err_lines}]"
    replacement = dict(response)
    replacement["stdout"], replacement["stderr"] = (out + note)[:max_chars], err[:max_chars // 3]
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse", "updatedToolOutput": replacement, "additionalContext": f"Output bounded; retained {kept_out + kept_err} diagnostic lines."}}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
