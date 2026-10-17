#!/usr/bin/env python3
"""Fail-closed path, size and content boundary checks before publishing a PR."""
import argparse
import json
from pathlib import Path
import re
import subprocess

ALLOWED_SUFFIXES = {".md", ".json", ".html", ".css", ".js", ".ts", ".tsx", ".py", ".svg", ".txt"}
SENSITIVE_PATTERNS = [
    re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(rb"sk-(?:proj-)?[A-Za-z0-9_-]{20,}"),
]
MAX_FILE_BYTES = 256 * 1024
MAX_TOTAL_BYTES = 1024 * 1024


def parse_porcelain(raw):
    """Return paths from NUL-separated git porcelain records; reject renames/copies."""
    values = raw.decode("utf-8", errors="strict").split("\0")
    paths = []
    i = 0
    while i < len(values):
        token = values[i]
        if not token:
            i += 1
            continue
        if len(token) < 4 or token[2] != " ":
            raise ValueError("Unrecognized git status record")
        status, name = token[:2], token[3:]
        if any(s in status for s in ("R", "C", "D", "U", "!")):
            raise ValueError(f"Forbidden rename/copy/deletion/conflict: {name}")
        if not name:
            raise ValueError("Empty path")
        paths.append(name)
        i += 1
    return paths


def validate_file(root, name, prefixes):
    path = Path(name)
    if path.is_absolute() or ".." in path.parts or any(part.startswith(".") for part in path.parts):
        raise ValueError(f"Unsafe path: {name}")
    posix = path.as_posix()
    if not any(posix.startswith(prefix) for prefix in prefixes):
        raise ValueError(f"Outside task allowlist: {name}")
    abs_path = root / path
    if abs_path.is_symlink() or not abs_path.is_file():
        raise ValueError(f"Expected regular file: {name}")
    if path.suffix.lower() not in ALLOWED_SUFFIXES:
        raise ValueError(f"Unsupported file type: {name}")
    payload = abs_path.read_bytes()
    if len(payload) > MAX_FILE_BYTES:
        raise ValueError(f"Oversize file: {name}")
    payload.decode("utf-8", errors="strict")
    if any(pattern.search(payload) for pattern in SENSITIVE_PATTERNS):
        raise ValueError(f"Credential-looking content in {name}")
    return len(payload)


def validate(root, task):
    outcome = subprocess.run(["git", "-C", str(root), "status", "--porcelain=v1", "--untracked-files=all", "-z"], capture_output=True, check=True)
    paths = parse_porcelain(outcome.stdout)
    if not paths:
        raise ValueError("No changed deliverable files. Refusing to publish an empty PR")
    prefixes = task["allowed_paths"]
    total_bytes = 0
    for name in paths:
        total_bytes += validate_file(root, name, prefixes)
    if total_bytes > MAX_TOTAL_BYTES:
        raise ValueError("Total change size too large")
    return paths


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-file", required=True)
    parser.add_argument("--repo-root", default=".")
    args = parser.parse_args()
    task = json.loads(Path(args.task_file).read_text(encoding="utf-8"))
    files = validate(Path(args.repo_root).resolve(), task)
    print(f"Validated {len(files)} files for {task['id']}")
    for path in files:
        print(f"  {path}")


if __name__ == "__main__":
    main()
