# Implementation Plan: Gemini CLI to Antigravity CLI Shim (with Masquerading)

This plan outlines the design and implementation of a lightweight shim for the Agent Client Protocol (ACP) that bridges to the Antigravity CLI (`agy.exe`). To support Stardock Clairvoyance's auto-detection and avoid conflicts with existing CLI installations, the shim masquerades as multiple AI coding providers.

The JSON-RPC/ACP bridge is intended to remain usable independently of
Clairvoyance. Provider masquerading, version interception, and PATH-based
discovery form a Clairvoyance-specific adapter around that core. At present,
only the Clairvoyance integration has end-to-end evidence; support for other
ACP hosts remains a design goal rather than a verified capability.

## Masquerading Strategy

Clairvoyance auto-detects installed AI agents by checking for specific executable names in the system `PATH`. The shim provides wrappers for all five main providers to allow swapping them out dynamically:

1. **`cursor.cmd`** (Masquerading as Cursor CLI)
2. **`copilot.cmd`** (Masquerading as Copilot CLI)
3. **`gemini.cmd`** (Masquerading as Gemini CLI)
4. **`claude.cmd`** (Masquerading as Claude Code CLI)
5. **`codex.cmd`** (Masquerading as Codex CLI)

All wrappers route to the same core Python entry point
(`src/agy_shim/main.py`), passing a `--provider <name>` parameter to set the
identity.

### Provider Version Interception
When Clairvoyance scans path binaries using `<provider> --version`, the shim intercepts the query and prints the exact version string matching that provider to ensure detection:
* `copilot` $\rightarrow$ `1.0.59`
* `claude` $\rightarrow$ `2.1.165`
* `codex` $\rightarrow$ `0.137.0`
* `gemini` $\rightarrow$ `0.45.1`
* `cursor` $\rightarrow$ `1.0.0`

---

## Core Components

The project is located in `D:\CODE-REPO\Tools\AGY-Shim`.

### 1. Unified Python Shim ([main.py](../src/agy_shim/main.py))
A Python script that:
* **Standard JSON-RPC 2.0 Server:** Handles incoming stdio commands and translates them to standard ACP messages (`initialize`, `session/new`, `session/load`, `session/prompt`, `session/cancel`, `session/close`).
* **Framing Auto-Detection:** Automatically detects whether the client is sending messages using LSP-style `Content-Length` framing or raw newline-delimited JSON.
* **Closed-Stdin Subprocess Spawning:** Safely executes `agy.exe` with redirected `stdin=subprocess.DEVNULL` to prevent blocking hangs, capturing stdout/stderr in separate threads to avoid OS pipe deadlock.
* **Workspace Isolation:** During initialization, the shim extracts the client's workspace path and redirects the session state and locking directory to `.gemini/agy-acp/` within the active workspace.
* **Exception-Safe Locking:** Uses a Python context manager (`with self._lock_session()`) for locking file operations, guaranteed to unlock files even if unexpected serialization errors occur.
* **Thread-Safe I/O Writes:** Serializes stdout printing using a global lock (`stdout_lock = threading.Lock()`) to prevent interleaving stdout data.
* **Subprocess Exit Verification:** Checks `proc.returncode` and maps non-zero exits to standard JSON-RPC protocol error responses.
* **Real-time SQLite Polling:** Connects to the WAL-mode SQLite database in read-only mode (`mode=ro`) and polls the `steps` table concurrently. Extracts and streams token updates (`session/update`) in real-time as `agy.exe` appends new execution steps.
* **Safe Resource Release:** Explicitly closes spawned subprocess stdout/stderr handles after reader threads complete to prevent file descriptor leaks.
* **Privacy-Safe Logging:** Records allowlisted lifecycle metadata only. Prompt
  content, command lines, personal paths, raw subprocess output, exception
  messages, and raw session/conversation IDs are excluded; identifiers are
  correlated using truncated hashes.
* **Log Rotation:** Automatically rotates `gemini_shim.log` when it exceeds 5MB to prevent unbounded disk usage.

### 2. Wrapper Scripts
Five command scripts in `bin/` route calls to the Python shim:
* **`cursor.cmd`**: starts `src/agy_shim/main.py` as `cursor`
* **`copilot.cmd`**: starts `src/agy_shim/main.py` as `copilot`
* **`gemini.cmd`**: starts `src/agy_shim/main.py` as `gemini`
* **`claude.cmd`**: starts `src/agy_shim/main.py` as `claude`
* **`codex.cmd`**: starts `src/agy_shim/main.py` as `codex`

### 3. Mock Agent Testing Environment
To prevent E2E tests from failing due to external network issues, OAuth credentials expiration, or Google API quota limits (e.g., `RESOURCE_EXHAUSTED (code 429)`), the test suite uses a local mock agent:
* **`tests/fixtures/mock_agy.py`**: A Python script that simulates the SQLite database creation and inserts steps to replicate the real `agy.exe` flow.
* **`tests/fixtures/mock_agy.cmd`**: A command wrapper for the mock script.
* During tests, `tests/test_e2e.py` sets `os.environ["AGY_PATH"]` to redirect execution to this mock agent, ensuring tests are deterministic and self-contained.

---

## Verification Plan

### Automated Tests
* Run [test_e2e.py](../tests/test_e2e.py). The suite automatically injects the mock testing path, validating both raw JSON lines and LSP Content-Length framing.

### Manual Verification
1. Run `.\bin\copilot.cmd --version` to verify version outputs.
2. Verify Clairvoyance's "Cloud AI" settings tab to check that providers are successfully detected as installed.
3. Open a workspace inside Clairvoyance, select the masqueraded agent, and verify multi-turn streaming responses with the real `agy.exe` binary.
