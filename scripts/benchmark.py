"""Compare real baseline and Firebreak metric snapshots."""
import argparse
import json
import os
import time


def load(path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def token_total(metrics):
    usage = metrics.get("usage", {})
    return sum(float(usage.get(key) or 0) for key in ("input_tokens", "output_tokens", "cache_creation_input_tokens", "cache_read_input_tokens"))


def confirmed(metrics):
    return int(metrics.get("findings", {}).get("by_status", {}).get("confirmed", 0))


def rejected(metrics):
    return int(metrics.get("findings", {}).get("by_status", {}).get("rejected", 0))


def safe_ratio(a, b):
    return round(a / b, 6) if a and b else None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", required=True)
    parser.add_argument("--firebreak", required=True)
    parser.add_argument("--out", default=".firebreak/benchmark.json")
    args = parser.parse_args()
    baseline, firebreak = load(args.baseline), load(args.firebreak)
    base_tokens, fire_tokens = token_total(baseline), token_total(firebreak)
    base_checked, fire_checked = confirmed(baseline) + rejected(baseline), confirmed(firebreak) + rejected(firebreak)
    result = {
        "version": 1,
        "created_at": time.time(),
        "baseline": baseline,
        "firebreak": firebreak,
        "comparison": {
            "token_saving_percent": round((1 - fire_tokens / base_tokens) * 100, 3) if base_tokens and fire_tokens else None,
            "baseline_tokens_per_confirmed_finding": safe_ratio(base_tokens, confirmed(baseline)),
            "firebreak_tokens_per_confirmed_finding": safe_ratio(fire_tokens, confirmed(firebreak)),
            "baseline_false_positive_rate": safe_ratio(rejected(baseline), base_checked),
            "firebreak_false_positive_rate": safe_ratio(rejected(firebreak), fire_checked),
            "baseline_cache_hit_ratio": baseline.get("cache_hit_ratio"),
            "firebreak_cache_hit_ratio": firebreak.get("cache_hit_ratio"),
            "baseline_context_peak_percent": baseline.get("context_peak_percent"),
            "firebreak_context_peak_percent": firebreak.get("context_peak_percent"),
            "confirmed_finding_delta": confirmed(firebreak) - confirmed(baseline)
        },
        "validity_note": "Compare identical repository state, audit prompt, model family, effort policy and time budget."
    }
    output = os.path.abspath(args.out)
    os.makedirs(os.path.dirname(output), exist_ok=True)
    with open(output, "w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2)
    print(json.dumps(result["comparison"]))


if __name__ == "__main__":
    main()
