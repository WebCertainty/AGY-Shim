"""Local test double for the Antigravity CLI conversation lifecycle.

The fixture accepts the CLI arguments used by AGY-Shim and writes representative
SQLite step records with protobuf-shaped payloads. It intentionally models
undocumented implementation details only for deterministic tests and is not an
independent specification of Antigravity behavior.
"""

import sys
import os
import sqlite3
import uuid
import time
import json

def make_step_payload(text):
    text_bytes = text.encode('utf-8')
    inner = bytearray()
    inner.append(0x0A)
    l = len(text_bytes)
    while l > 127:
        inner.append((l & 0x7F) | 0x80)
        l >>= 7
    inner.append(l)
    inner.extend(text_bytes)
    
    outer = bytearray()
    outer.extend([0x08, 0x0F])
    outer.extend([0xA2, 0x01])
    l_inner = len(inner)
    while l_inner > 127:
        outer.append((l_inner & 0x7F) | 0x80)
        l_inner >>= 7
    outer.append(l_inner)
    outer.extend(inner)
    return bytes(outer)

def main():
    # Parse arguments
    conversation_id = None
    prompt = ""
    
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--conversation" and i + 1 < len(args):
            conversation_id = args[i+1]
            i += 2
        elif args[i] in ("-p", "--prompt") and i + 1 < len(args):
            prompt = args[i+1]
            i += 2
        else:
            i += 1
            
    # Apply mock delay if requested via environment variable
    delay_str = os.environ.get("AGY_MOCK_SLOW_DELAY")
    if delay_str:
        try:
            time.sleep(float(delay_str))
        except ValueError:
            time.sleep(1.0)
            
    user_profile = os.environ.get("USERPROFILE") or os.path.expanduser("~")
    with open(os.path.join(user_profile, "mock_invocation.json"), "w", encoding="utf-8") as f:
        json.dump({
            "args": args,
            "cwd": os.getcwd(),
            "secret_inherited": "AGY_TEST_PARENT_SECRET" in os.environ,
        }, f)
    conversations_dir = os.path.join(user_profile, ".gemini", "antigravity-cli", "conversations")
    os.makedirs(conversations_dir, exist_ok=True)
    
    if not conversation_id:
        conversation_id = str(uuid.uuid4())
        
    db_path = os.path.join(conversations_dir, f"{conversation_id}.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS steps (
            idx INTEGER PRIMARY KEY,
            step_type INTEGER,
            step_payload BLOB
        )
    """)
    conn.commit()
    
    # Get current max index
    cursor.execute("SELECT MAX(idx) FROM steps")
    row = cursor.fetchone()
    max_idx = row[0] if row[0] is not None else -1
    
    # Determine response based on prompt
    response_text = "OK"
    if "what word did i" in prompt.lower() or "remember?" in prompt.lower() or "recall" in prompt.lower():
        response_text = "ORANGE_BANANA"
        
    # Write steps with simulated delay to allow polling thread to capture live updates
    max_idx += 1
    cursor.execute("INSERT OR REPLACE INTO steps (idx, step_type, step_payload) VALUES (?, ?, ?)",
                   (max_idx, 14, b""))
    conn.commit()
    time.sleep(0.1)
    
    max_idx += 1
    cursor.execute("INSERT OR REPLACE INTO steps (idx, step_type, step_payload) VALUES (?, ?, ?)",
                   (max_idx, 98, b""))
    conn.commit()
    time.sleep(0.1)
    
    max_idx += 1
    cursor.execute("INSERT OR REPLACE INTO steps (idx, step_type, step_payload) VALUES (?, ?, ?)",
                   (max_idx, 15, make_step_payload(response_text)))
    conn.commit()
    time.sleep(0.1)
    
    max_idx += 1
    cursor.execute("INSERT OR REPLACE INTO steps (idx, step_type, step_payload) VALUES (?, ?, ?)",
                   (max_idx, 17, b""))
    conn.commit()
    
    conn.close()
    print(response_text)

if __name__ == "__main__":
    main()
