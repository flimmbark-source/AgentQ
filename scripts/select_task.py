#!/usr/bin/env python3
"""Select exactly one eligible task. No credentials or private data are persisted."""
import argparse
import json
import os
from pathlib import Path
import re
import urllib.error
import urllib.request

ID_RE = re.compile(r"^AQ-[0-9]{3,}$")
PR_MARKER = "AgentQ Task: "


def read_queue(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("schema_version") != 1 or not isinstance(data.get("tasks"), list):
        raise ValueError("Expected schema_version=1 and tasks list")
    ids = set()
    for task in data["tasks"]:
        task_id = task.get("id", "")
        if not ID_RE.fullmatch(task_id) or task_id in ids:
            raise ValueError(f"Invalid or duplicate task ID: {task_id!r}")
        ids.add(task_id)
        if not isinstance(task.get("allowed_paths"), list) or not task["allowed_paths"]:
            raise ValueError(f"Task {task_id} must specify allowed_paths")
        for prefix in task["allowed_paths"]:
            if not isinstance(prefix, str) or not prefix.endswith("/") or prefix.startswith(("/", ".")) or ".." in prefix:
                raise ValueError(f"Unsafe allowed path: {prefix}")
        if not isinstance(task.get("dependencies", []), list):
            raise ValueError(f"Invalid dependencies in {task_id}")
    for task in data["tasks"]:
        for dep in task.get("dependencies", []):
            if dep not in ids or dep == task["id"]:
                raise ValueError(f"Bad dependency {dep} for {task['id']}")
    return data["tasks"]


def github_prs(repository, token):
    if not repository or not token:
        raise ValueError("GITHUB_REPOSITORY and GITHUB_TOKEN are required for live PR deduplication")
    results = []
    for page in range(1, 11):
        url = f"https://api.github.com/repos/{repository}/pulls?state=all&sort=updated&direction=desc&per_page=100&page={page}"
        request = urllib.request.Request(url, headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "AgentQ-task-selector",
        })
        with urllib.request.urlopen(request, timeout=15) as response:
            page_results = json.load(response)
        if not isinstance(page_results, list):
            raise ValueError("Unexpected GitHub PR response")
        results.extend(page_results)
        if len(page_results) < 100:
            return results
    raise RuntimeError("PR history too long for safe deduplication: fail closed")


def pr_task_id(pr):
    body = pr.get("body") or ""
    match = re.search(r"(?m)^AgentQ Task: (AQ-[0-9]{3,})\s*$", body)
    return match.group(1) if match else None


def select(tasks, prs, requested="", max_open=2):
    done = set()
    active = set()
    for pr in prs:
        task_id = pr_task_id(pr)
        if not task_id:
            continue
        if pr.get("merged_at"):
            done.add(task_id)
        elif pr.get("state") == "open":
            active.add(task_id)
    if len(active) >= max_open:
        return None, f"{len(active)} active AgentQ PRs, capacity limit {max_open}"
    candidates = sorted(tasks, key=lambda t: (int(t.get("priority", 999)), t["id"]))
    if requested:
        candidates = [t for t in candidates if t["id"] == requested]
        if not candidates:
            raise ValueError(f"Unknown task: {requested}")
    for task in candidates:
        task_id = task["id"]
        if task.get("status") != "ready" or task.get("approved_to_execute") is not True:
            continue
        if task_id in done or task_id in active:
            continue
        if any(dep not in done for dep in task.get("dependencies", [])):
            continue
        return task, "selected"
    return None, "no eligible tasks (already proposed, merged, blocked, or unapproved)"


def write_selection(path, task, reason):
    output = Path(path)
    output.mkdir(parents=True, exist_ok=True)
    (output / "selection.env").write_text(
        f"has_task={'true' if task else 'false'}\n"
        + f"task_id={task['id'] if task else ''}\n", encoding="utf-8")
    (output / "selection.json").write_text(json.dumps({"selected": task["id"] if task else None, "reason": reason}, indent=2) + "\n", encoding="utf-8")
    if not task:
        return
    (output / "task.json").write_text(json.dumps(task, indent=2) + "\n", encoding="utf-8")
    checks = "\n".join(f"- {item}" for item in task["acceptance_checks"])
    prefixes = "\n".join(f"- `{path}`" for path in task["allowed_paths"])
    prompt = f"""# AgentQ execution mission: {task['id']}

Read `AGENTS.md` first and follow its security, clinical, and scope boundaries.

**Title:** {task['title']}

**Objective:** {task['objective']}

**Acceptance checks:**
{checks}

**Write ONLY to these paths:**
{prefixes}

You are not allowed to modify `tasks/queue.json`, workflows, action configuration, or the product decision log. This public repository cannot access the private research workbook. Do not invent evidence or participant responses. This task is a development experiment and its output must clearly be presented as unvalidated.

Implement the smallest complete and testable result you can within this run. Work only on the selected task. Report what you created, local checks you ran, limitations, and recommended further human review. Do not commit or open a PR; the surrounding workflow handles publication.
"""
    (output / "prompt.md").write_text(prompt, encoding="utf-8")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--queue", default="tasks/queue.json")
    p.add_argument("--task-id", default="")
    p.add_argument("--out-dir", default=".agentq/runtime")
    p.add_argument("--max-open", type=int, default=2)
    p.add_argument("--offline", action="store_true", help="Local inspection only; never use this in live Actions")
    p.add_argument("--prs-fixture", help="Test fixture JSON, never a live action setting")
    args = p.parse_args()
    tasks = read_queue(args.queue)
    if args.prs_fixture:
        prs = json.loads(Path(args.prs_fixture).read_text(encoding="utf-8"))
    elif args.offline:
        prs = []
    else:
        prs = github_prs(os.getenv("GITHUB_REPOSITORY"), os.getenv("GITHUB_TOKEN"))
    task, reason = select(tasks, prs, args.task_id, args.max_open)
    write_selection(args.out_dir, task, reason)
    print(f"Selected: {task['id']}" if task else f"Skipped: {reason}")


if __name__ == "__main__":
    main()
