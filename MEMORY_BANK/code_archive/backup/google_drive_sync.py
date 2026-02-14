#!/usr/bin/env python3

# =============================================
# META DATA HEADER
# Name: google_drive_sync.py - Google Drive Integration for AIPass Backup System
# Date: 2025-10-30
# Version: 2.1.0
# Category: backup_system
#
# CHANGELOG (Max 5 entries - remove oldest when adding new):
#   - v2.1.0 (2025-10-30): Enhanced UI with colors, storage quota display, folder creation messages
#   - v2.0.0 (2025-09-03): Upgraded to AIPass standards with 3-file JSON, logging, sections
#   - v1.0.0 (2025-09-02): Initial implementation with OAuth, nested folders
# =============================================

"""
Google Drive Sync for AIPass Backup System

Integrates with Google OAuth to upload versioned backups to Google Drive.
Creates organized folder structure: /AIPass Backups/[project]/[files]

Features:
- OAuth2 authentication with token persistence
- Nested folder structure preservation
- Size-based change detection
- Update instead of duplicate uploads
- 3-file JSON standard compliance
"""

# =============================================
# IMPORTS
# =============================================

# Infrastructure import pattern - Direct system access
import sys
from pathlib import Path
AIPASS_ROOT = Path.home() / "aipass_core"
BACKUP_SYSTEM_ROOT = AIPASS_ROOT / "backup_system"
sys.path.append(str(AIPASS_ROOT))  # To ecosystem root
from prax.apps.prax_logger import system_logger as logger

# Standard imports
import json
import os
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple

# Google API imports
try:
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    GOOGLE_API_AVAILABLE = True
except ImportError as e:
    GOOGLE_API_AVAILABLE = False
    import sys
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    python_path = sys.executable
    error_msg = f"Google API packages not found in Python {python_version} ({python_path})"
    logger.error(f"{error_msg} - Missing module: {e.name if hasattr(e, 'name') else str(e)}")
    logger.error(f"Install with: {python_path} -m pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")

# =============================================
# CONSTANTS & CONFIG
# =============================================

# OAuth scopes for Drive access
SCOPES = ['https://www.googleapis.com/auth/drive.file']

# Module configuration (module is in apps/, so parent.parent gets to branch root)
MODULE_NAME = "google_drive_sync"
JSON_DIR = Path(__file__).parent.parent / "backup_system_json"
CONFIG_FILE = JSON_DIR / f"{MODULE_NAME}_config.json"
DATA_FILE = JSON_DIR / f"{MODULE_NAME}_data.json"
LOG_FILE = JSON_DIR / f"{MODULE_NAME}_log.json"

# =============================================
# HELPER FUNCTIONS
# =============================================

def load_config() -> Dict[str, Any]:
    """Load module configuration from JSON file"""
    try:
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # Create default config
            default_config = {
                "skill_name": MODULE_NAME,
                "timestamp": datetime.now().isoformat(),
                "config": {
                    "enabled": True,
                    "version": "2.0.0",
                    "auto_sync": False,
                    "skip_unchanged": True,
                    "api_settings": {
                        "timeout_seconds": 300,
                        "retry_attempts": 3,
                        "chunk_size_mb": 10
                    }
                }
            }
            save_config(default_config)
            return default_config
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        return {}

def save_config(config: Dict[str, Any]):
    """Save module configuration to JSON file"""
    try:
        JSON_DIR.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to save config: {e}")

def load_data() -> Dict[str, Any]:
    """Load runtime data from JSON file"""
    try:
        if DATA_FILE.exists():
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # Create default data
            default_data = {
                "last_updated": datetime.now().isoformat(),
                "runtime_state": {
                    "current_status": "inactive",
                    "last_sync": None,
                    "cached_folders": {},
                    "file_tracker": {},
                    "authenticated": False
                },
                "statistics": {
                    "total_uploads": 0,
                    "successful_uploads": 0,
                    "failed_uploads": 0,
                    "skipped_unchanged": 0,
                    "total_bytes_uploaded": 0
                }
            }
            save_data(default_data)
            return default_data
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        return {}

def save_data(data: Dict[str, Any]):
    """Save runtime data to JSON file"""
    try:
        JSON_DIR.mkdir(parents=True, exist_ok=True)
        data["last_updated"] = datetime.now().isoformat()
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to save data: {e}")

def load_log() -> Dict[str, Any]:
    """Load operation log from JSON file"""
    try:
        if LOG_FILE.exists():
            with open(LOG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # Create default log structure
            default_log = {
                "entries": [],
                "summary": {
                    "total_entries": 0,
                    "last_entry": None,
                    "next_id": 1
                }
            }
            save_log(default_log)
            return default_log
    except Exception as e:
        logger.error(f"Failed to load log: {e}")
        return {"entries": [], "summary": {"total_entries": 0, "next_id": 1}}

def save_log(log: Dict[str, Any]):
    """Save operation log to JSON file"""
    try:
        JSON_DIR.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, 'w', encoding='utf-8') as f:
            json.dump(log, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to save log: {e}")

def log_operation(operation: str, details: Dict[str, Any], success: bool = True, correlation_id: str | None = None):
    """Log critical business operations to module's JSON log file"""
    try:
        log = load_log()
        
        log_entry = {
            "id": log["summary"].get("next_id", 1),
            "timestamp": datetime.now().isoformat(),
            "level": "INFO" if success else "ERROR",
            "operation": operation,
            "message": details.get("message", ""),
            "success": success,
            "execution_time_ms": details.get("execution_time_ms", 0),
            "correlation_id": correlation_id
        }
        
        if not success:
            log_entry["error_details"] = details.get("error_details", {})
        
        # Add to beginning of entries (newest first)
        log["entries"].insert(0, log_entry)
        
        # Keep only last 100 entries
        log["entries"] = log["entries"][:100]
        
        # Update summary
        log["summary"]["total_entries"] += 1
        log["summary"]["last_entry"] = log_entry["timestamp"]
        log["summary"]["next_id"] = log_entry["id"] + 1
        
        save_log(log)
        
    except Exception as e:
        logger.error(f"Failed to log operation: {e}")

# =============================================
# MAIN FUNCTIONS
# =============================================

class GoogleDriveSync:
    """Handles Google Drive integration for backup uploads"""
    
    def __init__(self):
        """Initialize Google Drive sync with AIPass standards"""
        self.config = load_config()
        self.data = load_data()
        
        # Paths
        self.creds_path = Path.home() / '.aipass' / 'drive_creds.json'
        self.client_secrets_path = Path(__file__).parent / 'credentials.json'
        
        # Runtime state
        self.drive_service = None
        self.backup_folder_id = None
        self.project_folder_cache = self.data.get("runtime_state", {}).get("cached_folders", {})
        self.file_tracker = self.data.get("runtime_state", {}).get("file_tracker", {})
        
        # Check if Google API is available
        if not GOOGLE_API_AVAILABLE:
            logger.error("Google API client not available - sync disabled")
            self.config["config"]["enabled"] = False
            save_config(self.config)
        
    def authenticate(self) -> bool:
        """Authenticate with Google Drive using OAuth credentials"""
        if not GOOGLE_API_AVAILABLE:
            import sys
            python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
            print(f"\033[91m[ERROR] Google API packages missing for current Python interpreter\033[0m")
            print(f"  Python version: {python_version}")
            print(f"  Python path: {sys.executable}")
            print(f"\033[93m  Fix: {sys.executable} -m pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib\033[0m")
            return False
            
        start_time = datetime.now()
        creds = None
        
        # Load existing credentials if they exist
        if self.creds_path.exists():
            try:
                creds = Credentials.from_authorized_user_file(str(self.creds_path), SCOPES)
            except Exception as e:
                print(f"Warning: Could not load existing credentials: {e}")
                logger.warning(f"Could not load existing credentials: {e}")
                creds = None
        
        # If no valid credentials, start OAuth flow
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    print("Refreshed existing Google Drive credentials")
                    logger.info("Refreshed existing Google Drive credentials")
                except Exception as e:
                    print(f"Warning: Could not refresh credentials: {e}")
                    logger.warning(f"Could not refresh credentials: {e}")
                    creds = None
            
            if not creds:
                # Check if client secrets file exists
                if not self.client_secrets_path.exists():
                    print(f"Error: OAuth client secrets not found at: {self.client_secrets_path}")
                    print("Please ensure the Google Cloud OAuth JSON file is in the correct location")
                    logger.error(f"OAuth client secrets not found at: {self.client_secrets_path}")
                    return False
                
                try:
                    print("\033[94m[AUTH]\033[0m Starting OAuth flow...")
                    print("\033[93m→\033[0m Browser will open for Google sign-in")
                    logger.info("Starting Google Drive OAuth flow")

                    flow = InstalledAppFlow.from_client_secrets_file(
                        str(self.client_secrets_path), SCOPES
                    )
                    creds = flow.run_local_server(port=0)
                    print("\033[92m✓ OAuth authentication completed\033[0m")
                    logger.info("Google Drive authentication completed")
                    
                except Exception as e:
                    print(f"Error: OAuth flow failed: {e}")
                    logger.error(f"OAuth flow failed: {e}")
                    log_operation("authenticate", {"message": f"OAuth flow failed: {e}", "error_details": {"exception_type": type(e).__name__, "stack_trace": str(e)}}, success=False)
                    return False
        
        # Save credentials for next time
        try:
            # Create .aipass directory if it doesn't exist
            self.creds_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Save credentials
            with open(self.creds_path, 'w', encoding='utf-8') as f:
                f.write(creds.to_json())
            
            logger.info(f"Saved credentials to: {self.creds_path}")
        except Exception as e:
            print(f"Warning: Could not save credentials: {e}")
            logger.warning(f"Could not save credentials: {e}")
        
        # Build Drive service
        try:
            self.drive_service = build('drive', 'v3', credentials=creds)
            print("Google Drive service ready")

            # Update runtime state (ensure runtime_state exists first)
            if "runtime_state" not in self.data:
                self.data["runtime_state"] = {}
            self.data["runtime_state"]["authenticated"] = True
            save_data(self.data)
            
            # Log successful authentication
            execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
            log_operation("authenticate", {"message": "Successfully authenticated with Google Drive", "execution_time_ms": execution_time}, success=True)
            
            return True
        except Exception as e:
            print(f"Error: Failed to build Drive service: {e}")
            logger.error(f"Failed to build Drive service: {e}")
            log_operation("authenticate", {"message": f"Failed to build Drive service: {e}", "error_details": {"exception_type": type(e).__name__, "stack_trace": str(e)}}, success=False)
            return False

    def get_storage_quota(self) -> Optional[Dict[str, Any]]:
        """Get Google Drive storage quota information"""
        try:
            if not self.drive_service:
                return None

            about = self.drive_service.about().get(fields="storageQuota").execute()
            quota = about.get('storageQuota', {})

            # Convert bytes to GB for readability
            limit = int(quota.get('limit', 0))
            usage = int(quota.get('usage', 0))

            limit_gb = limit / (1024**3)
            usage_gb = usage / (1024**3)
            free_gb = (limit - usage) / (1024**3)
            percent_used = (usage / limit * 100) if limit > 0 else 0

            return {
                'limit_gb': limit_gb,
                'usage_gb': usage_gb,
                'free_gb': free_gb,
                'percent_used': percent_used
            }
        except Exception as e:
            logger.warning(f"Could not retrieve storage quota: {e}")
            return None

    def get_or_create_backup_folder(self) -> Optional[str]:
        """Get or create the main 'AIPass Backups' folder in Drive"""
        if self.backup_folder_id:
            return self.backup_folder_id
            
        try:
            # Search for existing 'AIPass Backups' folder
            if not self.drive_service:
                return None
            results = self.drive_service.files().list(
                q="name='AIPass Backups' and mimeType='application/vnd.google-apps.folder' and trashed=false",
                fields="files(id, name)"
            ).execute()
            
            folders = results.get('files', [])
            
            if folders:
                self.backup_folder_id = folders[0]['id']
                logger.info("Found existing 'AIPass Backups' folder")
            else:
                # Create new backup folder
                folder_metadata = {
                    'name': 'AIPass Backups',
                    'mimeType': 'application/vnd.google-apps.folder'
                }
                folder = self.drive_service.files().create(
                    body=folder_metadata,
                    fields='id'
                ).execute()
                self.backup_folder_id = folder.get('id')
                print("Created 'AIPass Backups' folder in Drive")
                logger.info("Created 'AIPass Backups' folder in Drive")
            
            return self.backup_folder_id
            
        except Exception as e:
            print(f"Error creating backup folder: {e}")
            logger.error(f"Error creating backup folder: {e}")
            return None
    
    def get_or_create_project_folder(self, project_name: str) -> Optional[str]:
        """Get or create project subfolder within AIPass Backups"""
        # Check if we have a cached folder ID
        if project_name in self.project_folder_cache:
            # Verify the cached folder still exists
            folder_id = self.project_folder_cache[project_name]
            try:
                # Try to get the folder to verify it exists
                if self.drive_service:
                    self.drive_service.files().get(fileId=folder_id, fields='id').execute()
                    return folder_id  # Folder exists, use it
            except Exception as e:
                # Folder doesn't exist (404 or other error), remove from cache
                print(f"Cached folder no longer exists, creating new one: {project_name}")
                del self.project_folder_cache[project_name]
                # Clear from persistent data too
                if project_name in self.data.get("runtime_state", {}).get("cached_folders", {}):
                    del self.data["runtime_state"]["cached_folders"][project_name]
                    save_data(self.data)
            
        backup_folder_id = self.get_or_create_backup_folder()
        if not backup_folder_id:
            return None
            
        try:
            # Search for existing project folder
            if not self.drive_service:
                return None
            results = self.drive_service.files().list(
                q=f"name='{project_name}' and mimeType='application/vnd.google-apps.folder' and '{backup_folder_id}' in parents and trashed=false",
                fields="files(id, name)"
            ).execute()
            
            folders = results.get('files', [])
            
            if folders:
                project_folder_id = folders[0]['id']
            else:
                # Create new project folder
                folder_metadata = {
                    'name': project_name,
                    'mimeType': 'application/vnd.google-apps.folder',
                    'parents': [backup_folder_id]
                }
                folder = self.drive_service.files().create(
                    body=folder_metadata,
                    fields='id'
                ).execute()
                project_folder_id = folder.get('id')
                print(f"Created project folder '{project_name}'")
                logger.info(f"Created project folder '{project_name}'")
            
            self.project_folder_cache[project_name] = project_folder_id
            return project_folder_id
            
        except Exception as e:
            print(f"Error creating project folder: {e}")
            logger.error(f"Error creating project folder: {e}")
            return None

    def get_or_create_nested_folder(self, parent_folder_id: str, folder_path: str) -> Optional[str]:
        """Create nested folder structure in Google Drive"""
        if not folder_path or folder_path == '.':
            return parent_folder_id
            
        # Use folder_path as cache key
        cache_key = f"{parent_folder_id}:{folder_path}"
        if cache_key in self.project_folder_cache:
            # Verify the cached folder still exists
            folder_id = self.project_folder_cache[cache_key]
            try:
                # Try to get the folder to verify it exists
                if self.drive_service:
                    self.drive_service.files().get(fileId=folder_id, fields='id').execute()
                    return folder_id  # Folder exists, use it
            except Exception as e:
                # Folder doesn't exist (404 or other error), remove from cache
                print(f"Cached nested folder no longer exists, recreating: {folder_path}")
                del self.project_folder_cache[cache_key]
                # Clear from persistent data too
                if cache_key in self.data.get("runtime_state", {}).get("cached_folders", {}):
                    del self.data["runtime_state"]["cached_folders"][cache_key]
                    save_data(self.data)
            
        try:
            # Split path into parts and create each level
            path_parts = folder_path.split('/')
            current_parent_id = parent_folder_id
            
            for part in path_parts:
                if not part:  # Skip empty parts
                    continue
                    
                # Search for existing folder at this level
                if not self.drive_service:
                    return parent_folder_id
                results = self.drive_service.files().list(
                    q=f"name='{part}' and mimeType='application/vnd.google-apps.folder' and '{current_parent_id}' in parents and trashed=false",
                    fields="files(id, name)"
                ).execute()
                
                folders = results.get('files', [])
                
                if folders:
                    current_parent_id = folders[0]['id']
                else:
                    # Create new subfolder
                    folder_metadata = {
                        'name': part,
                        'mimeType': 'application/vnd.google-apps.folder',
                        'parents': [current_parent_id]
                    }
                    if not self.drive_service:
                        return parent_folder_id
                    folder = self.drive_service.files().create(
                        body=folder_metadata,
                        fields='id'
                    ).execute()
                    current_parent_id = folder.get('id')
                    print(f"\033[96m  📁 Created folder in Drive: {part}\033[0m")
                    logger.info(f"Created subfolder '{part}'")
            
            # Cache the final folder ID
            self.project_folder_cache[cache_key] = current_parent_id
            return current_parent_id
            
        except Exception as e:
            logger.error(f"Error creating nested folder '{folder_path}': {e}")
            return parent_folder_id  # Fallback to parent folder
    
    def upload_backup_file(self, local_file: Path, project_name: str, note: str = "", backup_root: Optional[Path] = None) -> bool:
        """Upload a backup file to the appropriate project folder with nested structure"""
        if not self.drive_service:
            print("Error: Not authenticated with Drive")
            logger.error("Not authenticated with Drive")
            return False
            
        project_folder_id = self.get_or_create_project_folder(project_name)
        if not project_folder_id:
            return False
            
        try:
            # Calculate relative path from backup root to maintain folder structure
            if backup_root and backup_root in local_file.parents:
                relative_path = local_file.relative_to(backup_root)
                folder_path = str(relative_path.parent) if relative_path.parent != Path('.') else ""
                # Convert Windows paths to forward slashes for consistency
                folder_path = folder_path.replace('\\', '/')
            else:
                folder_path = ""
            
            # Get or create the nested folder structure
            target_folder_id = self.get_or_create_nested_folder(project_folder_id, folder_path)
            if not target_folder_id:
                print(f"Error: Could not create target folder for {local_file.name}")
                logger.error(f"Could not create target folder for {local_file.name}")
                return False
            
            file_metadata = {
                'name': local_file.name,
                'parents': [target_folder_id],
                'description': f'AIPass backup - {note}' if note else 'AIPass backup'
            }
            
            media = MediaFileUpload(str(local_file), resumable=True)
            
            # Get file tracker info to avoid API calls when possible
            if backup_root and backup_root in local_file.parents:
                relative_path = local_file.relative_to(backup_root)
                file_key = str(relative_path).replace('\\', '/')
            else:
                file_key = local_file.name
            
            existing_file = None
            tracked_file = self.file_tracker.get(file_key)
            
            # Use cached drive_id if file is tracked, otherwise find it
            if tracked_file and tracked_file.get("drive_id"):
                # File is tracked, use cached drive_id
                existing_file = {"id": tracked_file["drive_id"]}
                logger.info(f"Using cached drive_id for {local_file.name}")
            else:
                # File not tracked or no drive_id, need API call to find it
                existing_file = self._find_existing_file(local_file.name, target_folder_id)
            
            # For files called by new sync system, we already know they need upload
            # Skip the size comparison check to avoid redundant work
            
            if existing_file:
                # Update existing file - don't include parents field for updates
                update_metadata = {
                    'name': local_file.name,
                    'description': f'AIPass backup - {note}' if note else 'AIPass backup'
                }
                file = self.drive_service.files().update(
                    fileId=existing_file['id'],
                    body=update_metadata,
                    media_body=media
                ).execute()
                action = "Updated"
            else:
                # Create new file
                file = self.drive_service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id'
                ).execute()
                action = "Uploaded"
            
            print(f"{action} {local_file.name} to Drive ({project_name})")
            
            # Update file tracker with new drive_id
            drive_file_id = file.get('id') if 'file' in locals() else (existing_file.get('id') if existing_file else None)
            if drive_file_id and backup_root:
                self._update_file_tracker(local_file, backup_root, drive_file_id)
            
            # Update statistics (ensure statistics exists first)
            if "statistics" not in self.data:
                self.data["statistics"] = {
                    "total_uploads": 0,
                    "successful_uploads": 0,
                    "failed_uploads": 0,
                    "total_bytes_uploaded": 0
                }
            self.data["statistics"]["total_uploads"] += 1
            self.data["statistics"]["successful_uploads"] += 1
            self.data["statistics"]["total_bytes_uploaded"] += local_file.stat().st_size
            save_data(self.data)
            
            # Log operation
            log_operation(f"upload_file", {
                "message": f"{action} {local_file.name} to {project_name}",
                "file_size": local_file.stat().st_size,
                "project": project_name
            }, success=True)
            
            return True
            
        except Exception as e:
            print(f"Error uploading {local_file.name}: {e}")
            logger.error(f"Error uploading {local_file.name}: {e}")
            
            # Update failure statistics (ensure statistics exists first)
            if "statistics" not in self.data:
                self.data["statistics"] = {
                    "total_uploads": 0,
                    "successful_uploads": 0,
                    "failed_uploads": 0,
                    "total_bytes_uploaded": 0
                }
            self.data["statistics"]["total_uploads"] += 1
            self.data["statistics"]["failed_uploads"] += 1
            save_data(self.data)
            
            # Log failure
            log_operation("upload_file", {
                "message": f"Failed to upload {local_file.name}",
                "error_details": {"exception_type": type(e).__name__, "stack_trace": str(e)}
            }, success=False)
            return False
    
    def _find_existing_file(self, filename: str, parent_folder_id: str) -> Optional[Dict[str, Any]]:
        """Find existing file in Drive folder with metadata"""
        try:
            if not self.drive_service:
                return None
            results = self.drive_service.files().list(
                q=f"name='{filename}' and '{parent_folder_id}' in parents and trashed=false",
                fields="files(id, name, size, modifiedTime, md5Checksum)"
            ).execute()
            
            files = results.get('files', [])
            return files[0] if files else None
            
        except Exception as e:
            logger.warning(f"Could not check for existing file: {e}")
            return None
    
    def _load_file_tracker(self) -> Dict[str, Dict[str, Any]]:
        """Load file tracker from data JSON"""
        return self.data.get("runtime_state", {}).get("file_tracker", {})
    
    def _save_file_tracker(self):
        """Save file tracker to data JSON"""
        if "runtime_state" not in self.data:
            self.data["runtime_state"] = {}
        self.data["runtime_state"]["file_tracker"] = self.file_tracker
        save_data(self.data)
    
    def _check_file_needs_upload_local(self, local_file: Path, backup_root: Path) -> bool:
        """Check if file needs upload using local tracker (no API calls)"""
        try:
            # Calculate relative path for tracking
            if backup_root and backup_root in local_file.parents:
                relative_path = local_file.relative_to(backup_root)
                file_key = str(relative_path).replace('\\', '/')
            else:
                file_key = local_file.name
            
            # Get current file stats
            current_size = local_file.stat().st_size
            current_mtime = local_file.stat().st_mtime
            
            # Check if file is in tracker
            if file_key not in self.file_tracker:
                logger.info(f"New file detected: {file_key}")
                return True  # New file, needs upload
            
            tracked_file = self.file_tracker[file_key]
            
            # Compare local file stats with tracker
            if (current_size != tracked_file.get("local_size", 0) or 
                current_mtime != tracked_file.get("local_mtime", 0)):
                logger.info(f"Changed file detected: {file_key}")
                return True  # File changed, needs upload
            
            # File unchanged according to tracker
            logger.info(f"Skipping unchanged file: {file_key}")
            return False
            
        except Exception as e:
            logger.warning(f"Error checking file tracker for {local_file.name}: {e}")
            return True  # On error, assume file needs upload
    
    def _update_file_tracker(self, local_file: Path, backup_root: Path, drive_file_id: str):
        """Update file tracker after successful upload"""
        try:
            # Calculate relative path for tracking
            if backup_root and backup_root in local_file.parents:
                relative_path = local_file.relative_to(backup_root)
                file_key = str(relative_path).replace('\\', '/')
            else:
                file_key = local_file.name
            
            # Get current file stats
            current_size = local_file.stat().st_size
            current_mtime = local_file.stat().st_mtime
            
            # Update tracker
            self.file_tracker[file_key] = {
                "local_size": current_size,
                "local_mtime": current_mtime,
                "drive_id": drive_file_id,
                "drive_size": current_size,
                "last_sync": datetime.now().isoformat()
            }
            
            # Save tracker
            self._save_file_tracker()
            logger.info(f"Updated file tracker for: {file_key}")
            
        except Exception as e:
            logger.warning(f"Error updating file tracker for {local_file.name}: {e}")
    
    def _clean_file_tracker(self, existing_files: set):
        """Remove tracker entries for files that no longer exist"""
        try:
            keys_to_remove = []
            for file_key in self.file_tracker.keys():
                if file_key not in existing_files:
                    keys_to_remove.append(file_key)
            
            for key in keys_to_remove:
                del self.file_tracker[key]
                logger.info(f"Removed deleted file from tracker: {key}")
            
            if keys_to_remove:
                self._save_file_tracker()
                
        except Exception as e:
            logger.warning(f"Error cleaning file tracker: {e}")
    
    def _file_needs_upload(self, local_file: Path, drive_file: Optional[Dict[str, Any]]) -> bool:
        """Check if a file needs to be uploaded based on size comparison"""
        if not drive_file:
            return True  # File doesn't exist in Drive, needs upload
        
        try:
            local_size = local_file.stat().st_size
            drive_size = int(drive_file.get('size', 0))
            
            # If sizes are different, file has changed
            if local_size != drive_size:
                return True
            
            # If sizes are same, assume file is unchanged (for now)
            # TODO: Could add MD5 comparison for small files for better accuracy
            return False
            
        except Exception as e:
            logger.warning(f"Error comparing file {local_file.name}: {e}")
            return True  # Upload on error to be safe
    
    def sync_backup_files(self, backup_dir: Path, project_name: str, note: str = "", force_sync: bool = False) -> bool:
        """Sync backup files to Drive using local-first change detection"""
        if not backup_dir.exists():
            print(f"\033[91m✗ Error: Backup directory not found: {backup_dir}\033[0m")
            logger.error(f"Backup directory not found: {backup_dir}")
            return False

        print(f"\033[94m[SYNC]\033[0m Starting local-first change detection...")
        logger.info(f"Starting Drive sync for {project_name}, force_sync={force_sync}")

        # Load file tracker
        self.file_tracker = self._load_file_tracker()

        # Phase 1: Scan all files and determine which need upload (LOCAL ONLY - NO API CALLS)
        files_to_upload = []
        skipped_count = 0
        total_count = 0
        existing_files = set()

        print("\033[96m━━━ Phase 1: Local File Scan ━━━\033[0m")
        for backup_file in backup_dir.rglob("*"):
            if backup_file.is_file() and not backup_file.name.startswith('.'):
                total_count += 1

                # Track existing files for cleanup
                if backup_dir in backup_file.parents:
                    relative_path = backup_file.relative_to(backup_dir)
                    file_key = str(relative_path).replace('\\', '/')
                    existing_files.add(file_key)

                # Check if file needs upload (local check only)
                if force_sync or self._check_file_needs_upload_local(backup_file, backup_dir):
                    files_to_upload.append(backup_file)
                else:
                    skipped_count += 1

        # Clean tracker of deleted files
        self._clean_file_tracker(existing_files)

        upload_count = len(files_to_upload)
        print(f"\033[92m✓ Phase 1 complete\033[0m")
        print(f"  → {upload_count} files need upload")
        print(f"  → {skipped_count} files unchanged")
        print(f"  → {total_count} total files scanned")
        logger.info(f"Scan complete: {upload_count} to upload, {skipped_count} skipped, {total_count} total")

        # Phase 2: Upload only the files that need it (WITH API CALLS)
        success_count = 0

        if upload_count > 0:
            print(f"\033[96m━━━ Phase 2: Upload Changes ━━━\033[0m")
            for i, backup_file in enumerate(files_to_upload, 1):
                print(f"\033[93m↑\033[0m [{i}/{upload_count}] {backup_file.name}")
                result = self.upload_backup_file(backup_file, project_name, note, backup_dir)
                if result:
                    success_count += 1
        else:
            print(f"\033[96m━━━ Phase 2: Upload Changes ━━━\033[0m")
            print("\033[92m✓ No files to upload - all files are up to date!\033[0m")
        
        # Count skipped files as successful
        total_success = success_count + skipped_count
        
        # Update last sync time
        self.data["runtime_state"]["last_sync"] = datetime.now().isoformat()
        save_data(self.data)
        
        # Log sync operation
        log_operation("sync_backup", {
            "message": f"Synced {total_success}/{total_count} files for {project_name} ({upload_count} uploaded, {skipped_count} skipped)",
            "uploaded_count": success_count,
            "skipped_count": skipped_count,
            "total_count": total_count,
            "project": project_name,
            "force_sync": force_sync
        }, success=(total_success == total_count))

        # Display summary
        print("\033[96m━━━ Sync Summary ━━━\033[0m")
        if total_success == total_count:
            print(f"\033[92m✓ Sync complete: {total_success}/{total_count} files processed\033[0m")
        else:
            failed_count = total_count - total_success
            print(f"\033[93m⚠ Sync complete with errors: {total_success}/{total_count} files processed\033[0m")
            print(f"\033[91m  ✗ {failed_count} files failed\033[0m")

        print(f"  \033[92m↑\033[0m {success_count} files uploaded")
        print(f"  \033[90m→\033[0m {skipped_count} files unchanged")
        print("="*70)
        
        return total_success == total_count

def get_status() -> Dict[str, Any]:
    """Get current module status - required for monitoring"""
    data = load_data()
    config = load_config()
    
    return {
        "name": MODULE_NAME,
        "category": "backup_system",
        "enabled": config.get("config", {}).get("enabled", False),
        "authenticated": data.get("runtime_state", {}).get("authenticated", False),
        "last_sync": data.get("runtime_state", {}).get("last_sync"),
        "statistics": data.get("statistics", {})
    }

def clear_file_tracker():
    """Clear the file tracker cache for fresh sync"""
    try:
        data = load_data()
        if "runtime_state" in data and "file_tracker" in data["runtime_state"]:
            tracker_count = len(data["runtime_state"]["file_tracker"])
            data["runtime_state"]["file_tracker"] = {}
            save_data(data)
            print(f"Cleared {tracker_count} entries from file tracker")
            logger.info(f"Cleared {tracker_count} entries from file tracker")
            return True
        else:
            print("File tracker already empty")
            return True
    except Exception as e:
        print(f"Error clearing file tracker: {e}")
        logger.error(f"Error clearing file tracker: {e}")
        return False

def show_file_tracker_stats():
    """Show statistics about the file tracker"""
    try:
        data = load_data()
        tracker = data.get("runtime_state", {}).get("file_tracker", {})
        
        print(f"File Tracker Statistics:")
        print(f"  - Total tracked files: {len(tracker)}")
        
        if tracker:
            # Show some sample entries
            print(f"  - Sample entries:")
            for i, (file_key, info) in enumerate(list(tracker.items())[:5]):
                last_sync = info.get("last_sync", "unknown")[:19] if info.get("last_sync") else "unknown"
                print(f"    {i+1}. {file_key} (last sync: {last_sync})")
            
            if len(tracker) > 5:
                print(f"    ... and {len(tracker) - 5} more files")
        
        return True
    except Exception as e:
        print(f"Error showing tracker stats: {e}")
        logger.error(f"Error showing tracker stats: {e}")
        return False

def test_drive_sync():
    """Test Drive integration"""
    try:
        sync = GoogleDriveSync()
        
        if not sync.authenticate():
            return False
            
        print("Testing folder creation...")
        folder_id = sync.get_or_create_backup_folder()
        if folder_id:
            print(f"Backup folder ready: {folder_id}")
            
            # Log successful test
            log_operation("test_sync", {"message": "Drive sync test successful", "folder_id": folder_id}, success=True)
            return True
        else:
            print("Failed to create backup folder")
            log_operation("test_sync", {"message": "Failed to create backup folder"}, success=False)
            return False
            
    except Exception as e:
        print(f"Test failed: {e}")
        logger.error(f"Test failed: {e}")
        log_operation("test_sync", {
            "message": f"Test failed: {e}",
            "error_details": {"exception_type": type(e).__name__, "stack_trace": str(e)}
        }, success=False)
        return False

# =============================================
# CLI/EXECUTION
# =============================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Google Drive Sync for AIPass Backup System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
COMMANDS:
  Commands: test, sync, clear-tracker, show-stats

  test          - Test Google Drive connectivity
  sync          - Sync backup directory to Google Drive
  clear-tracker - Clear file tracker cache
  show-stats    - Show file tracker statistics

OPTIONS:
  --project     - Project name for sync (default: AIPass)
  --note        - Note for sync operation (default: Manual sync)
  --force       - Force sync all files (ignore tracker)

EXAMPLES:
  python3 google_drive_sync.py test
  python3 google_drive_sync.py sync /path/to/backups
  python3 google_drive_sync.py sync /path/to/backups --project "MyProject" --note "Daily backup"
  python3 google_drive_sync.py sync /path/to/backups --force
  python3 google_drive_sync.py clear-tracker
  python3 google_drive_sync.py show-stats
        """
    )

    parser.add_argument("command",
                       choices=['test', 'sync', 'clear-tracker', 'show-stats'],
                       help="Command to execute")
    parser.add_argument("path", nargs='?', help="Backup directory path (required for sync command)")
    parser.add_argument("--project", type=str, default="AIPass", help="Project name for sync")
    parser.add_argument("--note", type=str, default="Manual sync", help="Note for sync operation")
    parser.add_argument("--force", action="store_true", help="Force sync all files (ignore tracker)")

    args = parser.parse_args()

    # Check if module is enabled
    config = load_config()
    if not config.get("config", {}).get("enabled", True):
        print("Warning: Google Drive sync is disabled")
        sys.exit(0)

    if args.command == 'clear-tracker':
        if clear_file_tracker():
            print("File tracker cleared successfully")
            sys.exit(0)
        else:
            print("Failed to clear file tracker")
            sys.exit(1)

    elif args.command == 'show-stats':
        if show_file_tracker_stats():
            sys.exit(0)
        else:
            sys.exit(1)

    elif args.command == 'sync':
        if not args.path:
            print("Error: sync command requires a path argument")
            print("Usage: python3 google_drive_sync.py sync /path/to/backups")
            sys.exit(1)

        from pathlib import Path
        backup_path = Path(args.path)

        if not backup_path.exists():
            print(f"Error: Backup directory not found: {backup_path}")
            sys.exit(1)

        sync = GoogleDriveSync()
        if not sync.authenticate():
            print("Failed to authenticate with Google Drive")
            sys.exit(1)

        print(f"Syncing {backup_path} to Google Drive (project: {args.project})")
        if args.force:
            print("Force sync enabled - will upload all files")

        success = sync.sync_backup_files(backup_path, args.project, args.note, args.force)
        if success:
            print("Sync completed successfully")
            sys.exit(0)
        else:
            print("Sync failed")
            sys.exit(1)

    elif args.command == 'test':
        if test_drive_sync():
            print("Google Drive sync test successful")
            sys.exit(0)
        else:
            print("Google Drive sync test failed")
            sys.exit(1)