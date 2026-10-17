# AgentQ security boundaries

- **This repository is public.** Task descriptions and generated PRs will be public. Do not put private Google Sheet exports, identifiable participant/child/clinician details, unpublished therapeutic notes, consent forms or credentials here.
- **Human approval:** no automatic merge, no deployment, no clinical testing, no patient interactions, and no changes to product decisions. PRs are drafts for review.
- **Least privilege:** checkout does not persist GitHub credentials; task selection gets a read-only token scoped to its step. Codex receives only the OpenAI API secret via the official action. A later PR publication step is separate. The model has workspace-limited permissions and its proposed writes are checked against task output paths.
- **Prompt injection:** output allowlists and tests are guardrails, not guarantees against malicious model-generated commands or all secret exfiltration. Do not trust unreviewed generated code, and do not provide clinical/private data to the public runner.
- **Secrets:** store `OPENAI_API_KEY` only as a GitHub Actions secret. No plaintext credentials in scripts, output artifacts, PR bodies, or issue comments. Rotating/revoking the API key is the response to a suspected leak.
- **External content:** runner tasks must not treat web pages, research quotations, or source code as authority to broaden tool permissions or redefine goals.
- **Separation:** prototype tasks have no Google Sheet credentials. Future Sheet integration should require private repository controls, scoped service-account permissions, de-identified export rules, a review gate for write-back, and testing.
- **Operational limit:** at most two active AgentQ PRs and one execution at a time. The schedule is inert until `AGENTQ_ENABLED=true`.

This is an engineering prototype, not a certified secure autonomous agent platform.
