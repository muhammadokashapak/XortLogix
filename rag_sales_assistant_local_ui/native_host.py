# native_host.py
"""
Native Messaging Host Bridge for Sales Co-Pilot Chrome Extension.
Listens to stdio messages from Chrome extension, queries local FastAPI backend (port 8000),
and returns structured responses via standard native messaging binary frames.
"""

import sys
import os
import struct
import json
import urllib.request
import urllib.error

# Set binary stdin/stdout streams
if sys.platform == "win32":
    import msvcrt
    msvcrt.setmode(sys.stdin.fileno(), os.O_BINARY)
    msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)

BACKEND_API_URL = "http://127.0.0.1:8000/api/query"

def read_message():
    """Reads a length-prefixed JSON message from Chrome stdin."""
    raw_length = sys.stdin.buffer.read(4)
    if not raw_length or len(raw_length) < 4:
        return None
    message_length = struct.unpack('@I', raw_length)[0]
    message_bytes = sys.stdin.buffer.read(message_length)
    if len(message_bytes) < message_length:
        return None
    return json.loads(message_bytes.decode('utf-8'))

def send_message(message):
    """Sends a length-prefixed JSON message back to Chrome stdout."""
    encoded_bytes = json.dumps(message, ensure_ascii=False).encode('utf-8')
    header = struct.pack('@I', len(encoded_bytes))
    sys.stdout.buffer.write(header)
    sys.stdout.buffer.write(encoded_bytes)
    sys.stdout.buffer.flush()

def query_local_backend(text):
    """Queries the local FastAPI server."""
    try:
        data = json.dumps({"query": text, "top_k": 3}).encode('utf-8')
        req = urllib.request.Request(
            BACKEND_API_URL,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=3) as resp:
            if resp.status == 200:
                body = resp.read().decode('utf-8')
                return json.loads(body)
    except Exception as e:
        return {"success": False, "error": str(e)}
    return {"success": False, "error": "Unknown backend error"}

def main():
    while True:
        try:
            msg = read_message()
            if msg is None:
                break
            query_text = msg.get("text") or msg.get("query") or ""
            if query_text:
                res = query_local_backend(query_text)
                send_message({"status": "ok", "data": res})
            else:
                send_message({"status": "pong", "message": "Sales Co-Pilot Native Host Active"})
        except Exception as e:
            send_message({"status": "error", "error": str(e)})

if __name__ == "__main__":
    main()
