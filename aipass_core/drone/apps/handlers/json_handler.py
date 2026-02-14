#!/home/aipass/.venv/bin/python3
# -*- coding: utf-8 -*-

# ===================AIPASS====================
# META DATA HEADER
# Name: json_handler.py - Auto-Creating JSON Handler
# Date: 2025-11-07
# Version: 1.0.0
# Category: drone/handlers
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2025-11-07): Self-healing JSON system with default templates (adapted from cortex)
# =============================================

"""
JSON Handler - Auto-Creating & Self-Healing JSON System

Handles default JSON files (config, data, log) for drone modules:
- Auto-creates JSONs if missing
- Self-heals corrupted JSONs
- Provides load/save interface for modules
- Never manually create JSONs - they build themselves
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional


# =============================================================================
# CONSTANTS
# =============================================================================

AIPASS_ROOT = Path.home() / "aipass_core"
DRONE_ROOT = AIPASS_ROOT / "drone"
DRONE_JSON_DIR = DRONE_ROOT / "drone_json"
JSON_TEMPLATES_DIR = DRONE_ROOT / "apps" / "handlers" / "json_templates"


# =============================================================================
# TEMPLATE LOADING (from external JSON files)
# =============================================================================

def load_template(json_type: str, module_name: str, template_category: str = "default") -> Any:
    """
    Load JSON template from template file

    Args:
        json_type: Type of JSON (config, data, log)
        module_name: Name of module (for placeholder substitution)
        template_category: Category of template (default, custom, registry)

    Returns:
        Template data with placeholders replaced
    """
    # Check for custom template first
    if template_category == "custom":
        custom_path = JSON_TEMPLATES_DIR / "custom" / f"{module_name}_{json_type}.json"
        if custom_path.exists():
            template_path = custom_path
        else:
            # Fall back to default if custom doesn't exist
            template_path = JSON_TEMPLATES_DIR / "default" / f"{json_type}.json"
    else:
        # Use default or registry template
        template_path = JSON_TEMPLATES_DIR / template_category / f"{json_type}.json"

    if not template_path.exists():
        # Return None - caller handles missing template
        return None

    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            template = json.load(f)

        # Replace placeholders
        template_str = json.dumps(template)
        template_str = template_str.replace("{{MODULE_NAME}}", module_name)
        template_str = template_str.replace("{{TIMESTAMP}}", datetime.now().isoformat())

        return json.loads(template_str)

    except Exception:
        # Return None - caller handles load failure
        return None


# =============================================================================
# JSON VALIDATION
# =============================================================================

def validate_json_structure(data: Any, json_type: str) -> bool:
    """
    Validate JSON structure matches expected type

    Args:
        data: Loaded JSON data
        json_type: Type of JSON (config, data, log)

    Returns:
        True if valid structure, False if corrupted
    """
    if json_type == "config":
        # Config must be dict with required fields
        if not isinstance(data, dict):
            return False
        required = ["module_name", "version", "config"]
        return all(key in data for key in required)

    elif json_type == "data":
        # Data must be dict with timestamp fields
        if not isinstance(data, dict):
            return False
        required = ["created", "last_updated"]
        return all(key in data for key in required)

    elif json_type == "log":
        # Log must be array
        return isinstance(data, list)

    return False


# =============================================================================
# CORE JSON OPERATIONS
# =============================================================================

def get_json_path(module_name: str, json_type: str) -> Path:
    """
    Get path for module JSON file

    Args:
        module_name: Name of module
        json_type: Type of JSON (config, data, log)

    Returns:
        Path to JSON file
    """
    filename = f"{module_name}_{json_type}.json"
    return DRONE_JSON_DIR / filename


def ensure_json_exists(module_name: str, json_type: str) -> bool:
    """
    Ensure JSON file exists, create from template if missing

    Args:
        module_name: Name of module
        json_type: Type of JSON (config, data, log)

    Returns:
        True if file exists or was created successfully
    """
    # Ensure drone_json directory exists
    DRONE_JSON_DIR.mkdir(parents=True, exist_ok=True)

    json_path = get_json_path(module_name, json_type)

    # If exists, validate structure
    if json_path.exists():
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Validate structure
            if validate_json_structure(data, json_type):
                return True
            # Corrupted - fall through to regenerate
        except Exception:
            pass  # Unreadable - fall through to regenerate

    # Load template from file
    template = load_template(json_type, module_name, template_category="default")

    if template is None:
        return False

    # Write template
    try:
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(template, f, indent=2, ensure_ascii=False)
        return True
    except Exception:
        return False


def load_json(module_name: str, json_type: str) -> Optional[Any]:
    """
    Load JSON file, auto-create if missing

    Args:
        module_name: Name of module
        json_type: Type of JSON (config, data, log)

    Returns:
        Loaded JSON data or None if error
    """
    # Ensure file exists
    if not ensure_json_exists(module_name, json_type):
        return None

    json_path = get_json_path(module_name, json_type)

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return None


def save_json(module_name: str, json_type: str, data: Any) -> bool:
    """
    Save JSON file

    Args:
        module_name: Name of module
        json_type: Type of JSON (config, data, log)
        data: Data to save

    Returns:
        True if successful, False otherwise
    """
    json_path = get_json_path(module_name, json_type)

    # Validate structure before saving
    if not validate_json_structure(data, json_type):
        return False

    # Update timestamp for data JSONs
    if json_type == "data" and isinstance(data, dict):
        data["last_updated"] = datetime.now().isoformat()

    try:
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception:
        return False


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def log_operation(module_name: str, operation: str, data: Dict[str, Any] | None = None) -> bool:
    """
    Add entry to module log

    Args:
        module_name: Name of module
        operation: Operation description
        data: Optional data dict

    Returns:
        True if successful, False otherwise
    """
    log = load_json(module_name, "log")
    if log is None:
        log = []

    entry: Dict[str, Any] = {
        "timestamp": datetime.now().isoformat(),
        "operation": operation
    }

    if data:
        entry["data"] = data

    log.append(entry)

    return save_json(module_name, "log", log)


def update_data_metrics(module_name: str, **metrics) -> bool:
    """
    Update data metrics

    Args:
        module_name: Name of module
        **metrics: Metric key-value pairs to update

    Returns:
        True if successful, False otherwise
    """
    data = load_json(module_name, "data")
    if data is None:
        return False

    # Update provided metrics
    for key, value in metrics.items():
        data[key] = value

    return save_json(module_name, "data", data)


def increment_counter(module_name: str, counter_name: str, amount: int = 1) -> bool:
    """
    Increment a counter in data JSON

    Args:
        module_name: Name of module
        counter_name: Name of counter field
        amount: Amount to increment (default 1)

    Returns:
        True if successful, False otherwise
    """
    data = load_json(module_name, "data")
    if data is None:
        return False

    # Initialize counter if doesn't exist
    if counter_name not in data:
        data[counter_name] = 0

    data[counter_name] += amount

    return save_json(module_name, "data", data)
