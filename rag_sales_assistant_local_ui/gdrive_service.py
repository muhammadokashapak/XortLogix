# gdrive_service.py
"""
Google Drive API v3 Backup Service for Admin Account.
Automatically organizes uploaded strategy files under:
Sales_Bot_Client_Documents / User_{user_email} / filename
"""

import os
import io
import json
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger("GDriveService")

SCOPES = ['https://www.googleapis.com/auth/drive']
ROOT_FOLDER_NAME = "Sales_Bot_Client_Documents"

class GoogleDriveService:
    def __init__(self):
        self.service = None
        self.is_connected = False
        self.auth_type = "None"
        self.root_folder_id = None
        self._init_drive_client()

    def _init_drive_client(self):
        """Initializes Google Drive API client using Service Account or OAuth credentials."""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        sa_path = os.path.join(base_dir, "service_account.json")
        oauth_path = os.path.join(base_dir, "credentials.json")

        try:
            from googleapiclient.discovery import build
            from google.oauth2 import service_account

            # 1. Try Service Account JSON
            if os.path.exists(sa_path):
                creds = service_account.Credentials.from_service_account_file(
                    sa_path, scopes=SCOPES
                )
                self.service = build('drive', 'v3', credentials=creds)
                self.is_connected = True
                self.auth_type = "Service Account"
                logger.info(f"⚡ Google Drive connected via Service Account ({sa_path})")
                return

            # 2. Try Environment Variable JSON string
            sa_env = os.environ.get("GDRIVE_SERVICE_ACCOUNT_JSON", "").strip()
            if sa_env:
                sa_info = json.loads(sa_env)
                creds = service_account.Credentials.from_service_account_info(
                    sa_info, scopes=SCOPES
                )
                self.service = build('drive', 'v3', credentials=creds)
                self.is_connected = True
                self.auth_type = "Service Account (Env)"
                logger.info("⚡ Google Drive connected via Service Account Environment Variable")
                return

            logger.info("ℹ️ Google Drive running in Standby/Simulated Mode (Place 'service_account.json' to link Live Drive).")
            self.auth_type = "Standby Simulation Mode"
        except Exception as e:
            logger.warning(f"Google Drive initialization note: {e}")
            self.auth_type = f"Error: {e}"

    def get_or_create_folder(self, folder_name: str, parent_id: Optional[str] = None) -> Optional[str]:
        """Finds or creates a folder with the given name under parent_id."""
        if not self.service:
            return f"mock_folder_{folder_name}"

        try:
            # Query existing folder
            query = f"mimeType = 'application/vnd.google-apps.folder' and name = '{folder_name}' and trashed = false"
            if parent_id:
                query += f" and '{parent_id}' in parents"
            
            results = self.service.files().list(
                q=query, spaces='drive', fields='files(id, name)', pageSize=1
            ).execute()
            files = results.get('files', [])

            if files:
                return files[0]['id']

            # Create new folder
            folder_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            if parent_id:
                folder_metadata['parents'] = [parent_id]

            folder = self.service.files().create(body=folder_metadata, fields='id').execute()
            logger.info(f"📁 Created Google Drive folder: '{folder_name}' (ID: {folder.get('id')})")
            return folder.get('id')
        except Exception as e:
            logger.error(f"Error creating/fetching folder '{folder_name}': {e}")
            return None

    def upload_document(
        self,
        file_bytes: bytes,
        filename: str,
        user_email: str,
        mime_type: str = "application/octet-stream"
    ) -> Dict[str, Any]:
        """
        Uploads a strategy document into Admin Drive under:
        Sales_Bot_Client_Documents / User_{user_email} / filename
        """
        clean_email = user_email.strip().lower()
        subfolder_name = f"User_{clean_email.replace('@', '_at_')}"

        if not self.service:
            # Simulated Drive Backup when service_account.json not yet supplied
            import uuid
            mock_id = f"gdrive_{uuid.uuid4().hex[:12]}"
            mock_link = f"https://drive.google.com/file/d/{mock_id}/view?usp=sharing"
            logger.info(f"☁️ [SIMULATED GDRIVE BACKUP] Saved '{filename}' to folder '{ROOT_FOLDER_NAME}/{subfolder_name}'")
            return {
                "success": True,
                "file_id": mock_id,
                "web_view_link": mock_link,
                "folder_name": subfolder_name,
                "mode": "simulation",
                "message": "File backed up to Simulated Drive (Live Drive activates automatically when service_account.json is added)."
            }

        try:
            from googleapiclient.http import MediaIoBaseUpload

            # 1. Resolve Root Folder
            root_id = self.get_or_create_folder(ROOT_FOLDER_NAME)
            if not root_id:
                raise Exception("Could not resolve root backup folder.")

            # 2. Resolve User Subfolder
            user_folder_id = self.get_or_create_folder(subfolder_name, parent_id=root_id)
            if not user_folder_id:
                user_folder_id = root_id

            # 3. Upload File
            file_metadata = {
                'name': filename,
                'parents': [user_folder_id]
            }
            media = MediaIoBaseUpload(io.BytesIO(file_bytes), mimetype=mime_type, resumable=True)

            uploaded_file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, name, webViewLink, webContentLink'
            ).execute()

            file_id = uploaded_file.get('id')
            web_link = uploaded_file.get('webViewLink') or f"https://drive.google.com/file/d/{file_id}/view"

            logger.info(f"☁️ [GDRIVE SUCCESS] Uploaded '{filename}' to Google Drive: {web_link}")

            return {
                "success": True,
                "file_id": file_id,
                "web_view_link": web_link,
                "folder_id": user_folder_id,
                "folder_name": subfolder_name,
                "mode": "live"
            }
        except Exception as e:
            logger.error(f"Google Drive upload error: {e}")
            import uuid
            mock_id = f"err_{uuid.uuid4().hex[:8]}"
            return {
                "success": False,
                "error": str(e),
                "file_id": mock_id,
                "web_view_link": f"https://drive.google.com/drive/folders/{ROOT_FOLDER_NAME}",
                "mode": "error_fallback"
            }

# Singleton instance
gdrive_service = GoogleDriveService()
