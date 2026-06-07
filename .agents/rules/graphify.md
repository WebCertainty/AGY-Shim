---
trigger: always_on
description: Consult the optional local Graphify index when graphify-out/graph.json exists.
---

## graphify

This project supports an optional local Graphify index at `graphify-out/`.

Rules:
- For a codebase or architecture question, when `graphify-out/graph.json` exists, begin with exactly one `graphify query "<question>" --budget 800` command or one `query_graph` MCP call with an equivalent token budget.
- If Graphify is unavailable or the local graph does not exist, use targeted search and bounded file reads; do not treat that as a project failure.
- Do not search for or load a Graphify `SKILL.md`; this repository intentionally ships only its lean project rule.
- Use at most four source ranges, each no longer than 40 lines. Select up to three ranges from Graphify's reported symbols or locations and reserve the fourth for an immediately adjacent continuation when a relevant function crosses the boundary of an earlier range.
- Read the adjacent continuation only when the earlier range shows that the relevant function continues beyond its boundary. Do not spend the reserved range on an unrelated Graphify result.
- Prioritize concrete implementation functions named in the question or query over generic entry points, files, documentation nodes, and broad symbols such as `main`. When the question asks how an operation is performed, inspect the function that performs that operation before its caller or dispatcher.
- Reserve the adjacent continuation for the highest-priority implementation function unless that function is already complete within its first range.
- Do not use grep, repository-wide search, or whole-file reads during initial discovery. Expand a range or search only when the bounded reads leave a specific question unresolved; state that question before expanding.
- Prefer quoted source expressions and exact file locations over large excerpts.
- Use `graphify path` or `graphify explain` only when the initial query cannot answer a specific relationship or symbol question.
- If graphify-out/wiki/index.md exists, navigate it instead of reading raw files
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context
- After modifying code, refresh with `graphify update . --force --no-cluster` only when Graphify is installed and a local graph is in use.
