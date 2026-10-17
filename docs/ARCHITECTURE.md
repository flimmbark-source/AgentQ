# Runner architecture v0.1

## Execution boundary

`workflow_dispatch` (manual) or hourly schedule gated by Actions variable `AGENTQ_ENABLED=true` → `scripts/select_task.py` → official Codex action → `scripts/validate_changes.py` → standard-library unit tests → `peter-evans/create-pull-request` draft PR. Each invocation selects **at most one** task and must leave the default branch unchanged.

## Persistent state

- `tasks/queue.json`: only an explicit local queue of engineering work the user authorized. It is deliberately *not* the research database.
- GitHub pull requests: durable output and provenance. The selector reads past PRs and treats an open PR for a task as in progress, and a merged PR as done. A closed-unmerged PR permits retry.
- Google Sheet: canonical research state, **not accessed by this runner**. No automatic claims of syncing.

## Task contract

Each task has an ID, bounded objective, completion criteria, dependencies, approved execution flag and output path prefixes. A task cannot be selected until any dependencies were actually merged. No task is a license to change product decisions.

## Failure handling

If there are no eligible tasks, selection ends successfully without Codex. A missing API secret causes a clear failure on non-dry runs. Missing tests, broken output allowlist, and agent-written files outside authorized directories block PR creation. On failure, the workflow can be retried manually after fixing its configuration. Nothing is silently merged.

## Expanding to a real research lab

After this first complete PR cycle works, connect the live research workbook *read-only*, derive safe tasks from approved steps and record proposed research write-backs separately with source links. Keep any raw clinical or personal materials out of this public repository. Only then consider additional task families, longer-running experiments, integrated browser testing, and a human review queue.
