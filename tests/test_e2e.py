"""Deterministic end-to-end tests for the AGY-Shim ACP bridge.

The runner acts as a Clairvoyance-shaped ACP client and verifies initialization,
streaming, and multi-turn session continuity using both newline-delimited JSON
and LSP Content-Length framing. It injects the local mock agent, so these tests
do not require model credentials or consume API quota.
"""

import subprocess
import json
import sys
import os
import time
import tempfile
from pathlib import Path

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(TESTS_DIR)
SHIM_FILE = os.path.join(PROJECT_ROOT, "src", "agy_shim", "main.py")
os.environ["AGY_PATH"] = os.path.join(TESTS_DIR, "fixtures", "mock_agy.cmd")

def log(msg):
    print(f"[TEST-RUNNER] {msg}")

def run_test_with_framing(use_lsp=False):
    log(f"==================================================")
    log(f"Starting E2E Shim Test (use_lsp={use_lsp})")
    log(f"==================================================")
    
    runtime_dir = tempfile.TemporaryDirectory()
    log_path = os.path.join(runtime_dir.name, "logs", "shim.log")
    profile_dir = os.path.join(runtime_dir.name, "profile")
    workspace_dir = os.path.join(runtime_dir.name, "workspace")
    os.makedirs(profile_dir)
    os.makedirs(workspace_dir)
    private_path_sentinel = os.path.join(
        os.path.abspath(os.sep),
        "Users",
        "Sensitive User",
        "private.txt",
    )
    shim_env = os.environ.copy()
    shim_env["AGY_SHIM_LOG_FILE"] = log_path
    shim_env["USERPROFILE"] = profile_dir
    shim_env["AGY_SHIM_ALLOW_BYPASS"] = "1"
    proc = subprocess.Popen(
        [sys.executable, SHIM_FILE],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        bufsize=0,
        env=shim_env,
    )
    
    def send_req(msg_dict):
        body = json.dumps(msg_dict)
        if use_lsp:
            payload = f"Content-Length: {len(body.encode('utf-8'))}\r\n\r\n{body}"
        else:
            payload = f"{body}\n"
        log(f"--> Sending: {body[:150]}")
        proc.stdin.write(payload.encode('utf-8'))
        proc.stdin.flush()
        
    def read_resp():
        if use_lsp:
            # Read first line
            first_line = proc.stdout.readline()
            if not first_line:
                return None
            stripped = first_line.strip()
            if not stripped.startswith(b"Content-Length:"):
                log(f"Error: Expected Content-Length, got: {first_line}")
                return None
            try:
                content_length = int(stripped.split(b":")[1].strip())
            except ValueError:
                content_length = 0
            
            # Read until empty line
            while True:
                line = proc.stdout.readline()
                if not line or line.strip() == b"":
                    break
            
            body = proc.stdout.read(content_length)
            return json.loads(body.decode('utf-8'))
        else:
            line = proc.stdout.readline()
            if not line:
                return None
            return json.loads(line.strip().decode('utf-8'))

    try:
        # 1. Send initialize
        init_req = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": 1,
                "clientInfo": {"name": "test-runner", "version": "1.0.0"},
                "rootUri": Path(workspace_dir).as_uri(),
            }
        }
        send_req(init_req)
        resp = read_resp()
        log(f"<-- Received: {resp}")
        assert resp["id"] == 1, "ID mismatch in initialize response"
        assert "result" in resp, "Missing result in initialize response"
        assert resp["result"]["protocolVersion"] == 1, "Protocol version mismatch"
        assert resp["result"]["agentCapabilities"]["streaming"] is True, "Streaming capability should be advertised"
        log("Initialize test passed.")
        
        # 2. Send session/new
        new_sess_req = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "session/new",
            "params": {}
        }
        send_req(new_sess_req)
        resp = read_resp()
        log(f"<-- Received: {resp}")
        assert resp["id"] == 2, "ID mismatch in session/new response"
        session_id = resp["result"]["sessionId"]
        assert session_id, "Missing sessionId in response"
        log(f"Session created: {session_id}")
        
        # 3. Send session/prompt (turn 1)
        prompt_req = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "session/prompt",
            "params": {
                "sessionId": session_id,
                "prompt": [
                    {
                        "type": "text",
                        "text": (
                            "Remember this word: ORANGE_BANANA. Reply with only: OK. "
                            "Privacy sentinel: DO_NOT_LOG_THIS_SECRET. "
                            f"Private path: {private_path_sentinel}"
                        ),
                    }
                ]
            }
        }
        send_req(prompt_req)
        
        # Read notifications until final response (id=3)
        got_update = False
        final_text = ""
        
        while True:
            resp = read_resp()
            if not resp:
                log("Error: EOF before prompt finished")
                break
                
            log(f"<-- Received: {resp}")
            if resp.get("method") == "session/update":
                got_update = True
                content = resp["params"]["update"]["content"]
                if content.get("type") == "text":
                    final_text += content.get("text", "")
            elif resp.get("id") == 3:
                assert "error" not in resp, f"Prompt failed: {resp.get('error')}"
                assert resp["result"]["stopReason"] == "end_turn", "Stop reason mismatch"
                break
                
        log(f"Accumulated stream output (Turn 1): {repr(final_text)}")
        assert got_update, "Expected at least one session/update notification"
        log("Turn 1 test passed.")
        
        # 4. Send session/prompt (turn 2) - testing memory recall
        prompt_req_2 = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "session/prompt",
            "params": {
                "sessionId": session_id,
                "prompt": [
                    {"type": "text", "text": "What word did I ask you to remember? Reply with just that word."}
                ]
            }
        }
        send_req(prompt_req_2)
        
        final_text_2 = ""
        while True:
            resp = read_resp()
            if not resp:
                break
            log(f"<-- Received: {resp}")
            if resp.get("method") == "session/update":
                content = resp["params"]["update"]["content"]
                if content.get("type") == "text":
                    final_text_2 += content.get("text", "")
            elif resp.get("id") == 4:
                assert "error" not in resp, f"Prompt 2 failed: {resp.get('error')}"
                break
                
        log(f"Accumulated stream output (Turn 2): {repr(final_text_2)}")
        assert "orange_banana" in final_text_2.lower(), f"Recall failed. Expected 'ORANGE_BANANA', got {repr(final_text_2)}"
        log("Turn 2 (memory retention) test passed.")
        
    except Exception as e:
        log(f"TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        try:
            proc.terminate()
            proc.wait(timeout=1.0)
            err_data = proc.stderr.read()
            if err_data:
                log(f"Shim stderr: {err_data.decode('utf-8', errors='replace')}")
        except Exception as ex:
            log(f"Failed to read stderr: {ex}")
        sys.exit(1)
    finally:
        # Terminate
        proc.terminate()
        proc.wait()
        log("Shim process terminated.")

    with open(log_path, "r", encoding="utf-8") as f:
        shim_log = f.read()
    assert "DO_NOT_LOG_THIS_SECRET" not in shim_log, "Prompt content leaked to shim log"
    assert private_path_sentinel not in shim_log, "Personal path leaked to shim log"
    assert PROJECT_ROOT not in shim_log, "Project path leaked to shim log"
    assert session_id not in shim_log, "Raw session ID leaked to shim log"
    assert "subprocess_starting" in shim_log, "Expected sanitized lifecycle event"
    workspace_state = os.path.join(
        workspace_dir,
        ".gemini",
        "agy-acp",
        "sessions.json",
    )
    assert os.path.exists(workspace_state), "Workspace URI was not used for session state"
    runtime_dir.cleanup()
    log("Privacy-safe logging test passed.")
        
    log("All tests passed successfully for this framing mode!")

def test_bypass_enforcement():
    log("Running bypass enforcement test...")
    runtime_dir = tempfile.TemporaryDirectory()
    log_path = os.path.join(runtime_dir.name, "logs", "shim.log")
    profile_dir = os.path.join(runtime_dir.name, "profile")
    workspace_dir = os.path.join(runtime_dir.name, "workspace")
    os.makedirs(profile_dir)
    os.makedirs(workspace_dir)
    
    shim_env = os.environ.copy()
    shim_env["AGY_SHIM_LOG_FILE"] = log_path
    shim_env["USERPROFILE"] = profile_dir
    # Note: AGY_SHIM_ALLOW_BYPASS is intentionally NOT set
    
    proc = subprocess.Popen(
        [sys.executable, SHIM_FILE],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        bufsize=0,
        env=shim_env,
    )
    
    try:
        # 1. Initialize
        proc.stdin.write(json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": 1,
                "clientInfo": {"name": "test-runner", "version": "1.0.0"},
                "rootUri": Path(workspace_dir).as_uri(),
            }
        }).encode('utf-8') + b"\n")
        proc.stdout.readline()
        
        # 2. session/new
        proc.stdin.write(json.dumps({
            "jsonrpc": "2.0",
            "id": 2,
            "method": "session/new",
            "params": {}
        }).encode('utf-8') + b"\n")
        resp2 = json.loads(proc.stdout.readline().strip().decode('utf-8'))
        session_id = resp2["result"]["sessionId"]
        
        # 3. session/prompt (should fail)
        proc.stdin.write(json.dumps({
            "jsonrpc": "2.0",
            "id": 3,
            "method": "session/prompt",
            "params": {
                "sessionId": session_id,
                "prompt": [{"type": "text", "text": "Hello"}]
            }
        }).encode('utf-8') + b"\n")
        
        resp3 = json.loads(proc.stdout.readline().strip().decode('utf-8'))
        assert "error" in resp3, "Expected error due to missing bypass flag"
        assert resp3["error"]["code"] == -32000, f"Expected error code -32000, got {resp3['error']['code']}"
        assert "Safe-mode active" in resp3["error"]["message"]
        log("Bypass enforcement check passed.")
        
    finally:
        proc.terminate()
        proc.wait()
        runtime_dir.cleanup()

def test_concurrency_and_slot_release():
    log("Running concurrency and slot release test...")
    runtime_dir = tempfile.TemporaryDirectory()
    log_path = os.path.join(runtime_dir.name, "logs", "shim.log")
    profile_dir = os.path.join(runtime_dir.name, "profile")
    workspace_dir = os.path.join(runtime_dir.name, "workspace")
    os.makedirs(profile_dir)
    os.makedirs(workspace_dir)
    
    shim_env = os.environ.copy()
    shim_env["AGY_SHIM_LOG_FILE"] = log_path
    shim_env["USERPROFILE"] = profile_dir
    shim_env["AGY_SHIM_ALLOW_BYPASS"] = "1"
    shim_env["AGY_MOCK_SLOW_DELAY"] = "2.0" # Make mock sleep 2.0s
    
    proc = subprocess.Popen(
        [sys.executable, SHIM_FILE],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        bufsize=0,
        env=shim_env,
    )
    
    try:
        # 1. Initialize
        proc.stdin.write(json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": 1,
                "clientInfo": {"name": "test-runner", "version": "1.0.0"},
                "rootUri": Path(workspace_dir).as_uri(),
            }
        }).encode('utf-8') + b"\n")
        proc.stdout.readline()
        
        # 2. session/new
        proc.stdin.write(json.dumps({
            "jsonrpc": "2.0",
            "id": 2,
            "method": "session/new",
            "params": {}
        }).encode('utf-8') + b"\n")
        resp2 = json.loads(proc.stdout.readline().strip().decode('utf-8'))
        session_id = resp2["result"]["sessionId"]
        
        # 3. First session/prompt (slow)
        proc.stdin.write(json.dumps({
            "jsonrpc": "2.0",
            "id": 3,
            "method": "session/prompt",
            "params": {
                "sessionId": session_id,
                "prompt": [{"type": "text", "text": "First prompt"}]
            }
        }).encode('utf-8') + b"\n")
        
        # Sleep slightly to let first prompt start and lock the busy slot
        time.sleep(0.5)
        
        # 4. Second session/prompt (should return busy error immediately)
        proc.stdin.write(json.dumps({
            "jsonrpc": "2.0",
            "id": 4,
            "method": "session/prompt",
            "params": {
                "sessionId": session_id,
                "prompt": [{"type": "text", "text": "Second prompt"}]
            }
        }).encode('utf-8') + b"\n")
        
        # Read the immediate response (should be the busy error for ID 4)
        resp4 = json.loads(proc.stdout.readline().strip().decode('utf-8'))
        assert "error" in resp4, "Expected busy error for second concurrent prompt"
        assert resp4["id"] == 4
        assert resp4["error"]["code"] == -32000
        assert "Agent is busy" in resp4["error"]["message"]
        log("Concurrency rejection check passed.")
        
        # Now wait for the first prompt's updates and final response (ID 3)
        got_update = False
        while True:
            line = proc.stdout.readline()
            resp3 = json.loads(line.strip().decode('utf-8'))
            if resp3.get("method") == "session/update":
                got_update = True
            elif resp3.get("id") == 3:
                assert "error" not in resp3
                assert resp3["result"]["stopReason"] == "end_turn"
                break
        assert got_update
        log("First slow prompt completed successfully.")
        
        # 5. Third session/prompt (should be accepted since slot is released)
        proc.stdin.write(json.dumps({
            "jsonrpc": "2.0",
            "id": 5,
            "method": "session/prompt",
            "params": {
                "sessionId": session_id,
                "prompt": [{"type": "text", "text": "Third prompt"}]
            }
        }).encode('utf-8') + b"\n")
        
        # Read final response for ID 5 (with its updates)
        got_update = False
        while True:
            line = proc.stdout.readline()
            resp5 = json.loads(line.strip().decode('utf-8'))
            if resp5.get("method") == "session/update":
                got_update = True
            elif resp5.get("id") == 5:
                assert "error" not in resp5
                assert resp5["result"]["stopReason"] == "end_turn"
                break
        assert got_update
        log("Slot release and subsequent prompt check passed.")
        
    finally:
        proc.terminate()
        proc.wait()
        runtime_dir.cleanup()

def test_cancellation():
    log("Running cancellation tests (request and notification styles)...")
    runtime_dir = tempfile.TemporaryDirectory()
    log_path = os.path.join(runtime_dir.name, "logs", "shim.log")
    profile_dir = os.path.join(runtime_dir.name, "profile")
    workspace_dir = os.path.join(runtime_dir.name, "workspace")
    os.makedirs(profile_dir)
    os.makedirs(workspace_dir)
    
    shim_env = os.environ.copy()
    shim_env["AGY_SHIM_LOG_FILE"] = log_path
    shim_env["USERPROFILE"] = profile_dir
    shim_env["AGY_SHIM_ALLOW_BYPASS"] = "1"
    shim_env["AGY_MOCK_SLOW_DELAY"] = "3.0" # Make mock sleep 3.0s
    
    proc = subprocess.Popen(
        [sys.executable, SHIM_FILE],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        bufsize=0,
        env=shim_env,
    )
    
    try:
        # Initialize & session/new
        proc.stdin.write(json.dumps({
            "jsonrpc": "2.0", "id": 1, "method": "initialize",
            "params": {"protocolVersion": 1, "clientInfo": {"name": "test-runner"}, "rootUri": Path(workspace_dir).as_uri()}
        }).encode('utf-8') + b"\n")
        proc.stdout.readline()
        
        proc.stdin.write(json.dumps({
            "jsonrpc": "2.0", "id": 2, "method": "session/new", "params": {}
        }).encode('utf-8') + b"\n")
        resp2 = json.loads(proc.stdout.readline().strip().decode('utf-8'))
        session_id = resp2["result"]["sessionId"]
        
        # --- TEST 1: Request-Style Cancellation (with id) ---
        log("Testing request-style cancellation...")
        proc.stdin.write(json.dumps({
            "jsonrpc": "2.0",
            "id": 3,
            "method": "session/prompt",
            "params": {
                "sessionId": session_id,
                "prompt": [{"type": "text", "text": "Slow prompt 1"}]
            }
        }).encode('utf-8') + b"\n")
        
        time.sleep(0.5)
        
        # Send cancel request
        proc.stdin.write(json.dumps({
            "jsonrpc": "2.0",
            "id": 4,
            "method": "session/cancel",
            "params": {
                "sessionId": session_id
            }
        }).encode('utf-8') + b"\n")
        
        # Read messages until we have both response 3 and response 4
        responses = {}
        while len(responses) < 2 or 3 not in responses or 4 not in responses:
            line = proc.stdout.readline()
            if not line:
                break
            msg = json.loads(line.strip().decode('utf-8'))
            if msg.get("id") is not None:
                responses[msg.get("id")] = msg
            else:
                log(f"Received notification while waiting: {msg}")
            
        assert 4 in responses, "Missing cancel request response"
        assert "result" in responses[4]
        
        assert 3 in responses, "Missing prompt cancelled response"
        assert "error" in responses[3]
        assert "cancelled" in responses[3]["error"]["message"]
        log("Request-style cancellation passed.")
        
        # Verify slot released by running a successful prompt
        log("Testing slot release after cancellation...")
        proc.stdin.write(json.dumps({
            "jsonrpc": "2.0",
            "id": 5,
            "method": "session/prompt",
            "params": {
                "sessionId": session_id,
                "prompt": [{"type": "text", "text": "Subsequent prompt"}]
            }
        }).encode('utf-8') + b"\n")
        
        while True:
            line = proc.stdout.readline()
            msg = json.loads(line.strip().decode('utf-8'))
            if msg.get("id") == 5:
                assert "error" not in msg
                break
        log("Slot release after cancellation passed.")
        
        # --- TEST 2: Notification-Style Cancellation (no id) ---
        log("Testing notification-style cancellation...")
        proc.stdin.write(json.dumps({
            "jsonrpc": "2.0",
            "id": 6,
            "method": "session/prompt",
            "params": {
                "sessionId": session_id,
                "prompt": [{"type": "text", "text": "Slow prompt 2"}]
            }
        }).encode('utf-8') + b"\n")
        
        time.sleep(0.5)
        
        # Send cancel notification (no id)
        proc.stdin.write(json.dumps({
            "jsonrpc": "2.0",
            "method": "session/cancel",
            "params": {
                "sessionId": session_id
            }
        }).encode('utf-8') + b"\n")
        
        # Read response. Since cancel was a notification, we only expect ONE response (the prompt cancellation error, id=6)
        resp6 = None
        while True:
            line = proc.stdout.readline()
            if not line:
                break
            msg = json.loads(line.strip().decode('utf-8'))
            if msg.get("id") == 6:
                resp6 = msg
                break
            else:
                log(f"Received notification while waiting: {msg}")
                
        assert resp6 is not None
        assert "error" in resp6
        assert "cancelled" in resp6["error"]["message"]
        log("Notification-style cancellation passed.")
        
    finally:
        proc.terminate()
        proc.wait()
        runtime_dir.cleanup()

def main():
    # Test raw newline-delimited mode
    run_test_with_framing(use_lsp=False)
    
    # Test LSP Content-Length framing mode
    run_test_with_framing(use_lsp=True)
    
    # Run new security and concurrency test cases
    test_bypass_enforcement()
    test_concurrency_and_slot_release()
    test_cancellation()
    
    log("\n==================================================")
    log("ALL TESTS COMPLETED SUCCESSFULLY!")
    log("==================================================")

if __name__ == "__main__":
    main()
