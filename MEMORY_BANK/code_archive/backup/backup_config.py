#!/usr/bin/env python3

# =============================================
# META DATA HEADER
# Name: backup_config.py
# Date: 2025-10-14
# Version: 1.0.0
# Category: backup_system
#
# CHANGELOG:
#   - v1.0.0 (2025-10-14): Initial extraction from backup.py
#     * Extracted all ignore patterns and configuration (lines 165-457)
#     * Centralized configuration management
#     * Pattern matching utilities for file filtering
# =============================================

"""
Backup System Configuration

All configuration, constants, ignore patterns, and backup mode definitions.
Centralized configuration management with no logic dependencies.
"""

# =============================================
# IMPORTS
# =============================================

from pathlib import Path
from typing import Dict, Any, Set

# =============================================
# CONFIGURATION CONSTANTS
# =============================================

# Base backup directory - dynamically determined relative to branch root
# Module is in apps/, so parent.parent gets to branch root
BASE_BACKUP_DIR = str(Path(__file__).parent.parent / "backups")

# Specific backup destinations for each system
BACKUP_DESTINATIONS = {
    "system_snapshot": f"{BASE_BACKUP_DIR}",
    "versioned_backup": f"{BASE_BACKUP_DIR}",
}

# =============================================
# IGNORE PATTERNS
# =============================================

# Global ignore patterns (what NOT to backup across all systems)
GLOBAL_IGNORE_PATTERNS = [
    # Python cache and temp files
    "__pycache__",
    "*.pyc",
    "*.pyo",


    # Virtual environments
    ".venv",
    "venv",

    # Node.js
    "node_modules",
    "npm-debug.log",
    "yarn-error.log",

    # Operating system files
    ".DS_Store",
    "Thumbs.db",
    "desktop.ini",
    "nul",  # Windows reserved filename issue

    # Temporary files
    #"temp",
    ".temp",
    "tmp",
    ".tmp",
    "*.tmp",
    "*.temp",

    # Build and distribution directories
    "build",
    "dist",
    "install",
    "lib",
    "bin",

    # IDE and editor files
    "*.swp",
    "*.swo",
    "*~",

    # Backup directories (prevent recursive backups) - CRITICAL!
    "backups",  # Matches any directory named "backups"
    "backup_system/backups",  # Explicit path to our backup directory
    "*/backups",  # Any backups subdirectory
    "system_snapshot",  # Snapshot backup folder name
    "versioned_backup",  # Versioned backup folder name

    # System backups and trash
    "TimeShift*",
    "timeshift*",
    ".local/share/Trash",
    "Trash",

    # Linux system directories (don't backup user settings/cache)
    ".local",
    ".cache",
    ".config",
    ".mozilla",
    ".gnupg",
    ".ssh",
    ".vscode/cli",  # VS Code CLI binary (large, regenerates)
    #".vscode/extensions",
    ".vscode-server",
    ".npm-global",
    ".pki",
    ".dotnet",

    # Claude Code session files (change every session) - synced from .gitignore
    #".claude/projects",
    ".claude/todos",
    ".claude/shell-snapshots",
    ".claude/ide",
    ".claude/statsig",
    #".claude/plugins",
    ".claude/.credentials.json",
    ".claude/debug",
    ".claude/file-history",
    ".claude/history.jsonl",
    ".claude/.update.lock",
    #".claude/hooks/.last_diagnostics_file",
    ".serena/logs",
    ".code",


    # Development cache/build directories
    ".npm",
    ".cargo",
    ".rustup",
    ".gem",
    ".gradle",
    ".m2",

    # Application data we don't need in backups
    ".thunderbird",
    ".wine",
    ".steam",
    ".zoom",

    # User directories that shouldn't be backed up
    "Downloads",
    #"Music",
    "Videos",
    "Pictures",
    "Dropbox",
    "system_logs",

    # Archive and compressed files
    "*.zip",
    "*.tar",
    "*.gz",
    "*.bz2",
    "*.rar",
    "*.7z",
    "*.whl",  # Python wheel files (long filenames in archives)

    # Log files
    "*.log",
    "logs",

    # Most JSON files (frequent changes, not human-readable diffs)
    #"*_data.json",
    #"*_log.json",
    #"*_registry.json",
    #"snapshot_backup.json",
    #"snapshot_backup_changelog.json",

    # Miscellaneous
    "*.db",
    "*.bash",
    "*.bashrc",
    "*.bash_history",
    "*.bash_logout",
    #"*.claude.json.backup",
    #"*.env",
    "*.lesshst",
    "*.npmrc",
    "*.sudo_as_admin_successful",
]

# Notable patterns to highlight when skipped
CLI_TRACKING_PATTERNS = [
    "backups", 
    "templates", 
    "/home/aipass/aipass_core/ai_mail"
    "/home/aipass/aipass_core/api",
    "/home/aipass/aipass_core/backup_system",
    "/home/aipass/aipass_core/branch_operations"
    "/home/aipass/aipass_core/devepulse",
    "/home/aipass/aipass_core/drone",
    "/home/aipass/aipass_core/flow",
    "/home/aipass/aipass_core/MEMORY_BANK",
    "/home/aipass/aipass_core/prax",
]

# Files that should be backed up but NOT generate diff files
DIFF_IGNORE_PATTERNS = [
    # Log files (append-only, huge diffs)
    "*.log",
    "*.logs",
    "system_logs/*.log",

    # Most JSON files (frequent changes, not human-readable diffs)
    #"*_config.json",
    #"*_data.json",
    #"*_log.json",
    #"*_registry.json",

    # Python cache/compiled
    "*.pyc",
    "*.pyo",
    "*.pyd",
    "__pycache__/*",

    # Database files
    "*.db",
    "*.sqlite",
    "*.sqlite3",

    # Binary/media files
    "*.exe",
    "*.dll",
    "*.so",
    "*.dylib",

    # Pickle/cache files
    "*.pkl",
    "*.pickle",

    # Temporary files
    "*.tmp",
    "*.temp",
    "*.bak",
    "~*",
]

# Files that should be backed up despite matching ignore patterns
# Synced from .gitignore exceptions (! prefix patterns)
IGNORE_EXCEPTIONS = [
    ".gitignore",  # Root .gitignore file should be backed up
    "*.local.md",  # AIPass session tracking files (caught by .local pattern but should be backed up)
    ".vscode/settings.json",  # VS Code settings
    "*/.claude/settings.local.json",  # Claude local settings in any directory
    "tools/cleanup_configs/*.json",  # Cleanup config files
    "*_config.json",  # All config JSON files
    "drone/commands/global/*.json",  # Drone global commands
    ".claude.json",  # Claude config
    ".mcp.json",  # MCP config
    ".config/nerd-dictation/*",  # Nerd dictation config
    ".commands.json",  # Commands config

    # === TEMPLATES: FULL EXCEPTION - EVERY FILE ===
    "templates/**",  # FULL EXCEPTION: Include EVERY file in templates directory
    "*/templates/**",  # Templates in any subdirectory
    "templates/*/**",  # All subdirectories and files in templates
    "*/templates/*/**",  # All subdirectories and files in templates anywhere

    # === TEMPLATE SUBDIRECTORIES (explicit) ===
    "templates/ai_branch_setup_template/ai_mail.local/**",
    "templates/ai_branch_setup_template/logs/**",
    "templates/ai_branch_setup_template/standards.local/**",
    "templates/ai_branch_setup_template/.claude/**",
    "templates/ai_branch_setup_template/.archive/**",

    # === MARKERS ===
    ".gitkeep",  # Include all .gitkeep marker files (especially in templates)
    ".gitattributes",  # Git attributes files
    ".local.json"
]

# Files that SHOULD have diffs created (exceptions to ignore patterns)
DIFF_INCLUDE_PATTERNS = [
    "profile.json",
    "pyrightconfig.json"
    "package.json",
    ".mcp.json",
    "settings.json",
    "settings.local.json",
]

# =============================================
# BACKUP MODE CONFIGURATIONS
# =============================================

BACKUP_MODES = {
    'snapshot': {
        'name': 'System Snapshot',
        'description': 'Dynamic instant backup (overwrites previous)',
        'destination': BACKUP_DESTINATIONS["system_snapshot"],
        'folder_name': 'system_snapshot',
        'behavior': 'dynamic',  # overwrites previous
        'usage': 'Quick saves before changes'
    },
    'versioned': {
        'name': 'Versioned Backup',
        'description': 'Cumulative version history (keeps all file versions)',
        'destination': BACKUP_DESTINATIONS["versioned_backup"],
        'folder_name': 'versioned_backup',
        'behavior': 'versioned',  # keeps all versions
        'usage': 'Complete file version history in single location'
    },
}

# =============================================
# HELPER FUNCTIONS
# =============================================

def get_ignore_patterns() -> list:
    """Get the global ignore patterns list

    Returns:
        Copy of global ignore patterns list
    """
    return GLOBAL_IGNORE_PATTERNS.copy()


def get_cli_tracking_patterns() -> list:
    """Get the CLI tracking patterns list

    Returns:
        Copy of CLI tracking patterns list
    """
    return CLI_TRACKING_PATTERNS.copy()


def get_backup_destination(system_name: str) -> str:
    """Get backup destination for a specific backup system

    Args:
        system_name: Name of the backup system

    Returns:
        Path to backup destination, or base directory if not found
    """
    return BACKUP_DESTINATIONS.get(system_name, BASE_BACKUP_DIR)


def filter_tracked_items(skipped_items: Dict[str, Set[str]]) -> Dict[str, Set[str]]:
    """Filter skipped items to only show project-specific items

    Uses CLI tracking patterns to identify important items worth showing to user.

    Args:
        skipped_items: Dictionary with 'directories' and 'files' sets

    Returns:
        Filtered dictionary with only tracked items
    """
    tracking_patterns = get_cli_tracking_patterns()
    filtered_items = {
        "directories": set(),
        "files": set()
    }

    def matches_pattern(item_path: str, patterns: list) -> bool:
        """Check if item path matches any tracking pattern"""
        for pattern in patterns:
            if pattern in item_path or item_path.startswith(pattern):
                return True
            # Check wildcard patterns
            if pattern.startswith('*') and item_path.endswith(pattern[1:]):
                return True
        return False

    # Filter directories
    for directory in skipped_items.get("directories", set()):
        if matches_pattern(directory, tracking_patterns):
            filtered_items["directories"].add(directory)

    # Filter files
    for file_path in skipped_items.get("files", set()):
        if matches_pattern(file_path, tracking_patterns):
            filtered_items["files"].add(file_path)

    return filtered_items

# =============================================
# MODULE INITIALIZATION
# =============================================

# No initialization needed - pure configuration
