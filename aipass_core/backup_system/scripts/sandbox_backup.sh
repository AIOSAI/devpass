#!/bin/bash
# ===================AIPASS====================
# Name: sandbox_backup.sh - Versioned backup for sandbox/genesis
# Date: 2026-01-20
# Version: 1.0.0
#
# Backs up /mnt/sandbox/ to backup_system's versioned_backup folder
# Designed to complement the main AIPass backup system
# ==============================================

SANDBOX_SOURCE="/mnt/sandbox"
BACKUP_DEST="/home/aipass/aipass_core/backup_system/backups/versioned_backup/sandbox"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="/home/aipass/aipass_core/backup_system/logs/sandbox_backup.log"

# Ensure directories exist
mkdir -p "$BACKUP_DEST"
mkdir -p "$(dirname "$LOG_FILE")"

echo "[$TIMESTAMP] Starting sandbox backup..." | tee -a "$LOG_FILE"
echo "  Source: $SANDBOX_SOURCE" | tee -a "$LOG_FILE"
echo "  Destination: $BACKUP_DEST" | tee -a "$LOG_FILE"

# Use rsync with versioned backup approach
# -a = archive mode (preserves permissions, timestamps, etc.)
# -v = verbose
# --backup = make backups of changed files
# --backup-dir = where to put old versions
# --suffix = suffix for backup files
rsync -av \
    --backup \
    --backup-dir="$BACKUP_DEST/.versions/$TIMESTAMP" \
    --exclude="__pycache__" \
    --exclude=".venv" \
    --exclude="node_modules" \
    --exclude="*.pyc" \
    "$SANDBOX_SOURCE/" "$BACKUP_DEST/current/"

RESULT=$?

if [ $RESULT -eq 0 ]; then
    echo "[$TIMESTAMP] Sandbox backup completed successfully" | tee -a "$LOG_FILE"
else
    echo "[$TIMESTAMP] Sandbox backup failed with exit code $RESULT" | tee -a "$LOG_FILE"
fi

# Show what was backed up
echo "[$TIMESTAMP] Backup contents:" | tee -a "$LOG_FILE"
ls -la "$BACKUP_DEST/current/" 2>/dev/null | tee -a "$LOG_FILE"

exit $RESULT
