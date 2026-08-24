import os
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

import uvicorn

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

if __name__ == "__main__":
    port_str = os.getenv("PORT", "7860").strip()
    try:
        port = int(port_str)
    except ValueError:
        port = 7860

    host = "127.0.0.1"
    print(f"Starting XortLogix High Level Assistant on http://{host}:{port} ...", flush=True)
    uvicorn.run("app:app", host=host, port=port, log_level="info", reload=False)
