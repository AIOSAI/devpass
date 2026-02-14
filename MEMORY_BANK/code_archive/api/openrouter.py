#!/usr/bin/env python3

# =============================================
# META DATA HEADER
# Name: openrouter.py
# Date: 2025-08-30
# Version: 1.0.0
# Category: api
# 
# CHANGELOG:
#   - v1.0.0 (2025-08-30): Initial OpenRouter client using OpenAI SDK
# =============================================

"""
OpenRouter Client using OpenAI SDK
Following AIPass standards: 3-JSON pattern, prax logging, proper error handling

Uses OpenRouter as unified gateway to 323+ models from all providers
- OpenAI SDK with OpenRouter base URL
- Handles all 323 available models via single interface
- Full error handling and logging
- Real usage tracking integration
- Returns response or explicit error

Features:
- Unified access to all AI providers through OpenRouter
- OpenAI SDK compatibility with OpenRouter endpoints
- Real usage tracking via generation_id
- Per-caller usage breakdown
- Full error handling with context logging
- 3-file JSON structure (config/data/log)
"""

# INFRASTRUCTURE IMPORT PATTERN - Direct system access
import sys
from pathlib import Path
AIPASS_ROOT = Path.home() / "aipass_core"
API_ROOT = AIPASS_ROOT / "api"
sys.path.append(str(AIPASS_ROOT))  # To ecosystem root
from prax.apps.prax_logger import system_logger as logger

# Standard imports
import json
import argparse
from datetime import datetime
from typing import Dict, List, Optional

# OpenAI SDK for OpenRouter compatibility
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    logger.error("OpenAI SDK not available. Install with: pip install openai")
    OPENAI_AVAILABLE = False

# API modules
from api.apps.api_connect import APIConnect
from api.apps.api_usage import track_usage

# =============================================
# CONFIGURATION SECTION
# =============================================

MODULE_NAME = "openrouter"
MODULE_VERSION = "1.0.0"
MODULE_CATEGORY = "api"

# Standard 3-file JSON structure
CONFIG_FILE = f"{MODULE_NAME}_config.json"
DATA_FILE = f"{MODULE_NAME}_data.json"
LOG_FILE = f"{MODULE_NAME}_log.json"

# Module JSON directory (absolute path)
API_JSON_DIR = API_ROOT / "api_json"

# OpenRouter configuration - constants for config defaults
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "meta-llama/llama-3.3-70b-instruct:free"  # Updated 2025-10-18: Previous DeepSeek blocked by privacy settings
DEFAULT_TIMEOUT = 30

# =============================================
# CALLER DETECTION AND PROVISIONING
# =============================================

def get_caller_info() -> tuple[Optional[str], Optional[Path]]:
    """
    Detect caller module and determine JSON folder location
    Based on old openai_skill pattern for dynamic caller detection
    
    Returns:
        tuple[Optional[str], Optional[Path]]: (caller_name, json_folder_path) or (None, None) if detection fails
    """
    import inspect
    
    try:
        # Get stack frames to find caller
        stack = inspect.stack()
        
        for frame_info in stack[1:]:  # Skip current frame
            frame_path = Path(frame_info.filename)
            
            # Check for flow modules
            if "flow" in frame_path.parts:
                flow_index = frame_path.parts.index("flow")
                flow_path = Path(*frame_path.parts[:flow_index + 1])
                json_folder_path = flow_path / "flow_json"
                
                # Extract caller name from filename (e.g., flow_mbank.py -> flow_mbank)
                caller_name = frame_path.stem
                
                logger.info(f"[{MODULE_NAME}] Detected flow caller: {caller_name}")
                return caller_name, json_folder_path
            
            # Check for prax modules
            elif "prax" in frame_path.parts:
                prax_index = frame_path.parts.index("prax")
                prax_path = Path(*frame_path.parts[:prax_index + 1])
                json_folder_path = prax_path / "prax_json"
                
                caller_name = frame_path.stem
                logger.info(f"[{MODULE_NAME}] Detected prax caller: {caller_name}")
                return caller_name, json_folder_path
            
            # Check for skills modules
            elif any("skills" in part for part in frame_path.parts):
                # Find skills directory
                for i, part in enumerate(frame_path.parts):
                    if "skills" in part:
                        skills_path = Path(*frame_path.parts[:i + 2])  # Include skills_category
                        # Determine JSON folder based on category
                        category = frame_path.parts[i + 1] if i + 1 < len(frame_path.parts) else "skills_api"
                        json_folder_path = skills_path / f"{category}_json"
                        
                        caller_name = frame_path.stem
                        logger.info(f"[{MODULE_NAME}] Detected skills caller: {caller_name}")
                        return caller_name, json_folder_path
                        
        # No caller detected
        logger.warning(f"[{MODULE_NAME}] Could not detect caller from stack trace")
        return None, None
        
    except Exception as e:
        logger.error(f"[{MODULE_NAME}] Caller detection failed: {e}")
        return None, None

def ensure_caller_api_config(caller_name: str, json_folder_path: Path) -> bool:
    """
    Create API config for caller if it doesn't exist
    Creates openrouter_skill_config.json in caller's JSON folder
    
    Args:
        caller_name: Name of calling module
        json_folder_path: Path to caller's JSON folder
        
    Returns:
        bool: True if config was created, False if already exists or error
    """
    try:
        # API config file - separate from module's main config
        api_config_file = json_folder_path / "openrouter_skill_config.json"
        
        if not api_config_file.exists():
            # Create API-specific config with universal template
            api_config = {
                "skill_name": "openrouter",
                "timestamp": datetime.now().isoformat(),
                "config": {
                    "ai_model": DEFAULT_MODEL,
                    "ai_temperature": 0.5,
                    "ai_max_tokens": 1500,
                    "enabled": True
                }
            }
            
            # Ensure JSON folder exists
            json_folder_path.mkdir(parents=True, exist_ok=True)
            
            # Create the API config file
            with open(api_config_file, 'w', encoding='utf-8') as f:
                json.dump(api_config, f, indent=2, ensure_ascii=False)
            
            logger.info(f"[{MODULE_NAME}] Created API config for {caller_name} at {api_config_file}")
            
            # Also create API-specific data and log files
            api_data_file = json_folder_path / "openrouter_skill_data.json"
            api_log_file = json_folder_path / "openrouter_skill_log.json"
            
            # Data file tracks API usage for this caller
            if not api_data_file.exists():
                api_data = {
                    "skill_name": "openrouter",
                    "timestamp": datetime.now().isoformat(),
                    "data": {
                        "total_requests": 0,
                        "successful_requests": 0,
                        "failed_requests": 0,
                        "models_used": {},
                        "last_request": None
                    }
                }
                with open(api_data_file, 'w', encoding='utf-8') as f:
                    json.dump(api_data, f, indent=2, ensure_ascii=False)
            
            # Log file tracks API calls for this caller
            if not api_log_file.exists():
                api_log = {
                    "skill_name": "openrouter",
                    "timestamp": datetime.now().isoformat(),
                    "logs": []
                }
                with open(api_log_file, 'w', encoding='utf-8') as f:
                    json.dump(api_log, f, indent=2, ensure_ascii=False)
            
            # Log the provisioning operation to openrouter's own logs
            log_operation("config_provisioned", True, 
                        f"Created API config for {caller_name} at {json_folder_path}")
            
            return True
        else:
            # Config already exists, no action needed
            return False
            
    except Exception as e:
        logger.error(f"[{MODULE_NAME}] Failed to provision API config for {caller_name}: {e}")
        log_operation("config_provisioning", False, error=str(e))
        return False

# =============================================
# UTILITY FUNCTIONS
# =============================================

def log_operation(operation: str, success: bool, result: Optional[str] = None, error: Optional[str] = None, correlation_id: Optional[str] = None):
    """Log operation to both JSON logs (Tier 1) and system logs (Tier 2)"""
    try:
        # Tier 1: JSON Logs - Critical operations tracking
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "operation": operation,
            "success": success,
            "details": {
                "result": result,
                "error": error
            },
            "correlation_id": correlation_id
        }
        _append_to_json_log(log_entry)
        
        # Tier 2: System Logs - Debug/technical info
        if success:
            logger.info(f"{MODULE_NAME}: {operation} - {result or 'completed successfully'}")
        else:
            logger.error(f"{MODULE_NAME}: {operation} - {error or 'failed'}")
            
    except Exception as e:
        # Tier 3: Console Output - Clean user feedback
        print(f"[{MODULE_NAME}] Log error: {e}")

def _append_to_json_log(log_entry: dict):
    """Append entry to JSON log file with sequential IDs and newest-first ordering"""
    try:
        log_path = API_JSON_DIR / LOG_FILE
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing log or create new structure
        if log_path.exists():
            with open(log_path, 'r', encoding='utf-8') as f:
                log_data = json.load(f)
        else:
            log_data = {
                "module_name": MODULE_NAME,
                "timestamp": datetime.now().isoformat(),
                "log": {},
                "summary": {"total_entries": 0, "next_id": 1}
            }
        
        # Get next sequential ID
        next_id = log_data["summary"]["next_id"]
        entry_key = f"entry_{next_id:03d}"
        
        # Add ID to log entry
        log_entry["id"] = next_id
        
        # Create new log dict with newest entry first, then existing entries
        new_log = {entry_key: log_entry, **log_data["log"]}
        
        # Update log data structure
        log_data["log"] = new_log
        log_data["timestamp"] = datetime.now().isoformat()
        log_data["summary"]["total_entries"] = len(new_log)
        log_data["summary"]["next_id"] = next_id + 1
        log_data["summary"]["last_entry"] = log_entry["timestamp"]
        
        # Save updated log
        with open(log_path, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)
            
    except Exception as e:
        logger.error(f"[{MODULE_NAME}] Failed to append to JSON log: {e}")

def save_module_data(data_content: dict) -> bool:
    """Save data to module data file"""
    data = {
        "module_name": MODULE_NAME,
        "timestamp": datetime.now().isoformat(),
        "data": data_content
    }
    
    try:
        data_path = API_JSON_DIR / DATA_FILE
        data_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(data_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        log_operation("Data save failed", False, error=str(e))
        return False

def load_module_data() -> Dict:
    """Load data from module data file"""
    try:
        data_path = API_JSON_DIR / DATA_FILE
        if not data_path.exists():
            # Create initial data file
            initial_data = {
                "total_requests": 0,
                "successful_requests": 0,
                "failed_requests": 0,
                "models_used": {},
                "callers": {},
                "last_request": None
            }
            save_module_data(initial_data)
            return initial_data
        
        with open(data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get("data", {})
    except Exception as e:
        log_operation("Data load failed", False, error=str(e))
        return {}

def load_config() -> Dict:
    """Load module configuration"""
    config_path = API_JSON_DIR / CONFIG_FILE
    
    # Default config
    default_config = {
        "module_name": MODULE_NAME,
        "timestamp": datetime.now().isoformat(),
        "config": {
            "enabled": True,
            "base_url": OPENROUTER_BASE_URL,
            "default_model": DEFAULT_MODEL,
            "timeout_seconds": DEFAULT_TIMEOUT,
            "auto_track_usage": True,
            "retry_on_failure": False,
            "log_requests": True,
            "log_responses": False  # Disable by default for privacy
        }
    }
    
    try:
        if not config_path.exists():
            config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)
            log_operation("Config file created", True, str(config_path))
            return default_config
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config
    except Exception as e:
        log_operation("Config load failed", False, error=str(e))
        return default_config

def update_request_stats(caller: str, model: str, success: bool) -> None:
    """Update request statistics - both global and local module stats"""
    try:
        # Update global stats (existing logic)
        data = load_module_data()
        
        # Update totals
        data["total_requests"] += 1
        if success:
            data["successful_requests"] += 1
        else:
            data["failed_requests"] += 1
        
        # Update model usage
        if model not in data["models_used"]:
            data["models_used"][model] = 0
        data["models_used"][model] += 1
        
        # Update caller stats
        if caller not in data["callers"]:
            data["callers"][caller] = {"requests": 0, "successes": 0, "failures": 0}
        
        data["callers"][caller]["requests"] += 1
        if success:
            data["callers"][caller]["successes"] += 1
        else:
            data["callers"][caller]["failures"] += 1
        
        data["last_request"] = datetime.now().isoformat()
        
        save_module_data(data)
        
        # NEW: Update local module stats
        _update_local_module_stats(caller, model, success)
        
    except Exception as e:
        log_operation("Update stats failed", False, error=str(e))


def _update_local_module_stats(caller: str, model: str, success: bool) -> None:
    """Update local module's openrouter_skill_data.json file"""
    try:
        # Get caller's JSON folder path
        caller_name, json_folder = get_caller_info()
        
        if not caller_name or not json_folder:
            # Fallback: try to construct path from caller name
            possible_paths = [
                Path("flow") / "flow_json",
                Path("skills") / f"skills_{caller}" / f"{caller}_json",
                Path(f"{caller}") / f"{caller}_json"
            ]
            
            json_folder = None
            for path in possible_paths:
                if path.exists():
                    json_folder = path
                    break
            
            if not json_folder:
                logger.warning(f"[{MODULE_NAME}] Could not find JSON folder for caller '{caller}' - skipping local stats update")
                return
        
        # Path to local data file
        local_data_file = json_folder / "openrouter_skill_data.json"
        
        if not local_data_file.exists():
            logger.warning(f"[{MODULE_NAME}] Local data file not found for {caller}: {local_data_file}")
            return
        
        # Load local data
        with open(local_data_file, 'r', encoding='utf-8') as f:
            local_data = json.load(f)
        
        # Update local stats (same logic as global)
        stats = local_data["data"]
        
        # Update totals
        stats["total_requests"] += 1
        if success:
            stats["successful_requests"] += 1
        else:
            stats["failed_requests"] += 1
        
        # Update model usage
        if "models_used" not in stats:
            stats["models_used"] = {}
        if model not in stats["models_used"]:
            stats["models_used"][model] = 0
        stats["models_used"][model] += 1
        
        stats["last_request"] = datetime.now().isoformat()
        local_data["timestamp"] = datetime.now().isoformat()
        
        # Save updated local data
        with open(local_data_file, 'w', encoding='utf-8') as f:
            json.dump(local_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"[{MODULE_NAME}] Updated local stats for {caller} at {local_data_file}")
        
    except Exception as e:
        logger.error(f"[{MODULE_NAME}] Failed to update local stats for {caller}: {e}")
        # Don't re-raise - local stats failure shouldn't break the main request

# =============================================
# MAIN MODULE CLASSES
# =============================================

class OpenRouterClient:
    """
    OpenRouter client using OpenAI SDK - AIPass standards compliant
    - Uses OpenRouter base URL with OpenAI SDK
    - Handles all 323 available models
    - Connection pooling for performance
    - Proper error handling and logging
    - Returns response or explicit error
    """
    
    def __init__(self):
        self.api_connect = APIConnect()
        self.config = load_config()
        self.enabled = self.config.get("config", {}).get("enabled", True)
        self.base_url = self.config.get("config", {}).get("base_url", OPENROUTER_BASE_URL)
        self.timeout = self.config.get("config", {}).get("timeout_seconds", DEFAULT_TIMEOUT)
        self.auto_track = self.config.get("config", {}).get("auto_track_usage", True)
        
        # Connection pooling
        self._client_cache = {}
        self._last_api_key = None
        
        if not OPENAI_AVAILABLE:
            logger.error(f"[{MODULE_NAME}] OpenAI SDK not available - client disabled")
            self.enabled = False
        
        if not self.enabled:
            logger.warning(f"[{MODULE_NAME}] OpenRouter client is disabled")
    
    def get_response(self, messages: List[Dict], model: Optional[str] = None, caller: Optional[str] = None, **kwargs) -> Optional[str]:
        """
        Get AI response via OpenRouter with full tracking
        
        Args:
            messages (List[Dict]): OpenAI format messages
            model (str): Model to use (default from config)
            caller (str): Module making the request for tracking
            **kwargs: Additional parameters for OpenAI API
            
        Returns:
            str: AI response content or None on failure
        """
        if not self.enabled:
            log_operation("Request blocked", False, "OpenRouter client disabled")
            return None
        
        # Step 1: Detect caller if not provided and get folder path
        json_folder = None
        if not caller:
            detected_caller, json_folder = get_caller_info()
            if detected_caller:
                caller = detected_caller
                logger.info(f"[{MODULE_NAME}] Auto-detected caller: {caller}")
        
        # Step 2: Ensure caller has API config (auto-create if missing)
        if caller:
            # Get folder path if not already detected
            if not json_folder:
                caller_name, json_folder = get_caller_info()
            else:
                caller_name = caller
            if json_folder and caller_name:
                config_created = ensure_caller_api_config(caller_name, json_folder)
                if config_created:
                    # Config was just created, caller needs to reload and retry
                    error_msg = f"API config created for {caller}. Please reload config and retry."
                    log_operation("Request blocked", False, error_msg)
                    logger.info(f"[{MODULE_NAME}] {error_msg}")
                    return None  # Return None to maintain API contract
        
        # Step 3: Validate required parameters
        if not model:
            error_msg = f"Caller '{caller}' must specify a model from their API config"
            log_operation("Request failed", False, error_msg)
            return None
        
        if not caller:
            error_msg = "Caller identification required for tracking"
            log_operation("Request failed", False, error_msg)
            return None
        
        try:
            # Get and validate API key
            api_key = self.api_connect.get_api_key("openrouter")
            if not api_key:
                log_operation("Request failed", False, f"{caller} - No valid API key")
                update_request_stats(caller, model, False)
                return None
            
            # Get or create cached OpenAI client
            client = self._get_cached_client(api_key)
            
            # Log the request
            if self.config.get("config", {}).get("log_requests", True):
                logger.info(f"[{MODULE_NAME}] API request: {caller} using {model}")
            
            # Prepare API call parameters
            api_params = {
                "model": model,
                "messages": messages,
                **kwargs  # Allow additional parameters
            }
            
            # Make the request
            response = client.chat.completions.create(**api_params)
            
            # Extract response content
            if response and response.choices and len(response.choices) > 0:
                content = response.choices[0].message.content
                
                # Track REAL usage via generation_id
                if self.auto_track and response.id:
                    try:
                        track_usage(caller, response.id, model, api_key)
                    except Exception as track_error:
                        logger.warning(f"[{MODULE_NAME}] Usage tracking failed: {track_error}")
                
                # Update statistics
                update_request_stats(caller, model, True)
                
                # Log success
                response_preview = content[:100] + "..." if len(content) > 100 else content
                log_operation("Request successful", True, f"{caller} - {len(content)} chars")
                
                if self.config.get("config", {}).get("log_responses", False):
                    logger.info(f"[{MODULE_NAME}] Response preview: {response_preview}")
                
                return content
            else:
                # No valid response content
                log_operation("Request failed", False, f"{caller} - Empty response")
                update_request_stats(caller, model, False)
                return None
                
        except Exception as e:
            # Log error with full context
            error_msg = f"{caller} using {model} - {str(e)}"
            log_operation("Request failed", False, error_msg)
            update_request_stats(caller, model, False)
            logger.error(f"[{MODULE_NAME}] API request error: {error_msg}")
            return None  # Explicit failure, no retry loops!
    
    def _get_cached_client(self, api_key: str) -> 'OpenAI':
        """Get cached OpenAI client or create new one"""
        try:
            # Check if we have a cached client for this API key
            if api_key in self._client_cache:
                # Verify the cached client is still valid
                cached_client = self._client_cache[api_key]
                if cached_client and cached_client.api_key == api_key:
                    return cached_client
            
            # Create new client and cache it
            from openai import OpenAI
            client = OpenAI(
                base_url=self.base_url,
                api_key=api_key,
                timeout=self.timeout
            )
            
            # Cache the client (limit cache size to prevent memory growth)
            if len(self._client_cache) >= 5:  # Max 5 cached clients
                # Remove oldest client
                oldest_key = next(iter(self._client_cache))
                del self._client_cache[oldest_key]
            
            self._client_cache[api_key] = client
            self._last_api_key = api_key
            
            logger.info(f"[{MODULE_NAME}] Created new cached OpenAI client")
            return client
            
        except Exception as e:
            logger.error(f"[{MODULE_NAME}] Failed to create cached client: {e}")
            # Fallback to direct creation without caching
            from openai import OpenAI
            return OpenAI(
                base_url=self.base_url,
                api_key=api_key,
                timeout=self.timeout
            )
    
    def test_connection(self) -> bool:
        """Test OpenRouter connection with a simple request"""
        try:
            test_messages = [{"role": "user", "content": "Hi"}]
            test_model = self.config.get("config", {}).get("default_model", DEFAULT_MODEL)
            response = self.get_response(test_messages, model=test_model, caller="connection_test")
            
            if response:
                log_operation("Connection test", True, "OpenRouter accessible")
                return True
            else:
                log_operation("Connection test", False, "No response received")
                return False
                
        except Exception as e:
            log_operation("Connection test", False, error=str(e))
            return False
    
    def get_stats(self) -> Dict:
        """Get client statistics"""
        try:
            return load_module_data()
        except Exception as e:
            log_operation("Get stats failed", False, error=str(e))
            return {}

# =============================================
# MODULE-LEVEL FUNCTIONS
# =============================================

# Create global client instance with thread safety
_client = None
_client_lock = None

def _get_client_lock():
    """Get or create thread lock for client access"""
    global _client_lock
    if _client_lock is None:
        import threading
        _client_lock = threading.RLock()
    return _client_lock

def get_response(messages: List[Dict], model: Optional[str] = None, caller: Optional[str] = None, **kwargs) -> Optional[str]:
    """
    Get AI response via OpenRouter (module-level function for easy imports)
    
    Args:
        messages (List[Dict]): OpenAI format messages
        model (str): Model to use (optional)
        caller (str): Module making the request (recommended for tracking)
        **kwargs: Additional OpenAI API parameters
        
    Returns:
        str: AI response content or None on failure
    """
    global _client
    with _get_client_lock():
        if not _client:
            _client = OpenRouterClient()
    return _client.get_response(messages, model, caller, **kwargs)

def test_connection() -> bool:
    """Test OpenRouter connection"""
    global _client
    with _get_client_lock():
        if not _client:
            _client = OpenRouterClient()
    return _client.test_connection()

def get_available_models() -> Optional[List[str]]:
    """
    Get list of available models from OpenRouter API
    
    Returns:
        Optional[List[str]]: List of available model names or None on failure
    """
    try:
        models = _fetch_models_from_api()
        if models:
            return models
        
        # Explicit failure - no fallbacks
        log_operation("Get available models failed", False, "OpenRouter API not accessible")
        return None
        
    except Exception as e:
        log_operation("Get available models failed", False, error=str(e))
        return None

def _fetch_models_from_api() -> Optional[List[str]]:
    """Fetch models from OpenRouter /models endpoint"""
    try:
        api_connect = APIConnect()
        api_key = api_connect.get_api_key("openrouter")
        
        if not api_key:
            log_operation("Models fetch failed", False, "No API key available")
            return None
        
        import requests
        
        models_endpoint = f"{OPENROUTER_BASE_URL}/models"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(models_endpoint, headers=headers, timeout=10)
        response.raise_for_status()
        
        models_data = response.json()
        
        # Extract model IDs from response
        if "data" in models_data:
            model_list = [model["id"] for model in models_data["data"] if "id" in model]
            log_operation("Models fetched", True, f"{len(model_list)} models from OpenRouter API")
            return model_list
        
        log_operation("Models fetch failed", False, "Invalid response format from OpenRouter")
        return None
        
    except Exception as e:
        log_operation("Models fetch failed", False, error=str(e))
        return None

def get_stats() -> Dict:
    """Get client statistics"""
    global _client
    with _get_client_lock():
        if not _client:
            _client = OpenRouterClient()
    return _client.get_stats()

# =============================================
# INITIALIZATION
# =============================================

def initialize_module():
    """Initialize openrouter module and perform startup tasks"""
    try:
        logger.info(f"[{MODULE_NAME}] Initializing OpenRouter Client v{MODULE_VERSION}")
        
        # Check OpenAI SDK availability
        if not OPENAI_AVAILABLE:
            logger.error(f"[{MODULE_NAME}] OpenAI SDK not installed - run: pip install openai")
            log_operation("Initialization failed", False, "OpenAI SDK missing")
            return False
        
        # Load configuration
        config = load_config()
        logger.info(f"[{MODULE_NAME}] Configuration loaded")
        
        # Load module data
        data = load_module_data()
        total_requests = data.get("total_requests", 0)
        success_rate = 0
        if total_requests > 0:
            success_rate = (data.get("successful_requests", 0) / total_requests) * 100
        logger.info(f"[{MODULE_NAME}] Data loaded - {total_requests} requests, {success_rate:.1f}% success rate")
        
        
        # Initialize client
        global _client
        _client = OpenRouterClient()
        
        # Test connection if enabled
        if config.get("config", {}).get("test_on_init", False):
            if _client.enabled:
                if test_connection():
                    logger.info(f"[{MODULE_NAME}] Connection test successful")
                else:
                    logger.warning(f"[{MODULE_NAME}] Connection test failed")
        
        logger.info(f"[{MODULE_NAME}] Module initialization completed successfully")
        log_operation("Module initialized", True, f"Version {MODULE_VERSION}")
        return True
    except Exception as e:
        logger.error(f"[{MODULE_NAME}] Module initialization failed: {e}")
        log_operation("Initialization failed", False, error=str(e))
        return False

# Initialize on import
initialize_module()

def main():
    """CLI entry point for openrouter module"""
    parser = argparse.ArgumentParser(
        description='OpenRouter Client - Unified AI API Gateway',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
COMMANDS:
  Commands: test, stats, models, info

  test    - Test OpenRouter connection
  stats   - Display usage statistics
  models  - List available models
  info    - Show module information

EXAMPLES:
  python3 openrouter.py test
  python3 openrouter.py stats
  python3 openrouter.py models
  python3 openrouter.py info
        """
    )
    
    parser.add_argument('command',
                       nargs='?',
                       choices=['test', 'stats', 'models', 'info'],
                       help='Command to execute')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 0
    
    try:
        if args.command == 'test':
            print(f"Testing OpenRouter connection...")
            result = test_connection()
            if result:
                print("✅ Connection test successful")
                return 0
            else:
                print("❌ Connection test failed")
                return 1
        
        elif args.command == 'stats':
            print(f"OpenRouter Usage Statistics:")
            stats = get_stats()
            print(f"  Total Requests: {stats.get('total_requests', 0)}")
            print(f"  Successful: {stats.get('successful_requests', 0)}")
            print(f"  Failed: {stats.get('failed_requests', 0)}")
            print(f"  Models Used: {len(stats.get('models_used', {}))}")
            print(f"  Callers: {len(stats.get('callers', {}))}")
            return 0
        
        elif args.command == 'models':
            print(f"Fetching available models...")
            models = get_available_models()
            if models:
                print(f"✅ Available models: {len(models)}")
                for model in models[:10]:
                    print(f"  - {model}")
                if len(models) > 10:
                    print(f"  ... and {len(models) - 10} more")
                return 0
            else:
                print("❌ Failed to fetch models")
                return 1
        
        elif args.command == 'info':
            print(f"OpenRouter Module Information:")
            print(f"  Module Name: {MODULE_NAME}")
            print(f"  Version: {MODULE_VERSION}")
            print(f"  Category: {MODULE_CATEGORY}")
            print(f"  Base URL: {OPENROUTER_BASE_URL}")
            config = load_config()
            print(f"  Enabled: {config.get('config', {}).get('enabled', True)}")
            print(f"  Default Model: {config.get('config', {}).get('default_model', DEFAULT_MODEL)}")
            return 0
        
        else:
            print(f"Unknown command: {args.command}")
            parser.print_help()
            return 1
    
    except Exception as e:
        print(f"❌ Error executing command: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())