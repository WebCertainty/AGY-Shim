## graphify

This project supports an optional local knowledge graph at `graphify-out/`.

Rules:
- For a codebase or architecture question, when `graphify-out/graph.json` exists, begin with exactly one `graphify query "<question>" --budget 800` command.
- If Graphify is unavailable or the local graph does not exist, use targeted search and bounded file reads; do not treat that as a project failure.
- Do not search for or load a Graphify `SKILL.md`; this repository intentionally ships only its lean project policy.
- Use at most four source ranges, each no longer than 40 lines. Select up to three ranges from Graphify's reported symbols or locations and reserve the fourth for an immediately adjacent continuation when a relevant function crosses the boundary of an earlier range.
- Read the adjacent continuation only when the earlier range shows that the relevant function continues beyond its boundary. Do not spend the reserved range on an unrelated Graphify result.
- Prioritize concrete implementation functions named in the question or query over generic entry points, files, documentation nodes, and broad symbols such as `main`. When the question asks how an operation is performed, inspect the function that performs that operation before its caller or dispatcher.
- Reserve the adjacent continuation for the highest-priority implementation function unless that function is already complete within its first range.
- Do not use grep, repository-wide search, or whole-file reads during initial discovery. Expand a range or search only when the bounded reads leave a specific question unresolved; state that question before expanding.
- Prefer quoted source expressions and exact file locations over large excerpts.
- Use `graphify path` or `graphify explain` only when the initial query cannot answer a specific relationship or symbol question.
- Dirty graphify-out/ files are expected after hooks or incremental updates; dirty graph files are not a reason to skip graphify. Only skip graphify if the task is about stale or incorrect graph output, or the user explicitly says not to use it.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, refresh with `graphify update . --force --no-cluster` only when Graphify is installed and a local graph is in use.

## Current Status

- `main` is six commits ahead of `origin/main`.
- v0.1 is only confidently validated with the Copilot shim.
- v0.2 security, workspace, streaming, installer, launcher, test, and
  documentation remediation is implemented locally and awaiting final review.
- A project-scoped Graphify pilot is installed for Codex and Antigravity. Its generated index is local and ignored by Git.

## Open Issues

- Complete final post-remediation review of the simplified documentation and
  updated installer.
- Repeat live Clairvoyance authentication, workspace, streaming,
  cancellation, Staff, and nested-recruitment checks from `TESTING.md`.
- Decide whether to tag v0.2.0 after reviewing the final diff and test evidence.
- Push only after explicit user approval.

## Where We Left Off

- Committed the initial v0.2 remediation as `96492a1`.
- Updated `setup_agy_shim.ps1` to validate prerequisites, require explicit
  pre-mutation consent, support `-AgyPath`, and roll back failed changes.
- Simplified onboarding documentation, separated offline automated tests from
  live tests, declared the pytest extra, and categorized the changelog.
- Full deterministic suite last passed with 17 tests.
