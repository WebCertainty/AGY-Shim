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

- `main` is three commits ahead of `origin/main`.
- v0.1 is only confidently validated with the Copilot shim.
- v0.2 work is paused pending implementation and validation of the prioritized remediation plan.
- The shadow PM status report and prioritized remediation plan has been established at [sam-status.md](file:///D:/CODE-REPO/Tools/AGY-Shim/scratch/project-management/sam-status.md).
- A project-scoped Graphify pilot is installed for Codex and Antigravity. Its generated index is local and ignored by Git.

## Open Issues

- Execute Phase 1 High-Severity fixes (H1-H4) to resolve workspace boundary leaks, path traversal vulnerability, subprocess credential inheritance, and streaming delta mismatch.
- Execute Phase 2 Medium-Severity hardening and Phase 3 polish items.
- Perform independent post-remediation validations via Reese, Maxyi, and Max, and write findings to separate files under `scratch/reviews/`.
- Confirm that Codex and Antigravity actually use Graphify before broad search and file reads.
- Benchmark representative tasks before making Graphify part of the committed project workflow.

## Where We Left Off

- Consolidated all 17 findings from code review, security audit, and documentation review.
- Documented a master remediation plan with owners, dependencies, and acceptance criteria in [sam-status.md](file:///D:/CODE-REPO/Tools/AGY-Shim/scratch/project-management/sam-status.md).
- Ready to assign implementation tickets for Phase 1 High-Severity fixes (H1-H4) once developer resources are assigned.
