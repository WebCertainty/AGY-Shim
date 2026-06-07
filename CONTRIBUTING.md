# Contributing

> **TL;DR:** Use Windows and Python 3.10+, install `.[test]`, keep changes
> focused, run `python -m pytest -q`, and rebuild launchers when
> `scripts/launcher.cs` changes. Graphify is optional.

AGY-Shim is an experimental, limited-maintenance project. Small, focused
changes with clear evidence are preferred over broad refactors.

Reviewing an issue or pull request is not guaranteed. See
[SUPPORT.md](SUPPORT.md) for the project's maintenance expectations.

## Before Opening a Change

1. Read [README.md](README.md), [SECURITY.md](SECURITY.md), and
   [docs/architecture.md](docs/architecture.md).
2. Check existing issues and review notes.
3. For security findings, follow the private process in
   [SECURITY.md](SECURITY.md).
4. Explain any assumptions about undocumented Antigravity behavior.

## Development

Create a branch from `main`:

```powershell
git switch -c type/short-description
```

Suggested prefixes include `fix/`, `feature/`, `docs/`, `test/`, and
`security/`.

Before submitting:

```powershell
python -m pip install -e ".[test]"
python -m py_compile src\agy_shim\main.py tests\test_e2e.py tests\fixtures\mock_agy.py
python -m pytest -q
```

When `scripts/launcher.cs` changes, rebuild the provider executables with
`scripts/build_launchers.ps1`, verify both `.exe` and `.cmd` version output,
and include the source change and rebuilt binaries in the same pull request.

The default end-to-end test uses the deterministic local mock agent. Any live
Antigravity test must be identified separately because it can consume quota
and modify conversation state.

### Optional Graphify Workflow

Graphify is optional and is not installed with AGY-Shim. Contributors who want
graph-assisted navigation should follow [docs/graphify.md](docs/graphify.md).
Do not commit `graphify-out/`, generated Graphify skills, caches, reports, MCP
configuration, or `.git/hooks`.

If Graphify is not installed, use targeted search and bounded source reads.
Missing Graphify must not block normal development or pull-request checks.

## Pull Requests

A pull request should include:

- the problem and its impact;
- the chosen approach and alternatives considered;
- security and compatibility implications;
- tests performed and their results;
- manual verification steps;
- documentation changes, when behavior changed.

Do not commit logs, conversation databases, session state, credentials,
generated output, local environment configuration, or generated Graphify
artifacts.

## Review Standard

Reviews should prioritize:

1. security and trust boundaries;
2. protocol correctness;
3. cancellation and subprocess cleanup;
4. concurrency and persistent-state integrity;
5. compatibility with supported Antigravity versions;
6. test evidence and documentation accuracy.
