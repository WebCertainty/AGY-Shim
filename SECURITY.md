# Security Policy

## Project Status

AGY-Shim is experimental software under active security review. No release is
currently considered production-ready or supported for sensitive workloads.

## Reporting a Vulnerability

Do not open a public issue containing exploit details, credentials, private
conversation data, or other sensitive information.

For a public GitHub repository, use GitHub private vulnerability reporting
when enabled. If private vulnerability reporting is unavailable, email
[hello@webcertainty.com.au](mailto:hello@webcertainty.com.au) with a brief
request to establish a secure reporting channel. Do not include exploit
details or sensitive data in the initial email.

Include:

- the affected commit or version;
- prerequisites and environment details;
- reproducible steps or a proof of concept;
- expected and observed behavior;
- likely impact;
- suggested remediation, if known.

## Security Boundaries

Reviewers should assume that:

- prompts and ACP messages may be malicious;
- the workspace may contain attacker-controlled files;
- executable search paths may be attacker-controlled;
- SQLite conversation data may be malformed or concurrently modified;
- subprocess output may contain sensitive data;
- inherited environment variables may contain credentials;
- multiple clients or sessions may operate concurrently.

The current implementation invokes `agy.exe` with
`--dangerously-skip-permissions` but requires the environment variable
`AGY_SHIM_ALLOW_BYPASS=1` to be explicitly set. Without this variable, the
shim will reject prompt executions with an error. Run it only in an isolated
environment with the minimum credentials and filesystem access necessary.

## Disclosure

Please allow reasonable time to investigate and coordinate a fix before public
disclosure. Security fixes should include regression tests where practical.
