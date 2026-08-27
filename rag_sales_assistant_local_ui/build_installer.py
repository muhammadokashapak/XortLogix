import os
import sys
import subprocess

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ISCC_PATH = r"C:\Users\pc\AppData\Local\Programs\Inno Setup 6\ISCC.exe"
def run_cmd(cmd, cwd=BASE_DIR):
    print(f"\n[*] Running: {cmd}")
    res = subprocess.run(cmd, shell=True, cwd=cwd)
    if res.returncode != 0:
        print(f"[!] Command failed with exit code {res.returncode}")
        return False
    return True
def main():
    print("=" * 70)
    print(" [*] BUILDING SALES CO-PILOT AI STANDALONE WINDOWS INSTALLER")
    print("=" * 70)
    iscc_bin = ISCC_PATH if os.path.exists(ISCC_PATH) else "ISCC.exe"
    print("\n[*] Packaging Python application with PyInstaller...")
    if not run_cmd(f'"{sys.executable}" -m PyInstaller --clean --noconfirm sales_copilot.spec'):
        sys.exit(1)
    dist_exe = os.path.join(BASE_DIR, "dist", "SalesCoPilot", "SalesCoPilot.exe")
    print(f"\n[+] PyInstaller executable bundle generated at: {dist_exe}")
    dist_dir = os.path.join(BASE_DIR, "dist", "SalesCoPilot")

    iss_file = os.path.join(BASE_DIR, "installer_setup.iss")
    output_dir = os.path.join(BASE_DIR, "installer_output")
    os.makedirs(output_dir, exist_ok=True)
    print("\n[*] Compiling Windows Installer with Inno Setup Compiler...")
    if run_cmd(f'"{iscc_bin}" "{iss_file}"'):
        setup_exe = os.path.join(output_dir, "Sales_CoPilot_Setup.exe")
        print("\n" + "=" * 70)
        print(" [+] SUCCESS! Single-Click Windows Desktop Installer generated:")
        print(f"     Path: {setup_exe}")
        print("=" * 70)
    else:
        print("\n[!] Failed to compile Inno Setup script.")
        sys.exit(1)
if __name__ == "__main__":
    main()