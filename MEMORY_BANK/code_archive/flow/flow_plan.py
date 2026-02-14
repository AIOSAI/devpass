# =============================================
# META DATA HEADER
# Name: flow_plan.py
# Date: 2025-01-17
# Version: 1.0.0
# 
# CHANGELOG:
#   - v1.0.0 (2025-08-27): Cleaned module - removed orphaned CLAUDE.md event system
#   - v0.1.0 (2025-01-17): Initial Flow PLAN lifecycle management implementation
# =============================================

"""
Flow PLAN Management

Clean, focused PLAN lifecycle management for numbered PLAN system.
Handles creation, tracking, closing, and registry management.

Key Features:
- Numbered PLAN system (PLAN0001, PLAN0002, etc.)
- Template generation with proper structure (Objectives, Work Log, Notes, Completion)
- Registry-based state tracking (no filename changes on close)
- Drone command integration
- JSON persistence with 3-file system
- Auto-processing to memory bank via flow_mbank
"""

# Flow import pattern - system infrastructure like Prax
import sys
from pathlib import Path
AIPASS_ROOT = Path.home() / "aipass_core"
FLOW_ROOT = AIPASS_ROOT / "flow"
sys.path.append(str(AIPASS_ROOT))  # To ecosystem root

# Logger import
from prax.apps.modules.prax_logger import system_logger as logger

# Standard imports
import argparse
import json
import os
import subprocess
from datetime import datetime, timezone
from typing import Dict, List, Tuple, Optional, Any

# Flow module imports (absolute imports from flow.apps package)
# Note: Imported at top for clarity, used conditionally in functions
try:
    from flow.apps.archive_temp.flow_mbank import is_template_content, process_closed_plans
    FLOW_MBANK_AVAILABLE = True
except ImportError:
    FLOW_MBANK_AVAILABLE = False
    logger.warning("[FLOW_PLAN] flow_mbank not available - some features disabled")

# Template handler import
try:
    from flow.apps.archive_temp.flow_template_handler import get_template
    TEMPLATE_HANDLER_AVAILABLE = True
except ImportError:
    TEMPLATE_HANDLER_AVAILABLE = False
    logger.warning("[FLOW_PLAN] flow_template_handler not available - using fallback")

# =============================================
# CONFIGURATION SECTION
# =============================================

# Module identity
MODULE_NAME = "flow_plan"

# System paths
ECOSYSTEM_ROOT = AIPASS_ROOT  # C:\AIPass-Ecosystem
FLOW_JSON_DIR = FLOW_ROOT / "flow_json"

# Auto-create JSON directory
FLOW_JSON_DIR.mkdir(exist_ok=True)

# 3-file JSON structure
CONFIG_FILE = FLOW_JSON_DIR / "flow_plan_config.json"
DATA_FILE = FLOW_JSON_DIR / "flow_plan_data.json"
LOG_FILE = FLOW_JSON_DIR / "flow_plan_log.json"

# Central registry
REGISTRY_FILE = FLOW_JSON_DIR / "flow_registry.json"

# =============================================
# JSON FILE MANAGEMENT
# =============================================

def load_config() -> Dict[str, Any]:
    """Load flow_plan configuration"""
    default_config = {
        "enabled": True,
        "version": "0.1.0",
        "default_template": {
            "header_sections": ["Objectives", "Work Log", "Notes", "Completion"],
            "include_metadata_ref": True
        },
        "auto_number": True,
        "global_numbering": True
    }
    
    if not CONFIG_FILE.exists():
        save_config(default_config)
        return default_config
    
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"[FLOW_PLAN] Error loading config: {e}")
        return default_config

def save_config(config: Dict[str, Any]):
    """Save flow_plan configuration"""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[FLOW_PLAN] Error saving config: {e}")

def load_data() -> Dict[str, Any]:
    """Load flow_plan data"""
    if DATA_FILE.exists():
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"[FLOW_PLAN] Error loading data: {e}")
    
    default_data = {
        "created": datetime.now(timezone.utc).isoformat(),
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "plans_created": 0,
        "plans_closed": 0,
        "plans_processed": 0
    }
    return default_data

def save_data(data: Dict[str, Any]):
    """Save flow_plan data"""
    try:
        data["last_updated"] = datetime.now(timezone.utc).isoformat()
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[FLOW_PLAN] Error saving data: {e}")

def log_operation(operation: str, success: bool, details: str = "", error: str = ""):
    """Log flow_plan operations"""
    log_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "operation": operation,
        "success": success,
        "details": details,
        "error": error
    }
    
    logs = []
    if LOG_FILE.exists():
        try:
            with open(LOG_FILE, 'r', encoding='utf-8') as f:
                logs = json.load(f)
        except:
            logs = []
    
    logs.append(log_entry)
    
    # Keep last 1000 entries
    if len(logs) > 1000:
        logs = logs[-1000:]
    
    try:
        with open(LOG_FILE, 'w', encoding='utf-8') as f:
            json.dump(logs, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[FLOW_PLAN] Error saving log: {e}")

# =============================================
# REGISTRY MANAGEMENT
# =============================================

def normalize_registry_keys(registry: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
    """
    Validate and fix malformed registry keys.

    Registry keys should be 4-digit numbers ("0001", "0073") without "PLAN" prefix.
    This function detects and fixes wrong formats like "PLAN0073" → "0073".

    Returns:
        tuple: (fixed_registry, list_of_fixes)
    """
    plans = registry.get("plans", {})
    fixes = []

    for key in list(plans.keys()):
        # Check if key has wrong format (contains non-digits or PLAN prefix)
        if not key.isdigit() or (key.isdigit() and key.startswith("PLAN")):
            try:
                # Extract just the number
                num_str = key.replace("PLAN", "").lstrip("0") or "0"
                num = int(num_str)
                correct_key = f"{num:04d}"  # Format as "0073"

                if correct_key != key:
                    if correct_key in plans:
                        # Collision - both keys exist
                        logger.warning(f"[FLOW_PLAN] Registry key collision: '{key}' and '{correct_key}' both exist")
                        logger.warning(f"[FLOW_PLAN] Keeping existing '{correct_key}', deleting malformed '{key}'")
                        del plans[key]
                        fixes.append(f"Deleted duplicate '{key}' (kept '{correct_key}')")
                    else:
                        # Move to correct key
                        plans[correct_key] = plans[key]
                        del plans[key]
                        fixes.append(f"'{key}' → '{correct_key}'")
                        logger.warning(f"[FLOW_PLAN] Fixed malformed registry key: '{key}' → '{correct_key}'")
            except (ValueError, KeyError) as e:
                logger.error(f"[FLOW_PLAN] Failed to normalize registry key '{key}': {e}")
                fixes.append(f"ERROR: Failed to fix '{key}'")

    return registry, fixes

def load_registry() -> Dict[str, Any]:
    """Load the central flow registry with automatic key normalization"""
    if not REGISTRY_FILE.exists():
        default_registry = {
            "next_number": 1,
            "plans": {},
            "last_updated": datetime.now(timezone.utc).isoformat()
        }
        save_registry(default_registry)
        return default_registry

    try:
        with open(REGISTRY_FILE, 'r', encoding='utf-8') as f:
            registry = json.load(f)

        # Auto-heal: Normalize any malformed keys
        registry, fixes = normalize_registry_keys(registry)

        if fixes:
            # Report fixes to console and logs
            print(f"[FLOW_PLAN] Registry auto-heal: Fixed {len(fixes)} malformed key(s)")
            for fix in fixes:
                print(f"  • {fix}")
            logger.info(f"[FLOW_PLAN] Registry auto-heal completed: {fixes}")

            # Save corrected registry
            save_registry(registry)

        return registry
    except Exception as e:
        logger.error(f"[FLOW_PLAN] Error loading registry: {e}")
        return {"next_number": 1, "plans": {}}

def validate_registry_key(key: str) -> bool:
    """Validate that a registry key is in correct format: 4-digit zero-padded string

    Args:
        key: Registry key to validate

    Returns:
        True if valid (e.g., "0001", "0096"), False otherwise

    Examples:
        "0001" -> True (correct format)
        "0096" -> True (correct format)
        "96" -> False (not 4 digits)
        "PLAN0096" -> False (has prefix)
        "1" -> False (not zero-padded)
    """
    # Must be exactly 4 characters
    if len(key) != 4:
        return False

    # Must be all digits
    if not key.isdigit():
        return False

    # Passed all checks
    return True

def save_registry(registry: Dict[str, Any]):
    """Save the central flow registry with key validation

    VALIDATION: Rejects registry if any plan keys are malformed
    """
    try:
        # VALIDATION LAYER: Check all plan keys before saving
        invalid_keys = []
        for plan_key in registry.get("plans", {}).keys():
            if not validate_registry_key(plan_key):
                invalid_keys.append(plan_key)

        if invalid_keys:
            error_msg = f"Registry contains invalid key(s): {invalid_keys}. Keys must be 4-digit zero-padded strings (e.g., '0001', '0096')"
            logger.error(f"[FLOW_PLAN] VALIDATION FAILED: {error_msg}")
            raise ValueError(error_msg)

        # Validation passed - safe to save
        registry["last_updated"] = datetime.now(timezone.utc).isoformat()
        with open(REGISTRY_FILE, 'w', encoding='utf-8') as f:
            json.dump(registry, f, indent=2, ensure_ascii=False)

    except Exception as e:
        logger.error(f"[FLOW_PLAN] Error saving registry: {e}")
        raise  # Re-raise to prevent silent failures

# =============================================
# TEMPLATE GENERATION
# =============================================

def get_plan_template(number: int, location: str, subject: str = "") -> str:
    """Generate PLAN template content with proper structure and workflow guidance"""
    today = datetime.now().strftime('%Y-%m-%d')

    template = f"""# PLAN{number:04d} - {subject}

**Created**: {today}
**Location**: {location}
**Status**: Active
**Subject**: {subject}

---

## Planning Phase (Complete BEFORE Starting Work)

### Desired Result
[What do you want to achieve? Be specific about the end state.]

### Goals
[Break down into 3-5 concrete goals. What must be accomplished?]

### Approach & Strategy
[How will you tackle this? Research first? Agents for broad analysis? Direct work?]

**Agent Usage Decision:**
- [ ] **Use Agents** - For: Multi-file research, broad codebase analysis, pattern extraction, web research
  - *Why:* 200K tokens in 5 minutes vs 2 hours. Parallel work, clean context. Your time > token cost.
- [ ] **Direct Work** - For: Single file changes, quick tests, straightforward implementation

**If Using Agents - Preparation Steps:**
1. [ ] Gather YOUR context first (directory tree, file locations, understand scope)
2. [ ] Context refresh check: "Do I have enough information to instruct the agents?"
3. [ ] Prepare COMPLETE instructions (agents are stateless - only have your prompt)
4. [ ] Specify: WHERE to search, WHAT to find, WHAT to create, WHERE to save results
5. [ ] Remember: Agents have no prior context, no memory files, no conversation history
6. [ ] Your instructions determine success - be thorough and specific

**Check-In Points:**
- [ ] Check-in #1: After initial discovery/research (confirm direction)
- [ ] Check-in #2: Before finalizing solution (verify approach)

---

## Work Log

### {today}
- Started PLAN{number:04d}
- [Document each significant action with outcome]
- Use status symbols: check mark (success), X (failed), warning (partial)

**Pattern:** Make change → Test immediately → Document result → Next action

---

## Notes

[Working notes, discoveries, important context]

**Problem Solving:**
- When stuck: Focus on root cause, not workarounds
- Add logging to understand behavior
- Document WHY not just WHAT

---

## Completion

### Ready to Close
- [ ] All goals achieved
- [ ] Solution tested and validated
- [ ] Memory files updated (observations with patterns learned)
- [ ] Documentation created if needed

### Definition of Done
[What defines complete for this specific PLAN?]

---

## Quick Reference

**Workflow:** Build → Test → Iterate (no overthinking)
**Problem Solving:** Root cause > Workarounds, Investigate thoroughly
**Documentation:** Update memories in real-time, not at session end
**Standards:** `/home/aipass/Standards/STANDARDS.md` (for new modules/features and patterns)
"""
    return template

def is_empty_template(plan_file: Path) -> bool:
    """Check if plan file is an empty/unmodified template

    Returns True if the plan contains only template placeholders (no real work done)
    Strict check: must have clear signs of actual work beyond the default template lines
    """
    try:
        with open(plan_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # STRICT: Check for ANY of these signs of real work
        # If ANY are present, it's NOT empty

        # 1. Checked boxes [x] or [X]
        if '[x]' in content.lower():
            return False

        # 2. Status symbols used (✅ ❌ ⚠️) - but NOT the template instruction line
        if any(symbol in content for symbol in ['✅', '❌', '⚠️']):
            # Check if it's only in the template instruction line
            lines_with_symbols = [line for line in content.split('\n')
                                 if any(s in line for s in ['✅', '❌', '⚠️'])]
            # If there are status symbols in lines OTHER than the template instruction
            real_usage = [line for line in lines_with_symbols
                         if 'Use status symbols:' not in line]
            if real_usage:
                return False

        # 3. Template placeholders replaced
        # These are the key template markers - if ANY are missing, user modified the template
        required_markers = [
            "[What do you want to achieve? Be specific about the end state.]",
            "[Break down into 3-5 concrete goals. What must be accomplished?]",
            "[How will you tackle this? Research first? Agents for broad analysis? Direct work?]",
            "[Document each significant action with outcome]",
            "[Working notes, discoveries, important context]",
            "[What defines complete for this specific PLAN?]"
        ]

        markers_present = sum(1 for marker in required_markers if marker in content)

        # If 5 or more markers still present, it's essentially untouched
        if markers_present < 5:
            # User removed/replaced markers = real work
            return False

        # 4. Additional work log entries beyond the template "Started PLAN" line
        # Count bullet points that aren't the template default
        lines = content.split('\n')
        meaningful_bullets = 0
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('- ') and not any(x in stripped for x in [
                'Started PLAN',
                '[Document each',
                'Use status symbols',
                '**Pattern:**'
            ]):
                meaningful_bullets += 1

        if meaningful_bullets > 0:
            return False

        # If we got here, no signs of real work found
        return True

    except Exception as e:
        logger.error(f"[FLOW_PLAN] Error checking if plan is empty template: {e}")
        return False  # If we can't read it, don't delete it

# =============================================
# CORE PLAN FUNCTIONS
# =============================================

def create_plan(location: Optional[str] = None, subject: str = "", template_type: str = "default") -> tuple[bool, int, str, str, str]:
    """Create a new PLAN file with next number

    Args:
        location: Optional target directory for plan
        subject: Plan subject/title
        template_type: Template to use (default, master, api, etc.)

    Returns: (success, plan_number, location_description, template_type, error_message)
    """
    try:
        registry = load_registry()
        
        # AUTO-CLEANUP: Check for orphaned open PLANs before creating new one
        auto_closed_count = 0
        for num, info in registry["plans"].items():
            if info["status"] == "open":
                plan_file = Path(info.get("file_path", ""))
                if plan_file and not plan_file.exists():
                    # Auto-close missing plan
                    info["status"] = "closed"
                    info["closed"] = datetime.now(timezone.utc).isoformat()
                    info["closed_reason"] = "auto_closed_missing_file"
                    auto_closed_count += 1
                    logger.info(f"[FLOW_PLAN] Auto-closed PLAN{num} during create (file not found)")
        
        # Save registry if any plans were auto-closed
        if auto_closed_count > 0:
            save_registry(registry)
            data = load_data()
            data["plans_closed"] = data.get("plans_closed", 0) + auto_closed_count
            save_data(data)
            print(f"[AUTO-CLEANUP] Closed {auto_closed_count} orphaned plan(s)")
        
        next_num = registry["next_number"]
        
        # Determine location
        if location and location.startswith("@"):
            # Handle @folder syntax
            target_dir = ECOSYSTEM_ROOT / location[1:]
        elif location:
            target_dir = Path(location).resolve()
        else:
            target_dir = Path.cwd()
        
        # Ensure directory exists
        if not target_dir.exists():
            error_msg = f"Directory {target_dir} does not exist"
            logger.error(f"[FLOW_PLAN] {error_msg}")
            return False, 0, "", "", error_msg
        
        # Create PLAN file
        plan_file = target_dir / f"PLAN{next_num:04d}.md"
        
        if plan_file.exists():
            error_msg = f"PLAN{next_num:04d}.md already exists in {target_dir.name}/"
            logger.error(f"[FLOW_PLAN] {error_msg}")
            return False, 0, "", "", error_msg
        
        # Get relative location for template
        try:
            relative_location = str(target_dir.relative_to(ECOSYSTEM_ROOT))
            if relative_location == ".":
                relative_location = "root"
        except ValueError:
            relative_location = str(target_dir)
        
        # Generate template using template handler
        if TEMPLATE_HANDLER_AVAILABLE:
            content = get_template(template_type, number=next_num, location=relative_location, subject=subject)
        else:
            # Fallback to old hardcoded template (only supports default)
            logger.warning(f"[FLOW_PLAN] Template handler unavailable, using fallback (ignoring template_type '{template_type}')")
            content = get_plan_template(next_num, relative_location, subject)
        
        # Write PLAN file
        with open(plan_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Update registry
        registry["plans"][f"{next_num:04d}"] = {
            "location": str(target_dir),
            "relative_path": relative_location,
            "created": datetime.now(timezone.utc).isoformat(),
            "subject": subject,
            "status": "open",
            "file_path": str(plan_file)
        }
        registry["next_number"] = next_num + 1
        save_registry(registry)
        
        # Update data
        data = load_data()
        data["plans_created"] = data.get("plans_created", 0) + 1
        save_data(data)
        
        logger.info(f"[FLOW_PLAN] Created: {plan_file}")
        log_operation("create_plan", True, f"Created PLAN{next_num:04d} in {relative_location}")

        # Auto-trigger lightweight CLAUDE.md updater (instant, no AI)
        try:
            updater_path = FLOW_ROOT / "apps" / "flow_claude_updater.py"
            result = subprocess.run([sys.executable, str(updater_path), "update"], capture_output=True, text=True, timeout=10)

            if result.returncode == 0:
                logger.info(f"[FLOW_PLAN] Auto-updated CLAUDE.md after creating PLAN{next_num:04d}")
            else:
                logger.warning(f"[FLOW_PLAN] CLAUDE.md updater returned non-zero: {result.returncode}")
        except Exception as e:
            logger.warning(f"[FLOW_PLAN] Failed to auto-update CLAUDE.md: {e}")
            # Don't fail plan creation if updater fails - non-critical

        return True, next_num, relative_location, template_type, ""
        
    except Exception as e:
        error_msg = f"Error creating plan: {e}"
        logger.error(f"[FLOW_PLAN] {error_msg}")
        log_operation("create_plan", False, error=str(e))
        return False, 0, "", "", error_msg

def scan_and_fix_plan_locations(target_plan_num: Optional[str] = None) -> bool:
    """Scan filesystem for PLAN files and fix registry locations
    
    Args:
        target_plan_num: If provided, only fix this specific plan. Otherwise fix all mismatched plans.
    
    Returns:
        bool: True if any plans were fixed, False otherwise
    """
    try:
        registry = load_registry()
        fixed_count = 0
        
        # Search for all PLAN*.md files in the project
        ecosystem_root = Path(ECOSYSTEM_ROOT)
        plan_files = []
        
        # Find all PLAN files, excluding backup directories
        for plan_file in ecosystem_root.rglob("PLAN*.md"):
            # Skip backup directories
            if "backup_system" in plan_file.parts:
                continue
            if ".git" in plan_file.parts:
                continue
            if "__pycache__" in plan_file.parts:
                continue
            
            plan_files.append(plan_file)
        
        print(f"[FLOW_PLAN] Found {len(plan_files)} PLAN files in project")
        
        # Process each found file
        for plan_file in plan_files:
            # Extract plan number from filename
            filename = plan_file.name
            if not filename.startswith("PLAN") or not filename.endswith(".md"):
                continue
                
            try:
                # Extract number (e.g., "PLAN0002.md" -> "0002")
                plan_num = filename[4:8]  # PLAN0002.md -> 0002
                
                # If we're targeting a specific plan, skip others
                if target_plan_num and plan_num != target_plan_num:
                    continue
                
                # Check if this plan exists in registry
                if plan_num in registry["plans"]:
                    plan_info = registry["plans"][plan_num]
                    registered_path = Path(plan_info["file_path"])
                    
                    # If paths don't match, update registry
                    if registered_path.resolve() != plan_file.resolve():
                        print(f"[FLOW_PLAN] PLAN{plan_num}: {registered_path} -> {plan_file}")
                        
                        # Update registry with new location
                        plan_info["file_path"] = str(plan_file)
                        plan_info["location"] = str(plan_file.parent)
                        
                        # Update relative path
                        try:
                            relative_path = str(plan_file.parent.relative_to(ecosystem_root))
                            if relative_path == ".":
                                relative_path = "root"
                        except ValueError:
                            relative_path = str(plan_file.parent)
                        plan_info["relative_path"] = relative_path
                        
                        # Mark as resynced
                        plan_info["resynced"] = datetime.now(timezone.utc).isoformat()
                        
                        fixed_count += 1
                        log_operation("resync_plan", True, f"Fixed PLAN{plan_num} location: {relative_path}")
                        
                else:
                    # Plan file exists but not in registry - this could be a manually created plan
                    print(f"[FLOW_PLAN] Found unregistered PLAN file: {plan_file}")
                    print(f"[FLOW_PLAN] Manual registration not implemented yet - use 'drone create plan' instead")
                
            except (IndexError, ValueError) as e:
                print(f"[FLOW_PLAN] Skipping invalid filename: {filename} ({e})")
                continue
        
        # Save updated registry if any fixes were made
        if fixed_count > 0:
            save_registry(registry)
            print(f"[SUCCESS] [FLOW_PLAN] Fixed {fixed_count} plan location(s)")
            return True
        else:
            if target_plan_num:
                print(f"[FLOW_PLAN] PLAN{target_plan_num} not found in filesystem scan")
            else:
                print(f"[FLOW_PLAN] All plan locations are already correct")
            return False
            
    except Exception as e:
        logger.error(f"[FLOW_PLAN] Error during resync: {e}")
        log_operation("resync_plan", False, error=str(e))
        return False

def close_plan(plan_num: str, command: Optional[str] = None) -> bool:
    """Close a PLAN by marking it closed in registry (no file rename)"""
    try:
        # Handle both "28" and "0028" formats
        if plan_num.isdigit():
            plan_num = f"{int(plan_num):04d}"
        
        registry = load_registry()
        
        if plan_num not in registry["plans"]:
            logger.error(f"[FLOW_PLAN] PLAN{plan_num} not found in registry")
            print(f"[ERROR] PLAN{plan_num} does not exist - no plan with this number was ever created")
            return False
        
        plan_info = registry["plans"][plan_num]
        
        if plan_info["status"] == "closed":
            logger.warning(f"[FLOW_PLAN] PLAN{plan_num} is already closed")
            closed_date = plan_info.get("closed", "unknown date")
            reason = plan_info.get("closed_reason", "")
            if reason == "auto_closed_missing_file":
                print(f"[ERROR] PLAN{plan_num} is already closed (auto-closed on {closed_date} - file was manually deleted)")
            else:
                print(f"[ERROR] PLAN{plan_num} is already closed (closed on {closed_date})")
            return False
        
        # Verify file exists at registered location
        plan_file = Path(plan_info["file_path"])
        if not plan_file.exists():
            print(f"[WARNING] [FLOW_PLAN] PLAN{plan_num} missing from expected location: {plan_file}")
            print(f"[RESYNC] [FLOW_PLAN] Resyncing... scanning for moved/manually created plans")
            
            # Try to find and fix the plan location
            fixed = scan_and_fix_plan_locations(plan_num)
            if fixed:
                print(f"[SUCCESS] [FLOW_PLAN] Plan location updated! Continuing with close operation...")
                # Reload registry with updated location
                registry = load_registry()
                plan_info = registry["plans"][plan_num]
                plan_file = Path(plan_info["file_path"])
            else:
                # AUTO-CLOSE: File was manually deleted, mark as closed
                print(f"[AUTO-CLOSE] [FLOW_PLAN] PLAN{plan_num} not found - marking as closed (manually deleted)")
                plan_info["status"] = "closed"
                plan_info["closed"] = datetime.now(timezone.utc).isoformat()
                plan_info["closed_reason"] = "auto_closed_missing_file"
                save_registry(registry)
                
                # Update stats
                data = load_data()
                data["plans_closed"] = data.get("plans_closed", 0) + 1
                save_data(data)
                
                logger.info(f"[FLOW_PLAN] Auto-closed PLAN{plan_num} (file manually deleted)")
                log_operation("auto_close_plan", True, f"Auto-closed PLAN{plan_num} - file not found")
                print(f"[SUCCESS] [FLOW_PLAN] PLAN{plan_num} auto-closed (file was manually deleted)")
                
                # Auto-trigger plan summarizer to update CLAUDE.md
                try:
                    summarizer_path = FLOW_ROOT / "apps" / "flow_plan_summarizer.py"
                    result = subprocess.run([sys.executable, str(summarizer_path)], capture_output=True, text=True, timeout=60)
                    
                    # Show any errors from the summarizer
                    if result.stderr:
                        print(result.stderr.strip())
                    if result.stdout:
                        print(result.stdout.strip())
                    
                    logger.info(f"[FLOW_PLAN] Auto-triggered plan summarizer after auto-closing PLAN{plan_num}")
                    print(f"[SUCCESS] CLAUDE.md updated - removed auto-closed PLAN{plan_num}")
                except Exception as e:
                    logger.warning(f"[FLOW_PLAN] Failed to auto-trigger summarizer: {e}")
                    print(f"[WARNING] Could not auto-update CLAUDE.md: {e}")
                    print(f"         Run 'drone summarize' manually to update CLAUDE.md")
                
                return True
        
        # Mark as closed FIRST so process_closed_plans() can find it
        plan_info["status"] = "closed"
        plan_info["closed"] = datetime.now(timezone.utc).isoformat()
        save_registry(registry)

        # CHECK: Is this an empty template plan? Auto-delete if so
        # Use mbank's proven template detection (reusing working code)
        try:
            with open(plan_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Check if plan is empty template using mbank's detection
            if is_template_content(content):
                print(f"[FLOW_PLAN] PLAN{plan_num} is empty template - auto-deleting (no memory bank processing)")

                # Delete file
                plan_file.unlink()
                logger.info(f"[FLOW_PLAN] Deleted empty template PLAN{plan_num}")

                # Remove from registry
                del registry["plans"][plan_num]
                save_registry(registry)

                print(f"[SUCCESS] [FLOW_PLAN] Empty template deleted - PLAN{plan_num} removed from system")
                log_operation("delete_empty_template", True, f"PLAN{plan_num} was empty template, auto-deleted")
                return True
        except Exception as e:
            logger.error(f"[FLOW_PLAN] Failed to check/delete empty template PLAN{plan_num}: {e}")
            print(f"[WARNING] Could not check if template is empty: {e}")
            print(f"[FLOW_PLAN] Continuing with normal processing...")
            # Continue to normal processing if check fails

        # Auto-trigger plan summarizer BEFORE memory bank moves the file
        try:
            summarizer_path = FLOW_ROOT / "apps" / "flow_plan_summarizer.py"
            result = subprocess.run([sys.executable, str(summarizer_path)], capture_output=True, text=True, timeout=60)

            # Show any errors from the summarizer
            if result.stderr:
                print(result.stderr.strip())
            if result.stdout:
                print(result.stdout.strip())

            logger.info(f"[FLOW_PLAN] Auto-triggered plan summarizer for PLAN{plan_num}")
        except Exception as e:
            logger.warning(f"[FLOW_PLAN] Failed to auto-trigger summarizer: {e}")

        # Auto-trigger memory bank processing AFTER summarization
        memory_success = True
        try:
            print(f"[FLOW_PLAN] Auto-processing to memory bank...")
            results = process_closed_plans()
            
            # Check if THIS SPECIFIC PLAN failed (not just any plan in the batch)
            plan_failed = False
            plan_result = None
            for result in results.get("results", []):
                if result.get("plan") == f"PLAN{plan_num}":
                    plan_result = result
                    if result.get("status") == "error":
                        plan_failed = True
                    break
            
            # Handle new two-phase results with truthful status messages
            if plan_result and not plan_failed:
                # This plan was processed successfully (fully or partially)
                if plan_result.get("status") == "fully_processed":
                    print(f"[SUCCESS] [FLOW_PLAN] MEMORY BANK SUCCESS: PLAN{plan_num} fully processed")
                    print(f"   • Memory bank created and plan moved to backup folder")
                elif plan_result.get("status") == "memory_created_cleanup_failed":
                    print(f"[WARNING] [FLOW_PLAN] PARTIAL SUCCESS: PLAN{plan_num} memory created but cleanup failed")
                    print(f"   • Memory bank created successfully")
                    print(f"   • Plan file remains in root - cleanup failed")
                    cleanup_error = plan_result.get("error", "Unknown cleanup error")
                    print(f"   • Error: {cleanup_error}")
                    # Partial success is still considered success for closing
            elif plan_failed:
                # This specific plan failed - show error and revert
                error_msg = plan_result.get("error", "Unknown error") if plan_result else "Unknown error"
                print(f"[ERROR] [FLOW_PLAN] MEMORY PROCESSING FAILED for PLAN{plan_num}")
                print(f"   • {error_msg}")
                
                # Check if it's an API connection error - retry once for JSON initialization
                if "API CONNECTION ERROR" in error_msg or "API RESPONSE ERROR" in error_msg:
                    print(f"[FLOW_PLAN] API offline/JSON missing - waiting for API initialization...")
                    print(f"[FLOW_PLAN] Retrying memory processing in 3 seconds...")
                    
                    import time
                    time.sleep(3)
                    
                    # Single retry attempt
                    try:
                        retry_results = process_closed_plans()
                        retry_plan_result = None
                        for result in retry_results.get("results", []):
                            if result.get("plan") == f"PLAN{plan_num}":
                                retry_plan_result = result
                                break
                        
                        if retry_plan_result and retry_plan_result.get("status") != "error":
                            if retry_plan_result.get("status") == "fully_processed":
                                print(f"[SUCCESS] [FLOW_PLAN] RETRY SUCCESS: PLAN{plan_num} fully processed")
                                print(f"   • Memory bank created and plan moved to backup folder")
                            elif retry_plan_result.get("status") == "memory_created_cleanup_failed":
                                print(f"[WARNING] [FLOW_PLAN] RETRY PARTIAL SUCCESS: PLAN{plan_num} memory created but cleanup failed")
                                print(f"   • Memory bank created successfully")
                            memory_success = True
                        else:
                            print(f"[FLOW_PLAN] Retry failed - API still unavailable, plan reverted to OPEN")
                            memory_success = False
                    except Exception as retry_e:
                        print(f"[FLOW_PLAN] Retry failed - {str(retry_e)}, plan reverted to OPEN")
                        memory_success = False
                else:
                    print(f"[FLOW_PLAN] Plan reverted to OPEN - run 'drone mbank' to retry processing")
                    memory_success = False
            elif not plan_result:
                # Plan wasn't in the results (might already be processed or other issue)
                print(f"[FLOW_PLAN] PLAN{plan_num} not found in processing results")
                print(f"[FLOW_PLAN] Plan might already be processed or there was an error")
                
        except Exception as e:
            logger.warning(f"[FLOW_PLAN] Auto-processing failed: {e}")
            print(f"[ERROR] [FLOW_PLAN] MEMORY PROCESSING FAILED: {e}")
            print(f"[FLOW_PLAN] Plan stays OPEN - run 'drone mbank' manually to process to memory bank")
            memory_success = False
        
        # Update stats and logs (plan is already marked as closed above)
        if memory_success:
            # Update data
            data = load_data()
            data["plans_closed"] = data.get("plans_closed", 0) + 1
            save_data(data)

            logger.info(f"[FLOW_PLAN] Closed: PLAN{plan_num} (marked in registry)")
            # Include command in log details for debugging
            details = f"Closed PLAN{plan_num}"
            if command:
                details += f" (command: {command})"
            log_operation("close_plan", True, details)
        else:
            # Memory processing failed - revert plan status back to open
            plan_info["status"] = "open"
            plan_info.pop("closed", None)  # Remove closed timestamp
            save_registry(registry)
            
            logger.warning(f"[FLOW_PLAN] PLAN{plan_num} reverted to open due to processing failure")
            log_operation("close_plan", False, error="Memory processing failed")
        
        return memory_success

    except Exception as e:
        logger.error(f"[FLOW_PLAN] Error closing plan: {e}")
        log_operation("close_plan", False, error=str(e))
        return False

def close_all_plans() -> Tuple[int, int]:
    """Close all open plans in one operation

    Returns:
        Tuple[int, int]: (success_count, failure_count)
    """
    try:
        registry = load_registry()

        # Get all open plans
        open_plans = [
            (plan_num, plan_info)
            for plan_num, plan_info in registry["plans"].items()
            if plan_info["status"] == "open"
        ]

        if not open_plans:
            print("[FLOW_PLAN] No open plans to close")
            return 0, 0

        # Show what will be closed
        print(f"[FLOW_PLAN] Found {len(open_plans)} open plan(s) to close:")
        for plan_num, plan_info in open_plans:
            subject = plan_info.get("subject", "No subject")
            print(f"  • PLAN{plan_num}: {subject}")

        print(f"\n[FLOW_PLAN] Closing all {len(open_plans)} plan(s)...")
        print("-" * 60)

        # Close each plan
        success_count = 0
        failure_count = 0

        for plan_num, plan_info in open_plans:
            print(f"\n[FLOW_PLAN] Closing PLAN{plan_num}...")
            success = close_plan(plan_num, "close_all")

            if success:
                success_count += 1
            else:
                failure_count += 1

        # Summary
        print("\n" + "=" * 60)
        print(f"[FLOW_PLAN] CLOSE ALL COMPLETE")
        print(f"  • Successfully closed: {success_count}")
        print(f"  • Failed to close: {failure_count}")
        print(f"  • Total processed: {len(open_plans)}")
        print("=" * 60)

        log_operation("close_all_plans", True, f"Closed {success_count}/{len(open_plans)} plans")
        return success_count, failure_count

    except Exception as e:
        logger.error(f"[FLOW_PLAN] Error in close_all: {e}")
        log_operation("close_all_plans", False, error=str(e))
        return 0, 0

def restore_plan(plan_num: str) -> bool:
    """Restore a closed PLAN back to open status (reverse close operation)"""
    try:
        # Handle both "28" and "0028" formats
        if plan_num.isdigit():
            plan_num = f"{int(plan_num):04d}"

        registry = load_registry()

        if plan_num not in registry["plans"]:
            logger.error(f"[FLOW_PLAN] PLAN{plan_num} not found in registry")
            print(f"[ERROR] PLAN{plan_num} does not exist - no plan with this number was ever created")
            return False

        plan_info = registry["plans"][plan_num]

        # Check if plan is already open
        if plan_info["status"] == "open":
            logger.warning(f"[FLOW_PLAN] PLAN{plan_num} is already open")
            print(f"[ERROR] PLAN{plan_num} is already open - nothing to restore")
            return False

        # Verify file exists at registered location
        plan_file = Path(plan_info["file_path"])
        if not plan_file.exists():
            print(f"[ERROR] PLAN{plan_num} file not found at: {plan_file}")
            print(f"        Cannot restore - file must exist to reopen plan")
            return False

        # Restore plan to open status
        plan_info["status"] = "open"

        # Remove close metadata
        closed_date = plan_info.pop("closed", None)
        closed_reason = plan_info.pop("closed_reason", None)
        plan_info.pop("memory_created", None)

        save_registry(registry)

        # Update stats
        data = load_data()
        data["plans_closed"] = max(0, data.get("plans_closed", 0) - 1)
        save_data(data)

        logger.info(f"[FLOW_PLAN] Restored PLAN{plan_num} to open status")
        log_operation("restore_plan", True, f"Restored PLAN{plan_num} (was closed: {closed_date})")

        print(f"[SUCCESS] PLAN{plan_num} restored to open status")
        if closed_date:
            print(f"          (was closed: {closed_date})")
        if closed_reason:
            print(f"          (reason: {closed_reason})")

        # Auto-trigger plan summarizer to update CLAUDE.md
        try:
            summarizer_path = FLOW_ROOT / "apps" / "flow_plan_summarizer.py"
            result = subprocess.run([sys.executable, str(summarizer_path)], capture_output=True, text=True, timeout=60)

            if result.returncode == 0:
                logger.info(f"[FLOW_PLAN] Auto-updated CLAUDE.md after restoring PLAN{plan_num}")
                print(f"[SUCCESS] CLAUDE.md updated - PLAN{plan_num} now shows as active")
            else:
                logger.warning(f"[FLOW_PLAN] Summarizer returned non-zero exit code: {result.returncode}")
        except Exception as e:
            logger.warning(f"[FLOW_PLAN] Failed to auto-trigger summarizer: {e}")
            print(f"[WARNING] Could not auto-update CLAUDE.md: {e}")
            print(f"         Run 'drone summarize' manually to update CLAUDE.md")

        return True

    except Exception as e:
        logger.error(f"[FLOW_PLAN] Error restoring plan: {e}")
        log_operation("restore_plan", False, error=str(e))
        print(f"[ERROR] Failed to restore PLAN{plan_num}: {e}")
        return False

def show_plans(status_filter: str = "open") -> List[Dict[str, Any]]:
    """Show open or closed plans"""
    try:
        registry = load_registry()
        plans = []
        auto_closed_count = 0
        
        for num, info in registry["plans"].items():
            # Auto-close orphaned open plans
            if info["status"] == "open":
                plan_file = Path(info.get("file_path", ""))
                if plan_file and not plan_file.exists():
                    # Auto-close missing plan
                    info["status"] = "closed"
                    info["closed"] = datetime.now(timezone.utc).isoformat()
                    info["closed_reason"] = "auto_closed_missing_file"
                    auto_closed_count += 1
                    logger.info(f"[FLOW_PLAN] Auto-closed PLAN{num} during listing (file not found)")
            
            if info["status"] == status_filter:
                plans.append({
                    "number": num,
                    "subject": info.get("subject", ""),
                    "location": info.get("relative_path", ""),
                    "created": info.get("created", ""),
                    "closed": info.get("closed", "") if status_filter == "closed" else "",
                    "file_path": info.get("file_path", ""),
                    "closed_reason": info.get("closed_reason", "") if status_filter == "closed" else ""
                })
        
        # Save registry if any plans were auto-closed
        if auto_closed_count > 0:
            save_registry(registry)
            data = load_data()
            data["plans_closed"] = data.get("plans_closed", 0) + auto_closed_count
            save_data(data)
            print(f"[AUTO-CLOSE] Automatically closed {auto_closed_count} orphaned plan(s)")

            # Auto-trigger plan summarizer to update CLAUDE.md after auto-closing
            try:
                summarizer_path = FLOW_ROOT / "apps" / "flow_plan_summarizer.py"
                result = subprocess.run([sys.executable, str(summarizer_path)], capture_output=True, text=True, timeout=60)
                if result.returncode == 0:
                    print(f"[SUCCESS] CLAUDE.md updated - removed auto-closed plan(s)")
                logger.info(f"[FLOW_PLAN] Auto-triggered plan summarizer after auto-closing {auto_closed_count} plan(s)")
            except Exception as e:
                logger.warning(f"[FLOW_PLAN] Failed to auto-trigger summarizer: {e}")
                print(f"[WARNING] Could not auto-update CLAUDE.md: {e}")
                print(f"         Run 'drone summarize' manually to update CLAUDE.md")
        
        log_operation("show_plans", True, f"Retrieved {len(plans)} {status_filter} plans")
        return plans
        
    except Exception as e:
        logger.error(f"[FLOW_PLAN] Error showing plans: {e}")
        log_operation("show_plans", False, error=str(e))
        return []

def get_status() -> Dict[str, Any]:
    """Get PLAN system statistics"""
    try:
        registry = load_registry()
        data = load_data()
        
        open_count = sum(1 for p in registry["plans"].values() if p["status"] == "open")
        closed_count = sum(1 for p in registry["plans"].values() if p["status"] == "closed")
        
        # Count by location
        locations = {}
        for info in registry["plans"].values():
            loc = info.get("relative_path", "unknown")
            locations[loc] = locations.get(loc, 0) + 1
        
        status = {
            "next_number": registry.get("next_number", 1),
            "open_plans": open_count,
            "closed_plans": closed_count,
            "total_plans": len(registry["plans"]),
            "locations": locations,
            "data": data
        }
        
        log_operation("get_status", True, f"Status retrieved: {open_count} open, {closed_count} closed")
        return status
        
    except Exception as e:
        logger.error(f"[FLOW_PLAN] Error getting status: {e}")
        log_operation("get_status", False, error=str(e))
        return {}

# =============================================
# INITIALIZATION
# =============================================

def initialize_flow_plan():
    """Initialize flow_plan module"""
    logger.info(f"[FLOW_PLAN] Initializing Flow PLAN management v0.1.0")
    try:
        # Load configuration
        config = load_config()
        logger.info(f"[FLOW_PLAN] Configuration loaded")
        
        # Initialize data
        data = load_data()
        logger.info(f"[FLOW_PLAN] Data loaded")
        
        # Initialize registry
        registry = load_registry()
        logger.info(f"[FLOW_PLAN] Registry loaded: next number {registry.get('next_number', 1)}")
        
        logger.info(f"[FLOW_PLAN] Flow PLAN initialization completed successfully")
        log_operation("initialize", True, "Flow PLAN module initialized")
        return True
    except Exception as e:
        logger.error(f"[FLOW_PLAN] Initialization failed: {e}")
        log_operation("initialize", False, error=str(e))
        return False

# Initialize on import
initialize_flow_plan()
def main():
    """Main entry point for command-line usage"""
    parser = argparse.ArgumentParser(
        description='Flow PLAN Management - Numbered PLAN system with lifecycle tracking',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
COMMANDS:
  Commands: create, close, close_all, restore, show, status

  create     - Create new numbered PLAN (PLAN0001, PLAN0002, etc.)
  close      - Close an existing PLAN and mark for memory bank processing
  close_all  - Close ALL open plans in one sweep
  restore    - Restore a closed PLAN back to open status
  show       - Display open or closed PLANs
  status     - Show PLAN system status and statistics

EXAMPLES:
  python3 flow_plan.py create
  python3 flow_plan.py create /path/to/location "Task Subject"
  python3 flow_plan.py close 0001
  python3 flow_plan.py close_all
  python3 flow_plan.py restore 0001
  python3 flow_plan.py show open
  python3 flow_plan.py show closed
  python3 flow_plan.py status
        """
    )

    parser.add_argument('command',
                       nargs='?',
                       choices=['create', 'close', 'close_all', 'restore', 'show', 'status'],
                       help='Command to execute')

    parser.add_argument('args', nargs='*', help='Additional arguments for the command')

    args = parser.parse_args()

    # If no command, show status (default behavior)
    if not args.command:
        print(f"[FLOW_PLAN] Running in test mode")
        status = get_status()
        print(f"Status: {json.dumps(status, indent=2)}")
        return 0

    command = args.command.lower()

    if command == "create":
        # Handle create command
        location = args.args[0] if len(args.args) > 0 else None
        subject = args.args[1] if len(args.args) > 1 else "New Development Task"
        template_type = args.args[2] if len(args.args) > 2 else "default"

        display_location = location if location else "current directory"
        print(f"[FLOW_PLAN] Creating PLAN in {display_location}")
        success, plan_num, actual_location, used_template, error_msg = create_plan(location, subject, template_type)

        if success:
            # Map template names to display names
            template_display = {
                "default": "Standard Plan",
                "master": "Master Plan"
            }.get(used_template, used_template.title())

            print(f"[FLOW_PLAN] Created PLAN{plan_num:04d}")
            print(f"[FLOW_PLAN] Type: {template_display}")
            print(f"[FLOW_PLAN] Location: {actual_location}")
            print(f"[FLOW_PLAN] Subject: {subject}")
            print(f"[FLOW_PLAN] File: {actual_location}/PLAN{plan_num:04d}.md")
        else:
            print(f"[FLOW_PLAN] Failed to create PLAN: {error_msg}")

        return 0 if success else 1

    elif command == "close":
        # Handle close command
        if len(args.args) < 1:
            print("Error: close requires PLAN number")
            return 1

        plan_num = args.args[0]
        # Capture original command for logging
        original_command = f"python3 flow_plan.py close {plan_num}"
        success = close_plan(plan_num, original_command)

        if success:
            print(f"[FLOW_PLAN] PLAN{plan_num} closed successfully")
        else:
            print(f"[FLOW_PLAN] Failed to close PLAN{plan_num}")

        return 0 if success else 1

    elif command == "close_all":
        # Handle close_all command
        success_count, failure_count = close_all_plans()

        # Return 0 if all succeeded, 1 if any failed
        return 0 if failure_count == 0 else 1

    elif command == "restore":
        # Handle restore command
        if len(args.args) < 1:
            print("Error: restore requires PLAN number")
            return 1

        plan_num = args.args[0]
        success = restore_plan(plan_num)

        if success:
            print(f"[FLOW_PLAN] PLAN{plan_num} restored successfully")
        else:
            print(f"[FLOW_PLAN] Failed to restore PLAN{plan_num}")

        return 0 if success else 1

    elif command == "show":
        # Handle show command
        if len(args.args) < 1:
            print("Error: show requires 'open' or 'closed'")
            return 1

        status_filter = args.args[0].lower()
        if status_filter not in ["open", "closed"]:
            print("Error: show requires 'open' or 'closed'")
            return 1

        plans = show_plans(status_filter)

        print(f"\n{status_filter.upper()} PLANS:")
        print("-" * 60)

        for plan in plans:
            print(f"PLAN{plan['number']}: {plan['subject']}")
            print(f"  Location: {plan['location']}")
            print(f"  File: {plan['file_path']}")
            print(f"  Created: {plan['created']}")
            if status_filter == "closed" and plan['closed']:
                print(f"  Closed: {plan['closed']}")
            print()

        return 0

    elif command == "status":
        # Handle status command
        status = get_status()

        print("\nPLAN SYSTEM STATUS")
        print("-" * 40)
        print(f"Next number: PLAN{status['next_number']:04d}")
        print(f"Open plans: {status['open_plans']}")
        print(f"Closed plans: {status['closed_plans']}")
        print(f"Total plans: {status['total_plans']}")

        # Show actual open plans
        if status['open_plans'] > 0:
            open_plans = show_plans("open")
            print("\nOpen Plans:")
            for plan in open_plans:
                print(f"  PLAN{plan['number']}: {plan['subject']}")
                print(f"    Location: {plan['location']}")
                print(f"    File: {plan['file_path']}")
                print(f"    Created: {plan['created']}")

        # Show actual closed plans
        if status['closed_plans'] > 0:
            closed_plans = show_plans("closed")
            print("\nClosed Plans:")
            for plan in closed_plans:
                print(f"  PLAN{plan['number']}: {plan['subject']}")
                print(f"    Location: {plan['location']}")
                print(f"    File: {plan['file_path']}")
                print(f"    Created: {plan['created']}")
                if plan['closed']:
                    print(f"    Closed: {plan['closed']}")

        if status['locations']:
            print("\nPlans by location:")
            for loc, count in sorted(status['locations'].items()):
                print(f"  {loc}: {count}")

        # Auto-trigger plan summarizer to ensure CLAUDE.md is current
        try:
            summarizer_path = FLOW_ROOT / "apps" / "flow_plan_summarizer.py"
            result = subprocess.run([sys.executable, str(summarizer_path)], capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                logger.info(f"[FLOW_PLAN] Auto-updated CLAUDE.md after status command")
            else:
                logger.warning(f"[FLOW_PLAN] Summarizer returned non-zero exit code: {result.returncode}")
        except Exception as e:
            logger.warning(f"[FLOW_PLAN] Failed to auto-trigger summarizer: {e}")
            # Don't print warning to user - status command should be silent about CLAUDE.md updates

        return 0

    return 0
if __name__ == "__main__":
    sys.exit(main())