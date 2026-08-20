import json
import os
import sys
import time


def load_config(root):
    try:
        with open(os.path.join(root, "config", "firebreak.json"), encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError):
        return {}


def main():
    try:
        data = json.load(sys.stdin)
    except (ValueError, TypeError):
        data = {}
    workspace = data.get("workspace") or {}
    root = workspace.get("project_dir") or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    context = data.get("context_window") or {}
    usage = context.get("current_usage") or {}
    pct = float(context.get("used_percentage") or 0)
    config = load_config(root)
    state = "NORMAL"
    if pct >= float(config.get("context_compact_percent", 50)):
        state = "COMPACT"
    elif pct >= float(config.get("context_block_percent", 30)):
        state = "BLOCK"
    elif pct >= float(config.get("context_warn_percent", 20)):
        state = "WATCH"
    runtime = {
        "updated_at": time.time(), "session_id": data.get("session_id"),
        "context_percent": pct, "state": state,
        "model": (data.get("model") or {}).get("display_name"),
        "effort": (data.get("effort") or {}).get("level"),
        "input_tokens": usage.get("input_tokens", 0),
        "output_tokens": usage.get("output_tokens", 0),
        "cache_creation_input_tokens": usage.get("cache_creation_input_tokens", 0),
        "cache_read_input_tokens": usage.get("cache_read_input_tokens", 0)
    }
    try:
        path = os.path.join(root, ".firebreak", "runtime.json")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as handle:
            json.dump(runtime, handle, indent=2)
        os.replace(tmp, path)
    except OSError:
        pass
    print(f"FIREBREAK {state} | context {pct:.0f}% | cache-read {runtime['cache_read_input_tokens']}")


if __name__ == "__main__":
    main()
