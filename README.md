# AgentQ

A **human-supervised, scheduled AI development runner** for early Framework Transference product experiments. AgentQ turns a limited, explicit queue of development tasks into reviewable changes made by OpenAI Codex in GitHub Actions.

**Status:** The runner is scaffolded, **not yet activated**. The repository is currently **public**. Do not add private workbook exports, clinician notes, participant data, credentials, or unpublished sensitive material.

## The workflow

1. A manual or scheduled workflow reads `tasks/queue.json`, checks already open and merged AgentQ PRs, and selects an eligible task.
2. Codex receives the task and the guardrails in `AGENTS.md`, and works in a restricted checkout.
3. Deterministic checks validate outputs and prevent modifications outside task-specific paths.
4. A **draft pull request** proposes changed files. It is never auto-merged.
5. If an AgentQ PR is open, the same task is skipped on later runs; merged work is considered done. Closed-unmerged work is eligible for retry.

This is **bounded iterative development**, not an always-running process or a substitute for clinical research. Each runner invocation performs at most one task. It can develop software or write structured design drafts; it cannot test therapeutic outcomes without actual participant evidence.

## Getting started

See [Setup](docs/SETUP.md), [Safety](docs/SECURITY.md), and [Architecture](docs/ARCHITECTURE.md).

- Add the repository secret `OPENAI_API_KEY` in GitHub **Settings → Secrets and variables → Actions**. Do not paste it into chat or commit it.
- Run the `AgentQ Runner` workflow manually with `dry_run: true` first. This selects work and tests the configuration *without charging for Codex*.
- Run it manually with `dry_run: false` to let Codex propose a PR.
- After a successful supervised trial, set the Actions variable `AGENTQ_ENABLED` to `true` to allow scheduled runs (hourly). The maximum number of open AgentQ PRs is two.

The workflow becomes available on GitHub's **Actions** page after this branch is merged to the default branch. Review the draft PR before merging.

## Research integrity

The canonical research workbook is a **separate private Google Sheet**. This public code repository does **not** connect to it, synchronize decisions, or record clinical data. `tasks/queue.json` is a limited *execution authorization*, not a copy of the current research database. Any future integration must be designed and tested separately, preferably after making the repository private. See [Workbook integration](docs/WORKBOOK_INTEGRATION.md).

## Local checks

```bash
python -m unittest discover -s tests -v
python scripts/select_task.py --out-dir /tmp/agentq-preview
python scripts/validate_changes.py --task-file /tmp/agentq-preview/task.json --repo-root .
```

The last command checks current modified/untracked files against the selected task's allowlist; it is designed to run after Codex has created output.

## Bounded self-improvement

Each run records sanitized diagnostic information. An optional paid second Codex pass can propose one regression-tested AgentQ improvement in a separate draft PR. No self-editing is merged automatically, and a logged run is not proof of improved ability. See [Self-improvement](docs/SELF_IMPROVEMENT.md).
