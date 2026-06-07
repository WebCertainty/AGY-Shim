# Quickstart (Safe-mode vs Opt-in)

This quickstart shows the minimum steps to run AGY-Shim in safe-mode (default) and to opt-in for permission-bypass.

Graphify is not required for either mode. It is an optional developer tool
with a separate installation workflow documented in
[graphify.md](graphify.md).

## Safe-mode (recommended for evaluation)

Safe-mode prevents any prompt execution that would bypass interactive permissions checks. By default, AGY-Shim rejects session/prompt calls unless explicitly enabled.

Start the shim (example):

```powershell
$env:AGY_PATH = "$env:LOCALAPPDATA\agy\bin\agy.exe"
python -m src.agy_shim.main
```

Attempting to run a prompt will return an error unless AGY_SHIM_ALLOW_BYPASS is set.

## Opt-in (permission-bypass)

To allow prompt execution that passes `--dangerously-skip-permissions` to agy.exe, explicitly set the opt-in variable in an isolated test workspace only:

```powershell
$env:AGY_SHIM_ALLOW_BYPASS = "1"
python -m src.agy_shim.main
```

Notes and safety:
- Do not enable AGY_SHIM_ALLOW_BYPASS on systems with sensitive data or broad credentials.
- Prefer ephemeral VMs or isolated test accounts.
- The shim logs to `logs/gemini_shim.log` by default; do not expose logs containing sensitive material.
- Cancellation is supported by asynchronous dispatch; ensure callers test cancellation paths in integration.

