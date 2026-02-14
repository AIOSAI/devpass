#!/usr/bin/env python3

# =============================================
# META DATA HEADER
# Name: api_usage.py
# Date: 2025-08-30
# Version: 1.0.0
# Category: api
# 
# CHANGELOG:
#   - v1.0.0 (2025-08-30): Initial real usage tracking from OpenRouter
# =============================================

"""
API Usage Monitor with Real OpenRouter Tracking
Following AIPass standards: 3-JSON pattern, prax logging, proper error handling

- Real usage tracking from OpenRouter's /generation endpoint
- Per-caller breakdown of costs, tokens, and usage
- No fake estimates - only actual API data
- Replaces prax/prax_api_usage_monitor.py with accurate tracking

Features:
- Real-time usage tracking via generation_id
- Per-module cost breakdown
- Daily/monthly aggregation
- OpenRouter generation endpoint integration
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
import requests
import time
import argparse
from datetime import datetime, timedelta
from typing import Dict, Optional

# =============================================
# CONFIGURATION SECTION
# =============================================

MODULE_NAME = "api_usage"
MODULE_VERSION = "1.0.0"
MODULE_CATEGORY = "api"

# Standard 3-file JSON structure
CONFIG_FILE = f"{MODULE_NAME}_config.json"
DATA_FILE = f"{MODULE_NAME}_data.json"
LOG_FILE = f"{MODULE_NAME}_log.json"

# Module JSON directory (absolute path)
API_JSON_DIR = API_ROOT / "api_json"

# OpenRouter endpoints
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
GENERATION_ENDPOINT = f"{OPENROUTER_BASE_URL}/generation"
CREDITS_ENDPOINT = f"{OPENROUTER_BASE_URL}/auth/key"

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

def save_module_data(data_content: dict):
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

def load_module_data() -> dict:
    """Load data from module data file"""
    try:
        data_path = API_JSON_DIR / DATA_FILE
        if not data_path.exists():
            # Create initial data file
            initial_data = {
                "current_session": {
                    "start_time": datetime.now().isoformat(),
                    "total_requests": 0,
                    "total_cost": 0.0,
                    "total_tokens": 0
                },
                "usage_by_caller": {},
                "daily_totals": {},
                "monthly_totals": {},
                "generation_tracking": {}
            }
            save_module_data(initial_data)
            return initial_data
        
        with open(data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get("data", {})
    except Exception as e:
        log_operation("Data load failed", False, error=str(e))
        return {}

def load_config() -> dict:
    """Load module configuration"""
    config_path = API_JSON_DIR / CONFIG_FILE
    
    # Default config
    default_config = {
        "module_name": MODULE_NAME,
        "timestamp": datetime.now().isoformat(),
        "config": {
            "enabled": True,
            "auto_track": True,
            "max_retry_attempts": 3,
            "retry_delay_seconds": 1,
            "generation_check_delay": 2,
            "cleanup_old_data_days": 30,
            "detailed_logging": True
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

# =============================================
# MAIN MODULE CLASSES
# =============================================

class APIUsageTracker:
    """
    Track REAL API usage per module from OpenRouter generation endpoint
    - Store generation_id from each request
    - Query OpenRouter's /generation endpoint for exact metrics
    - Log: caller, model, actual tokens, real cost, generation time
    - No fake estimates or token counting libraries!
    """
    
    def __init__(self):
        self.data_path = API_JSON_DIR / DATA_FILE
        self.config = load_config()
        self.enabled = self.config.get("config", {}).get("enabled", True)
        
        if not self.enabled:
            logger.warning(f"[{MODULE_NAME}] Usage tracking is disabled in config")
    
    def track_usage(self, caller: str, generation_id: str, model: str, api_key: Optional[str] = None):
        """
        Get REAL metrics from OpenRouter and log them
        
        Args:
            caller (str): Module that made the API call (e.g., "flow_mbank")
            generation_id (str): OpenRouter generation ID from response
            model (str): Model used for the request
            api_key (str): OpenRouter API key for authentication
        """
        if not self.enabled:
            return
            
        try:
            logger.info(f"[{MODULE_NAME}] Tracking usage for {caller} - generation: {generation_id}")
            
            # Get API key if not provided
            if not api_key:
                from api.apps.api_connect import get_api_key
                api_key = get_api_key("openrouter")
                
            if not api_key:
                log_operation("Usage tracking failed", False, error="No API key available")
                return
            
            # Wait a moment for OpenRouter to process the generation
            time.sleep(self.config.get("config", {}).get("generation_check_delay", 2))
            
            # Query OpenRouter's generation endpoint for real metrics
            usage_data = self._get_generation_metrics(generation_id, api_key)
            
            if usage_data:
                # Store and aggregate the usage data
                self._store_usage_data(caller, model, generation_id, usage_data)
                log_operation("Usage tracked", True, f"Caller: {caller}, Cost: ${usage_data.get('total_cost', 0)}")
            else:
                log_operation("Usage tracking incomplete", False, "Failed to retrieve generation metrics")
                
        except Exception as e:
            log_operation("Usage tracking failed", False, error=str(e))
    
    def _get_generation_metrics(self, generation_id: str, api_key: str) -> Optional[Dict]:
        """Query OpenRouter's /generation endpoint for real metrics"""
        try:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            # Query the generation endpoint
            response = requests.get(
                f"{GENERATION_ENDPOINT}?id={generation_id}",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if data and "data" in data:
                    metrics = data["data"]
                    logger.info(f"[{MODULE_NAME}] Retrieved real metrics for generation {generation_id}")
                    return {
                        "total_cost": float(metrics.get("total_cost", 0)),
                        "tokens_prompt": int(metrics.get("tokens_prompt", 0)),
                        "tokens_completion": int(metrics.get("tokens_completion", 0)),
                        "generation_time": int(metrics.get("generation_time", 0)),
                        "latency": int(metrics.get("latency", 0)),
                        "provider_name": metrics.get("provider_name", "unknown")
                    }
            
            logger.warning(f"[{MODULE_NAME}] Failed to get generation metrics: {response.status_code}")
            return None
            
        except Exception as e:
            logger.error(f"[{MODULE_NAME}] Error getting generation metrics: {e}")
            return None
    
    def _store_usage_data(self, caller: str, model: str, generation_id: str, usage_data: Dict):
        """Store usage data with proper aggregation"""
        try:
            # Load current data
            current_data = load_module_data()
            
            # Update session totals
            current_data["current_session"]["total_requests"] += 1
            current_data["current_session"]["total_cost"] += usage_data["total_cost"]
            current_data["current_session"]["total_tokens"] += (
                usage_data["tokens_prompt"] + usage_data["tokens_completion"]
            )
            
            # Update per-caller tracking
            if caller not in current_data["usage_by_caller"]:
                current_data["usage_by_caller"][caller] = {
                    "requests": 0,
                    "total_cost": 0.0,
                    "total_tokens": 0,
                    "models_used": {},
                    "last_request": None
                }
            
            caller_data = current_data["usage_by_caller"][caller]
            caller_data["requests"] += 1
            caller_data["total_cost"] += usage_data["total_cost"]
            caller_data["total_tokens"] += usage_data["tokens_prompt"] + usage_data["tokens_completion"]
            caller_data["last_request"] = datetime.now().isoformat()
            
            # Track models used by caller
            if model not in caller_data["models_used"]:
                caller_data["models_used"][model] = 0
            caller_data["models_used"][model] += 1
            
            # Update daily totals
            today = datetime.now().date().isoformat()
            if today not in current_data["daily_totals"]:
                current_data["daily_totals"][today] = {"requests": 0, "cost": 0.0, "tokens": 0}
            
            current_data["daily_totals"][today]["requests"] += 1
            current_data["daily_totals"][today]["cost"] += usage_data["total_cost"]
            current_data["daily_totals"][today]["tokens"] += usage_data["tokens_prompt"] + usage_data["tokens_completion"]
            
            # Store generation details at the TOP (newest first)
            new_entry = {
                "timestamp": datetime.now().isoformat(),
                "caller": caller,
                "model": model,
                "usage_data": usage_data
            }
            
            # Create new dict with new entry first, then existing entries
            current_tracking = current_data["generation_tracking"]
            current_data["generation_tracking"] = {generation_id: new_entry, **current_tracking}
            
            # Save updated data
            save_module_data(current_data)
            
            logger.info(f"[{MODULE_NAME}] Stored usage data for {caller}: ${usage_data['total_cost']:.6f}")
            
        except Exception as e:
            log_operation("Store usage data failed", False, error=str(e))
    
    def get_caller_usage(self, caller: str) -> Dict:
        """Get usage statistics for specific caller"""
        try:
            data = load_module_data()
            return data.get("usage_by_caller", {}).get(caller, {})
        except Exception as e:
            log_operation("Get caller usage failed", False, error=str(e))
            return {}
    
    def get_session_summary(self) -> Dict:
        """Get current session usage summary"""
        try:
            data = load_module_data()
            return data.get("current_session", {})
        except Exception as e:
            log_operation("Get session summary failed", False, error=str(e))
            return {}
    
    def get_daily_usage(self, date: Optional[str] = None) -> Dict:
        """Get daily usage statistics"""
        try:
            data = load_module_data()
            if not date:
                date = datetime.now().date().isoformat()
            return data.get("daily_totals", {}).get(date, {})
        except Exception as e:
            log_operation("Get daily usage failed", False, error=str(e))
            return {}
    
    def cleanup_old_data(self, days: Optional[int] = None):
        """Clean up old generation tracking data"""
        try:
            if days is None:
                days = int(self.config.get("config", {}).get("cleanup_old_data_days", 30))
            
            cutoff_date = datetime.now() - timedelta(days=days)
            data = load_module_data()
            
            # Clean old generation tracking
            old_generations = []
            for gen_id, gen_data in data.get("generation_tracking", {}).items():
                try:
                    gen_date = datetime.fromisoformat(gen_data["timestamp"])
                    if gen_date < cutoff_date:
                        old_generations.append(gen_id)
                except:
                    # Remove invalid entries
                    old_generations.append(gen_id)
            
            for gen_id in old_generations:
                del data["generation_tracking"][gen_id]
            
            save_module_data(data)
            log_operation("Cleanup completed", True, f"Removed {len(old_generations)} old entries")
            
        except Exception as e:
            log_operation("Cleanup failed", False, error=str(e))

# =============================================
# MODULE-LEVEL FUNCTIONS
# =============================================

# Create global tracker instance
_tracker = None

def track_usage(caller: str, generation_id: str, model: str, api_key: Optional[str] = None):
    """
    Track API usage (module-level function for easy imports)
    
    Args:
        caller (str): Module that made the API call
        generation_id (str): OpenRouter generation ID
        model (str): Model used
        api_key (str): API key (optional)
    """
    global _tracker
    if not _tracker:
        _tracker = APIUsageTracker()
    _tracker.track_usage(caller, generation_id, model, api_key)

def get_caller_usage(caller: str) -> Dict:
    """Get usage statistics for specific caller"""
    global _tracker
    if not _tracker:
        _tracker = APIUsageTracker()
    return _tracker.get_caller_usage(caller)

def get_session_summary() -> Dict:
    """Get current session usage summary"""
    global _tracker
    if not _tracker:
        _tracker = APIUsageTracker()
    return _tracker.get_session_summary()

# =============================================
# INITIALIZATION
# =============================================

def initialize_module():
    """Initialize api_usage module and perform startup tasks"""
    try:
        logger.info(f"[{MODULE_NAME}] Initializing API Usage Tracker v{MODULE_VERSION}")
        
        # Load configuration
        config = load_config()
        logger.info(f"[{MODULE_NAME}] Configuration loaded")
        
        # Load module data
        data = load_module_data()
        total_requests = data.get("current_session", {}).get("total_requests", 0)
        total_cost = data.get("current_session", {}).get("total_cost", 0.0)
        logger.info(f"[{MODULE_NAME}] Session data loaded - {total_requests} requests, ${total_cost:.6f}")
        
        # Initialize tracker
        global _tracker
        _tracker = APIUsageTracker()
        
        # Cleanup old data if needed
        if config.get("config", {}).get("auto_cleanup", True):
            _tracker.cleanup_old_data()
        
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
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description='API Usage Monitor - Track real API usage from OpenRouter',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
COMMANDS:
  Commands: track, session-summary, caller-usage, daily-usage, cleanup, status, --caller, --generation-id, --model, --api-key, --date, --days

USAGE MODES:
  track              - Track API usage with generation ID
  session-summary    - Get current session usage summary
  caller-usage       - Get usage statistics for specific caller
  daily-usage        - Get daily usage statistics
  cleanup            - Clean up old generation tracking data
  status             - Show module status and configuration

OPTIONAL FLAGS:
  --caller           - Caller module name (for track and caller-usage)
  --generation-id    - OpenRouter generation ID (for track)
  --model            - Model name (for track)
  --api-key          - OpenRouter API key (optional, uses system config if not provided)
  --date             - Date for daily usage (YYYY-MM-DD format, default: today)
  --days             - Days to retain for cleanup (default: 30)

EXAMPLES:
  python3 api_usage.py track --caller mymodule --generation-id gen_123 --model gpt-4
  python3 api_usage.py session-summary
  python3 api_usage.py caller-usage --caller mymodule
  python3 api_usage.py daily-usage
  python3 api_usage.py daily-usage --date 2025-08-30
  python3 api_usage.py cleanup --days 30
  python3 api_usage.py status
        """
    )

    parser.add_argument('command',
                       nargs='?',
                       choices=['track', 'session-summary', 'caller-usage', 'daily-usage', 'cleanup', 'status'],
                       help='Command to execute')
    
    parser.add_argument('--caller', type=str, help='Caller module name')
    parser.add_argument('--generation-id', type=str, help='OpenRouter generation ID')
    parser.add_argument('--model', type=str, help='Model name')
    parser.add_argument('--api-key', type=str, help='OpenRouter API key')
    parser.add_argument('--date', type=str, help='Date for daily usage (YYYY-MM-DD)')
    parser.add_argument('--days', type=int, default=30, help='Days to retain for cleanup')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    try:
        global _tracker
        if not _tracker:
            _tracker = APIUsageTracker()

        if args.command == 'track':
            if not args.caller or not args.generation_id or not args.model:
                print("Error: track command requires --caller, --generation-id, and --model")
                return 1
            _tracker.track_usage(args.caller, args.generation_id, args.model, args.api_key)
            print(f"✅ Tracked usage for {args.caller}")
            return 0

        elif args.command == 'session-summary':
            summary = _tracker.get_session_summary()
            print("\nSession Summary:")
            print(f"  Total Requests: {summary.get('total_requests', 0)}")
            print(f"  Total Cost: ${summary.get('total_cost', 0.0):.6f}")
            print(f"  Total Tokens: {summary.get('total_tokens', 0)}")
            return 0

        elif args.command == 'caller-usage':
            if not args.caller:
                print("Error: caller-usage command requires --caller")
                return 1
            usage = _tracker.get_caller_usage(args.caller)
            if not usage:
                print(f"No usage data found for caller: {args.caller}")
                return 0
            print(f"\nUsage for {args.caller}:")
            print(f"  Requests: {usage.get('requests', 0)}")
            print(f"  Total Cost: ${usage.get('total_cost', 0.0):.6f}")
            print(f"  Total Tokens: {usage.get('total_tokens', 0)}")
            models = usage.get('models_used', {})
            if models:
                print(f"  Models Used: {', '.join(models.keys())}")
            return 0

        elif args.command == 'daily-usage':
            usage = _tracker.get_daily_usage(args.date)
            if not usage:
                date_str = args.date or "today"
                print(f"No usage data found for {date_str}")
                return 0
            date_str = args.date or datetime.now().date().isoformat()
            print(f"\nDaily Usage for {date_str}:")
            print(f"  Requests: {usage.get('requests', 0)}")
            print(f"  Total Cost: ${usage.get('cost', 0.0):.6f}")
            print(f"  Total Tokens: {usage.get('tokens', 0)}")
            return 0

        elif args.command == 'cleanup':
            _tracker.cleanup_old_data(args.days)
            print(f"✅ Cleaned up data older than {args.days} days")
            return 0

        elif args.command == 'status':
            config = load_config()
            print("\nModule Status:")
            print(f"  Module: {MODULE_NAME}")
            print(f"  Version: {MODULE_VERSION}")
            print(f"  Enabled: {_tracker.enabled}")
            print(f"  Auto Track: {config.get('config', {}).get('auto_track', True)}")
            print(f"  Generation Check Delay: {config.get('config', {}).get('generation_check_delay', 2)}s")
            print(f"  Cleanup Old Data Days: {config.get('config', {}).get('cleanup_old_data_days', 30)}")
            data = load_module_data()
            print(f"  Total Requests (Session): {data.get('current_session', {}).get('total_requests', 0)}")
            print(f"  Tracked Callers: {len(data.get('usage_by_caller', {}))}")
            return 0

    except Exception as e:
        print(f"Error: {e}")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())