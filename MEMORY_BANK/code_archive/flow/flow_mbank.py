# =============================================
# META DATA HEADER
# Name: flow_mbank.py
# Date: 2025-01-17
# Version: 1.0.0
# 
# CHANGELOG:
#   - v1.0.0 (2025-01-17): Full feature parity with prax_mbank
#   - v0.1.0 (2025-01-17): Migrated from prax_mbank with flow_registry integration
# =============================================

"""
Flow Memory Bank Processor

Automated conversion of closed PLAN files to TRL-compliant memory_bank entries.
Migrated from prax_mbank with registry-based detection instead of filename patterns.

Key Changes from prax_mbank:
- Reads flow_registry.json for closed PLANs (instead of PLAN_*_closed.md filename)
- Uses Flow import pattern (no registry check)
- Same functionality: process → memory → archive

Features:
- Registry-based closed PLAN detection
- OpenRouter-based content analysis for intelligent tagging
- PATH-TYPE-CATEGORY-ACTION-YYYYMMDD.md format
- Memory bank creation from processed plans
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
import re
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Any

# Import new unified API system
from api.apps.openrouter import get_response

# =============================================
# CONFIGURATION SECTION
# =============================================

# Module identity
MODULE_NAME = "flow_mbank"

# System paths
ECOSYSTEM_ROOT = AIPASS_ROOT  # /home/aipass/aipass_core
FLOW_JSON_DIR = FLOW_ROOT / "flow_json"
MEMORY_BANK_PATH = ECOSYSTEM_ROOT / "MEMORY_BANK"  # ALL CAPS - AI memory convention
# PROCESSED_PLANS_PATH removed - no longer archiving plans

# Auto-create directories
FLOW_JSON_DIR.mkdir(exist_ok=True)
MEMORY_BANK_PATH.mkdir(exist_ok=True)

# 3-file JSON structure
CONFIG_FILE = FLOW_JSON_DIR / "flow_mbank_config.json"
DATA_FILE = FLOW_JSON_DIR / "flow_mbank_data.json"
LOG_FILE = FLOW_JSON_DIR / "flow_mbank_log.json"

# Flow registry
REGISTRY_FILE = FLOW_JSON_DIR / "flow_registry.json"

# =============================================
# JSON FILE MANAGEMENT
# =============================================

def load_config() -> Dict[str, Any]:
    """Load flow_mbank configuration"""
    default_config = {
        "enabled": True,
        "version": "1.0.0",
        "archive_processed": False,
        "trl_mapping": {
            "types": {
                "SEED": "Seed AI System",
                "NEXUS": "Nexus AI System", 
                "SKILL": "Skills Modules",
                "PRAX": "Prax Infrastructure",
                "FLOW": "Flow Workflow System",
                "BACKUP": "Backup System",
                "DRONE": "Drone Commands",
                "HELP": "Help System",
                "MCP": "MCP Servers",
                "TOOLS": "Tools & Scripts",
            },
            "categories": {
                "API": "API & External Services",
                "MEM": "Memory & Storage",
                "DB": "Database & Data",
                "UI": "User Interface",
                "CFG": "Configuration",
                "DOC": "Documentation",
                "TEST": "Testing & QA",
                "SEC": "Security",
                "NET": "Networking",
                "FILE": "File Operations",
                "LOG": "Logging & Monitoring",
                "DEV": "Development"
            },
            "actions": {
                "IMP": "Implementation",
                "FIX": "Bug Fixes",
                "UPD": "Updates & Improvements",
                "NEW": "New Features",
                "REF": "Refactoring",
                "DOC": "Documentation",
                "TEST": "Testing",
                "CFG": "Configuration",
                "MIGR": "Migration",
                "OPT": "Optimization"
            }
        },
        "excluded_paths": [
            "admin", "archive", "backups", "tests", "trash", "__pycache__",
            ".git", ".venv", "venv", "node_modules", "mcp_servers"
        ]
    }
    
    if not CONFIG_FILE.exists():
        save_config(default_config)
        return default_config
    
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"[FLOW_MBANK] Error loading config: {e}")
        return default_config

def save_config(config: Dict[str, Any]):
    """Save flow_mbank configuration"""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[FLOW_MBANK] Error saving config: {e}")

def load_data() -> Dict[str, Any]:
    """Load flow_mbank data"""
    if DATA_FILE.exists():
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"[FLOW_MBANK] Error loading data: {e}")
    
    default_data = {
        "created": datetime.now(timezone.utc).isoformat(),
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "plans_processed": 0,
        "memory_entries_created": 0,
        "last_run": None
    }
    return default_data

def save_data(data: Dict[str, Any]):
    """Save flow_mbank data"""
    try:
        data["last_updated"] = datetime.now(timezone.utc).isoformat()
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[FLOW_MBANK] Error saving data: {e}")

def log_operation(operation: str, details: Dict[str, Any], success: bool = True, correlation_id: str | None = None):
    """Log flow_mbank operations with sequential ID, enhanced error details, and correlation tracking"""
    logs = []
    if LOG_FILE.exists():
        try:
            with open(LOG_FILE, 'r', encoding='utf-8') as f:
                logs = json.load(f)
        except:
            logs = []
    
    # Generate sequential ID
    next_id = 1
    if logs:
        # Find highest existing ID
        max_id = max([log.get("id", 0) for log in logs])
        next_id = max_id + 1
    
    log_entry = {
        "id": next_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "operation": operation,
        "success": success,
        "details": details
    }
    
    # Add correlation ID if provided
    if correlation_id:
        log_entry["correlation_id"] = correlation_id
    
    # Insert new entry at the top (newest first)
    logs.insert(0, log_entry)
    
    # Keep last 100 entries (remove from bottom)
    if len(logs) > 100:
        logs = logs[:100]

    try:
        with open(LOG_FILE, 'w', encoding='utf-8') as f:
            json.dump(logs, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[FLOW_MBANK] Error saving log: {e}")

def get_ai_model():
    """Get AI model from openrouter's API config"""
    try:
        # Ensure JSON directory exists
        FLOW_JSON_DIR.mkdir(parents=True, exist_ok=True)
        
        # Check if openrouter API config exists in our JSON folder
        api_config_file = FLOW_JSON_DIR / "openrouter_skill_config.json"
        
        if api_config_file.exists():
            with open(api_config_file, 'r', encoding='utf-8') as f:
                api_config = json.load(f)
                ai_model = api_config.get("config", {}).get("ai_model")
                
                if ai_model:
                    logger.info(f"[FLOW_MBANK] Loaded AI model from API config: {ai_model}")
                    return ai_model
                else:
                    logger.warning(f"[FLOW_MBANK] No ai_model found in API config")
                    return None
        else:
            logger.info(f"[FLOW_MBANK] No API config found - openrouter will create on first call")
            return None
            
    except Exception as e:
        logger.error(f"[FLOW_MBANK] Error loading AI model from API config: {e}")
        return None

# =============================================
# REGISTRY INTEGRATION
# =============================================

def load_flow_registry() -> Dict[str, Any]:
    """Load the flow registry"""
    if not REGISTRY_FILE.exists():
        logger.warning(f"[FLOW_MBANK] Flow registry not found at {REGISTRY_FILE}")
        return {"plans": {}}
    
    try:
        with open(REGISTRY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"[FLOW_MBANK] Error loading flow registry: {e}")
        return {"plans": {}}

def save_flow_registry(registry: Dict[str, Any]):
    """Save the flow registry"""
    try:
        registry["last_updated"] = datetime.now(timezone.utc).isoformat()
        with open(REGISTRY_FILE, 'w', encoding='utf-8') as f:
            json.dump(registry, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[FLOW_MBANK] Error saving flow registry: {e}")

def get_closed_plans() -> List[Dict[str, Any]]:
    """Get closed PLANs from flow registry (instead of filename scanning)

    AUTO-HEAL: Before getting closed plans, verify and heal any orphaned plans
    """
    # AUTO-HEAL LAYER: Fix orphaned plans before processing new ones
    heal_result = verify_and_heal_orphaned_plans()
    if heal_result["orphans_found"] > 0:
        logger.info(f"[FLOW_MBANK] Auto-heal found {heal_result['orphans_found']} orphan(s), healed {heal_result['successfully_healed']}")

    registry = load_flow_registry()
    closed_plans = []

    try:
        for plan_num, plan_info in registry.get("plans", {}).items():
            if plan_info.get("status") == "closed" and plan_info.get("processed") != True:
                file_path = Path(plan_info.get("file_path", ""))
                if file_path.exists():
                    closed_plans.append({
                        "number": plan_num,
                        "path": file_path,
                        "info": plan_info
                    })
                    logger.info(f"[FLOW_MBANK] Found closed plan: PLAN{plan_num}")
        
        log_operation("get_closed_plans", {"found": len(closed_plans), "plans": [p["number"] for p in closed_plans]})
        return closed_plans
        
    except Exception as e:
        logger.error(f"[FLOW_MBANK] Error getting closed plans: {e}")
        log_operation("get_closed_plans", {"error": str(e)}, success=False)
        return []

# =============================================
# CONTENT ANALYSIS
# =============================================

def analyze_plan_content(plan_path: Path) -> Dict[str, str]:
    """Use OpenRouter to analyze plan content and determine TRL tags"""
    config = load_config()
    
    try:
        # Read plan content
        with open(plan_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Prepare analysis prompt
        # Handle plans outside ECOSYSTEM_ROOT (e.g., root level plans)
        try:
            relative_path = str(plan_path.relative_to(ECOSYSTEM_ROOT))
            folder_context = str(plan_path.parent.relative_to(ECOSYSTEM_ROOT))
        except ValueError:
            # Plan is outside ECOSYSTEM_ROOT, use full paths
            relative_path = str(plan_path)
            folder_context = str(plan_path.parent)
        
        # Generate dynamic prompt from TRL mapping configuration
        trl_mapping = config["trl_mapping"]
        
        types_desc = "\\n".join([f"{k}: {v}" for k, v in trl_mapping["types"].items()])
        categories_desc = "\\n".join([f"{k}: {v}" for k, v in trl_mapping["categories"].items()])
        actions_desc = "\\n".join([f"{k}: {v}" for k, v in trl_mapping["actions"].items()])
        
        type_codes = "|".join(trl_mapping["types"].keys())
        category_codes = "|".join(trl_mapping["categories"].keys())
        action_codes = "|".join(trl_mapping["actions"].keys())
        
        prompt = f"""Analyze this completed plan file:

Content: {content}
Folder: {folder_context}  
File: {plan_path.name}

Determine the primary classification using these options:

TYPE options:
{types_desc}

CATEGORY options:
{categories_desc}

ACTION options:
{actions_desc}

Return ONLY a JSON object:
{{
  "type": "{type_codes}",
  "category": "{category_codes}", 
  "action": "{action_codes}",
  "summary": "brief description"
}}"""

        messages = [
            {"role": "system", "content": "You are a technical project analyzer. Return only valid JSON."},
            {"role": "user", "content": prompt}
        ]
        
        # Get AI model from openrouter's API config
        ai_model = get_ai_model()
        
        # Call new unified API system with caller tracking and model
        response = get_response(messages=messages, model=ai_model, caller="flow_mbank")
        
        # Note: Usage tracking now handled automatically by the API system
        # Real token counts and costs will be tracked via OpenRouter's generation endpoint
        # No need for manual token calculation or usage monitoring
        
        if response:
            try:
                # Extract JSON from markdown code blocks if present
                response_str = str(response).strip()
                
                # Check if response is wrapped in markdown code blocks
                if response_str.startswith("```json"):
                    # Extract content between ```json and ```
                    start = response_str.find("```json") + 7
                    end = response_str.rfind("```")
                    if end > start:
                        response_str = response_str[start:end].strip()
                elif response_str.startswith("```"):
                    # Extract content between ``` blocks (without json tag)
                    start = response_str.find("```") + 3
                    end = response_str.rfind("```")
                    if end > start:
                        response_str = response_str[start:end].strip()
                
                analysis = json.loads(response_str)
                log_operation("analyze_content", {"file": str(plan_path), "analysis": analysis})
                return analysis
            except json.JSONDecodeError as e:
                error_msg = f"Invalid JSON response from OpenRouter API: {e}"
                logger.error(f"[FLOW_MBANK] {error_msg}")
                logger.error(f"[FLOW_MBANK] Raw response: {response_str[:200]}...")
                raise Exception(f"❌ API RESPONSE ERROR: {error_msg}")
        else:
            error_msg = "No response from OpenRouter API - Check API key, internet connection, and model configuration"
            logger.error(f"[FLOW_MBANK] {error_msg}")
            raise Exception(f"❌ API CONNECTION ERROR: {error_msg}")
        
    except Exception as e:
        if "❌" in str(e):
            # Re-raise our formatted errors
            raise e
        else:
            # Format unexpected errors
            error_msg = f"Failed to analyze plan content: {e}"
            logger.error(f"[FLOW_MBANK] {error_msg}")
            log_operation("analyze_content", {"error": str(e), "file": str(plan_path)}, success=False)
            raise Exception(f"❌ ANALYSIS ERROR: {error_msg}")

# =============================================
# MEMORY BANK CREATION
# =============================================

def is_template_content(content: str) -> bool:
    """Check if plan content is still unedited template (v2.1)"""
    # Template v2.1 markers - if these are still present, it's an unedited template
    template_indicators = [
        "[What do you want to achieve? Be specific about the end state.]",
        "[Break down into 3-5 concrete goals. What must be accomplished?]",
        "[How will you tackle this? Research first? Agents for broad analysis? Direct work?]",
        "[Document each significant action with outcome]",
        "[Working notes, discoveries, important context]",
        "[What defines complete for this specific PLAN?]"
    ]

    # Check if 4+ template indicators are still present (allows minor edits)
    markers_found = sum(1 for indicator in template_indicators if indicator in content)

    # Return True if 4 or more markers present = essentially untouched template
    return markers_found >= 4

def create_memory_entry(plan_path: Path, analysis: Dict[str, str]) -> Optional[Path]:
    """Create memory bank entry from analyzed plan"""
    try:
        # Read plan content
        with open(plan_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if content is still template
        is_template = is_template_content(content)

        # Get folder context
        # Handle plans outside ECOSYSTEM_ROOT (e.g., root level plans)
        try:
            relative_path = plan_path.relative_to(ECOSYSTEM_ROOT)
            folder_context = str(relative_path.parent).replace("\\", "-").replace("/", "-")
        except ValueError:
            # Plan is outside ECOSYSTEM_ROOT, use absolute path as relative_path
            relative_path = plan_path  # FIX: Set relative_path for use in memory content
            folder_context = str(plan_path.parent).replace("\\", "-").replace("/", "-")

        if folder_context == "." or folder_context == "":
            folder_context = "root"
        
        # Create filename: PATH-TYPE-CATEGORY-ACTION-PLANXXXX-YYYYMMDD.md
        # Add TEMP indicator if content is unedited (TRL conformity)
        today = datetime.now().strftime("%Y%m%d")
        plan_num = plan_path.stem.replace("PLAN", "")  # Extract number from PLAN0007.md
        template_suffix = "-TEMP" if is_template else ""
        filename = f"{folder_context}-{analysis['type']}-{analysis['category']}-{analysis['action']}-PLAN{plan_num}{template_suffix}-{today}.md"
        
        # Sanitize filename
        filename = re.sub(r'[<>:"|?*]', '-', filename)
        filename = re.sub(r'-+', '-', filename)
        
        memory_file = MEMORY_BANK_PATH / filename
        
        # Ensure memory_bank directory exists
        memory_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Create memory entry content
        memory_content = f"""# {analysis['summary']}

**Source**: {relative_path}
**TRL Tags**: {analysis['type']}-{analysis['category']}-{analysis['action']}
**Created**: {datetime.now().strftime('%Y-%m-%d')}
**Location**: {relative_path.parent}

## Summary
{analysis['summary']}

## Original Content
{content}
"""
        
        # Write memory entry
        with open(memory_file, 'w', encoding='utf-8') as f:
            f.write(memory_content)
        
        logger.info(f"[FLOW_MBANK] Created memory entry: {memory_file}")
        log_operation("create_memory_entry", {"source": str(plan_path), "memory_file": str(memory_file), "analysis": analysis})
        
        return memory_file
        
    except Exception as e:
        logger.error(f"[FLOW_MBANK] Error creating memory entry: {e}")
        log_operation("create_memory_entry", {"error": str(e), "source": str(plan_path)}, success=False)
        return None

def scan_for_open_plans() -> List[Tuple[str, Path]]:
    """Scan for all open PLAN files (not closed)"""
    try:
        # Load registry to get open plans
        registry_file = FLOW_JSON_DIR / "flow_registry.json"
        if not registry_file.exists():
            logger.warning(f"[FLOW_MBANK] Registry not found")
            return []
        
        with open(registry_file, 'r', encoding='utf-8') as f:
            registry = json.load(f)
        
        open_plans = []
        
        # Get all open plans from registry
        for plan_id, plan_info in registry.get("plans", {}).items():
            if plan_info.get("status") == "open":
                plan_path = Path(plan_info.get("file_path", ""))
                if plan_path.exists():
                    # Determine if it's a whiteboard (PLAN.md) or numbered plan
                    if plan_path.name == "PLAN.md":
                        open_plans.append(("whiteboard", plan_path))
                    else:
                        open_plans.append(("active", plan_path))
        
        logger.info(f"[FLOW_MBANK] Found {len(open_plans)} open plans")
        return open_plans
        
    except Exception as e:
        logger.error(f"[FLOW_MBANK] Error scanning for open plans: {e}")
        return []

def cleanup_processed_plan(plan_path: Path, correlation_id: str | None = None) -> bool:
    """Move processed plan file to backup_system/processed_plans/

    VERIFICATION: Returns True ONLY if file successfully moved AND verified at destination
    """
    try:
        # Create processed_plans directory if it doesn't exist
        processed_plans_dir = ECOSYSTEM_ROOT / "backup_system" / "processed_plans"
        processed_plans_dir.mkdir(parents=True, exist_ok=True)

        # Move plan to processed_plans directory
        destination = processed_plans_dir / plan_path.name

        # Handle duplicate names by adding timestamp
        if destination.exists():
            timestamp = datetime.now().strftime("%H%M%S")
            stem = destination.stem
            suffix = destination.suffix
            destination = processed_plans_dir / f"{stem}_{timestamp}{suffix}"

        # Store source path for verification
        source_path = Path(plan_path)

        # Attempt move
        plan_path.rename(destination)

        # VERIFICATION LAYER: Confirm move actually happened
        # Check 1: File exists at destination
        if not destination.exists():
            logger.error(f"[FLOW_MBANK] VERIFICATION FAILED: File not found at destination after rename: {destination}")
            return False

        # Check 2: File no longer exists at source
        if source_path.exists():
            logger.error(f"[FLOW_MBANK] VERIFICATION FAILED: File still exists at source after rename: {source_path}")
            logger.error(f"[FLOW_MBANK] File may have been copied instead of moved, or filesystem is lying")
            return False

        # Both checks passed - move genuinely succeeded
        logger.info(f"[FLOW_MBANK] Moved processed plan to backup: {destination}")
        logger.info(f"[FLOW_MBANK] VERIFICATION PASSED: File confirmed at destination, removed from source")
        return True

    except Exception as e:
        logger.error(f"[FLOW_MBANK] Error archiving plan: {e}")
        return False

def verify_and_heal_orphaned_plans() -> dict:
    """Cross-check registry vs filesystem and auto-heal orphaned plans

    Detects plans where registry says processed=true but file still at original location.
    Attempts to move orphaned files to processed_plans/ directory.

    Returns:
        {
            'orphans_found': int,
            'successfully_healed': int,
            'failed_to_heal': int,
            'orphans': [list of plan details]
        }
    """
    logger.info("[FLOW_MBANK] Running orphan verification and auto-heal...")

    registry = load_flow_registry()
    processed_plans_dir = ECOSYSTEM_ROOT / "backup_system" / "processed_plans"

    orphans_found = 0
    successfully_healed = 0
    failed_to_heal = 0
    orphan_details = []

    for plan_num, plan_info in registry.get("plans", {}).items():
        # Only check plans marked as processed
        if plan_info.get("processed") == True and plan_info.get("cleanup_completed") == True:
            original_path = Path(plan_info.get("file_path", ""))

            # VERIFICATION: Does file still exist at original location?
            if original_path.exists():
                # ORPHAN DETECTED
                orphans_found += 1
                logger.warning(f"[FLOW_MBANK] ORPHAN DETECTED: PLAN{plan_num} marked as processed but file still at {original_path}")

                # Attempt auto-heal by moving file now
                try:
                    destination = processed_plans_dir / original_path.name

                    # Handle duplicates
                    if destination.exists():
                        timestamp = datetime.now().strftime("%H%M%S")
                        stem = destination.stem
                        suffix = destination.suffix
                        destination = processed_plans_dir / f"{stem}_{timestamp}{suffix}"

                    # Attempt move
                    original_path.rename(destination)

                    # Verify move (use same verification as cleanup function)
                    if destination.exists() and not original_path.exists():
                        successfully_healed += 1
                        logger.info(f"[FLOW_MBANK] AUTO-HEAL SUCCESS: PLAN{plan_num} moved to {destination}")
                        orphan_details.append({
                            "plan": f"PLAN{plan_num}",
                            "status": "healed",
                            "original_path": str(original_path),
                            "destination": str(destination)
                        })
                    else:
                        failed_to_heal += 1
                        logger.error(f"[FLOW_MBANK] AUTO-HEAL FAILED: PLAN{plan_num} verification failed after rename")
                        orphan_details.append({
                            "plan": f"PLAN{plan_num}",
                            "status": "heal_failed",
                            "error": "Verification failed after rename",
                            "path": str(original_path)
                        })

                except Exception as e:
                    failed_to_heal += 1
                    logger.error(f"[FLOW_MBANK] AUTO-HEAL FAILED: PLAN{plan_num} - {e}")
                    orphan_details.append({
                        "plan": f"PLAN{plan_num}",
                        "status": "heal_failed",
                        "error": str(e),
                        "path": str(original_path)
                    })

    result = {
        "orphans_found": orphans_found,
        "successfully_healed": successfully_healed,
        "failed_to_heal": failed_to_heal,
        "orphans": orphan_details
    }

    if orphans_found > 0:
        logger.info(f"[FLOW_MBANK] Auto-heal complete: {successfully_healed}/{orphans_found} orphans healed")
    else:
        logger.info("[FLOW_MBANK] No orphaned plans found - system integrity verified")

    return result

# =============================================
# MAIN PROCESSING FUNCTION
# =============================================

def process_closed_plans() -> Dict[str, Any]:
    """Main function to process all closed plans"""
    logger.info("[FLOW_MBANK] Starting closed plan processing...")
    
    # Load config first to ensure JSON files are created for first run
    config = load_config()
    
    # Load data
    data = load_data()
    processed_count = 0
    error_count = 0
    results = []
    
    try:
        # Get closed plans from registry
        closed_plans = get_closed_plans()
        
        if not closed_plans:
            logger.info("[FLOW_MBANK] No closed plans found for processing")
            return {"processed": 0, "errors": 0, "results": []}
        
        logger.info(f"[FLOW_MBANK] Found {len(closed_plans)} closed plans to process")
        
        # Process each closed plan
        for plan in closed_plans:
            try:
                plan_path = plan["path"]
                plan_num = plan["number"]
                plan_info = plan["info"]
                
                # Generate correlation ID for this plan's processing
                correlation_id = f"PLAN{plan_num}-{datetime.now().strftime('%H%M%S')}"
                
                logger.info(f"[FLOW_MBANK] Processing PLAN{plan_num}: {plan_path} (correlation: {correlation_id})")
                
                # Analyze content
                analysis = analyze_plan_content(plan_path)
                log_operation("analyze_content", {"file": str(plan_path), "analysis": analysis}, correlation_id=correlation_id)
                
                # Create memory entry
                memory_file = create_memory_entry(plan_path, analysis)
                if memory_file:
                    log_operation("create_memory_entry", {"source": str(plan_path), "memory_file": str(memory_file), "analysis": analysis}, correlation_id=correlation_id)
                
                if memory_file:
                    # Phase 1: Memory creation succeeded
                    registry = load_flow_registry()
                    if plan_num in registry.get("plans", {}):
                        registry["plans"][plan_num]["memory_created"] = True
                        registry["plans"][plan_num]["memory_created_date"] = datetime.now(timezone.utc).isoformat()
                        registry["plans"][plan_num]["memory_file"] = str(memory_file)
                        save_flow_registry(registry)
                        logger.info(f"[FLOW_MBANK] PLAN{plan_num} memory bank entry created successfully")
                    
                    # Phase 2: Try to cleanup/move plan to backup
                    cleanup_success = cleanup_processed_plan(plan_path, correlation_id)
                    if cleanup_success:
                        # Get the destination path for logging
                        processed_plans_dir = ECOSYSTEM_ROOT / "backup_system" / "processed_plans"
                        destination = processed_plans_dir / plan_path.name
                        log_operation("archive_plan", {"source": str(plan_path), "destination": str(destination)}, correlation_id=correlation_id)
                    else:
                        log_operation("archive_plan", {"source": str(plan_path), "error": "Failed to move plan to backup"}, success=False, correlation_id=correlation_id)
                    
                    # Update registry with final status
                    registry = load_flow_registry()
                    if plan_num in registry.get("plans", {}):
                        registry["plans"][plan_num]["cleanup_completed"] = cleanup_success
                        registry["plans"][plan_num]["cleanup_date"] = datetime.now(timezone.utc).isoformat()
                        
                        # Only mark as fully processed if BOTH phases succeeded
                        if cleanup_success:
                            registry["plans"][plan_num]["processed"] = True
                            registry["plans"][plan_num]["processed_date"] = datetime.now(timezone.utc).isoformat()
                        
                        save_flow_registry(registry)
                    
                    if cleanup_success:
                        # FULL SUCCESS: Memory created AND plan moved to backup
                        processed_count += 1
                        results.append({
                            "plan": f"PLAN{plan_num}",
                            "memory_file": str(memory_file),
                            "status": "fully_processed",
                            "correlation_id": correlation_id
                        })
                        logger.info(f"[FLOW_MBANK] PLAN{plan_num} fully processed - memory created and moved to backup")
                    else:
                        # PARTIAL SUCCESS: Memory created but cleanup failed
                        error_count += 1  # This is an error because plan is still in root
                        results.append({
                            "plan": f"PLAN{plan_num}",
                            "memory_file": str(memory_file),
                            "status": "memory_created_cleanup_failed",
                            "error": "Memory bank entry created but failed to move plan to backup folder",
                            "correlation_id": correlation_id
                        })
                        logger.error(f"[FLOW_MBANK] PLAN{plan_num} memory created but cleanup failed - plan still in root directory")
                else:
                    error_count += 1
                    results.append({
                        "plan": f"PLAN{plan_num}",
                        "status": "error", 
                        "error": "Failed to create memory entry",
                        "correlation_id": correlation_id
                    })
                    
            except Exception as e:
                error_count += 1
                plan_num = plan.get('number', 'unknown')
                logger.error(f"[FLOW_MBANK] Error processing plan {plan_num}: {e}")
                
                # Format error message for console display
                if "❌" in str(e):
                    # Our formatted API errors
                    error_msg = str(e)
                else:
                    # Unexpected errors
                    error_msg = f"❌ PROCESSING ERROR: {str(e)}"
                
                results.append({
                    "plan": f"PLAN{plan_num}",
                    "status": "error",
                    "error": error_msg
                })
        
        # Update data
        data["plans_processed"] = data.get("plans_processed", 0) + processed_count
        data["memory_entries_created"] = data.get("memory_entries_created", 0) + processed_count
        data["last_run"] = datetime.now(timezone.utc).isoformat()
        save_data(data)
        
        logger.info(f"[FLOW_MBANK] Processing complete: {processed_count} success, {error_count} errors")
        
        # Enhanced logging with detailed results
        log_details = {
            "processed": processed_count, 
            "errors": error_count,
            "results": results,
            "plans_attempted": len(closed_plans)
        }
        log_operation("process_closed_plans", log_details)
        
        return {
            "processed": processed_count,
            "errors": error_count,
            "results": results
        }
        
    except Exception as e:
        logger.error(f"[FLOW_MBANK] Error in main processing: {e}")
        log_operation("process_closed_plans", {"error": str(e)}, success=False)
        return {"processed": 0, "errors": 1, "results": []}

# =============================================
# STATUS AND INFORMATION
# =============================================

def get_status() -> Dict[str, Any]:
    """Get flow_mbank status information"""
    try:
        data = load_data()
        registry = load_flow_registry()
        
        # Count plans by status
        closed_count = sum(1 for p in registry.get("plans", {}).values() if p.get("status") == "closed")
        processed_count = sum(1 for p in registry.get("plans", {}).values() if p.get("processed") == True)
        pending_count = closed_count - processed_count
        
        status = {
            "module": MODULE_NAME,
            "data": data,
            "plans": {
                "closed": closed_count,
                "processed": processed_count,
                "pending": pending_count
            },
            "paths": {
                "memory_bank": str(MEMORY_BANK_PATH),
                "registry": str(REGISTRY_FILE)
            }
        }
        
        return status
        
    except Exception as e:
        logger.error(f"[FLOW_MBANK] Error getting status: {e}")
        return {"error": str(e)}

# =============================================
# INITIALIZATION
# =============================================

def initialize_flow_mbank():
    """Initialize flow_mbank module"""
    logger.info(f"[FLOW_MBANK] Initializing Flow Memory Bank v1.0.0")
    try:
        # Load configuration
        config = load_config()
        logger.info(f"[FLOW_MBANK] Configuration loaded")
        
        # Initialize data
        data = load_data()
        logger.info(f"[FLOW_MBANK] Data loaded")
        
        # Check for flow registry
        if REGISTRY_FILE.exists():
            logger.info(f"[FLOW_MBANK] Flow registry found")
        else:
            logger.warning(f"[FLOW_MBANK] Flow registry not found - will be created by flow_plan")
        
        logger.info(f"[FLOW_MBANK] Flow Memory Bank initialization completed successfully")
        log_operation("initialize", {"version": "1.0.0"})
        return True
    except Exception as e:
        logger.error(f"[FLOW_MBANK] Initialization failed: {e}")
        log_operation("initialize", {"error": str(e)}, success=False)
        return False

# Initialize on import
initialize_flow_mbank()

# =============================================
# INTERACTIVE MENU
# =============================================

def interactive_menu():
    """Interactive menu for flow_mbank operations"""
    config = load_config()
    print(f"\n{'='*60}")
    print(f"Flow Memory Bank Processor v{config.get('version', '0.1.0')}")
    print('='*60)
    print("Automated PLAN-to-Memory_Bank conversion system")
    print("")
    print("Options:")
    print("  1. Scan for closed plans")
    print("  2. Process all closed plans") 
    print("  3. Show configuration")
    print("  4. Show processing status")
    print("  5. Show help")
    print("  6. Show open plans")
    print("  q. Quit")
    print("")
    
    while True:
        try:
            choice = input("Select option (1-6, or 'q' to quit): ").strip().lower()
            
            if choice == 'q' or choice == 'quit':
                print("Goodbye!")
                break
            elif choice == '1':
                print(f"\n{'='*40}")
                print("SCANNING FOR CLOSED PLANS")
                print('='*40)
                # Get closed plans from registry
                registry_file = FLOW_JSON_DIR / "flow_registry.json"
                if registry_file.exists():
                    with open(registry_file, 'r', encoding='utf-8') as f:
                        registry = json.load(f)
                    closed_plans = []
                    for plan_id, plan_info in registry.get("plans", {}).items():
                        if plan_info.get("status") == "closed" and not plan_info.get("processed"):
                            closed_plans.append(plan_info.get("file_path"))
                    print(f"Found {len(closed_plans)} closed plan(s)")
                    for plan in closed_plans:
                        print(f"  {plan}")
                else:
                    print("Registry not found")
                print("\nPress Enter to continue...")
                input()
            elif choice == '2':
                print(f"\n{'='*40}")
                print("PROCESSING CLOSED PLANS")
                print('='*40)
                results = process_closed_plans()
                print(f"Processed: {results['processed']} plans")
                print(f"Errors: {results['errors']}")
                if results.get('results'):
                    for result in results['results']:
                        if result['status'] == 'success':
                            print(f"  ✓ {result['plan']}")
                        else:
                            print(f"  ✗ {result['plan']}: {result.get('error', 'Unknown')}")
                print("\nPress Enter to continue...")
                input()
            elif choice == '3':
                print(f"\n{'='*40}")
                print("CURRENT CONFIGURATION")
                print('='*40)
                config = load_config()
                print(json.dumps(config, indent=2))
                print("\nPress Enter to continue...")
                input()
            elif choice == '4':
                print(f"\n{'='*40}")
                print("PROCESSING STATUS")
                print('='*40)
                data = load_data()
                status = get_status()
                print(f"Last run: {data.get('last_run', 'Never')}")
                print(f"Memory entries created: {data.get('memory_entries_created', 0)}")
                print(f"Closed plans: {status['plans']['closed']}")
                print(f"Processed: {status['plans']['processed']}")
                print(f"Pending: {status['plans']['pending']}")
                print("\nPress Enter to continue...")
                input()
            elif choice == '5':
                print(f"\n{'='*40}")
                print("HELP & USAGE")
                print('='*40)
                print("This system automatically converts closed PLAN files to TRL memory entries.")
                print("")
                print("Workflow:")
                print("1. Use 'drone plan close <number>' to close a PLAN")
                print("2. Run 'Scan' to find all closed plans")
                print("3. Run 'Process' to convert them to memory_bank entries")
                print("4. Check 'Status' to see results")
                print("")
                print("Output format: PATH-TYPE-CATEGORY-ACTION-PLANXXXX-YYYYMMDD.md")
                print("Note: Processed plans are deleted after memory creation")
                print("\nPress Enter to continue...")
                input()
            elif choice == '6':
                print(f"\n{'='*40}")
                print("OPEN PLANS")
                print('='*40)
                open_plans = scan_for_open_plans()
                if not open_plans:
                    print("No open plans found")
                else:
                    print(f"Found {len(open_plans)} open plan(s):")
                    print("")
                    whiteboards = [p for p in open_plans if p[0] == "whiteboard"]
                    active_plans = [p for p in open_plans if p[0] == "active"]
                    
                    if whiteboards:
                        print("WHITEBOARDS (PLAN.md):")
                        for _, path in whiteboards:
                            print(f"  {path}")
                    
                    if active_plans:
                        if whiteboards:
                            print("")
                        print("ACTIVE PLANS (PLAN####.md):")
                        for _, path in active_plans:
                            print(f"  {path}")
                    
                    print("")
                    print("TIP: Click paths above to open files directly")
                print("\nPress Enter to continue...")
                input()
            else:
                print("Invalid choice. Please select 1-6 or 'q'.")
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except EOFError:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")
            print("Press Enter to continue...")
            try:
                input()
            except (EOFError, KeyboardInterrupt):
                break

def main():
    """Main entry point for command-line usage"""
    parser = argparse.ArgumentParser(
        description='Flow Memory Bank Processor - TRL-compliant memory conversion',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
COMMANDS:
  Commands: scan, process, config, status, open, menu

  scan     - Scan for closed plans ready to process
  process  - Process all closed plans to memory_bank
  config   - Show current configuration
  status   - Show processing status and statistics
  open     - Show all open (active) plans
  menu     - Interactive menu interface

EXAMPLES:
  python3 flow_mbank.py scan
  python3 flow_mbank.py process
  python3 flow_mbank.py config
  python3 flow_mbank.py status
  python3 flow_mbank.py open
  python3 flow_mbank.py menu

NOTE:
  If no command is provided, the interactive menu will be shown.
        """
    )

    parser.add_argument('command',
                       nargs='?',
                       choices=['scan', 'process', 'config', 'status', 'open', 'menu'],
                       help='Command to execute')

    args = parser.parse_args()

    # If no command, show interactive menu
    if not args.command:
        interactive_menu()
        return 0

    command = args.command.lower()

    if command == "scan":
        # Scan for closed plans
        print("[FLOW_MBANK] Scanning for closed plans...")
        closed_plans = get_closed_plans()

        if not closed_plans:
            print("No closed plans found")
        else:
            print(f"Found {len(closed_plans)} closed plan(s):")
            for plan in closed_plans:
                print(f"  PLAN{plan['number']}: {plan['path']}")

        return 0

    elif command == "process":
        # Process closed plans
        print("[FLOW_MBANK] Processing closed plans...")
        results = process_closed_plans()

        if results["processed"] > 0:
            print(f"Successfully processed {results['processed']} plans")
        if results["errors"] > 0:
            print(f"{results['errors']} errors occurred")

        for result in results.get("results", []):
            if result["status"] == "success":
                print(f"  ✓ {result['plan']} → {Path(result['memory_file']).name}")
            else:
                print(f"  ✗ {result['plan']}: {result.get('error', 'Unknown error')}")

        return 0 if results["errors"] == 0 else 1

    elif command == "config":
        # Show configuration
        config = load_config()
        print("\nFLOW MEMORY BANK CONFIGURATION")
        print("-" * 40)
        print(json.dumps(config, indent=2))
        return 0

    elif command == "status":
        # Show status
        status = get_status()
        print("\nFLOW MEMORY BANK STATUS")
        print("-" * 40)
        print(f"Closed plans: {status['plans']['closed']}")
        print(f"Processed: {status['plans']['processed']}")
        print(f"Pending: {status['plans']['pending']}")
        print(f"Total memory entries: {status['data']['memory_entries_created']}")

        if status['data']['last_run']:
            print(f"Last run: {status['data']['last_run']}")

        return 0

    elif command == "open":
        # Show open plans
        print("[FLOW_MBANK] Scanning for open plans...")
        open_plans = scan_for_open_plans()

        if not open_plans:
            print("No open plans found")
        else:
            print(f"Found {len(open_plans)} open plan(s):")

            # Separate whiteboards and active plans
            whiteboards = [p for p in open_plans if p[0] == "whiteboard"]
            active_plans = [p for p in open_plans if p[0] == "active"]

            if whiteboards:
                print("\nWHITEBOARDS (PLAN.md):")
                for _, path in whiteboards:
                    print(f"  {path}")

            if active_plans:
                print("\nACTIVE PLANS (PLAN####.md):")
                for _, path in active_plans:
                    print(f"  {path}")

        return 0

    elif command == "menu":
        # Show interactive menu
        interactive_menu()
        return 0

    return 0
if __name__ == "__main__":
    sys.exit(main())