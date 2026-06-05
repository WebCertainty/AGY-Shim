# AGY-Shim for Stardock Clairvoyance

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
- inherited environment variables and credentials;
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

The host-independent surface includes JSON-RPC over standard input/output,
session lifecycle methods, streaming updates, and cancellation. The
Clairvoyance compatibility layer includes the provider-named wrappers,
provider version interception, executable discovery assumptions, and the
workspace behavior exercised by the current tests.

Support for another ACP host must be established with host-specific
interoperability tests, including initialization negotiation, framing, session
lifecycle, cancellation, error responses, and concurrent requests.

## Architecture

```text
Clairvoyance or ACP client
          |
          | JSON-RPC 2.0 over stdio
          v
Provider wrapper (bin/*.cmd)
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

More detail is in [docs/architecture.md](docs/architecture.md).

## Requirements

- Windows (AGY-Shim is Windows-only and enforces this check on startup)
- Python 3.10 or later
- Antigravity CLI installed and authenticated
- An ACP-compatible host; currently tested with
  [Stardock Clairvoyance](https://www.clairvoyanceai.com)

### Environment Variables

* **`AGY_SHIM_ALLOW_BYPASS`**: Must be set exactly to `1` to run prompt execution. Without it, the shim operates in safe-mode and rejects all prompt requests.
* **`AGY_PATH`**: Explicit path to the `agy.exe` executable (optional).

The shim searches for `agy.exe` using:

1. `AGY_PATH`
2. the system `PATH`
3. `%LOCALAPPDATA%\agy\bin\agy.exe`
4. `%USERPROFILE%\AppData\Local\agy\bin\agy.exe`

## Installation

Clone the repository and add its `bin` directory to `PATH` only in an isolated
review environment.

```powershell
git clone https://github.com/OWNER/agy-shim.git
cd agy-shim
$env:AGY_PATH = "$env:LOCALAPPDATA\agy\bin\agy.exe"
$env:AGY_SHIM_ALLOW_BYPASS = "1"
$env:PATH = "$PWD\bin;$env:PATH"
```

Do not place the repository ahead of genuine provider CLIs in a production
`PATH` without understanding the executable-shadowing implications.

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
2. run `where.exe <provider>` (for example, `where.exe copilot`);
3. ensure this repository's `bin` directory is the executable selected for the
   intended shim identity;
4. restore the required `PATH` ordering if another CLI now takes precedence;
5. restart the host and run its detection again;
6. verify the wrapper with `.\bin\<provider>.cmd --version`.

## Usage

The wrappers currently supported are:

- `claude.cmd`
- `codex.cmd`
- `copilot.cmd`
- `cursor.cmd`
- `gemini.cmd`

Check compatibility version output:

```powershell
.\bin\codex.cmd --version
```

An ACP host starts a wrapper and communicates with it over standard input and
output. The shim is not designed as an interactive terminal application.

## Testing

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

See [docs/testing.md](docs/testing.md) for the intended verification matrix.

## Security

This tool launches an autonomous subprocess with workspace access. The current
implementation passes `--dangerously-skip-permissions` to `agy.exe`; this is a
material security decision, not a convenience flag.

Do not use AGY-Shim with sensitive repositories or credentials until the
security review is complete. Report vulnerabilities according to
[SECURITY.md](SECURITY.md).

## Documentation

- [Architecture](docs/architecture.md)
- [Security model](docs/security-model.md)
- [Testing](docs/testing.md)
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
