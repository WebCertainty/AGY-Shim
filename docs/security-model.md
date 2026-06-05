# Security Model

## Security Objective

Prevent an untrusted ACP request, workspace, subprocess, or conversation record
from escaping the intended workspace boundary, gaining unintended privileges,
exposing secrets, corrupting protocol state, or denying service.

AGY-Shim does not yet claim to meet this objective in production.

## Trust Boundaries

```text
ACP host -> shim parser -> subprocess invocation -> agy.exe
                         -> session-state files
                         -> conversation SQLite database
                         -> logs
```

Inputs crossing these boundaries must be treated as untrusted unless the
deployment explicitly establishes otherwise.

## High-Risk Behaviors

- The shim starts an autonomous agent with workspace access.
- `--dangerously-skip-permissions` may bypass interactive safeguards, gated by the `AGY_SHIM_ALLOW_BYPASS=1` environment variable.
- Child processes inherit the shim's environment by default.
- Executable discovery may be influenced by `AGY_PATH` and `PATH`.
- Wrapper names can shadow legitimate provider executables.
- Host sign-in or update controls can invoke unsupported provider commands,
  install genuine provider CLIs, or change which executable wins on `PATH`.
- Logs contain sanitized lifecycle metadata by default. Future logging changes
  could still reintroduce prompts, paths, subprocess output, or identifiers.
- SQLite/protobuf parsing consumes data outside the shim's control.
- Blocking request handling is mitigated by asynchronous thread dispatch and cancellation handlers.

## Required Review Areas

### Spoofing

- Validate the selected `agy.exe` path and provenance.
- Make compatibility identity visible to users and reviewers.

### Tampering

- Protect session state against concurrent or malicious modification.
- Handle malformed and changing SQLite/protobuf data defensively.
- Treat host-managed provider installation and update actions as configuration
  changes that can replace or bypass the intended shim executable.

### Repudiation

- Record security-relevant lifecycle events without recording sensitive prompt
  content by default.

### Information Disclosure

- Keep credentials, prompt content, raw subprocess output, conversation IDs,
  session IDs, exception messages, command lines, and personal paths out of
  logs. Session and conversation correlation uses truncated SHA-256 hashes.
- Keep generated logs under the ignored `logs/` directory by default. An
  operator-supplied `AGY_SHIM_LOG_FILE` location must have equivalent access
  controls and retention handling.
- Bound log retention and document deletion behavior.

### Denial of Service

- Bound message sizes, subprocess duration, memory use, and log growth.
- Ensure cancellation can execute while prompts are active.

### Elevation of Privilege

- Require explicit opt-in (`AGY_SHIM_ALLOW_BYPASS=1`) for the permission-bypass mode.
- Minimize inherited environment variables and filesystem access.

### Operational Controls

- Do not use host Sign In, Auth, Update, Reinstall, or Install actions for a
  masqueraded provider identity.
- Authenticate and update `agy.exe` through Antigravity's supported process.
- Verify executable resolution with `where.exe <provider>` after installation
  changes or host re-detection.

## Release Gates

- Independent code and security review completed.
- No unresolved Critical or High findings.
- Permission model documented and user-controlled.
- Cancellation and timeout behavior verified.
- Secret and history scans completed.
- Logs bounded and privacy-reviewed.
- Supported Antigravity and ACP versions documented.
