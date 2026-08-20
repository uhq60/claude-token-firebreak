import hashlib
import json
import os
import sys
import time


def main():
    try:
        event = json.load(sys.stdin)
    except (ValueError, TypeError):
        event = {}
    root = os.environ.get("CLAUDE_PROJECT_DIR") or event.get("cwd") or os.getcwd()
    state_dir = os.path.join(root, ".firebreak", "state")
    os.makedirs(state_dir, exist_ok=True)
    summary = str(event.get("compact_summary") or "")
    value = {"timestamp": time.time(), "phase": "post", "trigger": event.get("trigger"), "session_id": event.get("session_id"), "summary_chars": len(summary), "summary_sha256": hashlib.sha256(summary.encode("utf-8")).hexdigest()}
    with open(os.path.join(state_dir, "compact-events.jsonl"), "a", encoding="utf-8") as handle:
        handle.write(json.dumps(value) + "\n")


if __name__ == "__main__":
    main()
