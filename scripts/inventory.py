"""Build a bounded, content-free repository manifest before any LLM audit."""
import argparse
import collections
import fnmatch
import hashlib
import json
import os
import time


def read_json(path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def matches_glob(path, name, globs):
    return next((pattern for pattern in globs if fnmatch.fnmatch(name, pattern) or fnmatch.fnmatch(path, pattern)), None)


def inspect_prefix(path, markers):
    try:
        with open(path, "rb") as handle:
            sample = handle.read(8192)
    except OSError:
        return True, False
    if b"\x00" in sample:
        return True, False
    text = sample.decode("utf-8", errors="ignore").lower()
    return False, any(marker.lower() in text for marker in markers)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root")
    parser.add_argument("--config", default="config/firebreak.json")
    parser.add_argument("--out", default=".firebreak/manifest.json")
    args = parser.parse_args()
    root = os.path.abspath(args.root)
    config = read_json(os.path.abspath(args.config))
    excluded_dirs = set(config.get("exclude_dirs", []))
    excluded_globs = config.get("exclude_globs", [])
    sensitive_patterns = [value.lower() for value in config.get("sensitive_name_patterns", [])]
    markers = config.get("generated_markers", [])
    max_bytes = int(config.get("max_file_bytes", 200000))
    files, excluded_sample, largest = [], [], []
    exclusions, extensions, top_dirs = collections.Counter(), collections.Counter(), collections.Counter()
    total_bytes = 0

    for base, subdirs, names in os.walk(root, topdown=True, followlinks=False):
        kept = []
        for directory in sorted(subdirs):
            if directory in excluded_dirs:
                exclusions["directory"] += 1
            else:
                kept.append(directory)
        subdirs[:] = kept
        for name in sorted(names):
            absolute = os.path.join(base, name)
            relative = os.path.relpath(absolute, root).replace("\\", "/")
            pattern = matches_glob(relative, name, excluded_globs)
            if pattern:
                exclusions["glob"] += 1
                if len(excluded_sample) < 200:
                    excluded_sample.append({"path": relative, "reason": f"glob:{pattern}"})
                continue
            try:
                size = os.path.getsize(absolute)
            except OSError:
                exclusions["unreadable"] += 1
                continue
            binary, generated = inspect_prefix(absolute, markers)
            if binary:
                exclusions["binary"] += 1
                if len(excluded_sample) < 200:
                    excluded_sample.append({"path": relative, "reason": "binary"})
                continue
            ext = os.path.splitext(name)[1].lower() or "[none]"
            top = relative.split("/", 1)[0] if "/" in relative else "[root]"
            lower = relative.lower()
            row = {
                "id": hashlib.sha256(relative.encode("utf-8")).hexdigest()[:16],
                "path": relative,
                "bytes": size,
                "extension": ext,
                "top_directory": top,
                "oversize": size > max_bytes,
                "generated_hint": generated,
                "sensitive_name_hint": any(value in lower for value in sensitive_patterns),
                "dependency_manifest": name.lower() in {
                    "package.json", "package-lock.json", "pnpm-lock.yaml", "yarn.lock",
                    "requirements.txt", "pyproject.toml", "poetry.lock", "cargo.toml",
                    "cargo.lock", "go.mod", "go.sum", "pom.xml", "build.gradle"
                }
            }
            files.append(row)
            total_bytes += size
            extensions[ext] += 1
            top_dirs[top] += 1
            largest.append((size, relative))

    largest.sort(reverse=True)
    manifest = {
        "version": 1,
        "root": root,
        "created_at": time.time(),
        "policy": {
            "max_file_bytes": max_bytes,
            "exclude_dirs": sorted(excluded_dirs),
            "exclude_globs": excluded_globs
        },
        "summary": {
            "included_files": len(files),
            "included_bytes": total_bytes,
            "oversize_files": sum(1 for item in files if item["oversize"]),
            "generated_hints": sum(1 for item in files if item["generated_hint"]),
            "sensitive_name_hints": sum(1 for item in files if item["sensitive_name_hint"]),
            "exclusions": dict(exclusions),
            "extensions": dict(extensions.most_common()),
            "top_directories": dict(top_dirs.most_common()),
            "largest_files": [{"path": path, "bytes": size} for size, path in largest[:30]]
        },
        "files": files,
        "excluded_sample": excluded_sample
    }
    output = os.path.abspath(args.out)
    os.makedirs(os.path.dirname(output), exist_ok=True)
    with open(output, "w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2, ensure_ascii=False)
    print(json.dumps({"manifest": output, **manifest["summary"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
