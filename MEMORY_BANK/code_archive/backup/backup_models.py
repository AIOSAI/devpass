#!/usr/bin/env python3

# =============================================
# META DATA HEADER
# Name: backup_models.py
# Date: 2025-10-14
# Version: 1.0.0
# Category: backup_system
#
# CHANGELOG:
#   - v1.0.0 (2025-10-14): Initial extraction from backup.py
#     * Extracted BackupResult class (lines 654-681)
#     * Standalone data model with no dependencies
#     * Used by all backup modules for result tracking
# =============================================

"""
Backup System Data Models

Shared data structures used across all backup modules.
Simple data containers with no complex logic or dependencies.
"""

# =============================================
# IMPORTS
# =============================================

import datetime
from typing import List

# =============================================
# DATA MODELS
# =============================================

class BackupResult:
    """Result of a backup operation

    Tracks statistics and errors for backup operations.
    Used by all modules to report success/failure and collect metrics.
    """

    def __init__(self):
        # File statistics
        self.files_checked: int = 0
        self.files_copied: int = 0
        self.files_added: int = 0      # New files added (versioned mode)
        self.files_skipped: int = 0
        self.files_deleted: int = 0

        # Error tracking
        self.errors: int = 0
        self.error_details: List[str] = []
        self.warnings: List[str] = []
        self.critical_errors: List[str] = []

        # Metadata
        self.start_time = datetime.datetime.now()
        self.backup_path: str = ""
        self.mode: str = ""
        self.success: bool = True

    def add_error(self, error_msg: str, is_critical: bool = False):
        """Add an error to the result

        Args:
            error_msg: Error message describing what failed
            is_critical: If True, marks entire backup as failed
        """
        self.errors += 1
        self.error_details.append(error_msg)
        if is_critical:
            self.critical_errors.append(error_msg)
            self.success = False

    def add_warning(self, warning_msg: str):
        """Add a warning to the result

        Args:
            warning_msg: Warning message for non-critical issues
        """
        self.warnings.append(warning_msg)

# =============================================
# MODULE INITIALIZATION
# =============================================

# No initialization needed - pure data models
