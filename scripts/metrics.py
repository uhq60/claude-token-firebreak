"""Aggregate findings, runtime context and optional Claude usage exports."""
import argparse
import collections
import glob
import json
import os
import time


TOKEN_KEYS = ("input_tokens", "output_tokens", "cache_creation_input_tokens", "cache_read_input_tokens")


def jsonl_records(pattern):
    for path in glob.glob(pattern, recursive=True):
        try:
            with open(path, encoding="utf-8") as handle:
                for line in handle:
                    if line.strip():
                        yield json.loads(line)
        except (OSError, ValueError):
            continue


def token_totals(value, totals):
    if isinstance(value, dict):
        found = False
        for key in TOKEN_KEYS:
            if isinstance(value.get(key), (int, float)):
                totals[key] += value[key]
                found = True
        if found:
            return
        for child in value.values():
            token_totals(child, totals)
    elif isinstance(value, list):
        for child in value:
            token_totals(child, totals)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", help=".firebreak directory")
    parser.add_argument("--usage", action="append", default=[], help="JSON usage/statusline/OTel export")
    parser.add_argument("--context-percent", type=float)
    parser.add_argument("--duration-seconds", type=float)
    parser.add_argument("--out", default=".firebreak/metrics.json")
    args = parser.parse_args()
    root = os.path.abspath(args.root)
    records = list(jsonl_records(os.path.join(root, "**", "*.jsonl")))
    statuses = collections.Counter(str(item.get("status", "unknown")) for item in records if "severity" in item)
    severities = collections.Counter(str(item.get("severity", "UNKNOWN")) for item in records if "severity" in item)
    totals = collections.Counter()
    for path in args.usage:
        try:
            with open(path, encoding="utf-8") as handle:
                token_totals(json.load(handle), totals)
        except (OSError, ValueError):
            pass
    runtime = {}
    try:
        with open(os.path.join(root, "runtime.json"), encoding="utf-8") as handle:
            runtime = json.load(handle)
    except (OSError, ValueError):
        pass
    context_percent = args.context_percent if args.context_percent is not None else runtime.get("context_percent", 0)
    metrics = {
        "version": 1,
        "created_at": time.time(),
        "findings": {"total": sum(statuses.values()), "by_status": dict(statuses), "by_severity": dict(severities)},
        "usage": {key: totals.get(key, runtime.get(key, 0)) for key in TOKEN_KEYS},
        "context_peak_percent": context_percent,
        "duration_seconds": args.duration_seconds,
        "cache_hit_ratio": None
    }
    cache_base = metrics["usage"]["input_tokens"] + metrics["usage"]["cache_creation_input_tokens"] + metrics["usage"]["cache_read_input_tokens"]
    if cache_base:
        metrics["cache_hit_ratio"] = round(metrics["usage"]["cache_read_input_tokens"] / cache_base, 6)
    output = os.path.abspath(args.out)
    os.makedirs(os.path.dirname(output), exist_ok=True)
    with open(output, "w", encoding="utf-8") as handle:
        json.dump(metrics, handle, indent=2)
    print(json.dumps(metrics))


if __name__ == "__main__":
    main()
