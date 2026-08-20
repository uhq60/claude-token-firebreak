"""Partition an inventory into logical, file-count and byte-bounded shards."""
import argparse
import json
import os
import re


def load(path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def classify(path, rules):
    lower = path.lower()
    for label, pattern in rules.items():
        if re.search(pattern, lower, re.I):
            return label
    top = lower.split("/", 1)[0] if "/" in lower else "root"
    return re.sub(r"[^a-z0-9._-]+", "-", top) or "root"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest")
    parser.add_argument("--config", default="config/firebreak.json")
    parser.add_argument("--out", default=".firebreak/shards")
    parser.add_argument("--max-files", type=int)
    parser.add_argument("--max-bytes", type=int)
    args = parser.parse_args()
    manifest, config = load(args.manifest), load(args.config)
    max_files = args.max_files or int(config.get("max_files_per_shard", 60))
    max_bytes = args.max_bytes or int(config.get("max_bytes_per_shard", 1500000))
    groups = {}
    for item in manifest.get("files", []):
        label = classify(item["path"], config.get("logical_shards", {}))
        groups.setdefault(label, []).append(item)
    output = os.path.abspath(args.out)
    os.makedirs(output, exist_ok=True)
    index, number = [], 0
    for label in sorted(groups):
        batch, batch_bytes = [], 0
        for item in sorted(groups[label], key=lambda value: value["path"]):
            size = int(item.get("bytes", 0))
            if batch and (len(batch) >= max_files or batch_bytes + size > max_bytes):
                number += 1
                index.append(write_shard(output, number, label, batch, batch_bytes))
                batch, batch_bytes = [], 0
            batch.append(item)
            batch_bytes += size
        if batch:
            number += 1
            index.append(write_shard(output, number, label, batch, batch_bytes))
    with open(os.path.join(output, "index.json"), "w", encoding="utf-8") as handle:
        json.dump({"version": 1, "manifest": os.path.relpath(os.path.abspath(args.manifest), os.getcwd()).replace("\\", "/"), "shard_count": len(index), "shards": index}, handle, indent=2)
    print(json.dumps({"directory": output, "shards": len(index), "files": sum(item["file_count"] for item in index)}))


def write_shard(output, number, label, files, total_bytes):
    filename = f"{number:03d}-{label}.json"
    payload = {"version": 1, "shard": number, "label": label, "file_count": len(files), "total_bytes": total_bytes, "files": files}
    with open(os.path.join(output, filename), "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
    return {"path": filename, "label": label, "file_count": len(files), "total_bytes": total_bytes}


if __name__ == "__main__":
    main()
