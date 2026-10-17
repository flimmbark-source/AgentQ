# AgentQ bounded self-improvement

Every run saves a sanitized diagnostic (selection, generation, validation, publication, next stage) to its Actions summary and a 30-day artifact. This is learning data, not proof of improved capability.

On an eligible paid development run, an optional second Codex pass can seek one testable improvement to task selection or its tests. It runs only after a development PR was successfully created, with no other improvement PR open. Only scripts/select_task.py, tests/test_*.py, and docs/agent-improvement/*.md may be edited. The independent validator, workflow, security rules, model instructions, research data, queue and credentials cannot be changed by the improvement pass. A Python executable change needs a regression test. All tests rerun. Any candidate is submitted as a DRAFT PR for human approval; nothing is auto-merged.

The second model call incurs extra API usage. To try once, run AgentQ Runner manually with dry_run=false and self_improve=true. To try on future successful scheduled runs, add repository Actions variable AGENTQ_SELF_IMPROVE_ENABLED=true. This does not enable hourly runs; the separate AGENTQ_ENABLED flag controls them.

Not every run can yield a real improvement. Dry runs, failures, no tasks, no reproducible issue, and a waiting improvement PR produce no self-edit. A test pass is not proof of improvement; inspect before/after behavior and reject a change if its evidence is weak. No clinical benefits are inferred.
