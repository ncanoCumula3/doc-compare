"""
drive_service/drive.py
======================
Google Drive download. Auth + download copied verbatim (trimmed) from the
payroll app's services/proposal_store.py:136-187, so it uses the SAME service
account / key.

Source order for credentials:
  1. GOOGLE_SERVICE_ACCOUNT_JSON env var (deployed)
  2. service-account.json on disk (local dev)
Service account: apt-upload-files@attentive-apt.iam.gserviceaccount.com
"""

import io
import os

SERVICE_ACCOUNT_FILE = os.environ.get(
    "SERVICE_ACCOUNT_FILE",
    os.path.join(os.path.dirname(__file__), "service-account.json"))
CACHE_DIR = os.environ.get("DRIVE_CACHE_DIR",
                           os.path.join(os.path.dirname(__file__), "_drive_cache"))

_drive = None
_drive_attempted = False


def _connect_drive():
    """Lazily build a Drive v3 client. Returns the service or None."""
    global _drive, _drive_attempted
    if _drive_attempted:
        return _drive
    _drive_attempted = True
    sa_json_env = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    if not sa_json_env and not os.path.exists(SERVICE_ACCOUNT_FILE):
        print("  Drive: no GOOGLE_SERVICE_ACCOUNT_JSON env var and no service-account.json on disk")
        return None
    try:
        import json as _json
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
        scopes = ["https://www.googleapis.com/auth/drive"]
        if sa_json_env:
            info = _json.loads(sa_json_env)
            creds = service_account.Credentials.from_service_account_info(info, scopes=scopes)
        else:
            creds = service_account.Credentials.from_service_account_file(
                SERVICE_ACCOUNT_FILE, scopes=scopes)
        _drive = build("drive", "v3", credentials=creds, cache_discovery=False)
        print(f"  Drive: connected as {creds.service_account_email}")
    except Exception as e:
        print(f"  Drive: connection failed ({e.__class__.__name__}: {e})")
        _drive = None
    return _drive


def get_name(google_file_id):
    """Best-effort original filename for a Drive file id."""
    drive = _connect_drive()
    if drive is None:
        return google_file_id
    try:
        meta = drive.files().get(fileId=google_file_id,
                                 fields="name",
                                 supportsAllDrives=True).execute()
        return meta.get("name", google_file_id)
    except Exception:
        return google_file_id


def download(google_file_id, local_path=None):
    """Download a Drive file by id to local_path (cached). Returns the path or None."""
    drive = _connect_drive()
    if drive is None:
        return None
    if local_path is None:
        os.makedirs(CACHE_DIR, exist_ok=True)
        local_path = os.path.join(CACHE_DIR, google_file_id)
    if os.path.exists(local_path) and os.path.getsize(local_path) > 0:
        return local_path
    try:
        from googleapiclient.http import MediaIoBaseDownload
        req = drive.files().get_media(fileId=google_file_id)
        buf = io.BytesIO()
        downloader = MediaIoBaseDownload(buf, req)
        done = False
        while not done:
            _, done = downloader.next_chunk()
        os.makedirs(os.path.dirname(local_path) or ".", exist_ok=True)
        with open(local_path, "wb") as f:
            f.write(buf.getvalue())
        return local_path
    except Exception as e:
        print(f"  Drive download failed for {google_file_id}: {e}")
        return None


def configured():
    return _connect_drive() is not None
