# auth_gdrive_oauth.py
"""
1-Click OAuth 2.0 Authenticator for Personal Google Drive (15 GB Storage).
Run this once after placing credentials.json (OAuth Client ID).
It opens your browser, asks you to login to your Google account, and creates token.json.
"""

import os
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

def authenticate_google_drive():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    creds_path = os.path.join(base_dir, "credentials.json")
    token_path = os.path.join(base_dir, "token.json")

    if not os.path.exists(creds_path):
        print("❌ Error: 'credentials.json' not found in project folder!")
        print("Please download OAuth 2.0 Client ID credentials from Google Cloud Console.")
        return False

    SCOPES = ['https://www.googleapis.com/auth/drive']

    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.oauth2.credentials import Credentials

        print("=======================================================")
        print(" 🚀 GOOGLE DRIVE 1-CLICK OAUTH AUTHENTICATION")
        print("=======================================================")
        print("1. Opening your default web browser...")
        print("2. Please select your Google Account (e.g. okashaxortlogix@gmail.com)")
        print("3. Click 'Continue' / 'Allow' to grant Google Drive backup access.")
        print("=======================================================\n")

        flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
        creds = flow.run_local_server(port=0)

        with open(token_path, 'w', encoding='utf-8') as token_file:
            token_file.write(creds.to_json())

        print("\n✅ SUCCESS! Google Drive OAuth Token generated and saved to 'token.json'.")
        print("⚡ Full 15 GB personal storage is now active for automatic strategy backups!")
        return True

    except Exception as e:
        print(f"\n❌ Authentication error: {e}")
        return False

if __name__ == "__main__":
    authenticate_google_drive()
