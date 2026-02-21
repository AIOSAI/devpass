# BACKUP_SYSTEM Branch

**Purpose**: AIPass Core Infrastructure - Backup and Recovery System
**Location**: `/home/aipass/aipass_core/backup_system`

## Overview

Automated file backup system for AIPass with versioned and snapshot modes. Uses modular architecture with auto-discovered modules.

## Commands

Run with: `python3 apps/backup_system.py [command] [options]`

### Backup Commands
- `snapshot` - Full copy backup (overwrites destination)
- `versioned` - Timestamped backup with incremental copies

### Google Drive Sync Commands
- `drive-test` - Test Google Drive connectivity and authentication
- `drive-sync` - Sync snapshot backups to Google Drive (defaults to `backups/system_snapshot/`)
- `drive-stats` - Show Drive file tracker statistics
- `drive-clear-tracker` - Clear file tracker cache (forces full re-upload)

### Options
- `--verbose, -v` - Enable verbose output
- `--note NOTE` - Add a backup note/description
- `--dry-run` - Preview mode (shows what would be copied/deleted)
- `--project NAME` - Project name for Drive sync (default: AIPass)
- `--force` - Force sync all files (ignore change tracker)
- `--help, -h` - Show help message

### Usage Examples

```bash
# Versioned backup with note
drone backup versioned --note "Before refactor"

# Snapshot backup
drone backup snapshot

# Dry run to preview changes
drone @backup_system versioned --dry-run

# Test Google Drive connection
drone backup drive-test

# Sync backups to Google Drive
drone backup drive-sync

# Re-authenticate (if token expired)
python3 apps/modules/reauth_drive.py
```

## Architecture

```
apps/
├── backup_system.py              # Entry point v1.1.0 (auto-discovers modules)
├── modules/
│   ├── backup_core.py            # Backup orchestration v2.0.4 (snapshot/versioned)
│   ├── google_drive_sync.py      # Google Drive sync v2.3.2 (OAuth, parallel upload, thread-safe tracking)
│   ├── reauth_drive.py           # Standalone OAuth re-authentication utility
│   └── integrations.py           # Cloud sync v2.0.1 (Google Drive, readonly protection)
└── handlers/
    ├── config/config_handler.py  # Configuration & ignore patterns
    ├── diff/                     # Diff generation, version tracking, VS Code integration
    ├── json/                     # Metadata, statistics, changelogs, backup info
    ├── models/backup_models.py   # Data structures (BackupResult)
    ├── operations/               # File copy, cleanup, scanning, path building
    ├── reporting/                # Report formatting
    └── utils/system_utils.py     # System utilities (safe_print, temporarily_writable)
```

## Ignore Patterns

Configured in `apps/handlers/config/config_handler.py` (`GLOBAL_IGNORE_PATTERNS`). Key exclusions:
- Python/Node artifacts (`__pycache__`, `.venv`, `node_modules`)
- External repos (`external_repos`, named MCP server repos)
- Media files (`*.png`, `*.jpg`, `*.gif`, etc.)
- OS/IDE junk, archives, disk images, log files
- Recursive backup prevention (`backups`, `system_snapshot`, `versioned_backup`)

Exceptions (backed up despite pattern matches) in `IGNORE_EXCEPTIONS` — includes `BRANCH_REGISTRY.json`, `*_config.json`, templates, `.local.json` files.

> **Note**: Drive sync (`drive-sync`) reads FROM the backup directory — ignore patterns take effect when the backup runs, not at sync time. Run a fresh snapshot to apply pattern changes.

## Key Capabilities

- **Two Backup Modes**: Versioned (timestamped, keeps history) or snapshot (full copy)
- **Performance Optimized**: Skips unchanged files using mtime comparison
- **Accurate Dry-Run**: Preview exactly what would be copied/deleted
- **Clickable Paths**: Ctrl+click file paths in VS Code terminal
- **Smart Cleanup**: Respects exception patterns during cleanup
- **Cloud Integration**: Google Drive sync with OAuth2, parallel uploads (3 workers), local-first change detection, file tracking, SSL retry with backoff
- **Deleted Branch Storage**: Preserves pruned/deleted branches with timestamped directories for recovery

## Dependencies

- **prax**: Logging infrastructure
- **cli**: Console output formatting (Rich)

## Compliance

- **Seed Audit**: 91% compliant (15 documented bypasses for legitimate exceptions)
- **CLI Standard**: 100% compliant (uses cli.apps.modules.console)

## Memory Files

- `BACKUP_SYSTEM.id.json` - Branch identity
- `BACKUP_SYSTEM.local.json` - Session history
- `BACKUP_SYSTEM.observations.json` - Collaboration patterns

---

*Last Updated*: 2026-02-20
*Part of*: AIPass Core Infrastructure