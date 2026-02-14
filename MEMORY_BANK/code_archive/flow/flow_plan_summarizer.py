#!/usr/bin/env python3
# =============================================
# META DATA HEADER
# Name: flow_plan_summarizer.py - Generate AI summaries of PLAN files  
# Date: 2025-09-01
# Version: 1.0.1
# Category: flow
# 
# CHANGELOG (Max 5 entries - remove oldest when adding new):
#   - v1.0.1 (2025-09-05): Fixed header format to match STANDARDS.md
#   - v1.0.0 (2025-09-01): Initial implementation with API-only behavior
# =============================================
"""
FLOW PLAN SUMMARIZER
Generate AI-powered summaries of PLAN files and update CLAUDE.json / CLAUDE.local.md

Features:
- Reads from flow_registry.json for plan locations
- Caches summaries in plan_summaries.json  
- Writes aggregated plan data to CLAUDE.json (admin view)
- Generates branch-scoped CLAUDE.local.md files
- Only regenerates summaries for modified plans
- Strict API-only operation (no fallbacks)

Triggers:
- /updatedocs command (via hook)
- drone close plan (integrated)
- Manual: python flow/flow_plan_summarizer.py
"""

# =============================================
# IMPORTS
# =============================================
# Standard imports
import sys
import argparse
from pathlib import Path
AIPASS_ROOT = Path.home() / "aipass_core"
FLOW_ROOT = AIPASS_ROOT / "flow"
sys.path.append(str(AIPASS_ROOT))  # To ecosystem root
from prax.apps.modules.prax_logger import system_logger as logger

import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional

# Import API provider for summarization - REQUIRED, no fallbacks!
try:
    from api.apps.openrouter import get_response
    API_AVAILABLE = True
except ImportError:
    API_AVAILABLE = False
    logger.error("[FLOW_PLAN_SUMMARIZER] CRITICAL: API provider not available - cannot generate summaries")

# =============================================
# CONSTANTS & CONFIG
# =============================================

MODULE_NAME = "flow_plan_summarizer"
MODULE_VERSION = "2.0.0"
MODULE_CATEGORY = "flow"

# Paths
ECOSYSTEM_ROOT = AIPASS_ROOT
FLOW_JSON_DIR = FLOW_ROOT / "flow_json"

# Registry and data files
REGISTRY_FILE = FLOW_JSON_DIR / "flow_registry.json"
SUMMARIES_FILE = FLOW_JSON_DIR / "plan_summaries.json"  
CLAUDE_JSON_FILE = Path.home() / "CLAUDE.json"

# Standard 3-file JSON structure
CONFIG_FILE = f"{MODULE_NAME}_config.json"
DATA_FILE = f"{MODULE_NAME}_data.json"
LOG_FILE = f"{MODULE_NAME}_log.json"

# Full paths to JSON files
CONFIG_PATH = FLOW_JSON_DIR / CONFIG_FILE
DATA_PATH = FLOW_JSON_DIR / DATA_FILE
LOG_PATH = FLOW_JSON_DIR / LOG_FILE

# =============================================
# HELPER FUNCTIONS
# =============================================

def log_operation(operation: str, success: bool, details: str | None = None, error: str | None = None, correlation_id: str | None = None):
    """Log operation to both JSON logs (Tier 1) and system logs (Tier 2)"""
    try:
        # Tier 1: JSON Logs - Critical operations tracking
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "operation": operation,
            "success": success,
            "details": details,
            "error": error,
            "correlation_id": correlation_id
        }
        _append_to_json_log(log_entry)
        
        # Tier 2: System Logs - Debug/technical info
        if success:
            logger.info(f"{MODULE_NAME}: {operation} - {details or 'completed successfully'}")
        else:
            logger.error(f"{MODULE_NAME}: {operation} - {error or 'failed'}")
            
    except Exception as e:
        # Tier 3: Console Output - Clean user feedback
        print(f"[{MODULE_NAME}] Log error: {e}")

def _append_to_json_log(log_entry: dict):
    """Append entry to JSON log file with sequential IDs and newest-first ordering"""
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing log or create new structure
        if LOG_PATH.exists():
            with open(LOG_PATH, 'r', encoding='utf-8') as f:
                log_data = json.load(f)
        else:
            log_data = {
                "module_name": MODULE_NAME,
                "entries": [],
                "summary": {"total_entries": 0, "last_entry": None, "next_id": 1}
            }
        
        # Add new entry with sequential ID
        log_entry["id"] = log_data["summary"]["next_id"]
        log_data["entries"].insert(0, log_entry)  # Newest first
        
        # Update summary
        log_data["summary"]["total_entries"] += 1
        log_data["summary"]["last_entry"] = log_entry["timestamp"]
        log_data["summary"]["next_id"] += 1
        
        # Keep only last 100 entries
        if len(log_data["entries"]) > 100:
            log_data["entries"] = log_data["entries"][:100]
        
        # Save updated log
        with open(LOG_PATH, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)
            
    except Exception as e:
        logger.error(f"Failed to write to JSON log: {e}")

def load_module_config() -> Dict[str, Any]:
    """Load module configuration with proper error handling"""
    try:
        if not CONFIG_PATH.exists():
            CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
            default_config = {
                "module_name": MODULE_NAME,
                "timestamp": datetime.now().isoformat(),
                "config": {
                    "enabled": True,
                    "version": MODULE_VERSION,
                    "api_settings": {
                        "timeout_seconds": 30,
                        "max_tokens": 100,
                        "model": "deepseek/deepseek-chat-v3.1:free"
                    },
                    "cache_settings": {
                        "enabled": True,
                        "max_cache_entries": 50
                    },
                    "summary_settings": {
                        "hide_empty_plans": True
                    }
                }
            }
            
            with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)
            
            log_operation("config_created", True, "Default configuration file created")
        
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        log_operation("config_loaded", True, "Configuration loaded successfully")
        return config
        
    except Exception as e:
        log_operation("config_load_failed", False, error=str(e))
        raise

def load_module_data() -> Dict[str, Any]:
    """Load module runtime data"""
    try:
        if not DATA_PATH.exists():
            DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
            default_data = {
                "module_name": MODULE_NAME,
                "last_updated": datetime.now().isoformat(),
                "runtime_state": {
                    "current_status": "active",
                    "cached_summaries": {},
                    "last_summary_run": None
                },
                "statistics": {
                    "total_summaries_generated": 0,
                    "successful_operations": 0,
                    "failed_operations": 0,
                    "cache_hits": 0,
                    "cache_misses": 0
                }
            }
            
            with open(DATA_PATH, 'w', encoding='utf-8') as f:
                json.dump(default_data, f, indent=2, ensure_ascii=False)
        
        with open(DATA_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
            
    except Exception as e:
        log_operation("data_load_failed", False, error=str(e))
        return {"runtime_state": {"cached_summaries": {}}, "statistics": {}}

def save_module_data(data: Dict[str, Any]):
    """Save module runtime data"""
    try:
        data["last_updated"] = datetime.now().isoformat()
        DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
        
        with open(DATA_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        log_operation("data_saved", True, "Runtime data saved successfully")
        
    except Exception as e:
        log_operation("data_save_failed", False, error=str(e))
        raise

def load_registry() -> Dict[str, Any]:
    """Load the flow registry"""
    if not REGISTRY_FILE.exists():
        log_operation("registry_load_failed", False, error="Registry file not found")
        print("[WARNING] Flow registry missing - no plans found")
        return {"plans": {}}
    
    try:
        with open(REGISTRY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        log_operation("registry_load_failed", False, error=str(e))
        print(f"[ERROR] Flow registry corrupted - {str(e)}")
        return {"plans": {}}

def load_summaries() -> Dict[str, Any]:
    """Load existing summaries cache and clean up failed entries"""
    if not SUMMARIES_FILE.exists():
        return {}
    
    try:
        with open(SUMMARIES_FILE, 'r', encoding='utf-8') as f:
            summaries = json.load(f)
        
        # Self-healing: Remove failed summaries so they get retried
        cleaned_summaries = {}
        failed_count = 0
        for plan_num, summary_data in summaries.items():
            summary_text = summary_data.get("summary", "")
            if "Summary generation failed" in summary_text or "Unable to generate summary" in summary_text:
                failed_count += 1
                log_operation("cache_cleanup", True, f"PLAN{plan_num}: Removed failed summary from cache for retry")
            else:
                cleaned_summaries[plan_num] = summary_data
        
        if failed_count > 0:
            print(f"[HEALING] Cleaned {failed_count} failed summaries from cache for retry")
            
        return cleaned_summaries
        
    except Exception as e:
        log_operation("summaries_load_failed", False, error=str(e))
        return {}

def save_summaries(summaries: Dict[str, Any]):
    """Save summaries cache"""
    try:
        FLOW_JSON_DIR.mkdir(exist_ok=True)
        with open(SUMMARIES_FILE, 'w', encoding='utf-8') as f:
            json.dump(summaries, f, indent=2, ensure_ascii=False)
        log_operation("summaries_saved", True, "Cache file updated successfully")
    except Exception as e:
        log_operation("summaries_save_failed", False, error=str(e))


# =============================================
# OUTPUT GENERATION HELPERS
# =============================================

def _normalize_plan_entry(plan_num: str, info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Normalize plan metadata for downstream outputs."""
    plan_id = f"PLAN{plan_num}"
    file_path = info.get("file_path", "")
    path_obj: Optional[Path] = None

    if file_path:
        path_obj = Path(file_path)
        if not path_obj.is_absolute():
            path_obj = Path.home() / file_path

    branch_dir: Optional[Path] = None
    branch_relative_path = ""

    if path_obj is not None:
        if path_obj.is_file():
            branch_dir = path_obj.parent
        elif path_obj.exists():
            branch_dir = path_obj

        try:
            branch_relative_path = str(path_obj.relative_to(Path.home()))
        except Exception:
            branch_relative_path = str(path_obj)
    else:
        branch_relative_path = file_path

    branch_name = (info.get("location") or "").split("/", 1)[0]

    if not branch_name and branch_relative_path:
        branch_name = branch_relative_path.split("/", 1)[0]

    if branch_dir is not None and not branch_name:
        try:
            branch_name = branch_dir.relative_to(Path.home()).parts[0]
        except Exception:
            branch_name = branch_dir.name if branch_dir.name else "unknown"

    entry = {
        "plan": plan_id,
        "status": info.get("status", "unknown"),
        "summary": info.get("summary", ""),
        "subject": info.get("subject", ""),
        "branch": branch_name or "unknown",
        "location": info.get("location", "unknown"),
        "file_path": file_path,
        "relative_path": branch_relative_path,
        "generated_at": info.get("generated_at"),
        "is_empty": info.get("is_empty", False),
        "branch_path": None,
        "branch_relative_path": ""
    }

    if path_obj is not None and branch_dir is not None:
        try:
            entry["branch_relative_path"] = str(path_obj.relative_to(branch_dir))
        except Exception:
            entry["branch_relative_path"] = entry["relative_path"]

    if path_obj is not None:
        entry["absolute_path"] = str(path_obj)
        try:
            entry["file_uri"] = path_obj.as_uri()
        except ValueError:
            entry["file_uri"] = None

        entry["vscode_uri"] = f"vscode://file{entry['absolute_path']}" if entry.get("absolute_path") else None

    if branch_dir is not None:
        try:
            branch_dir.relative_to(Path.home())
            entry["branch_path"] = branch_dir
        except Exception:
            entry["branch_path"] = None

    return entry


def _build_plan_output_sets(summaries: Dict[str, Any]):
    """Partition plan entries into central and branch-specific collections."""
    active_entries = []
    closed_entries = []
    branch_map: Dict[Path, Dict[str, Any]] = {}

    for plan_num in sorted(summaries.keys()):
        entry = _normalize_plan_entry(plan_num, summaries[plan_num])
        if entry is None:
            continue

        json_entry = {k: v for k, v in entry.items() if k not in {"branch_path"} and v is not None}

        if entry["status"] == "closed":
            closed_entries.append(json_entry)
        else:
            active_entries.append(json_entry)

        branch_path = entry.get("branch_path")
        if branch_path:
            branch_bucket = branch_map.setdefault(
                branch_path,
                {"branch_name": entry["branch"], "active": [], "closed": []}
            )
            branch_entry = {k: v for k, v in entry.items() if k != "branch_path" and v is not None}
            if entry["status"] == "closed":
                branch_bucket["closed"].append(branch_entry)
            else:
                branch_bucket["active"].append(branch_entry)

    return active_entries, closed_entries, branch_map


def _write_central_summary_json(active_entries: list, closed_entries: list):
    """Persist aggregated plan data to CLAUDE.json."""
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "active_plans": active_entries,
        "recently_closed": closed_entries[-5:],
        "statistics": {
            "active_count": len(active_entries),
            "total_closed": len(closed_entries),
            "recently_closed_included": min(len(closed_entries), 5)
        }
    }

    try:
        with open(CLAUDE_JSON_FILE, 'w', encoding='utf-8') as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        log_operation(
            "claude_json_updated",
            True,
            f"Wrote {len(active_entries)} active and {min(len(closed_entries), 5)} recently closed plans to CLAUDE.json"
        )
    except Exception as e:
        log_operation("claude_json_update_failed", False, error=str(e))
        raise


def _format_plan_lines(entries: list, default_message: str) -> list:
    """Format plan entries as markdown bullet lines."""
    if not entries:
        return [default_message]

    lines = []
    for entry in entries:
        plan_id = entry["plan"]
        icon = "✅" if entry["status"] == "closed" else ("⚪" if entry.get("is_empty") else "🟢")

        link_target = entry.get("branch_relative_path") or entry.get("relative_path") or entry.get("file_path")
        if link_target:
            plan_link = f"[{plan_id}]({link_target})"
        else:
            plan_link = plan_id

        lines.append(f"- {plan_link} ({entry.get('branch', 'unknown')}) {icon}")
        lines.append(f"  {entry.get('summary', '')}")
    return lines


def _write_branch_local_files(branch_map: Dict[Path, Dict[str, Any]]):
    """Write CLAUDE.local.md files for each branch."""
    for branch_path, data in branch_map.items():
        branch_name = data.get("branch_name") or branch_path.name
        file_path = branch_path / "CLAUDE.local.md"

        lines = [
            "⚠️ WARNING: This file is automatically updated by the flow system. Manual edits will be overwritten.",
            "",
            f"## Plan Summaries — {branch_name}",
            ""
        ]

        lines.append("Active Plans:")
        lines.extend(_format_plan_lines(data.get("active", []), "- None"))
        lines.append("")

        lines.append("Recently Closed:")
        recent_closed = data.get("closed", [])[-5:]
        lines.extend(_format_plan_lines(recent_closed, "- None"))
        lines.append("")

        content = "\n".join(lines).rstrip() + "\n"

        try:
            branch_path.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            log_operation("branch_claude_local_updated", True, f"{branch_name}: {file_path}")
        except Exception as e:
            log_operation("branch_claude_local_failed", False, f"{branch_name}: {file_path}", error=str(e))


def write_plan_outputs(summaries: Dict[str, Any]):
    """Write centralized JSON and branch-local markdown outputs."""
    config = load_module_config()
    hide_empty = config.get("config", {}).get("summary_settings", {}).get("hide_empty_plans", True)

    filtered_summaries = {}
    for plan_num, info in summaries.items():
        if hide_empty and info.get("is_empty") and info.get("status") != "closed":
            continue
        filtered_summaries[plan_num] = info

    active_entries, closed_entries, branch_map = _build_plan_output_sets(filtered_summaries)
    _write_central_summary_json(active_entries, closed_entries)
    _write_branch_local_files(branch_map)

def extract_content_from_plan(plan_path: Path) -> str:
    """Extract meaningful content from a PLAN file"""
    try:
        content = plan_path.read_text(encoding='utf-8')
        
        # Check for actual work content in Work Log section
        work_log_section = False
        work_content = []
        notes_section = False
        notes_content = []
        objectives_section = False
        objectives_content = []
        
        lines = content.split('\n')
        for line in lines:
            # Track which section we're in
            if "## Work Log" in line:
                work_log_section = True
                notes_section = False
                objectives_section = False
                continue
            elif "## Notes" in line:
                notes_section = True
                work_log_section = False
                objectives_section = False
                continue
            elif "## Objectives" in line:
                objectives_section = True
                work_log_section = False
                notes_section = False
                continue
            elif line.startswith("## "):
                work_log_section = False
                notes_section = False
                objectives_section = False
                continue
            
            # Collect content from each section
            if work_log_section and line.strip() and not line.startswith("###"):
                # Skip "Started PLAN" lines but keep actual work items
                if "Started PLAN" not in line and "IMPORTANT" not in line and "CONTEXT" not in line:
                    work_content.append(line.strip())
            elif notes_section and line.strip():
                # Check if it's not the template marker
                if "[Working notes, thoughts, and important information]" not in line:
                    notes_content.append(line.strip())
            elif objectives_section and line.strip():
                # Check if it's not the template marker
                if "[What we're working on - specific goals and outcomes]" not in line:
                    objectives_content.append(line.strip())
        
        # Check if there's any actual work content
        has_work = len(work_content) > 0
        has_notes = len(notes_content) > 0
        has_objectives = len(objectives_content) > 0
        
        # If no actual content in any section, it's a template
        if not has_work and not has_notes and not has_objectives:
            return "Empty plan template"
        
        # Build summary from available content, prioritizing Work Log
        summary_parts = []
        if work_content:
            summary_parts.extend(work_content[:3])  # First 3 work items
        if objectives_content and len(summary_parts) < 3:
            summary_parts.extend(objectives_content[:2])  # Add objectives if needed
        if notes_content and len(summary_parts) < 3:
            summary_parts.extend(notes_content[:2])  # Add notes if needed
        
        # Return first 500 chars of meaningful content
        content = " ".join(summary_parts)[:500]
        return content if content else "Empty plan template"
        
    except Exception as e:
        log_operation("plan_file_read_failed", False, error=str(e))
        return "Error reading plan file"

def generate_ai_summary(content: str, plan_num: str) -> str:
    """Generate ~20 word AI summary of plan content"""
    # Check if it's an empty template
    if "Empty plan template" in content:
        return "Inactive - empty template, no work started"

    if not API_AVAILABLE:
        # NO FALLBACK! If API is not available, fail completely
        error_msg = f"PLAN{plan_num} - API NOT AVAILABLE: Cannot generate summary without AI"
        log_operation("summary_failed", False, error=error_msg)
        return error_msg

    try:
        # Load model from config instead of hardcoding
        config = load_module_config()
        model = config.get("config", {}).get("api_settings", {}).get("model", "meta-llama/llama-3.3-70b-instruct:free")

        # Use API to generate summary via OpenRouter

        prompt = f"""Generate a concise 15-20 word summary of this PLAN content.
Focus on the main objective or work being done.
If the plan is empty or just template text, respond with "Empty plan, no work started yet"

Content:
{content[:500]}

Summary (15-20 words):"""

        messages = [{"role": "user", "content": prompt}]
        response = get_response(messages, model=model, caller="flow_plan_summarizer")
        
        if response:
            summary = response.strip()
            # Ensure reasonable length
            if len(summary.split()) > 25:
                summary = " ".join(summary.split()[:20]) + "..."
            return summary
        else:
            # No response - check API logs for specific error type
            # get_response returns None when API fails
            return f"PLAN{plan_num} - API CONNECTION ERROR: Check API key and internet"
            
    except Exception as e:
        # Distinguish between different error types like flow_mbank does
        error_msg = str(e)
        
        # Check for specific error patterns
        if "API CONNECTION ERROR" in error_msg:
            return f"PLAN{plan_num} - API CONNECTION ERROR: No internet or invalid key"
        elif "API RESPONSE ERROR" in error_msg:
            return f"PLAN{plan_num} - API RESPONSE ERROR: Invalid response format"
        elif "missing required prefix" in error_msg.lower():
            return f"PLAN{plan_num} - INVALID KEY: Wrong API key prefix"
        elif "key too short" in error_msg.lower():
            return f"PLAN{plan_num} - INVALID KEY: API key too short"
        else:
            # Generic error
            log_operation("ai_summary_failed", False, error=error_msg)
            return f"PLAN{plan_num} - ERROR: {error_msg[:50]}"

def needs_summary_update(plan_info: Dict, cached_summary: Optional[Dict]) -> bool:
    """Check if a plan needs its summary regenerated"""
    if not cached_summary:
        return True
    
    # Check if plan file was modified since last summary
    plan_path = Path(plan_info.get("file_path", ""))
    if plan_path.exists():
        file_modified = datetime.fromtimestamp(plan_path.stat().st_mtime, timezone.utc).isoformat()
        summary_generated = cached_summary.get("generated_at", "")
        
        if file_modified > summary_generated:
            return True
    
    # Check if registry info was modified since last summary
    plan_modified = plan_info.get("closed") or plan_info.get("created")
    summary_generated = cached_summary.get("generated_at", "")
    
    if plan_modified > summary_generated:
        return True
        
    # Check if status changed
    if plan_info.get("status") != cached_summary.get("status"):
        return True
        
    return False

def generate_summaries() -> Dict[str, Any]:
    """Main function to generate summaries for all plans"""
    registry = load_registry()
    cached_summaries = load_summaries()
    updated_summaries = {}
    
    log_operation("summary_generation_started", True, f"Processing {len(registry.get('plans', {}))} plans")
    
    for plan_num, plan_info in registry.get("plans", {}).items():
        try:
            # Check if summary needs update
            cached = cached_summaries.get(plan_num)
            if not needs_summary_update(plan_info, cached):
                log_operation("cache_hit", True, f"PLAN{plan_num}: Using cached summary")
                # Use cached summary but ensure file_path is current from registry
                if cached is None:
                    # Defensive: if cache unexpectedly missing, initialize minimal record
                    cached = {
                        "summary": "",
                        "status": plan_info.get("status", "unknown"),
                        "location": plan_info.get("relative_path", "unknown"),
                        "subject": plan_info.get("subject", ""),
                        "file_path": plan_info.get("file_path", ""),
                        "generated_at": datetime.now(timezone.utc).isoformat(),
                        "is_empty": False
                    }
                else:
                    cached['file_path'] = plan_info.get("file_path", "")
                updated_summaries[plan_num] = cached
                continue
            
            # Read plan file
            plan_path = Path(plan_info["file_path"])
            if not plan_path.exists():
                # File missing - likely moved to backup after memory bank processing
                # Remove from summaries cache so it doesn't show in CLAUDE outputs
                if plan_num in cached_summaries:
                    del cached_summaries[plan_num]
                    logger.info(f"[{MODULE_NAME}] Removed missing plan PLAN{plan_num} from summaries cache")
                log_operation("plan_file_missing", False, f"PLAN{plan_num}: File not found at {plan_path}, removed from cache")
                continue
            
            # Extract content
            content = extract_content_from_plan(plan_path)

            # Check if this is an empty template BEFORE calling AI (save API calls)
            # Use the same detection logic as flow_plan.py auto-delete
            template_indicators = [
                "[What do you want to achieve? Be specific about the end state.]",
                "[Break down into 3-5 concrete goals. What must be accomplished?]",
                "[How will you tackle this? Research first? Agents for broad analysis? Direct work?]",
                "[Document each significant action with outcome]",
                "[Working notes, discoveries, important context]",
                "[What defines complete for this specific PLAN?]"
            ]

            with open(plan_path, 'r', encoding='utf-8') as f:
                full_content = f.read()
            markers_found = sum(1 for indicator in template_indicators if indicator in full_content)
            is_empty_template = markers_found >= 4

            if is_empty_template:
                # Skip AI call for empty templates - use fixed summary
                summary = "Empty plan template - no content added"
                log_operation("empty_template_skipped", True, f"PLAN{plan_num}: Skipped AI call for empty template (saves API cost)")
            else:
                # Debug logging - show what content was extracted
                if "Empty plan template" in content:
                    log_operation("content_extraction", False, f"PLAN{plan_num}: Detected as empty template", error="No meaningful content found")
                else:
                    log_operation("content_extraction", True, f"PLAN{plan_num}: Found {len(content)} chars of content")

                # Generate summary with AI
                summary = generate_ai_summary(content, plan_num)
            
            # Check if summary generation failed and show specific error type
            if any(error in summary for error in ["ERROR:", "CONNECTION ERROR", "RESPONSE ERROR", "INVALID KEY", "API NOT AVAILABLE"]):
                # Don't cache failed summaries - let them retry next time
                log_operation("summary_failed", False, f"PLAN{plan_num}: {summary}", error=summary)
                
                # Show specific error type in console
                if "API NOT AVAILABLE" in summary:
                    print(f"[ERROR] PLAN{plan_num} failed to summarize - API NOT AVAILABLE (no api modules found)")
                elif "API CONNECTION ERROR" in summary:
                    if "No internet" in summary:
                        print(f"[ERROR] PLAN{plan_num} failed to summarize - No internet connection (will retry next run)")
                    else:
                        print(f"[ERROR] PLAN{plan_num} failed to summarize - API connection failed (will retry next run)")
                elif "INVALID KEY" in summary:
                    if "Wrong API key prefix" in summary:
                        print(f"[ERROR] PLAN{plan_num} failed to summarize - Invalid API key prefix (check .env file)")
                    elif "too short" in summary:
                        print(f"[ERROR] PLAN{plan_num} failed to summarize - API key too short (check .env file)")
                    else:
                        print(f"[ERROR] PLAN{plan_num} failed to summarize - Invalid API key (check .env file)")
                elif "API RESPONSE ERROR" in summary:
                    print(f"[ERROR] PLAN{plan_num} failed to summarize - Invalid API response (will retry next run)")
                else:
                    # Generic error
                    print(f"[ERROR] PLAN{plan_num} failed to summarize - {summary.split('ERROR:')[1].strip()[:50]} (will retry next run)")
                    
                continue  # Skip caching, will retry next time
            
            # Store successful summary with metadata
            updated_summaries[plan_num] = {
                "summary": summary,
                "status": plan_info.get("status", "unknown"),
                "location": plan_info.get("relative_path", "unknown"),
                "subject": plan_info.get("subject", ""),
                "file_path": plan_info.get("file_path", ""),
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "is_empty": "Empty plan" in summary or "Inactive" in summary
            }
            
            log_operation("summary_generated", True, f"PLAN{plan_num}: Generated new summary")
            
        except Exception as e:
            log_operation("plan_processing_failed", False, f"PLAN{plan_num}", error=str(e))
            continue
    
    # Save updated summaries
    save_summaries(updated_summaries)
    return updated_summaries

# =============================================
# MAIN FUNCTIONS
# =============================================

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Generate AI-powered summaries of PLAN files and update CLAUDE.json / CLAUDE.local.md',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
COMMANDS:
  Commands: generate, status

  generate - Generate summaries for all plans
  status   - Show summarization status and statistics

EXAMPLES:
  python3 flow_plan_summarizer.py generate
  python3 flow_plan_summarizer.py status
        """
    )

    parser.add_argument('command',
                       nargs='?',
                       choices=['generate', 'status'],
                       default='generate',
                       help='Command to execute')

    args = parser.parse_args()

    if args.command == 'generate':
        try:
            log_operation("summarization_started", True, "Plan summarization process initiated")
            
            # Load configuration
            config = load_module_config()
            if not config.get("config", {}).get("enabled", True):
                log_operation("summarization_disabled", True, "Module is disabled in configuration")
                print("❌ Flow plan summarizer is disabled")
                return 1
            
            # Generate summaries
            summaries = generate_summaries()

            # Always update centralized JSON and branch files, even with empty summaries
            write_plan_outputs(summaries)
            
            # Update runtime statistics
            data = load_module_data()
            data["runtime_state"]["last_summary_run"] = datetime.now().isoformat()
            data["statistics"]["successful_operations"] = data["statistics"].get("successful_operations", 0) + 1
            save_module_data(data)
            
            if summaries:
                log_operation("summarization_completed", True, f"{len(summaries)} plans processed successfully")
                print(f"[SUCCESS] Plan summarization complete: {len(summaries)} plans processed")
            else:
                log_operation("summarization_completed", True, "No plans found - plan outputs refreshed with empty state")
                print("[SUCCESS] No plans found - CLAUDE.json and branch files updated with empty state")
            
            return 0
            
        except Exception as e:
            log_operation("summarization_failed", False, error=str(e))
            print(f"[ERROR] Plan summarization failed: {str(e)}")
            
            # Update failure statistics
            try:
                data = load_module_data()
                data["statistics"]["failed_operations"] = data["statistics"].get("failed_operations", 0) + 1
                save_module_data(data)
            except:
                pass  # Don't fail on statistics update failure
            
            return 1
    
    elif args.command == 'status':
        try:
            data = load_module_data()
            config = load_module_config()
            
            print("\n" + "="*60)
            print(f"FLOW PLAN SUMMARIZER STATUS")
            print("="*60)
            print(f"Module Version: {MODULE_VERSION}")
            print(f"Enabled: {config.get('config', {}).get('enabled', True)}")
            print(f"Current Status: {data.get('runtime_state', {}).get('current_status', 'unknown')}")
            print(f"\nLast Summary Run: {data.get('runtime_state', {}).get('last_summary_run', 'Never')}")
            print(f"\nStatistics:")
            stats = data.get('statistics', {})
            print(f"  Total Summaries Generated: {stats.get('total_summaries_generated', 0)}")
            print(f"  Successful Operations: {stats.get('successful_operations', 0)}")
            print(f"  Failed Operations: {stats.get('failed_operations', 0)}")
            print(f"  Cache Hits: {stats.get('cache_hits', 0)}")
            print(f"  Cache Misses: {stats.get('cache_misses', 0)}")
            print("="*60 + "\n")
            
            return 0
            
        except Exception as e:
            print(f"[ERROR] Failed to retrieve status: {str(e)}")
            return 1

# =============================================
# CLI/EXECUTION
# =============================================

if __name__ == "__main__":
    sys.exit(main())
