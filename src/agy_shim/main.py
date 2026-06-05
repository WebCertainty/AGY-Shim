"""ACP-to-Antigravity bridge used by the AGY-Shim Windows wrappers.

The process serves JSON-RPC over stdio, manages ACP sessions, launches
``agy.exe``, and streams response records from Antigravity's conversation
database. It relies on undocumented Antigravity formats and currently launches
the agent with permission checks bypassed; see SECURITY.md before use.
"""

import sys
import os
import json
import uuid
import time
import sqlite3
import subprocess
import threading
import datetime
import contextlib
import urllib.parse

try:
    import msvcrt
except ImportError:
    msvcrt = None

# Keep runtime logs at the repository root when running from a checkout.
PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(PACKAGE_DIR))
LOG_FILE = os.path.join(PROJECT_ROOT, "gemini_shim.log")

# Global stdout lock to prevent interleaved concurrent prints
stdout_lock = threading.Lock()
log_lock = threading.Lock()

def log(msg):
    try:
        timestamp = datetime.datetime.now().isoformat()
        with log_lock:
            if os.path.exists(LOG_FILE) and os.path.getsize(LOG_FILE) > 5 * 1024 * 1024:
                bak_file = LOG_FILE + ".bak"
                try:
                    if os.path.exists(bak_file):
                        os.remove(bak_file)
                    os.rename(LOG_FILE, bak_file)
                except:
                    pass
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(f"[{timestamp}] {msg}\n")
    except:
        pass

log("Gemini ACP Shim started")

# Auto-detect LSP framing vs raw lines
use_lsp_framing = False

def read_message():
    global use_lsp_framing
    try:
        first_line = sys.stdin.buffer.readline()
        if not first_line:
            return None
        
        stripped = first_line.strip()
        if stripped.startswith(b"Content-Length:"):
            use_lsp_framing = True
            try:
                content_length = int(stripped.split(b":")[1].strip())
            except ValueError:
                content_length = 0
            
            # Read header lines until empty line
            while True:
                line = sys.stdin.buffer.readline()
                if not line or line.strip() == b"":
                    break
            
            # Read body
            body = sys.stdin.buffer.read(content_length)
            return json.loads(body.decode('utf-8'))
        else:
            return json.loads(stripped.decode('utf-8'))
    except Exception as e:
        log(f"Error reading message: {e}")
        return None

def write_message(msg_dict):
    global use_lsp_framing
    try:
        body = json.dumps(msg_dict)
        if use_lsp_framing:
            payload = f"Content-Length: {len(body.encode('utf-8'))}\r\n\r\n{body}"
        else:
            payload = f"{body}\n"
        with stdout_lock:
            sys.stdout.buffer.write(payload.encode('utf-8'))
            sys.stdout.buffer.flush()
    except Exception as e:
        log(f"Error writing message: {e}")

class SessionStore:
    def __init__(self):
        user_profile = os.environ.get("USERPROFILE") or os.path.expanduser("~")
        self.state_dir = os.path.join(user_profile, ".gemini", "agy-acp")
        self.state_file = os.path.join(self.state_dir, "sessions.json")
        self.lock_file_path = self.state_file + ".lock"
        
    def set_workspace(self, workspace_path):
        if workspace_path and os.path.isdir(workspace_path):
            self.state_dir = os.path.join(workspace_path, ".gemini", "agy-acp")
            self.state_file = os.path.join(self.state_dir, "sessions.json")
            self.lock_file_path = self.state_file + ".lock"
            log(f"SessionStore workspace set to: {workspace_path}")
        
    @contextlib.contextmanager
    def _lock_session(self):
        os.makedirs(self.state_dir, exist_ok=True)
        lk_f = open(self.lock_file_path, "w")
        try:
            if msvcrt:
                try:
                    msvcrt.locking(lk_f.fileno(), msvcrt.LK_LOCK, 1)
                except Exception as e:
                    log(f"Lock acquire error: {e}")
            yield
        finally:
            try:
                if msvcrt:
                    msvcrt.locking(lk_f.fileno(), msvcrt.LK_UNLCK, 1)
            except:
                pass
            lk_f.close()
            
    def _read_data(self):
        data = {"sessions": {}}
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception as e:
                log(f"Error reading state file: {e}")
        return data
        
    def _write_data(self, data):
        tmp_file = self.state_file + ".tmp"
        try:
            with open(tmp_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            if os.path.exists(self.state_file):
                os.remove(self.state_file)
            os.rename(tmp_file, self.state_file)
        except Exception as e:
            log(f"Error writing state file: {e}")
            
    def get_session(self, session_id):
        with self._lock_session():
            data = self._read_data()
            sessions = data.get("sessions", {})
            return sessions.get(session_id)
            
    def save_session(self, session_id, conversation_id, last_step_idx):
        with self._lock_session():
            data = self._read_data()
            if "sessions" not in data:
                data["sessions"] = {}
            data["sessions"][session_id] = {
                "conversation_id": conversation_id,
                "last_step_idx": last_step_idx
            }
            self._write_data(data)

def extract_workspace_from_initialize(params):
    root_path = params.get("rootPath")
    if root_path:
        root_path = os.path.abspath(root_path)
        if os.path.isdir(root_path):
            return root_path
            
    root_uri = params.get("rootUri")
    if root_uri and root_uri.startswith("file://"):
        # Strip file:// or file:///
        raw_path = root_uri[7:]
        if raw_path.startswith("/"):
            raw_path = raw_path[1:]
        path = urllib.parse.unquote(raw_path).replace("/", "\\")
        if os.path.isdir(path):
            return path
            
    folders = params.get("workspaceFolders")
    if folders and isinstance(folders, list) and len(folders) > 0:
        uri = folders[0].get("uri")
        if uri and uri.startswith("file://"):
            raw_path = uri[7:]
            if raw_path.startswith("/"):
                raw_path = raw_path[1:]
            path = urllib.parse.unquote(raw_path).replace("/", "\\")
            if os.path.isdir(path):
                return path
                
    return None

# Protobuf Varint and Field Parsers
def read_varint(data, pos):
    result = 0
    shift = 0
    while pos < len(data):
        b = data[pos]
        result |= (b & 0x7f) << shift
        pos += 1
        if not (b & 0x80):
            break
        shift += 7
    return result, pos

def get_proto_field(blob, target_field):
    pos = 0
    while pos < len(blob):
        tag, pos = read_varint(blob, pos)
        field_number = tag >> 3
        wire_type = tag & 0x07
        if wire_type == 0:
            val, pos = read_varint(blob, pos)
        elif wire_type == 2:
            length, pos = read_varint(blob, pos)
            val = blob[pos:pos+length]
            pos += length
            if field_number == target_field:
                return val
        elif wire_type == 1:
            pos += 8
        elif wire_type == 5:
            pos += 4
        else:
            return None
    return None

def extract_text_from_step_payload(blob):
    try:
        field_20 = get_proto_field(blob, 20)
        if field_20 is None:
            return None
        field_1 = get_proto_field(field_20, 1)
        if field_1 is None:
            return None
        return field_1.decode('utf-8', errors='replace')
    except Exception as e:
        log(f"Error parsing protobuf payload: {e}")
        return None

# SQLite Reader
def read_response_from_db(conversations_dir, conversation_id, after_step_idx):
    db_path = os.path.join(conversations_dir, f"{conversation_id}.db")
    if not os.path.exists(db_path):
        return None
    conn = None
    try:
        abs_path = os.path.abspath(db_path).replace("\\", "/")
        db_uri = f"file:///{abs_path}?mode=ro"
        log(f"Opening DB path: {db_path} with URI: {db_uri}")
        conn = sqlite3.connect(db_uri, uri=True)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='steps';")
        if not cursor.fetchone():
            return None
            
        cursor.execute(
            "SELECT idx, step_payload FROM steps WHERE idx > ? AND step_type = 15 ORDER BY idx",
            (after_step_idx,)
        )
        rows = cursor.fetchall()
        
        max_idx = after_step_idx
        response_parts = []
        for idx, payload in rows:
            max_idx = max(max_idx, idx)
            text = extract_text_from_step_payload(payload)
            if text:
                response_parts.append(text)
                
        if not response_parts:
            return None
            
        return "\n".join(response_parts), max_idx
    except Exception as e:
        log(f"SQLite read error for {conversation_id}: {e}")
        return None
    finally:
        if conn:
            conn.close()

# CLI Path Lookup
def find_agy_path():
    env_path = os.environ.get("AGY_PATH")
    if env_path and os.path.exists(env_path):
        return env_path
    
    import shutil
    which_path = shutil.which("agy")
    if which_path:
        return which_path
    
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        default_path = os.path.join(local_app_data, "agy", "bin", "agy.exe")
        if os.path.exists(default_path):
            return default_path
            
    user_profile = os.environ.get("USERPROFILE") or os.path.expanduser("~")
    if user_profile:
        default_path = os.path.join(user_profile, "AppData", "Local", "agy", "bin", "agy.exe")
        if os.path.exists(default_path):
            return default_path
            
    return "agy"

# Directory Snapshots
def get_conversation_snapshot(conversations_dir):
    if not os.path.exists(conversations_dir):
        return set()
    try:
        files = os.listdir(conversations_dir)
        return {os.path.splitext(f)[0] for f in files if f.endswith(".db")}
    except Exception as e:
        log(f"Error snapshotting conversations directory: {e}")
        return set()

def scan_for_new_conv(conversations_dir, before_snapshot):
    try:
        after_snapshot = get_conversation_snapshot(conversations_dir)
        new_files = after_snapshot - before_snapshot
        if len(new_files) == 1:
            return list(new_files)[0]
        elif len(new_files) > 1:
            # Pick the newest
            latest_file = None
            latest_time = 0
            for f in new_files:
                p = os.path.join(conversations_dir, f + ".db")
                try:
                    t = os.path.getmtime(p)
                    if t > latest_time:
                        latest_time = t
                        latest_file = f
                except:
                    pass
            return latest_file
    except Exception as e:
        log(f"Error scanning for new conversation: {e}")
    return None

class ConversationIdHolder:
    def __init__(self, conv_id=None, last_step_idx=-1):
        self.lock = threading.Lock()
        self.conv_id = conv_id
        self.last_step_idx = last_step_idx
        
    def get(self):
        with self.lock:
            return self.conv_id
            
    def set(self, conv_id):
        with self.lock:
            self.conv_id = conv_id
            
    def get_last_step_idx(self):
        with self.lock:
            return self.last_step_idx
            
    def set_last_step_idx(self, idx):
        with self.lock:
            self.last_step_idx = idx

# Global Active Subprocesses
active_processes = {}
active_processes_lock = threading.Lock()

def send_update_notification(session_id, text):
    msg = {
        "jsonrpc": "2.0",
        "method": "session/update",
        "params": {
            "sessionId": session_id,
            "update": {
                "sessionUpdate": "agent_message_chunk",
                "content": {
                    "type": "text",
                    "text": text
                }
            }
        }
    }
    write_message(msg)

def poll_db_loop(session_id, conversations_dir, holder, stop_event):
    # Wait until conversation_id is bound
    conv_id = None
    while not stop_event.is_set():
        conv_id = holder.get()
        if conv_id:
            break
        time.sleep(0.1)
        
    if not conv_id:
        return
        
    initial_last_idx = holder.get_last_step_idx()
    log(f"Started polling DB {conv_id} from step {initial_last_idx}")
    
    sent_text = ""
    max_idx_seen = initial_last_idx
    
    def check_and_send():
        nonlocal sent_text, max_idx_seen
        try:
            res = read_response_from_db(conversations_dir, conv_id, initial_last_idx)
            if res:
                text, max_idx = res
                max_idx_seen = max(max_idx_seen, max_idx)
                if text.startswith(sent_text):
                    delta = text[len(sent_text):]
                    if delta:
                        log(f"Sending delta of length {len(delta)} (max_idx={max_idx})")
                        send_update_notification(session_id, delta)
                        sent_text = text
                else:
                    log(f"Warning: text mismatch. Re-sending all text.")
                    send_update_notification(session_id, text)
                    sent_text = text
        except Exception as ex:
            log(f"Error in check_and_send for session {session_id}: {ex}")
                
    try:
        while not stop_event.is_set():
            check_and_send()
            time.sleep(0.2)
            
        # Do one last check before exiting
        check_and_send()
        holder.set_last_step_idx(max_idx_seen)
    except Exception as e:
        log(f"Error in poll_db_loop: {e}")

def check_agy_logs_for_error(conversations_dir):
    try:
        import re
        cli_dir = os.path.dirname(conversations_dir)
        log_dir = os.path.join(cli_dir, "log")
        if not os.path.exists(log_dir):
            return None
        
        log_files = [os.path.join(log_dir, f) for f in os.listdir(log_dir) if f.startswith("cli-") and f.endswith(".log")]
        if not log_files:
            return None
        latest_log = max(log_files, key=os.path.getmtime)
        
        # Check if the log file was modified recently (e.g. within the last 30 seconds)
        # to prevent previous runs' errors from polluting successful runs
        if time.time() - os.path.getmtime(latest_log) > 30:
            return None
            
        with open(latest_log, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()[-100:]
            
        for line in reversed(lines):
            if "RESOURCE_EXHAUSTED" in line:
                hit_time_str = "unknown"
                reset_target_str = "unknown"
                resets_in = None
                
                # Format: E0605 23:37:18.381117
                ts_match = re.search(r'^[IWE](\d{2})(\d{2})\s+(\d{2}):(\d{2}):(\d{2})', line)
                if ts_match:
                    try:
                        month = int(ts_match.group(1))
                        day = int(ts_match.group(2))
                        hour = int(ts_match.group(3))
                        minute = int(ts_match.group(4))
                        second = int(ts_match.group(5))
                        current_year = datetime.datetime.now().year
                        hit_time = datetime.datetime(current_year, month, day, hour, minute, second)
                        hit_time_str = hit_time.strftime("%Y-%m-%d %H:%M:%S")
                        
                        resets_match = re.search(r'[Rr]esets in (\w+)', line)
                        if resets_match:
                            resets_in = resets_match.group(1)
                            pattern = re.compile(r'(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?')
                            m = pattern.match(resets_in)
                            if m:
                                h, m_val, s = m.groups()
                                hours = int(h) if h else 0
                                minutes = int(m_val) if m_val else 0
                                seconds = int(s) if s else 0
                                total_seconds = hours * 3600 + minutes * 60 + seconds
                                if total_seconds > 0:
                                    reset_time = hit_time + datetime.timedelta(seconds=total_seconds)
                                    reset_target_str = reset_time.strftime("%Y-%m-%d %H:%M:%S")
                    except Exception as ex:
                        log(f"Failed parsing log timestamp: {ex}")
                
                if hit_time_str == "unknown":
                    simple_ts = re.search(r'\d{2}:\d{2}:\d{2}', line)
                    if simple_ts:
                        hit_time_str = simple_ts.group(0)
                if resets_in is None:
                    resets_match = re.search(r'[Rr]esets in ([a-zA-Z0-9]+)', line)
                    if resets_match:
                        resets_in = resets_match.group(1)
                
                time_info = ""
                if hit_time_str != "unknown":
                    time_info += f"Quota was hit at {hit_time_str}. "
                if resets_in:
                    time_info += f"Reset target: {reset_target_str} (in {resets_in}). "
                
                return f"Error: Antigravity API Quota Exhausted (429). {time_info}Please check your AI Credit limits or wait for the quota window to reset."
            if "You are not logged into Antigravity" in line or "not authenticated" in line:
                return "Error: Not logged into Antigravity. Please run the login command in the IDE/CLI."
        return None
    except Exception as e:
        log(f"Error checking agy logs: {e}")
        return None

def handle_prompt(req_id, params, session_store, conversations_dir):
    session_id = params.get("sessionId")
    if not session_id:
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32602, "message": "missing sessionId"}
        }
        
    sess_data = session_store.get_session(session_id)
    if sess_data is None:
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32000, "message": f"unknown sessionId: {session_id}"}
        }
        
    conversation_id = sess_data.get("conversation_id")
    last_step_idx = sess_data.get("last_step_idx", -1)
    
    prompt_list = params.get("prompt", [])
    prompt_text = "\n".join([p.get("text", "") for p in prompt_list if p.get("type") == "text"])
    prompt_text = prompt_text.strip()
    
    before_snapshot = get_conversation_snapshot(conversations_dir)
    
    agy_exe = find_agy_path()
    args = [agy_exe]
    
    # Use current working directory as default
    cwd = os.getcwd()
    args.extend(["--add-dir", cwd])
    
    if conversation_id:
        args.extend(["--conversation", conversation_id])
        
    args.extend(["-p", prompt_text])
    args.append("--dangerously-skip-permissions")
    
    log(f"Spawning agy subprocess: {' '.join(args)} in {cwd}")
    
    stop_event = threading.Event()
    holder = ConversationIdHolder(conversation_id, last_step_idx)
    
    poll_thread = threading.Thread(
        target=poll_db_loop,
        args=(session_id, conversations_dir, holder, stop_event)
    )
    poll_thread.start()
    
    try:
        try:
            proc = subprocess.Popen(
                args,
                cwd=cwd,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace"
            )
        except Exception as e:
            log(f"Failed to spawn process: {e}")
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32000, "message": f"failed to run agy: {e}"}
            }
            
        with active_processes_lock:
            active_processes[session_id] = proc
            
        # Bind conversation ID in background if not already bound
        new_conv_id = None
        if not conversation_id:
            while proc.poll() is None and not new_conv_id:
                new_conv_id = scan_for_new_conv(conversations_dir, before_snapshot)
                if new_conv_id:
                    log(f"Detected new conversation ID: {new_conv_id}")
                    holder.set(new_conv_id)
                    break
                time.sleep(0.1)
                
        # Stderr logging thread
        def log_stderr(stream):
            try:
                for line in stream:
                    stripped = line.strip()
                    if stripped:
                        log(f"[agy stderr] {stripped}")
            except Exception as e:
                log(f"Error in log_stderr thread: {e}")
                    
        stderr_thread = threading.Thread(target=log_stderr, args=(proc.stderr,))
        stderr_thread.start()
        
        # Stdout reader thread to avoid blocking on full pipe
        stdout_lines = []
        def read_stdout(stream):
            try:
                for line in stream:
                    stdout_lines.append(line)
            except Exception as e:
                log(f"Error in read_stdout thread: {e}")
                
        stdout_thread = threading.Thread(target=read_stdout, args=(proc.stdout,))
        stdout_thread.start()
        
        # Wait for process to exit
        proc.wait()
        
        stderr_thread.join()
        stdout_thread.join()
        
        try:
            proc.stdout.close()
        except:
            pass
        try:
            proc.stderr.close()
        except:
            pass
        
        with active_processes_lock:
            active_processes.pop(session_id, None)
            
        # Check if conversation ID was created but not caught yet
        if not conversation_id and not holder.get():
            new_conv_id = scan_for_new_conv(conversations_dir, before_snapshot)
            if new_conv_id:
                log(f"Detected new conversation ID after exit: {new_conv_id}")
                holder.set(new_conv_id)
                
        # Sleep a bit to allow SQLite to finish writing
        time.sleep(0.5)
        
        if proc.returncode != 0:
            err_msg = f"agy.exe exited with non-zero code {proc.returncode}"
            log(f"Error: {err_msg}")
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {
                    "code": -32000,
                    "message": err_msg
                }
            }
            
        # Stop and join the polling thread BEFORE reading final states to prevent index race conditions
        stop_event.set()
        poll_thread.join(timeout=2.0)
        
        final_conv_id = holder.get()
        final_last_step_idx = holder.get_last_step_idx()
        
        if final_conv_id:
            session_store.save_session(session_id, final_conv_id, final_last_step_idx)
            log(f"Saved session {session_id}: conv_id={final_conv_id}, last_idx={final_last_step_idx}")
            
            if final_last_step_idx <= last_step_idx:
                err_msg = check_agy_logs_for_error(conversations_dir)
                if err_msg:
                    log(f"Detected error in agy logs: {err_msg}")
                    send_update_notification(session_id, err_msg)
                else:
                    stdout_text = "".join(stdout_lines).strip()
                    if stdout_text:
                        send_update_notification(session_id, stdout_text)
                    else:
                        send_update_notification(session_id, "Error: The agent completed the turn but produced no output. Please check the local agy logs.")
        else:
            stdout_text = "".join(stdout_lines).strip()
            if stdout_text:
                log("Fallback to stdout response because no conversation ID was found")
                send_update_notification(session_id, stdout_text)
            else:
                err_msg = check_agy_logs_for_error(conversations_dir)
                if err_msg:
                    send_update_notification(session_id, err_msg)
                else:
                    send_update_notification(session_id, "Error: The agent returned an empty response. Please check the local agy logs.")
                
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "stopReason": "end_turn"
            }
        }
    finally:
        with active_processes_lock:
            proc_to_kill = active_processes.pop(session_id, None)
            if proc_to_kill:
                try:
                    if proc_to_kill.poll() is None:
                        log(f"Cleaning up orphaned subprocess for session {session_id}")
                        proc_to_kill.terminate()
                        proc_to_kill.wait(timeout=1.0)
                except Exception as e:
                    log(f"Error cleaning up subprocess: {e}")
        stop_event.set()
        if poll_thread.is_alive():
            poll_thread.join(timeout=2.0)

def handle_cancel(req_id, params):
    session_id = params.get("sessionId")
    if not session_id:
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32602, "message": "missing sessionId"}
        }
        
    with active_processes_lock:
        proc = active_processes.get(session_id)
        if proc:
            log(f"Terminating subprocess for session {session_id}")
            proc.terminate()
            
    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "result": {}
    }

def main():
    provider = "gemini" # default fallback
    args = sys.argv[1:]
    
    if len(args) >= 2 and args[0] == "--provider":
        provider = args[1].lower()
        args = args[2:]
        
    if args:
        arg = args[0].lower()
        if arg in ("--version", "-v", "version"):
            # Return matching version for the provider as detected by Clairvoyance
            versions = {
                "copilot": "1.0.59",
                "claude": "2.1.165",
                "codex": "0.137.0",
                "gemini": "0.45.1",
                "cursor": "1.0.0"
            }
            print(versions.get(provider, "1.0.0"))
            sys.exit(0)
        elif arg in ("--help", "-h", "help"):
            print(f"Gemini ACP Shim (Masquerading as {provider})")
            sys.exit(0)
            
    session_store = SessionStore()
    user_profile = os.environ.get("USERPROFILE") or os.path.expanduser("~")
    conversations_dir = os.path.join(user_profile, ".gemini", "antigravity-cli", "conversations")
    
    while True:
        req = read_message()
        if req is None:
            break # EOF
            
        method = req.get("method")
        req_id = req.get("id")
        
        # If it's a notification (no id), we skip/ignore
        if req_id is None:
            continue
            
        params = req.get("params", {})
        
        log(f"Received request: {method} (id={req_id})")
        
        if method == "initialize":
            # Extract workspace path if available and configure local store
            workspace_path = extract_workspace_from_initialize(params)
            if workspace_path:
                session_store.set_workspace(workspace_path)
                
            resp = {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": 1,
                    "agentInfo": {"name": f"agy-shim-{provider}", "version": "1.0.0"},
                    "agentCapabilities": {"streaming": True, "loadSession": True}
                }
            }
            write_message(resp)
        elif method == "session/new":
            session_id = str(uuid.uuid4())
            session_store.save_session(session_id, None, -1)
            resp = {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "sessionId": session_id
                }
            }
            write_message(resp)
        elif method == "session/load":
            session_id = params.get("sessionId")
            sess_data = session_store.get_session(session_id) if session_id else None
            if sess_data is not None:
                resp = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "sessionId": session_id
                    }
                }
            else:
                resp = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32000, "message": f"unknown sessionId: {session_id}"}
                }
            write_message(resp)
        elif method == "session/prompt":
            # handle_prompt will send notifications, and return the final response dict
            resp = handle_prompt(req_id, params, session_store, conversations_dir)
            write_message(resp)
        elif method == "session/cancel":
            resp = handle_cancel(req_id, params)
            write_message(resp)
        elif method == "session/close":
            resp = {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {}
            }
            write_message(resp)
        else:
            resp = {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32601, "message": f"Method not found: {method}"}
            }
            write_message(resp)

if __name__ == "__main__":
    main()
