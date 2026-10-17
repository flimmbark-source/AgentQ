# Future Google research workbook integration

The canonical Framework Transference workbook exists outside GitHub and is **not connected to this runner**. Do not claim it is synced.

Before enabling direct access:

1. Make the repository private or prove that the exact published outputs are non-sensitive and explicitly approved for public release.
2. Establish a dedicated Google Cloud service identity scoped only to the workbook; do not use a personal all-Drive token. Keep credentials solely in GitHub Actions secrets.
3. Use separate read and write jobs. Extract minimal, de-identified execution-task metadata into short-lived runtime files for the agent; never expose the workbook credential or the complete workbook to Codex.
4. Retain the user's confirmed Decisions as a read-only, versioned snapshot for comparison. Have the agent propose, never directly approve, changes.
5. Write new cited observations/goal proposals through a narrow validator and an explicit review stage, with de-duplication IDs and auditing. Never overwrite user notes or participant reports.
6. Verify behavior against a dummy workbook and run a full cycle before linking the real one.

The initial AgentQ architecture intentionally postpones this integration to avoid overstating what it can do or exposing confidential research.
