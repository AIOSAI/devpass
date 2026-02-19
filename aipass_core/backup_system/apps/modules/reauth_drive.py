#!/usr/bin/env python3
"""
Standalone Google Drive re-authentication script.
Uses console-based OAuth flow (no browser needed).
Prints a URL for the user to visit, then accepts the auth code.
"""

import sys
import json
from pathlib import Path

SCOPES = ['https://www.googleapis.com/auth/drive.file']
CREDS_PATH = Path.home() / '.aipass' / 'drive_creds.json'
CLIENT_SECRETS = Path(__file__).parent.parent / 'credentials.json'

def reauth():
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build
    except ImportError as e:
        print(f"Missing package: {e}")
        print(f"Install: {sys.executable} -m pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")
        return False

    # Step 1: Try refreshing existing token first
    if CREDS_PATH.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(CREDS_PATH), SCOPES)
            if creds and creds.expired and creds.refresh_token:
                print("Attempting token refresh...")
                creds.refresh(Request())
                with open(CREDS_PATH, 'w') as f:
                    f.write(creds.to_json())
                print("Token refreshed successfully!")
                # Test connection
                service = build('drive', 'v3', credentials=creds)
                about = service.about().get(fields="user").execute()
                print(f"Authenticated as: {about['user']['emailAddress']}")
                return True
        except Exception as e:
            print(f"Refresh failed (expected): {e}")
            print("Proceeding with full re-authentication...")

    # Step 2: Full OAuth flow via console
    if not CLIENT_SECRETS.exists():
        print(f"ERROR: Client secrets not found at: {CLIENT_SECRETS}")
        return False

    print("\n" + "="*60)
    print("GOOGLE DRIVE RE-AUTHENTICATION")
    print("="*60)

    flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRETS), SCOPES)

    # Use run_local_server but with open_browser=False so it just prints the URL
    print("\nStarting local auth server...")
    print("A URL will be printed below - open it in your browser.")
    print("After authorizing, the browser will redirect to localhost.\n")

    try:
        creds = flow.run_local_server(port=8085, open_browser=False)
    except Exception as e:
        print(f"Auth flow error: {e}")
        return False

    # Save new credentials
    CREDS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CREDS_PATH, 'w') as f:
        f.write(creds.to_json())
    print(f"\nCredentials saved to: {CREDS_PATH}")

    # Test connection
    try:
        service = build('drive', 'v3', credentials=creds)
        about = service.about().get(fields="user,storageQuota").execute()
        email = about['user']['emailAddress']
        quota = about.get('storageQuota', {})
        usage_gb = int(quota.get('usage', 0)) / (1024**3)
        limit_gb = int(quota.get('limit', 0)) / (1024**3)
        print(f"\nAuthenticated as: {email}")
        print(f"Storage: {usage_gb:.2f} GB / {limit_gb:.2f} GB")
        print("\nRe-authentication SUCCESSFUL!")
        return True
    except Exception as e:
        print(f"Connection test failed: {e}")
        return False

if __name__ == "__main__":
    success = reauth()
    sys.exit(0 if success else 1)
