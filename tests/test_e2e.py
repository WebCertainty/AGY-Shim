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
    
    log_dir = tempfile.TemporaryDirectory()
    log_path = os.path.join(log_dir.name, "shim.log")
    shim_env = os.environ.copy()
    shim_env["AGY_SHIM_LOG_FILE"] = log_path
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
                "clientInfo": {"name": "test-runner", "version": "1.0.0"}
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
                            "Private path: C:\\Users\\Sensitive User\\private.txt"
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
        sys.exit(1)
    finally:
        # Terminate
        proc.terminate()
        proc.wait()
        log("Shim process terminated.")

    with open(log_path, "r", encoding="utf-8") as f:
        shim_log = f.read()
    assert "DO_NOT_LOG_THIS_SECRET" not in shim_log, "Prompt content leaked to shim log"
    assert "Sensitive User" not in shim_log, "Personal path leaked to shim log"
    assert PROJECT_ROOT not in shim_log, "Project path leaked to shim log"
    assert session_id not in shim_log, "Raw session ID leaked to shim log"
    assert "subprocess_starting" in shim_log, "Expected sanitized lifecycle event"
    log_dir.cleanup()
    log("Privacy-safe logging test passed.")
        
    log("All tests passed successfully for this framing mode!")

def main():
    # Test raw newline-delimited mode
    run_test_with_framing(use_lsp=False)
    
    # Test LSP Content-Length framing mode
    run_test_with_framing(use_lsp=True)
    
    log("\n==================================================")
    log("ALL TESTS COMPLETED SUCCESSFULLY!")
    log("==================================================")

if __name__ == "__main__":
    main()
