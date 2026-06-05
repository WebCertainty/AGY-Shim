# Contributing

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
python -m py_compile src\agy_shim\main.py tests\test_e2e.py tests\fixtures\mock_agy.py
python tests\test_e2e.py
python -m pip install --no-deps .
```

The default end-to-end test uses the deterministic local mock agent. Any live
Antigravity test must be identified separately because it can consume quota
and modify conversation state.

## Pull Requests

A pull request should include:

- the problem and its impact;
- the chosen approach and alternatives considered;
- security and compatibility implications;
- tests performed and their results;
- manual verification steps;
- documentation changes, when behavior changed.

Do not commit logs, conversation databases, session state, credentials,
generated output, or local environment configuration.

## Review Standard

Reviews should prioritize:

1. security and trust boundaries;
2. protocol correctness;
3. cancellation and subprocess cleanup;
4. concurrency and persistent-state integrity;
5. compatibility with supported Antigravity versions;
6. test evidence and documentation accuracy.
