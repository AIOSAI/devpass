#!/usr/bin/env python3

# ===================AIPASS====================
# META DATA HEADER
# Name: template_registry_watcher.py - Template Registry Auto-Sync
# Date: 2025-11-04
# Version: 1.0.0
# Category: templates
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2025-11-04): Clean implementation - pure file watcher, no infrastructure
# =============================================

"""
Template Registry Auto-Sync Watcher

WHAT IT DOES:
    Watches template directory and auto-regenerates template_registry.json
    when files are added, removed, or renamed.

THAT'S IT. Nothing else.

Filesystem = single source of truth, registry stays in sync.
"""

import sys
from pathlib import Path
AIPASS_ROOT = Path.home() / "aipass_core"

# Only imports needed for the core task
import json
import time
from datetime import datetime
from typing import Dict, Any
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


# =============================================================================
# CONSTANTS
# =============================================================================

TEMPLATE_DIR = AIPASS_ROOT / "branch_operations" / "templates" / "branch_ template"
REGISTRY_FILE = TEMPLATE_DIR / "template_registry.json"
DEBOUNCE_DELAY = 2.0


# =============================================================================
# CORE FUNCTIONS - Registry Generation
# =============================================================================

def scan_template_directory() -> Dict[str, Any]:
    """
    Scan template directory and build registry from filesystem

    Returns:
        Dict with files and directories structure
    """
    files = {}
    directories = {}

    file_counter = 1
    dir_counter = 1

    # Walk template directory
    for item in TEMPLATE_DIR.rglob("*"):
        # Skip git and cache directories
        if any(part in item.parts for part in ['.git', '__pycache__', '.backup']):
            continue

        relative_path = item.relative_to(TEMPLATE_DIR)

        if item.is_file():
            file_id = f"f{file_counter:03d}"
            files[file_id] = {
                "current_name": item.name,
                "path": str(relative_path),
                "has_branch_placeholder": "{{BRANCH}}" in item.name
            }
            file_counter += 1

        elif item.is_dir():
            dir_id = f"d{dir_counter:03d}"
            directories[dir_id] = {
                "current_name": item.name,
                "path": str(relative_path),
                "has_branch_placeholder": "{{BRANCH}}" in item.name
            }
            dir_counter += 1

    return {"files": files, "directories": directories}


def load_existing_registry() -> Dict[str, Any] | None:
    """
    Load existing registry to preserve custom metadata

    Returns:
        Existing registry dict or None if not found
    """
    if not REGISTRY_FILE.exists():
        return None

    try:
        with open(REGISTRY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return None


def merge_registry_metadata(new_structure: Dict, old_registry: Dict | None) -> Dict:
    """
    Preserve custom metadata from old registry

    Args:
        new_structure: Registry structure from filesystem scan
        old_registry: Existing registry with custom metadata

    Returns:
        Merged registry with new structure + preserved metadata
    """
    if not old_registry:
        return new_structure

    merged = new_structure.copy()

    # Preserve file metadata (purpose, description fields)
    for file_id, file_data in merged.get("files", {}).items():
        if file_id in old_registry.get("files", {}):
            old_data = old_registry["files"][file_id]
            if "purpose" in old_data:
                file_data["purpose"] = old_data["purpose"]
            if "description" in old_data:
                file_data["description"] = old_data["description"]

    # Preserve directory metadata
    for dir_id, dir_data in merged.get("directories", {}).items():
        if dir_id in old_registry.get("directories", {}):
            old_data = old_registry["directories"][dir_id]
            if "purpose" in old_data:
                dir_data["purpose"] = old_data["purpose"]
            if "description" in old_data:
                dir_data["description"] = old_data["description"]

    return merged


def regenerate_registry() -> bool:
    """
    Regenerate template_registry.json from filesystem

    Workflow:
        1. Scan template directory
        2. Load existing registry
        3. Merge (preserve metadata)
        4. Write atomically

    Returns:
        True if successful, False otherwise
    """
    try:
        # Scan filesystem
        new_structure = scan_template_directory()

        # Load existing registry
        old_registry = load_existing_registry()

        # Merge (preserve metadata)
        merged_registry = merge_registry_metadata(new_structure, old_registry)

        # Add metadata
        merged_registry["metadata"] = {
            "version": "1.0.0",
            "last_updated": datetime.now().isoformat(),
            "auto_generated": True,
            "description": "Template file registry - enables safe renames and updates"
        }

        # Write atomically (temp file → rename)
        temp_file = REGISTRY_FILE.with_suffix('.json.tmp')
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(merged_registry, f, indent=2, ensure_ascii=False)
        temp_file.replace(REGISTRY_FILE)

        return True

    except Exception:
        return False


# =============================================================================
# WATCHER - Filesystem Monitoring
# =============================================================================

class TemplateDirectoryWatcher(FileSystemEventHandler):
    """Watches template directory and triggers registry regeneration"""

    def __init__(self):
        self.last_event_time = 0
        self.pending_regeneration = False

    def on_any_event(self, event):
        """Handle filesystem events with debouncing"""
        # Ignore temporary files and system files
        if any(pattern in str(event.src_path) for pattern in ['.tmp', '.backup', '__pycache__', '.git']):
            return

        # Debounce rapid changes (batch file operations)
        current_time = time.time()
        if current_time - self.last_event_time < DEBOUNCE_DELAY:
            self.pending_regeneration = True
            return

        self.last_event_time = current_time
        regenerate_registry()


# =============================================================================
# ORCHESTRATOR INTERFACE
# =============================================================================

def handle_command(args) -> bool:
    """
    Orchestrator interface - called by branch_operations.py

    Args:
        args: Command arguments from orchestrator

    Returns:
        True if command was handled, False otherwise
    """
    if not hasattr(args, 'command'):
        return False

    # Start watcher daemon
    if args.command in ["watch-templates", "template-watch"]:
        observer = Observer()
        event_handler = TemplateDirectoryWatcher()
        observer.schedule(event_handler, str(TEMPLATE_DIR), recursive=True)
        observer.start()

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()
        return True

    # One-time registry regeneration
    elif args.command == "regenerate-registry":
        return regenerate_registry()

    return False
