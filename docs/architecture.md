# Architecture

> **TL;DR:** Provider wrappers forward ACP JSON-RPC over standard streams to a
> Python bridge, which starts `agy.exe` in the initialized workspace and reads
> responses from Antigravity's conversation database.

## Purpose

AGY-Shim translates ACP JSON-RPC messages received over standard input into
Antigravity CLI invocations and translates Antigravity output back into ACP
session updates.

The core protocol bridge is intended to be host-independent. The executable
wrappers and provider identities are a separate compatibility layer created
for Clairvoyance discovery. Keeping those concerns separate should allow
future ACP hosts to invoke the core bridge directly or through their own
adapter.

## Components

| Component | Responsibility |
| --- | --- |
| `bin/<provider>/*.exe` launchers | Present native Windows executable names and forward stdio to Python |
| `bin/<provider>/*.cmd` wrappers | Provide shell-compatible fallback entry points and version responses |
| `src/agy_shim/main.py` | ACP framing, dispatch, sessions, subprocesses, and streaming |
| `agy.exe` | Executes prompts and maintains Antigravity conversations |
| Conversation SQLite DB | Supplies incremental response records |
| Session state | Maps ACP session IDs to Antigravity conversation IDs |

## Host Control Boundary

Provider identities exist only for executable discovery and version detection.
Host controls labelled Sign In, Auth, Update, Reinstall, or Install belong to
the genuine provider CLI lifecycle and are outside the AGY-Shim protocol.

Those controls must not be used for a masqueraded identity. They may send
unsupported CLI arguments to the shim or install a genuine provider binary
that changes executable resolution. Antigravity authentication and upgrades
must be managed directly through Antigravity; AGY-Shim upgrades must be managed
through this repository.

## Native Launcher Boundary

Some Windows host discovery paths request a provider executable directly and
do not behave like an interactive shell resolving a `.cmd` file through
`PATHEXT`. Each provider directory therefore includes a small native launcher
compiled from `scripts/launcher.cs`.

The launcher derives the provider identity from its filename, starts
`src/agy_shim/main.py`, avoids opening another console window, forwards
stdin/stdout/stderr as byte streams, and preserves the Python exit code. It
does not parse ACP, read Antigravity databases, or invoke `agy.exe` directly.

The binaries are build outputs rather than independent source. Rebuild them
with `scripts/build_launchers.ps1` and verify their version responses before
release.

## Request Flow

1. The host starts a provider `.exe` launcher or `.cmd` fallback from
   `bin/<provider>/`.
2. The launcher or wrapper starts `src/agy_shim/main.py` with a provider identity.
3. The host sends ACP JSON-RPC requests over standard input.
4. The shim creates or restores session state.
5. For a prompt, the shim starts `agy.exe` for the active workspace.
6. The shim reads response updates from Antigravity's conversation database.
7. Updates are emitted as ACP `session/update` notifications.
8. The shim emits the final JSON-RPC response and persists session progress.

## Protocol Surface

The intended methods are:

- `initialize`
- `session/new`
- `session/load`
- `session/prompt`
- `session/cancel`
- `session/close`

The implementation accepts LSP-style `Content-Length` framing and
newline-delimited JSON. The exact ACP version and compatibility contract must
be confirmed with each target host before claiming support.

Current interoperability evidence covers a simulated ACP client shaped around
Clairvoyance and manual use with Clairvoyance. It does not establish universal
ACP compatibility. A new host requires tests for capability negotiation,
framing, session lifecycle, streaming, cancellation, errors, and concurrency.

## External Coupling

Incremental streaming currently depends on undocumented Antigravity details:

- conversation database location;
- SQLite table and column names;
- step type values;
- protobuf field numbers and encoding;
- CLI arguments and exit behavior.

Changes to Antigravity may therefore break streaming or session continuity
without changing AGY-Shim.

## Unresolved Decisions

- Whether provider masquerading is acceptable for long-term distribution.
- Whether to expose a provider-neutral launcher for ACP hosts that do not use
  Clairvoyance-style provider discovery.
- Whether the shim should be packaged as a dedicated executable.
- Whether Antigravity can expose a supported JSON streaming interface.
- Whether sessions should be workspace-local, user-local, or host-managed.
- What concurrency model is required by each supported ACP host.
