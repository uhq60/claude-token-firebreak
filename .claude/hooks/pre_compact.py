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
    value = {"timestamp": time.time(), "phase": "pre", "trigger": event.get("trigger"), "session_id": event.get("session_id"), "custom_instructions": event.get("custom_instructions", "")[:1000], "resume_from": [".firebreak/manifest.json", ".firebreak/shards/", ".firebreak/verified-findings/", ".firebreak/metrics.json"]}
    with open(os.path.join(state_dir, "pre-compact.json"), "w", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2)


if __name__ == "__main__":
    main()
