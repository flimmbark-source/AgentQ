#!/usr/bin/env python3
"""Bounded run retrospectives and optional human-reviewed self-improvements."""
import argparse
import json
import os
from pathlib import Path
import subprocess
from select_task import github_prs
from validate_changes import parse_porcelain, SENSITIVE_PATTERNS, MAX_FILE_BYTES, MAX_TOTAL_BYTES

STEPS = ("select", "codex", "validate", "publish")
ALLOWED_OUTCOMES = {"success", "failure", "skipped", "cancelled", "unknown"}
MARKER = "AgentQ Improvement For Run:"

def summarize(task, dry, steps, pr):
    if any(v not in ALLOWED_OUTCOMES for v in steps.values()):
        raise ValueError("Invalid outcome")
    if dry: stage = "dry_run"
    elif steps.get("select") != "success": stage = "selection_failed"
    elif not task: stage = "no_task"
    elif steps.get("codex") != "success": stage = "generation_failed"
    elif steps.get("validate") != "success": stage = "validation_failed"
    elif steps.get("publish") != "success" or not pr: stage = "publication_failed"
    else: stage = "awaiting_review"
    return {"schema_version": 1, "run_id": str(os.getenv("GITHUB_RUN_ID", "local")),
            "task_id": task or None, "dry_run": bool(dry), "steps": steps,
            "stage": stage, "deliverable_pr": pr or None, "improvement_verified": False}

def allowed(name):
    return name == "scripts/select_task.py" or (name.startswith("tests/test_") and name.endswith(".py")) or (name.startswith("docs/agent-improvement/") and name.endswith(".md"))

def verify(root, filenames):
    total = 0
    for name in filenames:
        path = Path(name)
        if path.is_absolute() or ".." in path.parts or any(p.startswith(".") for p in path.parts) or not allowed(name):
            raise ValueError("Protected self-change path: " + name)
        file = root / path
        if file.is_symlink() or not file.is_file(): raise ValueError("Invalid self-change file: " + name)
        raw = file.read_bytes()
        raw.decode("utf-8")
        if len(raw) > MAX_FILE_BYTES or any(p.search(raw) for p in SENSITIVE_PATTERNS):
            raise ValueError("Unsafe self-change file: " + name)
        total += len(raw)
    if total > MAX_TOTAL_BYTES: raise ValueError("Oversized self-change")
    if "scripts/select_task.py" in filenames and not any(n.startswith("tests/test_") for n in filenames):
        raise ValueError("Executable change needs regression test")
    return filenames

def pending(prs):
    return any(p.get("state") == "open" and MARKER in (p.get("body") or "") for p in prs)

def improvement_prompt(report):
    if report.get("schema_version") != 1 or report.get("stage") != "awaiting_review":
        raise ValueError("Need successful PR before self-improvement attempt")
    summary = json.dumps({k: report.get(k) for k in ("run_id", "task_id", "stage", "steps")}, indent=2)
    return ("AgentQ self-review. Previous run summary (sanitized):\n" + summary + "\n\n"
            "Identify one reproducible weakness in task selection or tests. Make the smallest fix and a regression test. "
            "Allowed paths: scripts/select_task.py, tests/test_*.py, docs/agent-improvement/*.md ONLY. "
            "Do not edit workflows, AGENTS.md, validators, secrets, task queue, research records, dependencies or product files. "
            "Do not add permissions, network calls, auto-merge or clinical features. "
            "If there is no grounded improvement, make no edits. Run python -m unittest discover -s tests -v. "
            "Report baseline failure, changed behavior, tests and remaining uncertainty. "
            "Do not commit, merge, approve or create PRs: a separate trusted step creates a draft PR.")

def main():
    p = argparse.ArgumentParser()
    p.add_argument("mode", choices=("report", "capacity", "prompt", "validate"))
    p.add_argument("--out", required=True)
    p.add_argument("--report", default="")
    p.add_argument("--task", default="")
    p.add_argument("--pr", default="")
    p.add_argument("--dry-run", action="store_true")
    for name in STEPS: p.add_argument("--"+name, default="unknown", choices=sorted(ALLOWED_OUTCOMES))
    a = p.parse_args()
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    if a.mode == "report":
        report = summarize(a.task, a.dry_run, {n: getattr(a,n) for n in STEPS}, a.pr)
        out.write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
        if os.getenv("GITHUB_STEP_SUMMARY"):
            with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as f:
                f.write("\n## AgentQ learning review\n")
                f.write("- Stage: "+report["stage"]+"\n")
                f.write("- Verified improvement: no (requires test evidence and human review).\n")
    elif a.mode == "capacity":
        prs = github_prs(os.getenv("GITHUB_REPOSITORY"), os.getenv("GITHUB_TOKEN"))
        out.write_text("has_capacity="+("false" if pending(prs) else "true")+"\n")
    elif a.mode == "prompt":
        report = json.loads(Path(a.report).read_text(encoding="utf-8"))
        out.write_text(improvement_prompt(report)+"\n", encoding="utf-8")
    else:
        status = subprocess.run(["git","status","--porcelain=v1","--untracked-files=all","-z"], capture_output=True, check=True)
        filenames = verify(Path(".").resolve(), parse_porcelain(status.stdout))
        out.write_text("has_improvement="+("true" if filenames else "false")+"\n")
        print("Improvement candidate files:", filenames)
    print("Self-review mode:", a.mode)

if __name__ == "__main__":
    main()
