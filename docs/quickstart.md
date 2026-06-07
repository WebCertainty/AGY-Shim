# Quickstart and Safe Mode

> **TL;DR:** From the repository root, run the setup wizard, choose the
> Gemini wrapper, explicitly accept the bypass risk, restart the ACP host,
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

Open Command Prompt and replace `YOUR-INSTALL-FOLDER` with an existing
permanent folder, for example `D:\Tools`:

```bat
cd /d "YOUR-INSTALL-FOLDER"
git clone https://github.com/WebCertainty/AGY-Shim.git
cd AGY-Shim
powershell -ExecutionPolicy Bypass -File .\scripts\setup_agy_shim.ps1
```

Keep the cloned repository in place. The launchers execute
`src\agy_shim\main.py` from this checkout, so no Python package installation is
required for normal use.

For Clairvoyance, choose `User` scope and the `gemini` provider. The wizard
will explain the permission-bypass risk and make no environment changes unless
you explicitly type `Y`.

Restart Clairvoyance after a User-scope installation.

## Verify

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup_agy_shim.ps1 -Action Verify
.\bin\gemini\gemini.cmd --version
```

Expected version: `0.45.1`.

## Safe mode

Without `AGY_SHIM_ALLOW_BYPASS=1`, the shim can start but rejects
`session/prompt`. This is intentional: Antigravity cannot display interactive
permission prompts through the headless ACP bridge.

The installer sets the flag only after explicit consent. To inspect behavior
without enabling prompts, start the module directly from the repository root:

```powershell
$env:AGY_PATH = "$env:LOCALAPPDATA\agy\bin\agy.exe"
Remove-Item env:AGY_SHIM_ALLOW_BYPASS -ErrorAction SilentlyContinue
python .\src\agy_shim\main.py
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
| Wrong provider CLI starts | Run `where.exe gemini` and check PATH precedence |
| Host does not see changes | Restart it after User-scope installation |
| Login prompt or auth error | Authenticate Antigravity itself, not the wrapper |

Do not use a host's provider Sign In, Auth, Update, Reinstall, or Install
controls. The displayed provider is only a compatibility identity.
