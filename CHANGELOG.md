# Changelog

All notable changes to this project are recorded in this file.

## v0.1 - Initial public evaluation release
- Add Windows-only AGY-Shim: Python-based ACP bridge for Antigravity (agy.exe).
- Rationale: addresses the Gemini CLI -> Antigravity CLI transition (see blog post https://developers.googleblog.com/an-important-update-transitioning-gemini-cli-to-antigravity-cli/)
- Security: permission-bypass mode gated by AGY_SHIM_ALLOW_BYPASS=1; see SECURITY.md and docs/security-model.md
- CI: syntax checks and environment policy
- README, SECURITY, docs and tests added.

