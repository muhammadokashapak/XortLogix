import os
import sys
import uvicorn

# Ensure current directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    port_str = os.getenv("PORT", "7860").strip()
    try:
        port = int(port_str)
    except ValueError:
        port = 7860

    host = "0.0.0.0"
    print(f"🚀 [Railway / Production] Launching GoHighLevel RAG on {host}:{port} (PORT env={os.getenv('PORT')}) ...")
    uvicorn.run("app:app", host=host, port=port, log_level="info")
