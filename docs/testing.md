# End-to-End Testing Methodology & Evidence

This document outlines the testing strategy, design of the mock execution environment, and the actual test evidence for the **AGY-Shim** tool in `D:\CODE-REPO\Tools\AGY-Shim`.

---

## 1. Testing Philosophy & Methodology

Relying on live cloud model APIs for automated E2E tests introduces flakiness (due to network latency, OAuth credential expiration, or Google API quota limits like `RESOURCE_EXHAUSTED`). To ensure high-fidelity, deterministic E2E validation, the test suite uses a hybrid approach:

1. **Simulated ACP Client:** The [test_e2e.py](../tests/test_e2e.py) test runner acts as a client host shaped around Stardock Clairvoyance, writing requests to the shim's standard input and asserting on standard output responses and streaming notifications.
2. **Dual Framing Modes:** The runner executes the entire E2E conversation under two separate serialization frameworks:
   - **Newline-Delimited Raw Mode:** Standard line-based JSON-RPC messaging.
   - **LSP Content-Length Mode:** Header-based framing (`Content-Length: ...\r\n\r\n{...}`) matching the LSP standard.
3. **Local Mock Agent Fixture:** Before executing the shim, the test runner sets the `AGY_PATH` environment variable to point to [mock_agy.cmd](../tests/fixtures/mock_agy.cmd). This causes the shim to spawn [mock_agy.py](../tests/fixtures/mock_agy.py) instead of the real `agy.exe`, enabling offline, deterministic verification of SQLite database parsing.

These tests validate the bridge behavior expected by Clairvoyance; they are
not a general ACP conformance suite. Compatibility with another ACP host must
be recorded separately against that host and version.

## Continuous Integration

The GitHub Actions workflow at
[`windows-ci.yml`](../.github/workflows/windows-ci.yml) runs on pushes and pull
requests using Python 3.10 and 3.14 on Windows. It verifies:

- package metadata and wheel construction;
- Python syntax compilation;
- raw-line and LSP-framed deterministic E2E tests;
- version interception for all five provider wrappers.
- privacy-safe logging that excludes prompt content, personal paths, project
  paths, and raw session identifiers.

---

## 2. E2E Test Flow & Assertions

For each framing mode, the E2E suite executes a multi-turn conversation on a single session:

### Turn 1: Prompt & Stream Verification
* **Action:** Sends a `session/prompt` request with the prompt: `Remember this word: ORANGE_BANANA. Reply with only: OK`.
* **Subprocess Execution:** The mock agent is spawned, creating a WAL-mode SQLite database, writing intermediate steps, and inserting the response payload into the `steps` table.
* **Assertions:**
  - Asserts that at least one `session/update` notification (agent message chunk) is received.
  - Asserts that the accumulated streamed text equals `"OK"`.
  - Asserts that the final RPC response returns `stopReason: "end_turn"`.

### Turn 2: Session Loading & Memory Recall
* **Action:** Sends a second `session/prompt` with the prompt: `What word did I ask you to remember? Reply with just that word.`.
* **Subprocess Execution:** The mock agent loads the existing conversation ID via `--conversation <id>` and appends the recall response steps to the database.
* **Assertions:**
  - Asserts that the recall response streams the word `ORANGE_BANANA` (case-insensitive check), validating that the session state mapping and database index polling persisted correctly across turns.

### Logging Privacy Regression
* **Action:** Adds a unique secret marker and personal-path sentinel to the
  first prompt while directing the shim log to an isolated temporary file.
* **Assertions:** Confirms the log contains a sanitized subprocess lifecycle
  event but does not contain the prompt marker, personal path, project path, or
  raw ACP session ID.

---

## 3. Mock Agent Design (`mock_agy.py`)

The local mock agent matches the real `agy` step-writing database lifecycle:
* **Protobuf Encoder:** Encodes strings into a serialized binary structure matching the `agy` step schema:
  - Top-level field `1` (varint `15` representing `step_type = 15`).
  - Top-level field `20` (length-delimited sub-message).
  - Sub-message field `1` (length-delimited UTF-8 string containing response text).
* **SQLite Persistence:** Spawns a WAL-mode database in the standard conversations directory (`~/.gemini/antigravity-cli/conversations/`), writing steps `14` (input), `98` (working), `15` (message), and `17` (status) with artificial delays (0.1s) to allow the polling thread to stream increments.

---

## 4. Test Evidence Record

The following table records the environment parameters and test outcomes of the verification pass:

| Field | Value |
| --- | --- |
| **Commit Hash** | `2b42876218322f1ace62b5f49d0dc66eb955c2ae (with local changes)` |
| **Windows Version** | `Microsoft Windows [Version 10.0.26200.8524]` |
| **Python Version** | `Python 3.14.5` |
| **Antigravity CLI Version** | `1.0.5` |
| **ACP Host (Target)** | `Stardock Clairvoyance` |
| **Static Syntax Compilation** | **PASS** |
| **Raw Line Framing E2E Tests** | **PASS** |
| **LSP Content-Length E2E Tests**| **PASS** |
| **Multi-Turn Recall Verification**| **PASS** |
| **Reviewer / Author** | Antigravity AI Assistant |
| **Date** | June 5, 2026 |

No other ACP host is covered by this evidence record.

---

## 5. Actual Test Execution Output

```
[TEST-RUNNER] ==================================================
[TEST-RUNNER] Starting E2E Shim Test (use_lsp=False)
[TEST-RUNNER] ==================================================
[TEST-RUNNER] --> Sending: {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": 1, "clientInfo": {"name": "test-runner", "version": "1.0.0"}}}
[TEST-RUNNER] <-- Received: {'jsonrpc': '2.0', 'id': 1, 'result': {'protocolVersion': 1, 'agentInfo': {'name': 'agy-shim-gemini', 'version': '1.0.0'}, 'agentCapabilities': {'streaming': True, 'loadSession': True}}}
[TEST-RUNNER] Initialize test passed.
[TEST-RUNNER] --> Sending: {"jsonrpc": "2.0", "id": 2, "method": "session/new", "params": {}}
[TEST-RUNNER] <-- Received: {'jsonrpc': '2.0', 'id': 2, 'result': {'sessionId': '2bf6aa5e-414b-48bc-b934-4e218bf3829a'}}
[TEST-RUNNER] Session created: 2bf6aa5e-414b-48bc-b934-4e218bf3829a
[TEST-RUNNER] --> Sending: {"jsonrpc": "2.0", "id": 3, "method": "session/prompt", "params": {"sessionId": "2bf6aa5e-414b-48bc-b934-4e218bf3829a", "prompt": [{"type": "text", "text": "Remember this word: ORANGE_BANANA. Reply with only: OK"}]}}
[TEST-RUNNER] <-- Received: {'jsonrpc': '2.0', 'method': 'session/update', 'params': {'sessionId': '2bf6aa5e-414b-48bc-b934-4e218bf3829a', 'update': {'sessionUpdate': 'agent_message_chunk', 'content': {'type': 'text', 'text': 'OK'}}}}
[TEST-RUNNER] <-- Received: {'jsonrpc': '2.0', 'id': 3, 'result': {'stopReason': 'end_turn'}}
[TEST-RUNNER] Accumulated stream output (Turn 1): 'OK'
[TEST-RUNNER] Turn 1 test passed.
[TEST-RUNNER] --> Sending: {"jsonrpc": "2.0", "id": 4, "method": "session/prompt", "params": {"sessionId": "2bf6aa5e-414b-48bc-b934-4e218bf3829a", "prompt": [{"type": "text", "text": "What word did I ask you to remember? Reply with just that word."}]}}
[TEST-RUNNER] <-- Received: {'jsonrpc': '2.0', 'method': 'session/update', 'params': {'sessionId': '2bf6aa5e-414b-48bc-b934-4e218bf3829a', 'update': {'sessionUpdate': 'agent_message_chunk', 'content': {'type': 'text', 'text': 'OK'}}}}
[TEST-RUNNER] <-- Received: {'jsonrpc': '2.0', 'method': 'session/update', 'params': {'sessionId': '2bf6aa5e-414b-48bc-b934-4e218bf3829a', 'update': {'sessionUpdate': 'agent_message_chunk', 'content': {'type': 'text', 'text': '\nORANGE_BANANA'}}}}
[TEST-RUNNER] <-- Received: {'jsonrpc': '2.0', 'id': 4, 'result': {'stopReason': 'end_turn'}}
[TEST-RUNNER] Accumulated stream output (Turn 2): 'OK\nORANGE_BANANA'
[TEST-RUNNER] Turn 2 (memory retention) test passed.
[TEST-RUNNER] Shim process terminated.
[TEST-RUNNER] All tests passed successfully for this framing mode!
[TEST-RUNNER] ==================================================
[TEST-RUNNER] Starting E2E Shim Test (use_lsp=True)
[TEST-RUNNER] ==================================================
[TEST-RUNNER] --> Sending: {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": 1, "clientInfo": {"name": "test-runner", "version": "1.0.0"}}}
[TEST-RUNNER] <-- Received: {'jsonrpc': '2.0', 'id': 1, 'result': {'protocolVersion': 1, 'agentInfo': {'name': 'agy-shim-gemini', 'version': '1.0.0'}, 'agentCapabilities': {'streaming': True, 'loadSession': True}}}
[TEST-RUNNER] Initialize test passed.
[TEST-RUNNER] --> Sending: {"jsonrpc": "2.0", "id": 2, "method": "session/new", "params": {}}
[TEST-RUNNER] <-- Received: {'jsonrpc': '2.0', 'id': 2, 'result': {'sessionId': '97b4f11f-75d5-4e5c-915f-9ab907d0998c'}}
[TEST-RUNNER] Session created: 97b4f11f-75d5-4e5c-915f-9ab907d0998c
[TEST-RUNNER] --> Sending: {"jsonrpc": "2.0", "id": 3, "method": "session/prompt", "params": {"sessionId": "97b4f11f-75d5-4e5c-915f-9ab907d0998c", "prompt": [{"type": "text", "text": "Remember this word: ORANGE_BANANA. Reply with only: OK"}]}}
[TEST-RUNNER] <-- Received: {'jsonrpc': '2.0', 'method': 'session/update', 'params': {'sessionId': '97b4f11f-75d5-4e5c-915f-9ab907d0998c', 'update': {'sessionUpdate': 'agent_message_chunk', 'content': {'type': 'text', 'text': 'OK'}}}}
[TEST-RUNNER] <-- Received: {'jsonrpc': '2.0', 'id': 3, 'result': {'stopReason': 'end_turn'}}
[TEST-RUNNER] Accumulated stream output (Turn 1): 'OK'
[TEST-RUNNER] Turn 1 test passed.
[TEST-RUNNER] --> Sending: {"jsonrpc": "2.0", "id": 4, "method": "session/prompt", "params": {"sessionId": "97b4f11f-75d5-4e5c-915f-9ab907d0998c", "prompt": [{"type": "text", "text": "What word did I ask you to remember? Reply with just that word."}]}}
[TEST-RUNNER] <-- Received: {'jsonrpc': '2.0', 'method': 'session/update', 'params': {'sessionId': '97b4f11f-75d5-4e5c-915f-9ab907d0998c', 'update': {'sessionUpdate': 'agent_message_chunk', 'content': {'type': 'text', 'text': 'OK'}}}}
[TEST-RUNNER] <-- Received: {'jsonrpc': '2.0', 'method': 'session/update', 'params': {'sessionId': '97b4f11f-75d5-4e5c-915f-9ab907d0998c', 'update': {'sessionUpdate': 'agent_message_chunk', 'content': {'type': 'text', 'text': '\nORANGE_BANANA'}}}}
[TEST-RUNNER] <-- Received: {'jsonrpc': '2.0', 'id': 4, 'result': {'stopReason': 'end_turn'}}
[TEST-RUNNER] Accumulated stream output (Turn 2): 'OK\nORANGE_BANANA'
[TEST-RUNNER] Turn 2 (memory retention) test passed.
[TEST-RUNNER] Shim process terminated.
[TEST-RUNNER] All tests passed successfully for this framing mode!

==================================================
[TEST-RUNNER] ALL TESTS COMPLETED SUCCESSFULLY!
==================================================
```
