# Review Handoff

## Review Goal

Determine whether AGY-Shim is suitable for further development and integration
with Clairvoyance, identify the changes required before production use or
public distribution, and assess how cleanly the host-independent ACP core is
separated from the Clairvoyance compatibility layer.

## Scope

- ACP protocol handling and claimed compatibility
- separation of the general ACP core from Clairvoyance-specific discovery,
  provider identities, and workspace assumptions
- subprocess lifecycle, cancellation, and cleanup
- workspace and filesystem boundaries
- permission and credential handling
- session persistence and concurrency
- SQLite/protobuf parsing resilience
- logging, privacy, and diagnostics
- provider discovery and executable shadowing
- tests, documentation, packaging, and licensing

## Out of Scope

- Security guarantees of the Antigravity service itself
- Endorsement of provider masquerading by third-party vendors
- Production support commitments

## Requested Reviewer Output

For each finding, provide:

- severity and confidence;
- affected file and line;
- concrete failure or exploit scenario;
- impact and prerequisites;
- recommended remediation;
- suggested regression test.

Please distinguish verified behavior from inference.

Treat Clairvoyance as the only currently tested ACP host. Do not infer general
ACP compatibility from the simulated client tests. Any broader compatibility
claim requires host-specific interoperability or conformance evidence.

## Current Evidence

See [reviews/code-review-report.md](reviews/code-review-report.md) for the
completed review. Reviewers must verify its claims against the target commit
because paths and implementation details may have changed after the report was
written.

- **Publication Commit:** Verify the current `HEAD`; the completed review
  predates the cleaned single-commit publication history.
- **Current Test Results:** Deterministic E2E tests pass on Windows using raw
  JSON and LSP Content-Length framing. The mock agent avoids external
  credentials, model quota, and live conversation changes.
- **Known Unresolved Risks:** Unconditional permission bypass, reliance on
  undocumented Antigravity SQLite/protobuf formats, and unverified
  interoperability with ACP hosts other than Clairvoyance.
- **Supported Environment:** Windows 10/11 and Python 3.10 or later.
  Antigravity compatibility must be verified against the installed CLI
  version.
- **Named Contact for Technical/Security Questions:** WebCertainty
  (`hello@webcertainty.com.au`)
