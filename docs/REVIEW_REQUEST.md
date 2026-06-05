# Security & Review Request

This branch requests an external security and review pass for the v0.1 evaluation release.

Changes in this release:
- Windows-only AGY-Shim: Python ACP bridge for Antigravity (agy.exe)
- Rationale for emergency shim due to Gemini CLI -> Antigravity CLI transition
- Permission-bypass gated by AGY_SHIM_ALLOW_BYPASS=1
- CI: syntax checks and guard to ensure AGY_SHIM_ALLOW_BYPASS is not set in CI
- Quickstart, changelog, PR/issue templates, and security contact guidance

Requested reviewers: security, core reviewers for subprocess and CI.

See: CHANGELOG.md and SECURITY.md for details.
