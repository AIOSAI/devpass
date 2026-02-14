#!/usr/bin/env python3

# =============================================
# META DATA HEADER
# Name: flow_claude_updater.py
# Date: 2025-10-24
# Version: 2.0.0
# Description: Lightweight plan output updates - fast synchronization without AI calls
#
# CHANGELOG:
#   - v2.0.0 (2025-10-24): Added 3-file JSON structure (config/data/log), metadata header, skip archived plans
#   - v1.0.0 (2025-10-18): Initial implementation with cache-based updates
# =============================================

"""
Flow CLAUDE Output Updater - Lightweight plan summary synchronization
=====================================================================

PURPOSE:
--------
Updates CLAUDE.json and branch CLAUDE.local.md files from cached summaries WITHOUT calling AI.
This is the fast operation that runs after every flow action (create/close/restore).

WHEN TO USE:
------------
- After creating a plan (placeholder entry written for branch + admin views)
- After closing a plan (moves to recently closed without new AI call)
- After restoring a plan (move back to Active Plans)
- After any registry change (keep CLAUDE outputs synchronized)

WHEN NOT TO USE:
----------------
- When plan content changed (use flow_plan_summarizer.py to regenerate summary)
- When closing a plan (flow_plan_summarizer.py generates final summary first)

PERFORMANCE:
------------
- No AI calls = instant updates (~0.1s)
- Reads: plan_summaries.json (cache), flow_registry.json (metadata)
- Writes: CLAUDE.json + branch CLAUDE.local.md files
- Safe to call on every flow action

DESIGN PHILOSOPHY:
------------------
Separation of concerns:
1. flow_plan_summarizer.py = AI summarization (heavy, only when needed)
2. flow_claude_updater.py = File update (light, every action)

This prevents the "update CLAUDE" problem where summaries weren't
showing up because we were conflating "generate summary" with "update file".

Author: Flow Branch
Date: 2025-10-24
Version: 1.0.0
"""

import json
import argparse
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Optional

# Path setup - standard pattern for all flow modules
AIPASS_ROOT = Path.home() / "aipass_core"
FLOW_ROOT = AIPASS_ROOT / "flow"
sys.path.append(str(AIPASS_ROOT))

# Import logger
from prax.apps.modules.prax_logger import system_logger as logger
from flow.apps.archive_temp.flow_plan_summarizer import write_plan_outputs

# =============================================
# CONFIGURATION
# =============================================

# Module identity
MODULE_NAME = "flow_claude_updater"

# System paths
ECOSYSTEM_ROOT = AIPASS_ROOT
FLOW_JSON_DIR = FLOW_ROOT / "flow_json"

# Auto-create JSON directory
FLOW_JSON_DIR.mkdir(exist_ok=True)

# 3-file JSON structure
CONFIG_FILE = FLOW_JSON_DIR / "flow_claude_updater_config.json"
DATA_FILE = FLOW_JSON_DIR / "flow_claude_updater_data.json"
LOG_FILE = FLOW_JSON_DIR / "flow_claude_updater_log.json"

# Shared files from other modules
REGISTRY_FILE = FLOW_JSON_DIR / "flow_registry.json"
SUMMARIES_FILE = FLOW_JSON_DIR / "plan_summaries.json"
CLAUDE_JSON_FILE = Path.home() / "CLAUDE.json"

# =============================================
# JSON FILE MANAGEMENT
# =============================================

def load_updater_config() -> Dict[str, Any]:
    """Load updater's own configuration"""
    default_config = {
        "version": "1.0.0",
        "auto_update_enabled": True,
        "update_timeout_seconds": 10
    }

    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return {**default_config, **config}
        except Exception as e:
            logger.error(f"[{MODULE_NAME}] Config load failed: {e}")
            return default_config
    else:
        # Create default config
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2)
        except Exception as e:
            logger.error(f"[{MODULE_NAME}] Config creation failed: {e}")
        return default_config

def load_data() -> Dict[str, Any]:
    """Load runtime data"""
    default_data = {
        "total_updates": 0,
        "last_update_timestamp": 0,
        "plans_updated": 0
    }

    if DATA_FILE.exists():
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"[{MODULE_NAME}] Data load failed: {e}")
            return default_data
    else:
        # Create default data
        try:
            with open(DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(default_data, f, indent=2)
        except Exception as e:
            logger.error(f"[{MODULE_NAME}] Data creation failed: {e}")
        return default_data

def save_data(data: Dict[str, Any]):
    """Save runtime data"""
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logger.error(f"[{MODULE_NAME}] Data save failed: {e}")

def log_operation(operation: str, success: bool, details: str):
    """Log operation to JSON file"""
    log_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "operation": operation,
        "success": success,
        "details": details
    }

    # Load existing log
    if LOG_FILE.exists():
        try:
            with open(LOG_FILE, 'r', encoding='utf-8') as f:
                log_data = json.load(f)
        except Exception:
            log_data = {"operations": []}
    else:
        log_data = {"operations": []}

    log_data["operations"].append(log_entry)
    log_data["operations"] = log_data["operations"][-100:]  # Keep last 100

    try:
        with open(LOG_FILE, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2)
    except Exception as e:
        logger.error(f"[{MODULE_NAME}] Log save failed: {e}")

# =============================================
# SHARED FILE OPERATIONS
# =============================================

def load_registry() -> Dict[str, Any]:
    """Load the flow registry"""
    if not REGISTRY_FILE.exists():
        logger.warning(f"[{MODULE_NAME}] Registry file not found")
        return {"plans": {}}

    try:
        with open(REGISTRY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"[{MODULE_NAME}] Registry load failed: {e}")
        return {"plans": {}}

def load_summaries() -> Dict[str, Any]:
    """Load existing summaries cache"""
    if not SUMMARIES_FILE.exists():
        return {}

    try:
        with open(SUMMARIES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"[{MODULE_NAME}] Summaries load failed: {e}")
        return {}

# =============================================
# CORE UPDATE FUNCTION
# =============================================

def is_template_file(file_path: str) -> bool:
    """Check if a PLAN file is an empty template"""
    try:
        path = Path(file_path)
        if not path.exists():
            return True  # Missing file treated as empty

        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Use same template detection as flow_plan_summarizer.py
        template_indicators = [
            "[What do you want to achieve? Be specific about the end state.]",
            "[Break down into 3-5 concrete goals. What must be accomplished?]",
            "[How will you tackle this? Research first? Agents for broad analysis? Direct work?]",
            "[Document each significant action with outcome]",
            "[Working notes, discoveries, important context]",
            "[What defines complete for this specific PLAN?]"
        ]

        markers_found = sum(1 for indicator in template_indicators if indicator in content)
        return markers_found >= 4  # 4+ markers = empty template

    except Exception as e:
        logger.error(f"[{MODULE_NAME}] Error checking template status: {e}")
        return True  # Treat errors as empty to be safe

def update_plan_outputs_from_cache() -> bool:
    """Refresh CLAUDE.json and branch CLAUDE.local.md files from cached summaries."""
    try:
        # Load data
        registry = load_registry()
        cached_summaries = load_summaries()
        summaries: Dict[str, Any] = {}
        now_iso = datetime.now(timezone.utc).isoformat()

        for plan_num, plan_info in registry.get("plans", {}).items():
            if plan_num in cached_summaries:
                cached_entry = cached_summaries[plan_num].copy()
                cached_entry["status"] = plan_info.get("status", "unknown")
                cached_entry["location"] = plan_info.get("relative_path", "unknown")
                cached_entry["subject"] = plan_info.get("subject", "")
                cached_entry["file_path"] = plan_info.get("file_path", "")
                cached_entry.setdefault("generated_at", now_iso)
                cached_entry.setdefault("is_empty", False)
                summaries[plan_num] = cached_entry
            else:
                file_path = plan_info.get("file_path", "")
                plan_status = plan_info.get("status", "open")

                if plan_status == "closed" and not Path(file_path).exists():
                    logger.info(f"[{MODULE_NAME}] PLAN{plan_num}: Closed and archived, skipping cached update")
                    continue

                is_template = is_template_file(file_path)
                summary_text = "Empty plan template - no content added" if is_template else "Plan in progress - summary will be generated when closed"

                summaries[plan_num] = {
                    "summary": summary_text,
                    "status": plan_status,
                    "location": plan_info.get("relative_path", "unknown"),
                    "subject": plan_info.get("subject", ""),
                    "file_path": file_path,
                    "generated_at": now_iso,
                    "is_empty": is_template,
                    "is_placeholder": True
                }

        write_plan_outputs(summaries)

        data = load_data()
        data["total_updates"] += 1
        data["last_update_timestamp"] = datetime.now(timezone.utc).isoformat()
        data["plans_updated"] = len(summaries)
        save_data(data)

        log_operation("plan_outputs_updated", True, f"Updated CLAUDE outputs for {len(summaries)} plans (cache)")
        logger.info(f"[{MODULE_NAME}] Refreshed CLAUDE outputs from cache ({len(summaries)} plans)")

        return True

    except Exception as e:
        logger.error(f"[{MODULE_NAME}] Plan output refresh failed: {e}")
        return False

# =============================================
# CLI INTERFACE
# =============================================

def main():
    """Command-line interface"""
    parser = argparse.ArgumentParser(
        description='Flow plan output updater - fast CLAUDE.json/CLAUDE.local.md refresh from cache (no AI)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
COMMANDS:
  Commands: update

DESCRIPTION:
  Lightweight updater that syncs CLAUDE.json and CLAUDE.local.md files with cached plan summaries.
  No AI calls = instant updates. Run this after every flow action.

WHEN TO USE:
  - After creating a plan (writes placeholder entries)
  - After closing/restoring a plan (updates statuses without new AI calls)
  - After any registry change (keeps CLAUDE outputs current)

WHEN NOT TO USE:
  - To regenerate summaries (use flow_plan_summarizer.py instead)
  - During plan close (summarizer runs first, then this)

EXAMPLES:
  python3 flow_claude_updater.py
  python3 flow_claude_updater.py update

PERFORMANCE:
  Runs in <0.1s (no AI calls, just file I/O)
        """
    )

    parser.add_argument('command',
                       nargs='?',
                       choices=['update'],
                       default='update',
                       help='Command to execute (default: update)')

    args = parser.parse_args()

    if args.command == 'update':
        success = update_plan_outputs_from_cache()

        if success:
            print(f"[{MODULE_NAME}] ✅ CLAUDE.json and branch CLAUDE.local.md updated from cache (instant, no AI)")
            return 0
        else:
            print(f"[{MODULE_NAME}] ❌ CLAUDE output refresh failed - check logs")
            return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
