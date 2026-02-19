#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: process.py - DPLAN Memory Bank Processing Handler
# Date: 2026-02-18
# Version: 1.0.0
# Category: devpulse/handlers/mbank
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2026-02-18): Initial version - adapted from Flow's mbank/process.py
#
# CODE STANDARDS:
#   - 3-tier compliant: NO Prax imports, NO logging
#   - Raises exceptions for errors (module logs them)
# ==============================================

"""
DPLAN Memory Bank Processing Handler

Converts closed DPLAN files to Memory Bank entries with TRL classification.
Adapted from Flow's mbank/process.py for single-user DPLANs.

Key Functions:
- process_closed_plans() - Main entry: analyze, create memory entry, archive
- analyze_plan_content() - AI-powered TRL classification
- create_memory_entry() - Write to MEMORY_BANK/plans/
- is_template_content() - Template detection
"""

import sys
from pathlib import Path

AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))
sys.path.insert(0, str(Path.home()))

import json
import re
import time
from datetime import datetime
from typing import Dict, Optional, Any

# Import OpenRouter API via module layer (cross-branch access)
from api.apps.modules.openrouter_client import get_response

# =============================================================================
# CONSTANTS
# =============================================================================

DEV_PLANNING_ROOT = Path.home() / "aipass_os" / "dev_central" / "dev_planning"
PROCESSED_PLANS_DIR = DEV_PLANNING_ROOT / "processed_plans"
MEMORY_BANK_PATH = Path.home() / "MEMORY_BANK" / "plans"
API_DELAY_SECONDS = 3

# Shared API config (same as Flow uses)
API_CONFIG_FILE = AIPASS_ROOT / "flow" / "apps" / "handlers" / "json_templates" / "custom" / "api_config.json"

# TRL mapping (reuse Flow's registry)
TRL_REGISTRY_FILE = AIPASS_ROOT / "flow" / "flow_json" / "flow_mbank_registry.json"


# =============================================================================
# CONFIGURATION
# =============================================================================

def get_ai_model() -> Optional[str]:
    """Get AI model from shared API config"""
    try:
        if API_CONFIG_FILE.exists():
            with open(API_CONFIG_FILE, 'r', encoding='utf-8') as f:
                api_config = json.load(f)
                return api_config.get("api_settings", {}).get("model")
        return None
    except Exception:
        return None


def load_trl_registry() -> Dict[str, Any]:
    """Load TRL mapping registry (shared with Flow)"""
    default_registry = {
        "trl_mapping": {
            "types": {
                "SEED": "Seed AI System", "NEXUS": "Nexus AI System",
                "SKILL": "Skills Modules", "PRAX": "Prax Infrastructure",
                "FLOW": "Flow Workflow System", "BACKUP": "Backup System",
                "DRONE": "Drone Commands", "HELP": "Help System",
                "MCP": "MCP Servers", "TOOLS": "Tools & Scripts"
            },
            "categories": {
                "API": "API & External Services", "MEM": "Memory & Storage",
                "DB": "Database & Data", "UI": "User Interface",
                "CFG": "Configuration", "DOC": "Documentation",
                "TEST": "Testing & QA", "SEC": "Security",
                "NET": "Networking", "FILE": "File Operations",
                "LOG": "Logging & Monitoring", "DEV": "Development"
            },
            "actions": {
                "IMP": "Implementation", "FIX": "Bug Fixes",
                "UPD": "Updates & Improvements", "NEW": "New Features",
                "REF": "Refactoring", "DOC": "Documentation",
                "TEST": "Testing", "CFG": "Configuration",
                "MIGR": "Migration", "OPT": "Optimization"
            }
        }
    }

    if not TRL_REGISTRY_FILE.exists():
        return default_registry

    try:
        with open(TRL_REGISTRY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return default_registry


# =============================================================================
# STATUS EXTRACTION (inlined - handler independence)
# =============================================================================

def _extract_status(plan_file: Path) -> str:
    """Extract status from plan file by checking checkboxes."""
    try:
        content = plan_file.read_text(encoding='utf-8')
        if re.search(r'- \[x\] Complete', content, re.IGNORECASE):
            return "complete"
        if re.search(r'- \[x\] Abandoned', content, re.IGNORECASE):
            return "abandoned"
        if re.search(r'- \[x\] Ready for Execution', content, re.IGNORECASE):
            return "ready"
        if re.search(r'- \[x\] In Progress', content, re.IGNORECASE):
            return "in_progress"
        if re.search(r'- \[x\] Planning', content, re.IGNORECASE):
            return "planning"
        return "planning"
    except Exception:
        return "unknown"


def _archive_plan(plan_file: Path) -> tuple[bool, str]:
    """Move closed plan to processed_plans/ directory."""
    try:
        PROCESSED_PLANS_DIR.mkdir(parents=True, exist_ok=True)
        destination = PROCESSED_PLANS_DIR / plan_file.name
        if destination.exists():
            timestamp = datetime.now().strftime("%H%M%S")
            destination = PROCESSED_PLANS_DIR / f"{destination.stem}_{timestamp}{destination.suffix}"
        source_path = Path(plan_file)
        plan_file.rename(destination)
        if not destination.exists():
            return (False, "Move verification failed: destination not found")
        if source_path.exists():
            return (False, "Move verification failed: source still exists")
        return (True, "")
    except Exception as e:
        return (False, f"Failed to archive plan: {e}")


# =============================================================================
# TEMPLATE DETECTION
# =============================================================================

def is_template_content(content: str) -> bool:
    """Check if DPLAN content is still an unedited template.

    DPLAN templates use different markers than Flow templates.

    Args:
        content: Plan file content

    Returns:
        True if plan is essentially an untouched template
    """
    dplan_markers = [
        "> One-line description",
        "## Vision",
        "## Current State",
        "## What Needs Building",
        "## Design Decisions",
    ]

    found = sum(1 for m in dplan_markers if m in content)
    # If most structural markers present AND no substantial content beyond them,
    # check that content sections are essentially empty
    if found < 3:
        return False

    # Check if content sections have real text (beyond headers and placeholders)
    lines = content.split('\n')
    content_lines = 0
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith('#'):
            continue
        if stripped.startswith('>'):
            continue
        if stripped == '---':
            continue
        if stripped.startswith('- ['):
            continue
        if stripped.startswith('*Created:') or stripped.startswith('*Updated:'):
            continue
        content_lines += 1

    return content_lines < 5


# =============================================================================
# CONTENT ANALYSIS
# =============================================================================

def analyze_plan_content(plan_path: Path) -> Dict[str, str]:
    """Use OpenRouter to analyze DPLAN content and determine TRL tags.

    Args:
        plan_path: Path to DPLAN file

    Returns:
        Dict with keys: type, category, action, summary

    Raises:
        Exception: If API call fails or response is invalid
    """
    trl_registry = load_trl_registry()

    with open(plan_path, 'r', encoding='utf-8') as f:
        content = f.read()

    trl_mapping = trl_registry["trl_mapping"]

    types_desc = "\n".join([f"{k}: {v}" for k, v in trl_mapping["types"].items()])
    categories_desc = "\n".join([f"{k}: {v}" for k, v in trl_mapping["categories"].items()])
    actions_desc = "\n".join([f"{k}: {v}" for k, v in trl_mapping["actions"].items()])

    type_codes = "|".join(trl_mapping["types"].keys())
    category_codes = "|".join(trl_mapping["categories"].keys())
    action_codes = "|".join(trl_mapping["actions"].keys())

    prompt = f"""Analyze this completed development plan file:

Content: {content[:3000]}
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

    ai_model = get_ai_model()
    response = get_response(prompt, model=ai_model, caller="devpulse_mbank")

    if not response:
        raise Exception("No response from OpenRouter API")

    response_str = response.get('content', '').strip()

    # Handle markdown code blocks
    if response_str.startswith("```json"):
        start = response_str.find("```json") + 7
        end = response_str.rfind("```")
        if end > start:
            response_str = response_str[start:end].strip()
    elif response_str.startswith("```"):
        start = response_str.find("```") + 3
        end = response_str.rfind("```")
        if end > start:
            response_str = response_str[start:end].strip()

    # Parse JSON
    try:
        analysis = json.loads(response_str)
    except json.JSONDecodeError:
        first_brace = response_str.find('{')
        last_brace = response_str.rfind('}')
        if first_brace != -1 and last_brace > first_brace:
            analysis = json.loads(response_str[first_brace:last_brace + 1])
        else:
            raise Exception(f"API returned invalid JSON: {response_str[:100]}")

    for field in ['type', 'category', 'action', 'summary']:
        if field not in analysis:
            raise Exception(f"API response missing required field: {field}")

    return analysis


# =============================================================================
# MEMORY BANK CREATION
# =============================================================================

def create_memory_entry(plan_path: Path, analysis: Dict[str, str]) -> Optional[Path]:
    """Create memory bank entry from analyzed DPLAN.

    Args:
        plan_path: Path to source DPLAN file
        analysis: Dict with type, category, action, summary

    Returns:
        Path to created memory file, or None if duplicate
    """
    with open(plan_path, 'r', encoding='utf-8') as f:
        content = f.read()

    is_template = is_template_content(content)

    # Build filename: context-TYPE-CATEGORY-ACTION-DPLAN-XXX-YYYYMMDD.md
    today = datetime.now().strftime("%Y%m%d")
    plan_stem = plan_path.stem
    match = re.match(r"DPLAN-(\d+)", plan_stem)
    plan_id = match.group(0) if match else plan_stem

    template_suffix = "-TEMP" if is_template else ""
    filename = f"dev-central-{analysis['type']}-{analysis['category']}-{analysis['action']}-{plan_id}{template_suffix}-{today}.md"

    # Sanitize
    filename = re.sub(r'[<>:"|?*]', '-', filename)
    filename = re.sub(r'-+', '-', filename)

    memory_file = MEMORY_BANK_PATH / filename
    memory_file.parent.mkdir(parents=True, exist_ok=True)

    # Duplicate check
    if memory_file.exists():
        return None

    memory_content = f"""# {analysis['summary']}

**Source**: dev_central/dev_planning/{plan_path.name}
**TRL Tags**: {analysis['type']}-{analysis['category']}-{analysis['action']}
**Created**: {datetime.now().strftime('%Y-%m-%d')}
**Plan ID**: {plan_id}

## Summary
{analysis['summary']}

## Original Content
{content}
"""

    with open(memory_file, 'w', encoding='utf-8') as f:
        f.write(memory_content)

    return memory_file


# =============================================================================
# TEMP FILE CLEANUP
# =============================================================================

def cleanup_temp_files() -> Dict[str, Any]:
    """Remove old -TEMP files from MEMORY_BANK (empty template plans).

    Returns:
        Dict with cleanup stats
    """
    files_found = 0
    files_deleted = 0

    if not MEMORY_BANK_PATH.exists():
        return {"files_found": 0, "files_deleted": 0}

    for temp_file in MEMORY_BANK_PATH.glob("*dev-central*-TEMP-*.md"):
        files_found += 1
        try:
            temp_file.unlink()
            if not temp_file.exists():
                files_deleted += 1
        except Exception:
            pass

    return {"files_found": files_found, "files_deleted": files_deleted}


# =============================================================================
# MAIN PROCESSING
# =============================================================================

def process_closed_plans() -> Dict[str, Any]:
    """Process all closed DPLANs: analyze, create memory entries, archive.

    Returns:
        Dict with success, processed count, errors, and per-plan results
    """
    try:
        # Find closed (complete) plans still in dev_planning/
        closed_plans = []
        if DEV_PLANNING_ROOT.exists():
            for plan_file in DEV_PLANNING_ROOT.glob("DPLAN-*.md"):
                if not re.match(r"DPLAN-\d+", plan_file.name):
                    continue
                status = _extract_status(plan_file)
                if status == "complete":
                    match = re.match(r"DPLAN-(\d+)", plan_file.name)
                    if match:
                        closed_plans.append({
                            "number": match.group(1),
                            "path": plan_file
                        })

        if not closed_plans:
            cleanup_result = cleanup_temp_files()
            return {
                "success": True, "processed": 0, "errors": 0,
                "results": [], "cleanup": cleanup_result
            }

        processed_count = 0
        error_count = 0
        results = []
        rate_limited = False

        for i, plan in enumerate(closed_plans):
            if rate_limited:
                results.append({
                    "plan": f"DPLAN-{plan['number']}",
                    "status": "skipped",
                    "error": "Skipped due to API rate limit"
                })
                continue

            if i > 0:
                time.sleep(API_DELAY_SECONDS)

            try:
                plan_path = plan["path"]
                plan_num = plan["number"]

                # Phase 1: Analyze content
                analysis = analyze_plan_content(plan_path)

                # Phase 2: Create memory entry
                memory_file = create_memory_entry(plan_path, analysis)

                if memory_file:
                    # Phase 3: Archive plan
                    ok, err = _archive_plan(plan_path)

                    if ok:
                        processed_count += 1
                        results.append({
                            "plan": f"DPLAN-{plan_num}",
                            "memory_file": str(memory_file),
                            "status": "fully_processed"
                        })
                    else:
                        error_count += 1
                        results.append({
                            "plan": f"DPLAN-{plan_num}",
                            "memory_file": str(memory_file),
                            "status": "memory_created_archive_failed",
                            "error": err
                        })
                else:
                    # Duplicate - already processed
                    ok, err = _archive_plan(plan_path)
                    processed_count += 1
                    results.append({
                        "plan": f"DPLAN-{plan_num}",
                        "status": "duplicate_archived"
                    })

            except Exception as e:
                error_count += 1
                error_str = str(e)
                if "429" in error_str or "rate limit" in error_str.lower():
                    rate_limited = True
                    results.append({
                        "plan": f"DPLAN-{plan.get('number', '?')}",
                        "status": "rate_limited",
                        "error": error_str
                    })
                else:
                    results.append({
                        "plan": f"DPLAN-{plan.get('number', '?')}",
                        "status": "error",
                        "error": error_str
                    })

        cleanup_result = cleanup_temp_files()

        return {
            "success": True,
            "processed": processed_count,
            "errors": error_count,
            "results": results,
            "cleanup": cleanup_result
        }

    except Exception as e:
        return {
            "success": False, "processed": 0, "errors": 0,
            "results": [], "error": str(e)
        }
