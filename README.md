# AGY-Shim

AGY-Shim is an experimental Windows bridge that lets an ACP host, currently
tested with Stardock Clairvoyance, run Antigravity (`agy.exe`) through a
provider-compatible command such as `copilot`.

> [!WARNING]
> Prompt execution requires Antigravity's
> `--dangerously-skip-permissions` mode. Use an isolated test workspace with
> minimal credentials. Do not use AGY-Shim for production or sensitive work.

## Quick Start

### Required

- Windows 10 or 11
- Python 3.10 or later
- Antigravity CLI installed and authenticated
- An ACP host; current live evidence is for Stardock Clairvoyance

Graphify is optional. It is not installed with AGY-Shim and is not required
to install, run, package, or test the shim.

### 1. Clone

```powershell
git clone https://github.com/WebCertainty/AGY-Shim.git
cd AGY-Shim
```

Keep the cloned directory in a permanent location. The provider launchers run
the Python source directly from this checkout; AGY-Shim does not need to be
installed as a Python package for normal use.

### 2. Configure the Copilot wrapper

The interactive installer is recommended because it explains the security
opt-in before making changes:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup_agy_shim.ps1
```

Choose:

1. `Install`
2. `User` scope for a desktop-launched host such as Clairvoyance
3. `copilot`
4. Accept the permission-bypass warning only if the test environment is
   appropriate

For a temporary terminal-only test, choose `Session` scope instead.

### 3. Verify

Restart the ACP host after a User-scope installation, then run:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup_agy_shim.ps1 -Action Verify
.\bin\copilot\copilot.cmd --version
```

Expected Copilot compatibility version: `1.0.59`.

Do not use the host application's Sign In, Auth, Update, Reinstall, or Install
controls for the displayed Copilot identity. Authenticate Antigravity
separately using its supported process.

### 4. Test

Install the test extra and run the deterministic offline suite:

```powershell
python -m pip install -e ".[test]"
python -m pytest -q
```

The automated suite uses a local mock agent. It does not call the real
Antigravity service or consume API quota.

For live host, authentication, workspace, streaming, cancellation, Staff, and
nested-recruitment checks, follow [TESTING.md](TESTING.md).

### 5. Uninstall

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup_agy_shim.ps1 -Action Uninstall -Scope User
```

Restart PowerShell and the ACP host afterward.

## Ask Clairvoyance to set it up

From the repository root, give a trusted coding agent this prompt:

```text
Install and validate AGY-Shim for the Copilot wrapper.

1. Confirm this is Windows, Python is 3.10 or later, and Antigravity's agy.exe
   exists and is already authenticated.
2. Explain that prompt execution requires --dangerously-skip-permissions and
   wait for my explicit approval before changing PATH or environment variables.
3. After approval, run:
   powershell -ExecutionPolicy Bypass -File .\scripts\setup_agy_shim.ps1
   Select Install, User scope, and copilot.
4. Run the installer again with -Action Verify.
5. Run .\bin\copilot\copilot.cmd --version and report the result.
6. For optional developer tests, install the test extra with
   python -m pip install -e ".[test]" and run
   python -m pytest -q.
7. Do not use provider Sign In, Auth, Update, Reinstall, or Install controls.
8. Do not modify source files, commit, or push. Report every command and result.
```

The agent must still ask you to accept the permission-bypass risk. A prompt is
not consent.

## What the shim does

```text
ACP host
   |
   | JSON-RPC over stdin/stdout
   v
bin/<provider>/<provider>.exe or .cmd
   |
   v
src/agy_shim/main.py
   |                         |
   | starts agy.exe          | reads responses
   v                         v
Antigravity process     conversation SQLite database
```

The provider names are compatibility identities only. AGY-Shim does not turn
Antigravity into Copilot, Claude, Codex, Gemini, or Cursor.

The native C# launchers exist because some Windows hosts require a real `.exe`
and do not apply shell `.cmd` lookup behavior. They forward standard streams
to the Python bridge and contain no ACP implementation. Rebuild them with:

```powershell
.\scripts\build_launchers.ps1
```

See [docs/architecture.md](docs/architecture.md) for the detailed request and
process lifecycle.

## Compatibility and constraints

- Windows only; WSL, MSYS2, Cygwin, macOS, and Linux are not supported.
- Python 3.10 or later is required.
- Only one prompt may execute at a time; overlapping prompts receive an
  `Agent is busy` error.
- The shim depends on Antigravity's internal conversation database format,
  which may change without notice.
- All wrappers pass deterministic discovery and version tests.
- The automated bridge suite is host-independent and mock-based.
- Copilot has the strongest manual v0.1 evidence.
- Gemini through AGY-Shim has active v0.2 Clairvoyance evidence.
- Claude, Codex, and Cursor require dated live-host validation before
  compatibility should be claimed.

Google has announced that on 18 June 2026 the Gemini CLI will transition to
the Antigravity CLI:
https://developers.googleblog.com/an-important-update-transitioning-gemini-cli-to-antigravity-cli/

AGY-Shim is an independent evaluation project. It is not an official Google,
Stardock, GitHub, OpenAI, Anthropic, Cursor, or Antigravity product.

## Configuration

The installer manages:

- `AGY_PATH`: explicit path to `agy.exe`
- `AGY_SHIM_ALLOW_BYPASS=1`: required opt-in for prompt execution
- the selected `bin/<provider>` directory on `PATH`

An explicit Antigravity path can be supplied:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup_agy_shim.ps1 `
  -Action Install -Scope User -Provider copilot `
  -AgyPath "C:\Path\To\agy.exe"
```

For non-interactive automation, `-Bypass` records the caller's explicit
acceptance of the permission-bypass risk:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup_agy_shim.ps1 `
  -Action Install -Scope User -Provider copilot -Bypass
```

Use this only in controlled automation. The interactive installer is the
recommended user path.

## Troubleshooting

| Symptom | Action |
| --- | --- |
| `Safe-mode active` | Run the installer and explicitly accept the bypass warning |
| `agy.exe` not found | Install/authenticate Antigravity or pass `-AgyPath` |
| Wrong CLI launches | Run `where.exe copilot`; the AGY-Shim path must be first |
| Host still sees old PATH | Restart the host after User-scope changes |
| Authentication prompt | Authenticate `agy.exe` separately; do not authenticate the wrapper identity |
| `Agent is busy` | Wait for or cancel the active prompt before starting another |
| Quota error | Wait for the reported reset time or review Antigravity account limits |

## Documentation

- [Operator testing guide](TESTING.md)
- [Quickstart and safe-mode reference](docs/quickstart.md)
- [Architecture](docs/architecture.md)
- [Security model](docs/security-model.md)
- [Automated test methodology](docs/testing.md)
- [Optional Graphify workflow](docs/graphify.md)
- [Contributing](CONTRIBUTING.md)
- [Support policy](SUPPORT.md)
- [Changelog](CHANGELOG.md)

## Security and support

Read [SECURITY.md](SECURITY.md) before enabling prompt execution. Report
vulnerabilities privately as described there.

This project is shared as-is with limited maintenance. See
[SUPPORT.md](SUPPORT.md).

## License

AGY-Shim is available under the [MIT License](LICENSE). Third-party
acknowledgements are in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
