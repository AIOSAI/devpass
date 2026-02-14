#!/usr/bin/env python3

# =============================================
# META DATA HEADER
# Name: flow_registry_monitor.py
# Date: 2025-08-23
# Version: 2.0.0
# Category: flow
# 
# CHANGELOG:
#   - v2.0.0 (2025-08-27): Cleaned module - removed orphaned callback system and CLAUDE.md references
#   - v1.0.0 (2025-08-23): Initial implementation
#     * Feature: Real-time monitoring of PLAN files
#     * Feature: Auto-registry updates on file events
#     * Feature: Self-healing registry on startup
# =============================================

"""
Flow Registry Monitor

Clean, focused registry monitoring system that keeps PLAN registry synchronized with filesystem state.

Features:
- Automatic PLAN file detection and tracking
- Registry updates on file move/delete/create
- Self-healing registry on startup
- Background monitoring service
- Pattern-based file watching (PLAN*.md)
- Manual entry handling and auto-recovery

Author: AIPass Development Team
Status: Production Ready
"""

import argparse
import json
import re
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from datetime import datetime, timezone
from typing import Dict, Any, Optional

# NEW AIPASS IMPORT PATTERN
import sys
from pathlib import Path
AIPASS_ROOT = Path.home() / "aipass_core"
FLOW_ROOT = AIPASS_ROOT / "flow"
sys.path.append(str(AIPASS_ROOT))
from prax.apps.modules.prax_logger import system_logger as logger

# =============================================
# CONSTANTS AND PATHS
# =============================================

MODULE_NAME = "flow_registry_monitor"
# Scan entire system for plans (AIPass Admin compatibility)
ECOSYSTEM_ROOT = Path("/")
# Registry location updated for aipass_core structure
FLOW_DIR = FLOW_ROOT
FLOW_JSON_DIR = FLOW_DIR / "flow_json"
REGISTRY_FILE = FLOW_JSON_DIR / "flow_registry.json"

# Module-specific JSON files (3-file pattern)
CONFIG_FILE = FLOW_JSON_DIR / "registry_monitor_config.json"
DATA_FILE = FLOW_JSON_DIR / "registry_monitor_data.json"
LOG_FILE = FLOW_JSON_DIR / "registry_monitor_log.json"

# PLAN file pattern
PLAN_PATTERN = re.compile(r'^PLAN\d{4}\.md$')

# Folders to ignore during monitoring (default fallback - prefer config file)
IGNORE_FOLDERS = {
    "admin", "archive", "mcp-servers", "backups", "tests", "trash", "tools",
    "__pycache__", ".git", ".venv", "venv", "node_modules", ".pytest_cache",
    "dist", "build", ".idea", ".vscode", "aipass-help",
    ".local", "Downloads", "downloads",
    # System directories (permission errors)
    "proc", "sys", "dev", "run", "boot", "lost+found",
    # Backup/snapshot directories
    "timeshift", "snapshots", ".snapshots", "backup", ".backup"
}

# =============================================
# FILE WATCHER CLASS
# =============================================

class PlanFileWatcher(FileSystemEventHandler):
    """Monitors PLAN file changes and updates registry automatically"""
    
    def on_created(self, event):
        """Handle file creation events"""
        if not event.is_directory and self._is_plan_file(str(event.src_path)):
            file_path = Path(str(event.src_path))
            logger.info(f"[{MODULE_NAME}] New PLAN file detected: {file_path.name}")
            self._add_plan_to_registry(file_path)
    
    def on_deleted(self, event):
        """Handle file deletion events"""
        if not event.is_directory and self._is_plan_file(str(event.src_path)):
            file_path = Path(str(event.src_path))
            logger.info(f"[{MODULE_NAME}] PLAN file deleted: {file_path.name}")
            self._remove_plan_from_registry(file_path)
    
    def on_moved(self, event):
        """Handle file move/rename events"""
        if not event.is_directory and self._is_plan_file(str(event.dest_path)):
            src_path = Path(str(event.src_path))
            dest_path = Path(str(event.dest_path))
            logger.info(f"[{MODULE_NAME}] PLAN file moved: {src_path.name} -> {dest_path}")
            self._update_plan_location(src_path, dest_path)
    
    def _is_plan_file(self, file_path: str) -> bool:
        """Check if file is a PLAN file"""
        return PLAN_PATTERN.match(Path(file_path).name) is not None
    
    def _get_plan_number(self, file_path: Path) -> Optional[str]:
        """Extract plan number from filename (e.g., PLAN0001.md -> 0001)"""
        match = re.search(r'PLAN(\d{4})\.md$', file_path.name)
        return match.group(1) if match else None
    
    def _add_plan_to_registry(self, file_path: Path):
        """Add new PLAN file to registry"""
        try:
            registry = self._load_registry()
            plan_number = self._get_plan_number(file_path)
            
            if not plan_number:
                logger.warning(f"[{MODULE_NAME}] Invalid PLAN filename: {file_path.name}")
                return
            
            # Check if already exists
            if plan_number in registry.get("plans", {}):
                existing_plan = registry["plans"][plan_number]
                
                # If plan is closed, preserve closed status and just update location
                if existing_plan.get("status") == "closed":
                    logger.info(f"[{MODULE_NAME}] PLAN{plan_number} is closed - updating location only")
                    existing_plan["location"] = str(file_path.parent)
                    existing_plan["relative_path"] = str(file_path.parent.relative_to(ECOSYSTEM_ROOT))
                    existing_plan["file_path"] = str(file_path)
                    registry["last_updated"] = datetime.now(timezone.utc).isoformat()
                    self._save_registry(registry)
                    return
                else:
                    logger.info(f"[{MODULE_NAME}] PLAN{plan_number} already in registry")
                    return
            
            # Add to registry
            relative_path = str(file_path.parent.relative_to(ECOSYSTEM_ROOT))
            registry.setdefault("plans", {})[plan_number] = {
                "location": str(file_path.parent),
                "relative_path": relative_path,
                "created": datetime.now(timezone.utc).isoformat(),
                "subject": "Auto-detected PLAN",
                "status": "open",
                "file_path": str(file_path)
            }
            
            # Update next_number if needed
            current_next = registry.get("next_number", 1)
            plan_num_int = int(plan_number)
            if plan_num_int >= current_next:
                registry["next_number"] = plan_num_int + 1
            
            self._save_registry(registry)
            self._log_event("plan_added", {
                "plan_number": plan_number,
                "location": relative_path,
                "file_path": str(file_path)
            })
            logger.info(f"[{MODULE_NAME}] Added PLAN{plan_number} to registry")
            
        except Exception as e:
            logger.error(f"[{MODULE_NAME}] Error adding plan to registry: {e}")
            self._log_event("error", {"operation": "add_plan", "error": str(e)})
    
    def _remove_plan_from_registry(self, file_path: Path):
        """Remove PLAN file from registry (or mark as archived if closed)"""
        try:
            registry = self._load_registry()
            plan_number = self._get_plan_number(file_path)

            if not plan_number:
                return

            plans = registry.get("plans", {})
            if plan_number in plans:
                plan_info = plans[plan_number]

                # If plan is closed/processed, preserve it in registry but mark as archived
                # This allows "Recently Closed" to show in CLAUDE.md
                if plan_info.get("status") == "closed" or plan_info.get("processed"):
                    plan_info["archived"] = True
                    plan_info["archived_date"] = datetime.now(timezone.utc).isoformat()
                    # Keep file_path to show where it was moved to
                    registry["last_updated"] = datetime.now(timezone.utc).isoformat()
                    self._save_registry(registry)
                    self._log_event("plan_archived", {
                        "plan_number": plan_number,
                        "file_path": str(file_path)
                    })
                    logger.info(f"[{MODULE_NAME}] Archived PLAN{plan_number} in registry (preserving history)")
                else:
                    # Plan is open but file deleted - remove from registry completely
                    del plans[plan_number]
                    registry["plans"] = plans
                    registry["last_updated"] = datetime.now(timezone.utc).isoformat()
                    self._save_registry(registry)
                    self._log_event("plan_removed", {
                        "plan_number": plan_number,
                        "file_path": str(file_path)
                    })
                    logger.info(f"[{MODULE_NAME}] Removed PLAN{plan_number} from registry")

        except Exception as e:
            logger.error(f"[{MODULE_NAME}] Error removing plan from registry: {e}")
            self._log_event("error", {"operation": "remove_plan", "error": str(e)})
    
    def _update_plan_location(self, src_path: Path, dest_path: Path):
        """Update PLAN file location in registry"""
        try:
            registry = self._load_registry()
            plan_number = self._get_plan_number(dest_path)
            
            if not plan_number:
                return
            
            plans = registry.get("plans", {})
            if plan_number in plans:
                relative_path = str(dest_path.parent.relative_to(ECOSYSTEM_ROOT))
                plans[plan_number].update({
                    "location": str(dest_path.parent),
                    "relative_path": relative_path,
                    "file_path": str(dest_path)
                })
                registry["last_updated"] = datetime.now(timezone.utc).isoformat()
                self._save_registry(registry)
                self._log_event("plan_moved", {
                    "plan_number": plan_number,
                    "old_location": str(src_path),
                    "new_location": str(dest_path)
                })
                logger.info(f"[{MODULE_NAME}] Updated PLAN{plan_number} location")
        
        except Exception as e:
            logger.error(f"[{MODULE_NAME}] Error updating plan location: {e}")
            self._log_event("error", {"operation": "update_location", "error": str(e)})
    
    def _load_registry(self) -> Dict[str, Any]:
        """Load the flow registry"""
        if not REGISTRY_FILE.exists():
            return {"plans": {}, "next_number": 1}
        
        try:
            with open(REGISTRY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"[{MODULE_NAME}] Error loading registry: {e}")
            return {"plans": {}, "next_number": 1}
    
    def _save_registry(self, registry: Dict[str, Any]):
        """Save the flow registry"""
        try:
            FLOW_JSON_DIR.mkdir(parents=True, exist_ok=True)
            registry["last_updated"] = datetime.now(timezone.utc).isoformat()
            with open(REGISTRY_FILE, 'w', encoding='utf-8') as f:
                json.dump(registry, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"[{MODULE_NAME}] Error saving registry: {e}")
    
    def _log_event(self, event_type: str, details: Dict[str, Any]):
        """Log monitoring events"""
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "details": details
        }
        
        # Load existing logs
        logs = []
        if LOG_FILE.exists():
            try:
                with open(LOG_FILE, 'r', encoding='utf-8') as f:
                    logs = json.load(f)
            except:
                logs = []
        
        logs.append(log_entry)
        
        # Keep last 100 events
        if len(logs) > 100:
            logs = logs[-100:]
        
        # Save logs
        try:
            FLOW_JSON_DIR.mkdir(parents=True, exist_ok=True)
            with open(LOG_FILE, 'w', encoding='utf-8') as f:
                json.dump(logs, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"[{MODULE_NAME}] Error saving log: {e}")
        

# =============================================
# CONFIGURATION MANAGEMENT
# =============================================

def create_config_file():
    """Create default config file if it doesn't exist"""
    if CONFIG_FILE.exists():
        return
    
    default_config = {
        "module_name": MODULE_NAME,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "config": {
            "enabled": True,
            "version": "1.0.0",
            "monitoring_enabled": True,
            "scan_on_startup": True,
            "auto_heal_registry": True,
            "file_pattern": "PLAN*.md",
            "ignore_folders": list(IGNORE_FOLDERS)
        }
    }
    
    try:
        FLOW_JSON_DIR.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=2, ensure_ascii=False)
        logger.info(f"[{MODULE_NAME}] Config file created")
    except Exception as e:
        logger.error(f"[{MODULE_NAME}] Error creating config file: {e}")

def load_config() -> Dict[str, Any]:
    """Load configuration"""
    create_config_file()
    
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"[{MODULE_NAME}] Error loading config: {e}")
        return {"config": {"enabled": True}}

def update_data_file(stats: Dict[str, Any]):
    """Update data file with current statistics"""
    data = {
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "runtime_state": {
            "monitoring_active": True,
            "observer_running": True
        },
        "statistics": stats
    }
    
    try:
        FLOW_JSON_DIR.mkdir(parents=True, exist_ok=True)
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[{MODULE_NAME}] Error updating data file: {e}")

# =============================================
# PLAN FILE SCANNING AND HEALING
# =============================================

def scan_plan_files() -> Dict[str, Any]:
    """Scan ecosystem for PLAN files and heal registry"""
    logger.info(f"[{MODULE_NAME}] Starting PLAN file scan from: {ECOSYSTEM_ROOT}")

    # Load ignore patterns from config (fallback to hardcoded)
    config = load_config()
    ignore_folders = config.get("config", {}).get("ignore_folders", list(IGNORE_FOLDERS))
    logger.info(f"[{MODULE_NAME}] Using {len(ignore_folders)} ignore patterns from config")

    # Find all PLAN files (detect duplicates)
    # Handle permission errors gracefully when scanning system-wide
    plan_files = {}
    duplicates = {}

    def handle_walk_error(error):
        """Handle permission errors during os.walk"""
        if isinstance(error, PermissionError):
            # Silent skip for common system directories
            pass
        else:
            logger.warning(f"[{MODULE_NAME}] Error during scan: {error}")

    # Use os.walk() with error handling for system-wide scanning
    import os
    for root, dirs, files in os.walk(str(ECOSYSTEM_ROOT), topdown=True, onerror=handle_walk_error):
        # Skip ignored directories entirely (modify dirs in-place to prevent descent)
        dirs[:] = [d for d in dirs if not any(ignored in d for ignored in ignore_folders)]

        # Check for PLAN files in this directory
        for filename in files:
            if PLAN_PATTERN.match(filename):
                file_path = Path(root) / filename
                match = re.search(r'PLAN(\d{4})\.md$', filename)
                if match:
                    plan_number = match.group(1)

                    # Duplicate detection
                    if plan_number in plan_files:
                        if plan_number not in duplicates:
                            duplicates[plan_number] = [plan_files[plan_number]]
                        duplicates[plan_number].append(file_path)
                        logger.warning(f"[{MODULE_NAME}] Duplicate PLAN{plan_number} found: {file_path}")
                    else:
                        plan_files[plan_number] = file_path

    # Auto-renumber duplicates (keep first, renumber rest)
    renumbered = []
    if duplicates:
        logger.warning(f"[{MODULE_NAME}] Found {len(duplicates)} duplicate PLAN files:")
        for plan_num, paths in duplicates.items():
            logger.warning(f"[{MODULE_NAME}]   PLAN{plan_num}: {len(paths)} copies")
            for path in paths:
                logger.warning(f"[{MODULE_NAME}]     - {path}")

        # Get next available plan number
        current_max = max(int(num) for num in plan_files.keys()) if plan_files else 0
        next_available = current_max + 1

        for plan_num, paths in duplicates.items():
            # Keep first occurrence, renumber the rest
            for dup_path in paths[1:]:  # Skip first path (already in plan_files)
                old_name = dup_path.name
                new_num = f"{next_available:04d}"
                new_name = f"PLAN{new_num}.md"
                new_path = dup_path.parent / new_name

                try:
                    # Rename file on filesystem
                    dup_path.rename(new_path)
                    logger.info(f"[{MODULE_NAME}] Auto-renumbered: {old_name} → {new_name} at {dup_path.parent}")

                    # Add to plan_files with new number
                    plan_files[new_num] = new_path
                    renumbered.append({
                        "old_number": plan_num,
                        "new_number": new_num,
                        "path": str(new_path)
                    })

                    next_available += 1
                except Exception as e:
                    logger.error(f"[{MODULE_NAME}] Failed to renumber {old_name}: {e}")

    # Load current registry
    registry = load_registry()
    plans = registry.get("plans", {})
    
    # Track changes for healing
    added = []
    updated = []
    removed = []
    
    # Add missing files to registry
    for plan_number, file_path in plan_files.items():
        relative_path = str(file_path.parent.relative_to(ECOSYSTEM_ROOT))
        
        if plan_number not in plans:
            # Add missing plan
            plans[plan_number] = {
                "location": str(file_path.parent),
                "relative_path": relative_path,
                "created": datetime.now(timezone.utc).isoformat(),
                "subject": "Auto-detected PLAN",
                "status": "open",
                "file_path": str(file_path)
            }
            added.append(plan_number)
        else:
            # Update location if moved (PRESERVE all other metadata!)
            current_path = plans[plan_number].get("file_path", "")
            if current_path != str(file_path):
                # Only update path fields, keep status/closed/memory_created/etc
                plans[plan_number]["location"] = str(file_path.parent)
                plans[plan_number]["relative_path"] = relative_path
                plans[plan_number]["file_path"] = str(file_path)
                updated.append(plan_number)
                logger.info(f"[{MODULE_NAME}] Updated PLAN{plan_number} location: {relative_path}")
    
    # Remove orphaned registry entries
    for plan_number in list(plans.keys()):
        if plan_number not in plan_files:
            del plans[plan_number]
            removed.append(plan_number)
    
    # Update next_number
    if plan_files:
        max_number = max(int(num) for num in plan_files.keys())
        registry["next_number"] = max_number + 1
    
    # Save healed registry
    registry["plans"] = plans
    save_registry(registry)
    
    # Log healing results
    if added or updated or removed or renumbered:
        logger.info(f"[{MODULE_NAME}] Registry healed - Added: {len(added)}, Updated: {len(updated)}, Removed: {len(removed)}, Renumbered: {len(renumbered)}")

        healing_log = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": "registry_healed",
            "details": {
                "added": added,
                "updated": updated,
                "removed": removed,
                "renumbered": renumbered,
                "total_plans": len(plans)
            }
        }
        
        
        # Save healing log
        logs = []
        if LOG_FILE.exists():
            try:
                with open(LOG_FILE, 'r', encoding='utf-8') as f:
                    logs = json.load(f)
            except:
                pass
        
        logs.append(healing_log)
        if len(logs) > 100:
            logs = logs[-100:]
        
        try:
            with open(LOG_FILE, 'w', encoding='utf-8') as f:
                json.dump(logs, f, indent=2, ensure_ascii=False)
        except:
            pass
    
    # Update statistics
    stats = {
        "total_plans": len(plans),
        "open_plans": sum(1 for plan in plans.values() if plan.get("status") == "open"),
        "scan_timestamp": datetime.now(timezone.utc).isoformat(),
        "files_found": len(plan_files),
        "healing_performed": len(added) + len(updated) + len(removed) > 0
    }
    
    update_data_file(stats)
    
    logger.info(f"[{MODULE_NAME}] Scan complete - found {len(plans)} PLAN files")
    return registry

def load_registry() -> Dict[str, Any]:
    """Load PLAN registry"""
    if not REGISTRY_FILE.exists():
        return {"plans": {}, "next_number": 1}
    
    try:
        with open(REGISTRY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"[{MODULE_NAME}] Error loading registry: {e}")
        return {"plans": {}, "next_number": 1}

def save_registry(registry: Dict[str, Any]):
    """Save PLAN registry"""
    try:
        FLOW_JSON_DIR.mkdir(parents=True, exist_ok=True)
        registry["last_updated"] = datetime.now(timezone.utc).isoformat()
        with open(REGISTRY_FILE, 'w', encoding='utf-8') as f:
            json.dump(registry, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[{MODULE_NAME}] Error saving registry: {e}")

# =============================================
# MONITOR CONTROL
# =============================================

_observer = None

def start_monitor():
    """Start PLAN file monitoring"""
    global _observer
    
    config = load_config()
    if not config.get("config", {}).get("monitoring_enabled", True):
        logger.info(f"[{MODULE_NAME}] Monitoring disabled in config")
        return
    
    if _observer and _observer.is_alive():
        logger.info(f"[{MODULE_NAME}] Monitor already running")
        return
    
    try:
        _observer = Observer()
        _observer.schedule(PlanFileWatcher(), str(ECOSYSTEM_ROOT), recursive=True)
        _observer.start()
        logger.info(f"[{MODULE_NAME}] PLAN file monitor started")
        
        # Log monitoring start
        try:
            logs = []
            if LOG_FILE.exists():
                with open(LOG_FILE, 'r', encoding='utf-8') as f:
                    logs = json.load(f)
            
            logs.append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "event_type": "monitor_started",
                "details": {"watch_location": str(ECOSYSTEM_ROOT)}
            })
            
            if len(logs) > 100:
                logs = logs[-100:]
            
            FLOW_JSON_DIR.mkdir(parents=True, exist_ok=True)
            with open(LOG_FILE, 'w', encoding='utf-8') as f:
                json.dump(logs, f, indent=2, ensure_ascii=False)
        except:
            pass
    
    except Exception as e:
        logger.error(f"[{MODULE_NAME}] Error starting monitor: {e}")

def stop_monitor():
    """Stop PLAN file monitoring"""
    global _observer
    
    if _observer and _observer.is_alive():
        _observer.stop()
        _observer.join()
        logger.info(f"[{MODULE_NAME}] PLAN file monitor stopped")

def get_status() -> Dict[str, Any]:
    """Get monitoring status"""
    config = load_config()
    
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        stats = data.get("statistics", {})
    except:
        stats = {"total_plans": 0}
    
    return {
        "module": MODULE_NAME,
        "version": "1.0.0",
        "enabled": config.get("config", {}).get("enabled", True),
        "monitoring_active": _observer and _observer.is_alive(),
        "statistics": stats,
        "paths": {
            "registry": str(REGISTRY_FILE),
            "config": str(CONFIG_FILE),
            "data": str(DATA_FILE),
            "log": str(LOG_FILE)
        }
    }

# =============================================
# AUTO-START PATTERN (Like prax_on_off.py)
# =============================================

# Auto-start when imported  
logger.info(f"[{MODULE_NAME}] Starting automatically on import")
logger.info(f"[{MODULE_NAME}] Monitoring ecosystem: {ECOSYSTEM_ROOT}")

# Create config file if missing
create_config_file()

# Initial scan and heal registry
registry = scan_plan_files()
logger.info(f"[{MODULE_NAME}] Initial scan complete - found {len(registry.get('plans', {}))} PLAN files")

# NOTE: Monitoring is NOT auto-started to allow --help to work quickly
# Use 'python flow_registry_monitor.py start' to begin monitoring

logger.info(f"[{MODULE_NAME}] Auto-initialization complete - ready for commands")

# =============================================
# COMMAND LINE INTERFACE
# =============================================

def main():
    """Main entry point for command-line usage"""
    parser = argparse.ArgumentParser(
        description='Flow Registry Monitor - Central PLAN tracking and auto-healing',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
COMMANDS:
  Commands: status, scan, start, stop, heal

  status   - Show registry status and statistics
  scan     - Scan for PLAN files and update registry
  start    - Start persistent monitoring (Ctrl+C to stop)
  stop     - Stop monitoring service
  heal     - Auto-heal registry (rescan and fix)

EXAMPLES:
  python3 flow_registry_monitor.py status
  python3 flow_registry_monitor.py scan
  python3 flow_registry_monitor.py start
  python3 flow_registry_monitor.py stop
  python3 flow_registry_monitor.py heal

NOTE:
  If no command is provided, shows status in interactive mode.
        """
    )

    parser.add_argument('command',
                       nargs='?',
                       choices=['status', 'scan', 'start', 'stop', 'heal'],
                       help='Command to execute')

    args = parser.parse_args()

    # If no command, show status
    if not args.command:
        print(f"[{MODULE_NAME}] Flow Registry Monitor v1.0.0")
        status = get_status()
        print(f"Status: {json.dumps(status, indent=2)}")
        return 0

    command = args.command.lower()

    if command == "status":
        status = get_status()
        print(f"[{MODULE_NAME}] Status:")
        print(json.dumps(status, indent=2))

    elif command == "scan":
        print(f"[{MODULE_NAME}] Scanning for PLAN files...")
        registry = scan_plan_files()
        print(f"Found {len(registry.get('plans', {}))} PLAN files")

    elif command == "start":
        print(f"[{MODULE_NAME}] Starting monitor...")
        start_monitor()
        print("Monitor started")

        # PERSISTENT MONITORING LOOP - Keep script alive
        try:
            print("Press Ctrl+C to stop monitoring...")
            import time
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print(f"\n[{MODULE_NAME}] Stopping monitor...")
            stop_monitor()
            print("Monitor stopped")

    elif command == "stop":
        print(f"[{MODULE_NAME}] Stopping monitor...")
        stop_monitor()
        print("Monitor stopped")

    elif command == "heal":
        print(f"[{MODULE_NAME}] Healing registry...")
        registry = scan_plan_files()
        print("Registry healed")

    return 0

if __name__ == "__main__":
    sys.exit(main())
