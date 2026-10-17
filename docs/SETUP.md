# Set up the AgentQ runner

**Read [SECURITY.md](SECURITY.md) first.** This repository is public as of initial setup. Neither clinical data nor private workbook content should be committed here.

1. Merge the setup pull request into `main` after inspecting all files. GitHub only registers workflow dispatch and schedule definitions from the default branch.
2. In the repository, open **Settings → Secrets and variables → Actions → Secrets → New repository secret**. Name the secret `OPENAI_API_KEY` and enter a separately budgeted [OpenAI API key](https://platform.openai.com/api-keys). This API incurs usage-based charges independent of a ChatGPT subscription. Never send the key in chat.
3. Under **Settings → Actions → General → Workflow permissions**, grant **Read and write permissions** and enable **Allow GitHub Actions to create and approve pull requests** if these controls are available. The workflow uses scoped permissions. Do **not** turn on automatic merging.
4. Open **Actions → AgentQ Runner → Run workflow**, select `dry_run: true`. Confirm it selects `AQ-001` and skips Codex (no model call). Review its log.
5. Run again with `dry_run: false` after confirming the secret is set. Review the Codex result, safety checks and resulting **draft PR**. If the workflow cannot create a PR, inspect the workflow permissions in step 3. Do not silently substitute a commit to `main`.
6. For unattended cycles, set repository **Settings → Secrets and variables → Actions → Variables → New repository variable** to `AGENTQ_ENABLED = true`. Hourly scheduling is then permitted. Set it back to `false` to pause paid scheduled runs; dispatch runs remain available.
7. Review and merge satisfactory AgentQ draft PRs. With two open AgentQ PRs, the runner pauses instead of flooding the repository. It recognizes completed tasks via merged PRs in GitHub, not by secretly changing product decisions.

## Current boundaries

- The runner only works against the explicit repo-local `tasks/queue.json` (three approved development tasks). It does not yet read or write the Google research workbook. Direct Google Sheets synchronization requires a separate connector and security design.
- The GitHub runner uses the official `openai/codex-action@v1`, a workspace-restricted permission profile, and a reduced-privilege safety strategy. It does not automatically merge PRs.
- `AGENTQ_ENABLED` is **not** set by this code. The first scheduled run will be a no-op until you enable it.
- GitHub scheduled workflows can be delayed or skipped under load; they are not uninterrupted agents. A run executes at most one task and has a 35-minute timeout.
- The same task will not be selected while an AgentQ draft PR for it is open or after one is merged. Closing a draft PR without merging permits another attempt.

## Run tests without an API key

```bash
python -m unittest discover -s tests -v
python scripts/select_task.py --out-dir /tmp/agentq-preview
```

## Cost and access

Model calls consume your OpenAI API budget, plus applicable GitHub Actions minutes. Review costs regularly at the provider dashboards. If this public repository contains sensitive project material, change repository visibility in GitHub settings **before** running development tasks that would need to read it.

## Optional self-improvement

After verifying a paid development run, select self_improve=true on a manual workflow dispatch to permit one extra paid model pass. To enable it on future scheduled paid runs, set Actions variable AGENTQ_SELF_IMPROVE_ENABLED=true. Leave it false or unset otherwise. This is separate from AGENTQ_ENABLED, which controls the hourly runner schedule. See SELF_IMPROVEMENT.md.
