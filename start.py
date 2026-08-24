import os
import sys
import uvicorn

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GHL_DIR = os.path.join(BASE_DIR, "GHL RAG")
if os.path.exists(GHL_DIR):
    os.chdir(GHL_DIR)
    sys.path.insert(0, GHL_DIR)
else:
    sys.path.insert(0, BASE_DIR)

if __name__ == "__main__":
    port_str = os.getenv("PORT", "7860").strip()
    try:
        port = int(port_str)
    except ValueError:
        port = 7860

    host = "0.0.0.0"
    print(f"🚀 [Railway / Production] Launching GoHighLevel RAG on {host}:{port} (PORT env={os.getenv('PORT')}) ...")
    uvicorn.run("app:app", host=host, port=port, log_level="info")
