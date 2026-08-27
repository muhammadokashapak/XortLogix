# 📦 Sales Co-Pilot AI • Installer Build & Release Guide

This document describes how to build and distribute the standalone Windows Desktop Installer (`Sales_CoPilot_Setup.exe`).

---

## 🚀 One-Click Build Command

To generate the single-click installer executable:

```powershell
python build_installer.py
```

This automated pipeline performs:
1. **PyInstaller Execution:** Bundles the Python runtime, FastAPI server, ChromaDB vector engine, C-extensions (`soundcard`, `av`), and static assets into `dist/SalesCoPilot/`.
2. **Inno Setup Compilation:** Compiles `installer_setup.iss` using `ISCC.exe` into a single Windows Setup executable: `installer_output/Sales_CoPilot_Setup.exe`.

---

## 📁 Installer Features & Experience

* **Single Setup Executable:** `Sales_CoPilot_Setup.exe` (~100-200MB self-contained installer).
* **Zero Technical Prerequisites:** End users do **NOT** need Python, Node.js, npm, pip, or CMD commands.
* **Component Options:**
  - `☑ Core Sales Co-Pilot Desktop Engine & Web Cockpit (Required)`
  - `☑ Chrome Extension Integration (Floating HUD for Zoom & Google Meet)`
* **Auto-Configuration:**
  - Installs binaries cleanly to `%LocalAppData%\Programs\SalesCoPilot`.
  - Configures Native Messaging Host (`com.xortlogix.salescopilot`).
  - Creates Desktop & Start Menu Shortcuts.
  - Automatically handles port 8000 cleanup.
* **Clean Uninstaller:** Includes `unins000.exe` for seamless removal.
