# run_assistant.py
"""
One-Click Launcher for Real-Time Local AI Sales Assistant (Voice RAG Co-Pilot).
Starts the FastAPI + WebSocket backend and automatically opens the modern Glassmorphism UI.
"""

import sys
import os
import time
import webbrowser
import threading
import uvicorn
import requests

# Fix Windows console unicode issues
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
if hasattr(sys.stderr, 'reconfigure'):
    try:
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

def check_ollama():
    try:
        r = requests.get("http://127.0.0.1:11434/api/tags", timeout=1.5)
        return r.status_code == 200
    except Exception:
        return False

def open_browser():
    time.sleep(1.5)
    print("\n[*] Opening Real-Time Sales Co-Pilot UI at http://127.0.0.1:8000 ...")
    webbrowser.open("http://127.0.0.1:8000")

def free_port(port=8000):
    """Automatically terminates any lingering process occupying port 8000 on Windows."""
    try:
        import subprocess
        out = subprocess.check_output(f"netstat -ano | findstr :{port}", shell=True).decode(errors='ignore')
        for line in out.strip().splitlines():
            if "LISTENING" in line:
                parts = line.strip().split()
                pid = parts[-1]
                if pid and pid != str(os.getpid()):
                    print(f"[*] Freeing port {port} from previous process (PID: {pid})...")
                    subprocess.run(f"taskkill /F /PID {pid}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    time.sleep(0.5)
    except Exception:
        pass

def run_server_loop():
    free_port(8000)
    while True:
        try:
            uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=False, log_level="info")
            break
        except KeyboardInterrupt:
            print("\n[!] Server stopped by user (Ctrl+C).")
            break
        except Exception as e:
            if "10048" in str(e):
                print("[*] Port 8000 occupied. Automatically releasing port...")
                free_port(8000)
                time.sleep(1)
            else:
                print(f"\n[!] Server error: {e}")
                print("[*] Restarting in 2 seconds...")
                time.sleep(2)

def main():
    print("=" * 75)
    print(" [*] REAL-TIME LOCAL AI SALES ASSISTANT (VOICE RAG CO-PILOT)")
    print("=" * 75)
    print(" - Audio & Voice: Web Speech API + Local OpenAI Whisper")
    print(" - Retrieval Engine: ChromaDB + Dynamic Playbook Ingestion & Vector Embeddings")
    print(" - LLM Inference: Local Ollama (llama3.2:3b / 1b / phi3)")
    print(" - UI Interface: Cyber-Dark Glassmorphism Web Cockpit + Floating Zoom HUD")
    print("=" * 75)
    
    ollama_ok = check_ollama()
    if ollama_ok:
        print(" [+] Ollama server detected at http://127.0.0.1:11434")
    else:
        print(" [!] Note: Ollama is not currently running.")
        print("     The Sales Assistant will operate in Direct KB Mode with instant <20ms responses.")
        print("     To enable Ollama LLM synthesis, run 'ollama serve' in a separate terminal.")
    
    import socket
    local_ip = "127.0.0.1"
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
    except Exception:
        pass

    print("\n [+] Server listening on all interfaces:")
    print(f"     - Local PC:   http://127.0.0.1:8000")
    print(f"     - Mobile/LAN: http://{local_ip}:8000")
    print("     Press Ctrl+C to stop the server.\n")

    # Open browser in a separate background thread
    threading.Thread(target=open_browser, daemon=True).start()

    # Run resilient server loop
    run_server_loop()

if __name__ == "__main__":
    main()


