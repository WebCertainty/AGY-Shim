# Testing AGY-Shim

This guide validates that AGY-Shim is installed, authenticated, operating in
the correct workspace, and communicating reliably with an ACP host.

The automated suite is host-independent. The live Staff and recruitment tests
are Clairvoyance-specific and optional for users of other ACP hosts.

## Prerequisites

- Windows with Python 3.10 or later.
- An authenticated Antigravity CLI (`agy.exe`).
- AGY-Shim installed for the provider identity being tested.
- `AGY_SHIM_ALLOW_BYPASS=1` set through the approved installation flow.
- Sufficient Antigravity API quota for the complete live test.

Run live tests with a newly created agent after restarting the ACP host. An
agent started before a shim update does not validate the updated process.

## 1. Automated Verification

From the repository root:

```powershell
python -m pip install --no-deps .
python -m py_compile src\agy_shim\main.py tests\test_e2e.py tests\test_security.py tests\fixtures\mock_agy.py
python -m pytest -q
```

Expected result: all tests pass.

Check each wrapper:

```powershell
.\bin\copilot\copilot.cmd --version
.\bin\claude\claude.cmd --version
.\bin\codex\codex.cmd --version
.\bin\gemini\gemini.cmd --version
.\bin\cursor\cursor.cmd --version
.\bin\cursor\cursor-agent.cmd --version
```

The native `.exe` launchers must return the same values. Rebuild them into a
temporary directory to verify provenance without overwriting the checkout:

```powershell
$launcherOutput = Join-Path $env:TEMP "agy-shim-launchers"
Remove-Item $launcherOutput -Recurse -Force -ErrorAction SilentlyContinue
.\scripts\build_launchers.ps1 -OutputRoot "$launcherOutput\bin" -IncludeRuntime
& "$launcherOutput\bin\copilot\copilot.exe" --version
```

Pass: the rebuilt executable returns the expected provider version and
forwards stdio without opening an additional console window.

Expected output:

| Wrapper | Version |
| --- | --- |
| Copilot | `1.0.59` |
| Claude | `2.1.165` |
| Codex | `0.137.0` |
| Gemini | `0.45.1` |
| Cursor | `1.0.0` |
| Cursor Agent | `1.0.0` |

These values verify wrapper discovery only. They do not prove live
interoperability for every provider identity.

## 2. Fresh-Agent Live Test

Restart the ACP host and create a new AGY-Shim agent in the repository
workspace. Run these prompts sequentially in the same conversation.

### Authentication

```text
Reply with exactly: AUTH_OK
```

Pass: the agent replies `AUTH_OK` without a login or authentication error.

### Workspace

```text
Report your current working directory and the Git repository root. Do not modify any files.
```

Pass: both paths resolve to the intended project workspace.

### File Access

```text
Read pyproject.toml and report only the declared project version.
```

Pass: the agent returns the version declared by the local checkout.

### Multi-Turn Memory

```text
Remember this exact token for the next turn: ORANGE_MANGO_8421. Reply with exactly: READY
```

Then:

```text
What exact token did I ask you to remember? Reply with the token only.
```

Pass: the agent returns `ORANGE_MANGO_8421`.

### Streaming

```text
Write exactly five short paragraphs explaining how AGY-Shim bridges an ACP host to Antigravity. Do not read files, run commands, or modify anything.
```

Pass: content appears progressively, with no repeated prefixes, duplicated
paragraphs, or missing final response.

## 3. Cancellation

Start a long read-only task:

```text
Perform a detailed read-only review of every Markdown file in this repository. Do not modify files. Report each file separately and do not combine sections.
```

Cancel the request while it is running. Then send:

```text
Reply with exactly: CANCEL_RECOVERY_OK
```

Pass:

- The long-running request stops promptly.
- The follow-up returns `CANCEL_RECOVERY_OK`.
- No orphaned `agy.exe` process remains.

## 4. Optional Graphify Test

This test applies only when Graphify has been installed separately. Graphify
is not an AGY-Shim runtime or test dependency. Installation and graph-building
instructions are in [docs/graphify.md](docs/graphify.md).

```text
Run graphify --version and report the output only. Do not modify files.
```

Pass: Graphify reports its installed version.

If Graphify is not installed, record this optional test as `NOT APPLICABLE`;
do not fail AGY-Shim validation.

Graphify is navigation assistance, not authoritative evidence. Conclusions
must still be verified against the referenced source code.

## 5. Clairvoyance Staff Test

This section validates Clairvoyance Staff transport through AGY-Shim.

Ask a newly created AGY-Shim Staff member:

```text
Without using prior conversation context, reply with:
1. Your provider/model identity.
2. Your current working directory.
3. The project version from pyproject.toml.
Do not modify files.
```

Then test Staff memory:

```text
Remember this exact token: DIRECT_STAFF_7319. Reply with exactly: READY
```

```text
Reply with the remembered token only.
```

Pass:

- The Staff member identifies its provider/model.
- It reports the intended workspace and version.
- It returns `DIRECT_STAFF_7319` on the next turn.

## 6. Clairvoyance Nested Recruitment Test

Create the output directory if needed:

```powershell
New-Item -ItemType Directory -Force .\scratch\agent-tests | Out-Null
```

Ask an AGY-Shim Staff member:

```text
Recruit one Engineer to inspect pyproject.toml and CHANGELOG.md. Ask the recruit to determine whether the declared version has a matching changelog entry. The recruit must not modify project files and must write its result to scratch\agent-tests\nested-recruit-result.md. Report the recruit's name and completion status.
```

After the recruit completes:

```text
Read scratch\agent-tests\nested-recruit-result.md and summarize its conclusion in one sentence. Do not modify project files.
```

Pass:

- A visible recruit is created.
- The recruit completes independently.
- The requested result file is written.
- The parent Staff member receives completion and summarizes it accurately.

Nested recruitment is a Clairvoyance feature. Failure here does not
necessarily indicate a defect in the core ACP bridge.

## 7. Post-Test Checks

Confirm:

- No unexpected files were modified.
- No authentication prompt appeared.
- No duplicate streamed output appeared.
- No orphaned `agy.exe` process remains.
- Runtime logs contain lifecycle metadata but no prompt text, credentials,
  personal paths, raw session IDs, or conversation IDs.

Record the host version, wrapper identity, AGY-Shim version, Antigravity
version, test date, and any failed step when reporting an issue.
