# Optional Graphify Integration

Graphify is an optional developer tool used to reduce broad repository
searches and large file reads by coding agents. It is not required to install,
run, package, or test AGY-Shim.

AGY-Shim does not declare Graphify as a Python package dependency. Installing
AGY-Shim does not install Graphify, and AGY-Shim does not invoke Graphify at
runtime.

## Shipped Integration Files

The repository ships only the project-specific policy and scan configuration:

- `AGENTS.md` for Codex and compatible coding agents;
- `.agents/rules/graphify.md` for Antigravity;
- `.graphifyignore` for the local graph scan scope.

The repository does not vendor Graphify skills, hooks, source code, generated
graphs, caches, reports, or MCP configuration.

## Install Graphify

Install `uv` if it is not already available:

```powershell
winget install --id astral-sh.uv --exact
```

Install the version validated by this project as an isolated user tool:

```powershell
uv tool install "graphifyy==0.8.34"
```

The Python package name is `graphifyy`; the command is `graphify`.
The optional `[mcp]` extra is not required by the shipped CLI-based policy.

Open a new terminal after installation if `graphify` is not immediately found
on `PATH`. Verify:

```powershell
graphify --version
```

The project policy was validated with Graphify `0.8.34`. Later versions may
change query ranking, generated hooks, or integration templates and should be
retested before being treated as equivalent. Upgrade explicitly after
validation:

```powershell
uv tool install --upgrade "graphifyy==<VERSION>"
```

## Build the Local Graph

From the AGY-Shim repository root:

```powershell
graphify update . --force --no-cluster
```

This creates `graphify-out/`, which is local and ignored by Git. Do not commit
the generated graph.

The `.graphifyignore` file excludes generated files, binaries, logs, scratch
work, agent configuration, and historical session material.

## Query Policy

For codebase questions, the shipped agent rules use this pattern:

```powershell
graphify query "<question or relevant symbols>" --budget 800
```

Agents should inspect named implementation functions before generic entry
points, read no more than three initial ranges of 40 lines, and reserve one
adjacent continuation for the highest-priority function.

Graphify output is navigation guidance. Every conclusion must be verified
against the referenced source.

## Automatic Refresh

Graphify can install local Git hooks:

```powershell
graphify hook install
graphify hook status
```

These hooks live under `.git/hooks`, are not committed, and update the graph
after commits and branch switches. Developers who do not install the hooks
must refresh manually after code changes:

```powershell
graphify update . --force --no-cluster
```

## Codex and Antigravity

Do not run `graphify install --project` for this repository unless you
intentionally want to replace or merge the shipped policies. That command
generates large vendor-managed skill directories and hook configuration that
the lean repository integration deliberately excludes.

Codex reads the shipped `AGENTS.md`. Antigravity reads the shipped
`.agents/rules/graphify.md`. Both can call the globally installed `graphify`
command without vendored skills.

## Without Graphify

Graphify is optional. If it is not installed or `graphify-out/graph.json` does
not exist:

- AGY-Shim continues to build, test, install, and run normally;
- coding agents should use targeted repository search and bounded file reads;
- Graphify-specific tests should be skipped and recorded as not applicable.

Do not treat a missing Graphify installation as an AGY-Shim runtime failure.
