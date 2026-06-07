# Changelog

All notable changes to this project are recorded in this file.

## v0.2.0 - Stability, provider isolation, and security hardening
- **Real-Time Quota Detection**: Added active log scanning to detect `RESOURCE_EXHAUSTED` (429) errors in real-time, sending immediate warnings to the UI and cleanly terminating the subprocess.
- **Session Resumption Support**: Persist conversation ID mapping to `sessions.json` on failures, allowing users to resume conversations once rate limits reset or overage is enabled.
- **Path Backslash & Escape Fixes**: Standardized character escaping for Windows paths (`\`) and Python double underscores (`__`) in agent outputs to prevent markdown rendering errors in Stardock Clairvoyance.
- **Provider Wrapper Isolation**: Relocated provider wrappers (e.g. `cursor`, `gemini`, etc.) to individual `bin/<provider>/` subdirectories to prevent PATH conflicts or shadowing other genuine CLIs on the system.
- **Improved Installation Script**: Completely rewrote `setup_agy_shim.ps1` to support automated/interactive installs with conflict detection, session vs permanent scope configuration, status verification (`-Action Verify`), and complete rollback (`-Action Uninstall`).
- **Workspace Boundary Fix**: Propagate the ACP initialized workspace to `agy.exe` for both `cwd` and `--add-dir`.
- **Credential Isolation**: Filter the child-process environment rather than passing parent credentials to `agy.exe`.
- **Input and State Hardening**: Reject unsafe conversation identifiers and oversized LSP messages.
- **Streaming Safety**: Avoid re-emitting cumulative response text after a polling mismatch.
- **Optional Graphify Policy**: Add lean Codex and Antigravity navigation rules plus separate installation documentation without vendoring Graphify or generated graphs.

## v0.1 - Initial public evaluation release
- Add Windows-only AGY-Shim: Python-based ACP bridge for Antigravity (agy.exe).
- Rationale: addresses the Gemini CLI -> Antigravity CLI transition (see blog post https://developers.googleblog.com/an-important-update-transitioning-gemini-cli-to-antigravity-cli/)
- Security: permission-bypass mode gated by AGY_SHIM_ALLOW_BYPASS=1; see SECURITY.md and docs/security-model.md
- CI: syntax checks and environment policy
- README, SECURITY, docs and tests added.

