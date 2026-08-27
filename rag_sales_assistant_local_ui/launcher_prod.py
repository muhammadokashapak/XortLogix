# launcher_prod.py
"""
Production Entrypoint for Sales Co-Pilot AI (PyInstaller Bundle).
Handles runtime environment path resolution (sys._MEIPASS vs local folder),
releases port 8000 if occupied, initializes SQLite database schemas,
boots the FastAPI server, and launches the UI in default browser.
"""

import sys
import os
import time
import socket
import threading
import webbrowser
import logging

# Set Windows AppUserModelID so Taskbar displays official XOrtLogix icon
if sys.platform == 'win32':
    try:
        import ctypes
        myappid = "xortlogix.salescopilot.ai.1.0"
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except Exception:
        pass

# Ensure UTF-8 output encoding on Windows console
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

# Determine runtime base directory
if getattr(sys, 'frozen', False):
    # Running inside PyInstaller frozen executable
    BASE_DIR = os.path.dirname(sys.executable)
    BUNDLE_DIR = getattr(sys, '_MEIPASS', BASE_DIR)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    BUNDLE_DIR = BASE_DIR

# Set environment variables for server
os.environ["SALES_COPILOT_BASE_DIR"] = BASE_DIR
os.environ["SALES_COPILOT_BUNDLE_DIR"] = BUNDLE_DIR

# Ensure sys.path includes bundle directory
if BUNDLE_DIR not in sys.path:
    sys.path.insert(0, BUNDLE_DIR)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Configure logging
log_file = os.path.join(BASE_DIR, "sales_copilot.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(log_file, encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("SalesCoPilotLauncher")

def free_port(port=8000):
    """Terminates any process occupying port 8000."""
    try:
        import subprocess
        out = subprocess.check_output(f"netstat -ano | findstr :{port}", shell=True).decode(errors='ignore')
        for line in out.strip().splitlines():
            if "LISTENING" in line:
                parts = line.strip().split()
                pid = parts[-1]
                if pid and pid != str(os.getpid()):
                    logger.info(f"Releasing port {port} from process PID {pid}...")
                    subprocess.run(f"taskkill /F /PID {pid}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    time.sleep(0.5)
    except Exception as e:
        logger.debug(f"Port clean check note: {e}")

def open_ui():
    """Opens default browser to local app URL after server starts."""
    time.sleep(1.8)
    url = "http://127.0.0.1:8000"
    logger.info(f"Opening Sales Co-Pilot UI at {url}")
    try:
        webbrowser.open(url)
    except Exception as e:
        logger.error(f"Failed to open browser: {e}")

def main():
    logger.info("=" * 65)
    logger.info("  ⚡ SALES CO-PILOT AI • ENTERPRISE DESKTOP LAUNCHER")
    logger.info("=" * 65)
    logger.info(f"Executable Path: {sys.executable}")
    logger.info(f"Base Directory:   {BASE_DIR}")
    logger.info(f"Bundle Directory: {BUNDLE_DIR}")

    free_port(8000)

    # Import server app after paths are set up
    try:
        import models_db
        models_db.init_db()
        logger.info("Database schemas initialized.")
    except Exception as e:
        logger.error(f"Database initialization warning: {e}")

    try:
        import uvicorn
        from server import app

        # Launch UI in background thread
        threading.Thread(target=open_ui, daemon=True).start()

        port = int(os.environ.get("PORT", 8000))
        logger.info(f"Starting server on http://127.0.0.1:{port}...")
        uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")

    except KeyboardInterrupt:
        logger.info("Application stopped by user.")
    except Exception as e:
        logger.critical(f"Fatal launcher error: {e}", exc_info=True)
        time.sleep(3)

if __name__ == "__main__":
    main()
