# Quickstart and Safe Mode

> **TL;DR:** From the repository root, run the setup wizard, choose the
> Copilot wrapper, explicitly accept the bypass risk, restart the ACP host,
> then run `-Action Verify`.

This page is the short operational reference. For the full onboarding path,
use [README.md](../README.md).

## Prerequisites

- Windows 10 or 11
- Python 3.10 or later
- Antigravity CLI installed and authenticated
- The AGY-Shim repository checked out locally

Graphify is optional and is not required for this workflow.

## Install

```powershell
python -m pip install .
powershell -ExecutionPolicy Bypass -File .\scripts\setup_agy_shim.ps1
```

For Clairvoyance, choose `User` scope and the `copilot` provider. The wizard
will explain the permission-bypass risk and make no environment changes unless
you explicitly type `Y`.

Restart Clairvoyance after a User-scope installation.

## Verify

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup_agy_shim.ps1 -Action Verify
.\bin\copilot\copilot.cmd --version
```

Expected version: `1.0.59`.

## Safe mode

Without `AGY_SHIM_ALLOW_BYPASS=1`, the shim can start but rejects
`session/prompt`. This is intentional: Antigravity cannot display interactive
permission prompts through the headless ACP bridge.

The installer sets the flag only after explicit consent. To inspect behavior
without enabling prompts, start the module directly from the repository root:

```powershell
$env:AGY_PATH = "$env:LOCALAPPDATA\agy\bin\agy.exe"
Remove-Item env:AGY_SHIM_ALLOW_BYPASS -ErrorAction SilentlyContinue
python -m agy_shim.main
```

## Uninstall

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup_agy_shim.ps1 -Action Uninstall -Scope User
```

Restart PowerShell and the ACP host afterward.

## Common failures

| Message or symptom | Resolution |
| --- | --- |
| `Safe-mode active` | Run the setup wizard and explicitly accept the warning |
| `agy.exe` not found | Install Antigravity or pass `-AgyPath` to the installer |
| Wrong provider CLI starts | Run `where.exe copilot` and check PATH precedence |
| Host does not see changes | Restart it after User-scope installation |
| Login prompt or auth error | Authenticate Antigravity itself, not the wrapper |

Do not use a host's provider Sign In, Auth, Update, Reinstall, or Install
controls. The displayed provider is only a compatibility identity.
