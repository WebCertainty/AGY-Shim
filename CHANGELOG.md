# Changelog

All notable changes to this project are recorded in this file.

## v0.2.0 - Stability & Reliability Release
- **Real-Time Quota Detection**: Added active log scanning to detect `RESOURCE_EXHAUSTED` (429) errors in real-time, sending immediate warnings to the UI and cleanly terminating the subprocess.
- **Session Resumption Support**: Persist conversation ID mapping to `sessions.json` on failures, allowing users to resume conversations once rate limits reset or overage is enabled.
- **Path Backslash & Escape Fixes**: Standardized character escaping for Windows paths (`\`) and Python double underscores (`__`) in agent outputs to prevent markdown rendering errors in Stardock Clairvoyance.
- **Provider Wrapper Isolation**: Relocated provider wrappers (e.g. `cursor`, `gemini`, etc.) to individual `bin/<provider>/` subdirectories to prevent PATH conflicts or shadowing other genuine CLIs on the system.
- **Improved Installation Script**: Completely rewrote `setup_agy_shim.ps1` to support automated/interactive installs with conflict detection, session vs permanent scope configuration, status verification (`-Action Verify`), and complete rollback (`-Action Uninstall`).

## v0.1 - Initial public evaluation release
- Add Windows-only AGY-Shim: Python-based ACP bridge for Antigravity (agy.exe).
- Rationale: addresses the Gemini CLI -> Antigravity CLI transition (see blog post https://developers.googleblog.com/an-important-update-transitioning-gemini-cli-to-antigravity-cli/)
- Security: permission-bypass mode gated by AGY_SHIM_ALLOW_BYPASS=1; see SECURITY.md and docs/security-model.md
- CI: syntax checks and environment policy
- README, SECURITY, docs and tests added.

