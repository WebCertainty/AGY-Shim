# AGY-Shim for Stardock Clairvoyance

> WARNING: Google has announced that on 18 June 2026 the Gemini CLI will transition to the Antigravity CLI.
> See: https://developers.googleblog.com/an-important-update-transitioning-gemini-cli-to-antigravity-cli/
>
> This repository provides an experimental Windows-only shim to bridge Antigravity (agy.exe) to ACP hosts for short-term evaluation. See the Rationale and Security sections below before using.

## Major Updates (Version 0.2.0)

- **Path Backslash & Escape Fixes**: Standardized character escaping for Windows paths (`\` and `\\`) and Python double underscores (`__`) inside agent outputs so they render correctly in Stardock Clairvoyance without formatting loss or markdown breakage.
- **Provider Wrapper Isolation**: Relocated provider wrappers (e.g. `cursor`, `gemini`, etc.) to individual `bin/<provider>/` subdirectories to prevent PATH conflicts or shadowing other genuine CLIs on the system.
- **Improved Installation Script**: Completely rewrote `setup_agy_shim.ps1` to support automated/interactive installs with conflict detection, session vs permanent scope configuration, status verification (`-Action Verify`), and complete rollback (`-Action Uninstall`).

AGY-Shim is an experimental Windows bridge that exposes the Antigravity CLI
(`agy.exe`) through an Agent Client Protocol (ACP) JSON-RPC interface.

The protocol core is designed to work with ACP-compatible hosts generally.
The provider wrappers, discovery behavior, version responses, and current
end-to-end validation are tailored to Stardock Clairvoyance. Compatibility
with other ACP hosts has not yet been verified.

It is intended for technical evaluation and review. It is not an official
Stardock, Google, Anthropic, OpenAI, GitHub, Cursor, or Antigravity product.

## Status

**Maturity:** Experimental, externally reviewed, limited maintenance.

The core bridge has demonstrated initialization, session creation, streamed
responses, and multi-turn conversation continuity. The current implementation
and security model are documented for evaluation but are not approved for
production or sensitive workloads.

Known review areas include:

- subprocess lifecycle and cancellation;
- use of `--dangerously-skip-permissions`;
- child-process environment compatibility after credential filtering;
- executable discovery and provider masquerading;
- reliance on Antigravity's internal SQLite and protobuf formats;
- log retention and sensitive-data handling;
- concurrent ACP requests and sessions.

See [SECURITY.md](SECURITY.md) and [docs/review-handoff.md](docs/review-handoff.md).

This project is maintained primarily for the author's own use and shared
as-is. See [SUPPORT.md](SUPPORT.md) for maintenance and support expectations.

Generated privacy-safe runtime events are written to
`logs/gemini_shim.log` by default. The directory is excluded from Git.

## Compatibility

AGY-Shim should currently be described as **an experimental ACP bridge for
Antigravity, tested with Clairvoyance**, rather than a universally compatible
ACP implementation.

**Provider evidence (v0.2.0):**
* All five primary wrappers pass version-detection checks.
* The deterministic test harness validates the shared ACP bridge, not live host interoperability for each provider identity.
* Copilot has the strongest manual v0.1 evidence. Gemini/AGY-Shim is under active evaluation; Claude, Codex, and Cursor require dated host-specific validation before compatibility is claimed.

The host-independent surface includes JSON-RPC over standard input/output,
session lifecycle methods, streaming updates, and cancellation. The
Clairvoyance compatibility layer includes the provider-named wrappers,
provider version interception, executable discovery assumptions, and the
workspace behavior exercised by the current tests.

Support for another ACP host must be established with host-specific
interoperability tests, including initialization negotiation, framing, session
lifecycle, cancellation, error responses, and concurrent requests.

## Rationale

Google has announced that on 18 June 2026 the Gemini CLI will transition to the
Antigravity CLI (https://developers.googleblog.com/an-important-update-transitioning-gemini-cli-to-antigravity-cli/), and Antigravity does not yet offer a native
ACP integration. This creates an immediate compatibility gap for Gemini
subscribers who rely on third‑party harnesses (for example, Clairvoyance by
Stardock). To provide a pragmatic, short-term path forward, Antigravity 2.0
and Clairvoyance agents (Codex and Gemini) were used to develop this
Windows-only Python shim that lets agy.exe masquerade as a recognized
provider CLI. It has been tested against Clairvoyance's cloud detection
(masquerading as "Copilot CLI").

During development, Antigravity and Codex token usage was exhausted; an
AGY-SHIM agent was used to perform additional code reviews, publishing,
and verification tasks (including gstack /cso and /review skill checks), and
final reviews were completed using Antigravity (outside Clairvoyance), and
within Clairvoyance using Codex and Gemini agents, with a last-pass review by
the AGY-SHIM agent.

This implementation is intentionally limited (Windows-only, review-only)
and intended for evaluation rather than production deployment. See SECURITY.md
and docs/security-model.md for the security rationale and required opt-ins.

## Architecture

```text
Clairvoyance or ACP client
          |
          | JSON-RPC 2.0 over stdio
          v
Provider wrapper (bin/<provider>/<provider>.cmd)
          |
          v
src/agy_shim/main.py
     |              |
     | starts       | polls read-only
     v              v
  agy.exe      Antigravity conversation SQLite DB
     |
     v
Antigravity agent runtime
```

The provider wrappers allow host applications that discover known CLI names to
start the same shim. Provider names and version output are compatibility
identities only; they do not turn Antigravity into those products.

Each provider directory also contains a native `.exe` launcher. Some Windows
host discovery paths resolve a provider specifically as an executable rather
than applying interactive-shell `.cmd` lookup rules. The C# launcher provides
that native entry point, starts the Python bridge without opening another
console window, forwards stdin/stdout/stderr as byte streams, and returns the
Python process exit code. It contains no ACP or Antigravity implementation.

The launcher source is [scripts/launcher.cs](scripts/launcher.cs). Rebuild all
provider executables with:

```powershell
.\scripts\build_launchers.ps1
```

More detail is in [docs/architecture.md](docs/architecture.md).

## Requirements

- Windows (AGY-Shim is Windows-only and enforces this check on startup)
- Python 3.10 or later
- Antigravity CLI (`agy.exe`) for live prompt execution
- Antigravity CLI installed and authenticated
- An ACP-compatible host; currently tested with
  [Stardock Clairvoyance](https://www.clairvoyanceai.com)

Graphify is an optional developer tool. It is not required to install
or run AGY-Shim. See [docs/graphify.md](docs/graphify.md) for the separate
installation and local-index workflow.

### Environment Variables

* **`AGY_SHIM_ALLOW_BYPASS`**: Must be set exactly to `1` to run prompt execution. Without it, the shim operates in safe-mode and rejects all prompt requests.
* **`AGY_PATH`**: Explicit path to the `agy.exe` executable (optional).

The shim searches for `agy.exe` using:

1. `AGY_PATH`
2. the system `PATH`
3. `%LOCALAPPDATA%\agy\bin\agy.exe`
4. `%USERPROFILE%\AppData\Local\agy\bin\agy.exe`

### Recommended: Automated Installation Script (Recommended)

A PowerShell helper script is available at `scripts/setup_agy_shim.ps1` to automatically configure, verify, and uninstall the shim in both User (permanent) and Session (temporary) scopes. It isolates each provider wrapper in its own directory to prevent shadowing genuine CLIs you have installed.

> [!WARNING]
> Use ONLY in isolated test VMs or ephemeral accounts. Do NOT enable `AGY_SHIM_ALLOW_BYPASS` on production or sensitive machines. Inspect the script before running; verify the `agy.exe` path and that prepending the repo's provider bin directory to your PATH is acceptable in your environment.

#### Usage:
- **Interactive Setup Wizard (Recommended)**:
  Running the script without parameters launches a step-by-step interactive wizard. It will guide you through selecting the action (Install, Verify, Uninstall), scope (Permanent/User, Temporary/Session), provider identity (detecting and warning about conflicts), and the required permission bypass security opt-in.
  ```powershell
  powershell -ExecutionPolicy Bypass -File .\scripts\setup_agy_shim.ps1
  ```
- **Silent/Bypass Permanent Install** (non-interactive / scriptable, e.g. for `cursor`):
  ```powershell
  powershell -ExecutionPolicy Bypass -File .\scripts\setup_agy_shim.ps1 -Action Install -Scope User -Provider cursor -Bypass
  ```
- **Status Verification**:
  Verifies environment variables and PATH precedence for all shimmable providers.
  ```powershell
  powershell -ExecutionPolicy Bypass -File .\scripts\setup_agy_shim.ps1 -Action Verify
  ```
- **Complete Uninstall (Rollback)**:
  Cleanly removes all AGY-Shim provider directories from your PATH and deletes environment variables from both User registry and the current session.
  ```powershell
  powershell -ExecutionPolicy Bypass -File .\scripts\setup_agy_shim.ps1 -Action Uninstall -Scope User
  ```

---

### Alternative: Manual Configuration

If you prefer to configure the shim manually, follow the options below. **Note: You must target the specific provider-specific subfolder (e.g., `bin/cursor`) to avoid shadowing other genuine CLIs on your system.**

#### Option A: Temporary PowerShell Session PATH (for testing/CLI-only)

This sets the variables only in the current PowerShell terminal session. Replace `cursor` with your chosen provider wrapper.

```powershell
$env:AGY_PATH = "$env:LOCALAPPDATA\agy\bin\agy.exe"
$env:AGY_SHIM_ALLOW_BYPASS = "1"
$env:PATH = "$PWD\bin\cursor;$env:PATH"
```

#### Option B: Permanent User PATH (required for GUI hosts like Clairvoyance)

If you launch Clairvoyance from the desktop, Start Menu, or outside the temporary PowerShell window, it inherits your permanent User environment variables rather than temporary session ones.

1. **Prepend the provider-specific `bin` subfolder to your permanent User `PATH`:**
   ```powershell
   $provider = "cursor" # <-- Replace with the provider you want to shim (e.g., cursor, gemini, copilot)
   $shimBin = "C:\Path\To\agy-shim\bin\$provider" # <-- Replace with your actual absolute path
   $oldPath = [Environment]::GetEnvironmentVariable("Path", "User")
   if ($oldPath -notlike "*$shimBin*") {
       [Environment]::SetEnvironmentVariable("Path", "$shimBin;$oldPath", "User")
   }
   ```
2. **Set the bypass flag permanently:**
   ```powershell
   [Environment]::SetEnvironmentVariable("AGY_SHIM_ALLOW_BYPASS", "1", "User")
   ```
3. **Restart your GUI host application** (or any active terminal) for the new environment variables to take effect.

#### Manual Verification (Run in a new PowerShell window)

To verify that the permanent changes were applied correctly before running Clairvoyance, open a new PowerShell window and run:

```powershell
# 1. Confirm that the shim wrapper is detected first on your PATH
where.exe cursor

# 2. Confirm that the bypass environment variable is set
$env:AGY_SHIM_ALLOW_BYPASS
```

*Expected output:*
- The `where.exe` command should list the path to the shim's provider-specific folder first (e.g., `C:\Path\To\agy-shim\bin\cursor\cursor.exe` or `.cmd`).
- The `$env:AGY_SHIM_ALLOW_BYPASS` command should print `1`.

#### Manual Rollback (To undo these changes permanently)

If you need to remove the shim and restore your previous configuration, open a PowerShell window and run:

```powershell
# 1. Remove the shim bin folder from your permanent User PATH
$provider = "cursor"
$shimBin = "C:\Path\To\agy-shim\bin\$provider"
$oldPath = [Environment]::GetEnvironmentVariable("Path", "User")
$newPath = ($oldPath -split ";" | Where-Object { $_ -ne $shimBin -and $_ -ne "" }) -join ";"
[Environment]::SetEnvironmentVariable("Path", $newPath, "User")

# 2. Remove the bypass environment variable
[Environment]::SetEnvironmentVariable("AGY_SHIM_ALLOW_BYPASS", $null, "User")
```

Do not place the repository ahead of genuine provider CLIs in a production
PATH without understanding the executable-shadowing implications.


### Important: Do Not Use Host Sign-In or Update Controls

> **After AGY-Shim is detected, do not click the host application's Sign In,
> Auth, Update, Reinstall, or Install controls for the provider identity shown.**

The wrappers identify themselves as Copilot, Claude, Codex, Gemini, or Cursor
only so a host can discover and launch the ACP bridge. They are not those
provider CLIs, and their authentication and update flows do not apply to
AGY-Shim.

Using a host's built-in provider controls may:

- launch an unsupported authentication command against the shim;
- install or update the genuine provider CLI;
- replace or take precedence over the shim's wrapper on `PATH`;
- cause the host to launch the wrong executable on its next detection pass.

Authenticate and update the **Antigravity CLI (`agy.exe`) separately**, using
Antigravity's own supported process. Update AGY-Shim only by updating this
repository.

If a provider control was used accidentally:

1. close the ACP host;
2. run `where.exe copilot`;
3. ensure this repository's `bin` directory is the executable selected for the
   intended shim identity;
4. restore the required `PATH` ordering if another CLI now takes precedence;
5. restart the host and run its detection again;
6. verify the wrapper with `.\bin\copilot\copilot.cmd --version`.

## Usage

The wrappers currently supported are:

- `bin/claude/claude.exe` and `claude.cmd`
- `bin/codex/codex.exe` and `codex.cmd`
- `bin/copilot/copilot.exe` and `copilot.cmd`
- `bin/cursor/cursor.exe`, `cursor-agent.exe`, and their `.cmd` fallbacks
- `bin/gemini/gemini.exe` and `gemini.cmd`

Check compatibility version output:

```powershell
.\bin\copilot\copilot.cmd --version
```

An ACP host starts a wrapper and communicates with it over standard input and
output. The shim is not designed as an interactive terminal application.

## Testing

See [TESTING.md](TESTING.md) for the complete automated and live validation
regimen, including fresh-agent, cancellation, Clairvoyance Staff, and nested
recruitment tests.

Graphify is not installed by AGY-Shim. Graphify-assisted testing is optional
and requires the separate setup documented in
[docs/graphify.md](docs/graphify.md).

Syntax validation:

```powershell
python -m py_compile src\agy_shim\main.py tests\test_e2e.py tests\fixtures\mock_agy.py
```

Live end-to-end test:

```powershell
python tests\test_e2e.py
```

The live test invokes the installed Antigravity agent and may consume model
quota, modify its conversation store, and exercise autonomous permissions.
Run it only in an appropriate test workspace.

See [scripts/setup_agy_shim.ps1](scripts/setup_agy_shim.ps1) for the helper script and verification steps.


See [docs/testing.md](docs/testing.md) for the intended verification matrix.

## Security

This tool launches an autonomous subprocess with workspace access. The current
implementation passes `--dangerously-skip-permissions` to `agy.exe` but requires the
environment variable `AGY_SHIM_ALLOW_BYPASS=1` to be explicitly set. This is a
material security decision, not a convenience flag.

Do not use AGY-Shim with sensitive repositories or credentials until the
security review is complete. Report vulnerabilities according to
[SECURITY.md](SECURITY.md).

## Documentation

- [Architecture](docs/architecture.md)
- [Security model](docs/security-model.md)
- [Testing](docs/testing.md)
- [Optional Graphify integration](docs/graphify.md)
- [Review handoff](docs/review-handoff.md)
- [Completed code review](docs/reviews/code-review-report.md)
- [Implementation plan](docs/implementation-plan.md)
- [Contributing](CONTRIBUTING.md)
- [Support policy](SUPPORT.md)

## License

AGY-Shim is available under the [MIT License](LICENSE).

The original idea and architecture were inspired in part by the
[OpenAB project](https://github.com/openabdev/openab). No OpenAB source code is
included in the distributable working tree.

The local review-method documents
[`cso-checklist.md`](docs/reviews/cso-checklist.md) and
[`engineering-checklist.md`](docs/reviews/engineering-checklist.md) were
adapted from ideas in [gstack](https://github.com/garrytan/gstack), which is
MIT-licensed.
See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
