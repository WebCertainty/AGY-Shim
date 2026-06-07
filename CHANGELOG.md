# Changelog

All notable changes to this project are recorded here.

## v0.2.0 - Stability, isolation, and security hardening

### Features

- Added real-time Antigravity quota detection for recent
  `RESOURCE_EXHAUSTED` errors, including reset-time reporting.
- Added session resumption by persisting ACP-to-Antigravity conversation
  mappings after recoverable failures.
- Added native Windows `.exe` launchers for hosts that do not resolve `.cmd`
  wrappers, with a reproducible build script.
- Added Install, Verify, and Uninstall actions for User and Session scopes.

### Bug Fixes

- Propagate the ACP-initialized workspace to `agy.exe` as both its working
  directory and `--add-dir` value.
- Prevent cumulative response text from being re-emitted after a database
  polling prefix mismatch.
- Preserve Windows paths, Markdown escapes, double underscores, code spans,
  and fenced code blocks during streamed output.
- Make automated tests independent of the caller's bypass environment.
- Improve cancellation cleanup and prevent orphaned child processes in tested
  request paths.

### Improvements

- Isolated wrappers under `bin/<provider>/` to reduce collisions with genuine
  provider CLIs.
- Added deterministic wrapper and launcher version checks.
- Added explicit `-AgyPath` support and preservation of existing `AGY_PATH`.
- Validate the selected wrapper and `agy.exe` before modifying the environment.
- Make installer changes transactional with rollback after failure.
- Require affirmative bypass consent before any installation mutation.
- Added clearer PATH precedence and installation-status reporting.

### Security

- Filter the `agy.exe` child environment to avoid passing unrelated parent
  credentials.
- Reject unsafe conversation identifiers before constructing database paths.
- Limit accepted LSP `Content-Length` values to reduce memory and blocking
  risks.
- Keep runtime event logs bounded to approved metadata rather than prompt
  content or command lines.
- Preserve safe mode unless `AGY_SHIM_ALLOW_BYPASS` is exactly `1`.

### Testing

- Expanded deterministic newline and LSP-framed ACP coverage.
- Added workspace propagation, credential filtering, unsafe identifier,
  message-size, streaming restart, path escaping, cancellation, and error
  regression tests.
- Added a user validation guide covering live authentication, workspace,
  streaming, cancellation, Clairvoyance Staff, and nested recruitment.
- Added Windows CI checks for launcher rebuilding and native wrapper execution.

### Documentation

- Reworked the README around a short install, verify, test, and uninstall path.
- Documented the native C# launcher purpose and reproducible build process.
- Added concise dependency, constraint, troubleshooting, and security guidance.
- Added optional Graphify navigation policy without making Graphify a runtime
  or test dependency.
- Added a copy-paste Clairvoyance installation and validation prompt.

### Known Limitations

- Windows only.
- Experimental and not approved for production or sensitive workloads.
- Prompt execution requires Antigravity's
  `--dangerously-skip-permissions` mode.
- Only one prompt executes at a time; overlapping prompts receive a busy error.
- Antigravity's internal SQLite and protobuf formats may change.
- Deterministic tests validate the shared bridge, not live interoperability
  for every provider identity.
- Copilot has the strongest v0.1 live evidence; Gemini through AGY-Shim has
  active v0.2 Clairvoyance evidence. Other identities require dated live-host
  validation.

## v0.1 - Initial public evaluation release

### Features

- Added the Windows Python ACP bridge for Antigravity (`agy.exe`).
- Added Copilot-oriented provider masquerading for Clairvoyance discovery.
- Added initialize, session creation, prompt streaming, persistence,
  cancellation, and basic error handling.

### Security

- Gated autonomous prompt execution behind
  `AGY_SHIM_ALLOW_BYPASS=1`.
- Added the initial security policy and security model.

### Testing and documentation

- Added initial syntax, environment-policy, and deterministic test coverage.
- Added README, support, contributing, security, and architecture documents.
