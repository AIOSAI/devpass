#!/usr/bin/env python3

# =============================================
# META DATA HEADER
# Name: api_connect.py
# Date: 2025-08-30
# Version: 1.0.0
# Category: api
# 
# CHANGELOG:
#   - v1.0.0 (2025-08-30): Initial API key provider with validation
# =============================================

"""
API Key Provider with Validation
Following AIPass standards: 3-JSON pattern, prax logging, proper error handling

- Provides keys and open router and other providers import the keys as needed, also auto create .env file with a defaults keys place holders.
- Api_connect does not need any model selection configs. all model config setting will go to the module that calls the provider eg. openrouther.py

Features:
- API key validation and format checking
- Auto-creation of .env template
- 3-file JSON structure (config/data/log)
- Prax logging integration
- Multiple provider support
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
import os
import argparse
from datetime import datetime
from typing import Dict, Optional

# =============================================
# CONFIGURATION SECTION
# =============================================

MODULE_NAME = "api_connect"
MODULE_VERSION = "1.0.0"
MODULE_CATEGORY = "api"

# Standard 3-file JSON structure
CONFIG_FILE = f"{MODULE_NAME}_config.json"
DATA_FILE = f"{MODULE_NAME}_data.json"
LOG_FILE = f"{MODULE_NAME}_log.json"

# Module JSON directory (absolute path)
API_JSON_DIR = API_ROOT / "api_json"

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
                "api_keys_validated": 0,
                "last_key_check": None,
                "env_template_created": False
            }
            save_module_data(initial_data)
            return initial_data
        
        with open(data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get("data", {})
    except Exception as e:
        log_operation("Data load failed", False, error=str(e))
        return {}
    
# =============================================
# MAIN MODULE CLASSES
# =============================================

class APIConnect:
    """
    API key provider that follows AIPass standards
    - Reads keys from api_json/api_config.json or .env
    - Auto-creates .env template if missing
    - Validates key format and completeness
    - Integrates with prax logging
    """
    
    def __init__(self):
        self.config_path = API_JSON_DIR / CONFIG_FILE
        # Use absolute paths based on this module's location
        module_dir = Path(__file__).parent  # /home/aipass/api
        self.env_path = module_dir / ".env"  # /home/aipass/api/.env
        self.api_env_path = module_dir.parent / ".env"  # /home/aipass/.env (root fallback)
        self.config = None
        self._load_config()
    
    def _load_config(self):
        """Load configuration from JSON file or create default"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    self.config = json.load(f)
                logger.info(f"api_connect: loaded config from {self.config_path}")
            else:
                # Create default config
                self._create_default_config()
                logger.info(f"api_connect: created default config at {self.config_path}")
        except Exception as e:
            logger.error(f"api_connect_error: failed to load config - {str(e)}")
            self.config = self._get_default_config()
    
    def _create_default_config(self):
        """Create default configuration file"""
        default_config = self._get_default_config()
        
        # Ensure directory exists
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write config file
        with open(self.config_path, 'w') as f:
            json.dump(default_config, f, indent=2)
        
        # Create .env template if it doesn't exist
        self._create_env_template()
        
        self.config = default_config
    
    def _get_default_config(self):
        """Get default configuration structure"""
        return {
            "skill_name": "api_system",
            "timestamp": datetime.now().isoformat() + "Z",
            "version": "1.0.0",
            "config": {
                "enabled": True,
                "providers": {
                    "openrouter": {
                        "api_key": "",
                        "base_url": "https://openrouter.ai/api/v1"
                    }
                },
                "default_provider": "openrouter",
                "timeout_seconds": 30,
                "key_validation": {
                    "openrouter": {
                        "prefix": "sk-or-v1-",
                        "min_length": 40
                    }
                }
            }
        }
    
    def _create_env_template(self):
        """Create .env template if it doesn't exist"""
        if not self.env_path.exists():
            env_template = """# AIPass API Keys
# Add your API keys here

# OpenRouter API Key (recommended - access to 323+ models)
OPENROUTER_API_KEY=sk-or-v1-your-key-here

# Backup OpenAI API Key (if needed)
OPENAI_API_KEY=sk-your-openai-key-here

# Other provider keys can be added as needed
"""
            with open(self.env_path, 'w') as f:
                f.write(env_template)
            logger.info(f"api_connect: created .env template at {self.env_path}")
    
    def get_api_key(self, provider="openrouter"):
        """
        Get validated API key for provider
        
        Args:
            provider (str): Provider name (default: "openrouter")
            
        Returns:
            str: Validated API key or None if invalid/missing
        """
        try:
            # First check config file
            if self.config and "config" in self.config:
                providers = self.config["config"].get("providers", {})
                if provider in providers and providers[provider].get("api_key"):
                    key = providers[provider]["api_key"]
                    if self._validate_key(key, provider):
                        logger.info(f"api_connect: using {provider} key from config")
                        return key
            
            # Fall back to environment variables
            env_var = f"{provider.upper()}_API_KEY"
            key = os.getenv(env_var)
            if key and self._validate_key(key, provider):
                logger.info(f"api_connect: using {provider} key from environment")
                return key
            
            # Check .env files directly
            key = self._read_env_file(env_var)
            if key and self._validate_key(key, provider):
                logger.info(f"api_connect: using {provider} key from .env file")
                return key
            
            # No valid key found
            logger.error(f"api_connect_error: no valid {provider} key found")
            return None
            
        except Exception as e:
            logger.error(f"api_connect_error: failed to get {provider} key - {str(e)}")
            return None
    
    def _validate_key(self, key, provider):
        """
        Validate API key format and optionally test connection
        
        Args:
            key (str): API key to validate
            provider (str): Provider name for validation rules
            
        Returns:
            bool: True if key is valid format
        """
        if not key or not isinstance(key, str):
            return False
        
        # Get validation rules from config
        if not self.config or "config" not in self.config:
            return len(key.strip()) > 10  # Basic length check
        
        validation = self.config["config"].get("key_validation", {})
        if provider not in validation:
            return len(key.strip()) > 10  # Basic length check
        
        rules = validation[provider]
        
        # Check prefix if specified
        if "prefix" in rules and not key.startswith(rules["prefix"]):
            logger.error(f"api_connect_error: {provider} key missing required prefix {rules['prefix']}")
            logger.error(f"api_connect_error: Expected prefix '{rules['prefix']}' but got '{key[:10]}...'")
            return False
        
        # Check minimum length
        if "min_length" in rules and len(key) < rules["min_length"]:
            logger.error(f"api_connect_error: {provider} key too short (min: {rules['min_length']})")
            return False
        
        return True
    
    def _read_env_file(self, env_var: str) -> Optional[str]:
        """Read environment variable from .env files"""
        # Check both root .env and api/.env
        env_files = [self.env_path, self.api_env_path]
        
        for env_file in env_files:
            if env_file.exists():
                try:
                    with open(env_file, 'r') as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith('#') and '=' in line:
                                key, value = line.split('=', 1)
                                if key.strip() == env_var:
                                    return value.strip()
                except Exception as e:
                    logger.warning(f"api_connect: error reading {env_file}: {e}")
        
        return None
    
    def get_provider_config(self, provider="openrouter"):
        """
        Get full provider configuration
        
        Args:
            provider (str): Provider name
            
        Returns:
            dict: Provider configuration or None
        """
        if not self.config or "config" not in self.config:
            return None
        
        providers = self.config["config"].get("providers", {})
        return providers.get(provider)
    
    def update_config(self, updates):
        """
        Update configuration and save to file
        
        Args:
            updates (dict): Configuration updates to apply
        """
        try:
            if not self.config:
                self.config = self._get_default_config()
            
            # Deep merge updates
            self._deep_update(self.config, updates)
            
            # Update timestamp
            self.config["timestamp"] = datetime.now().isoformat() + "Z"
            
            # Save to file
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            
            logger.info(f"api_connect: updated config at {self.config_path}")
            
        except Exception as e:
            logger.error(f"api_connect_error: failed to update config - {str(e)}")
    
    def _deep_update(self, base, updates):
        """Recursively update nested dictionary"""
        for key, value in updates.items():
            if isinstance(value, dict) and key in base and isinstance(base[key], dict):
                self._deep_update(base[key], value)
            else:
                base[key] = value


# Module-level convenience function
def get_api_key(provider="openrouter") -> Optional[str]:
    """
    Get API key for provider (module-level function for easy imports)
    
    Args:
        provider (str): Provider name (default: "openrouter")
        
    Returns:
        Optional[str]: Validated API key or None
    """
    connector = APIConnect()
    return connector.get_api_key(provider)


def get_provider_config(provider="openrouter") -> Optional[Dict]:
    """
    Get provider configuration (module-level function)
    
    Args:
        provider (str): Provider name
        
    Returns:
        Optional[Dict]: Provider configuration or None
    """
    connector = APIConnect()
    return connector.get_provider_config(provider)

# =============================================
# INITIALIZATION
# =============================================

def initialize_module():
    """Initialize api_connect module and perform startup tasks"""
    try:
        logger.info(f"[{MODULE_NAME}] Initializing API Connect v{MODULE_VERSION}")
        
        # Load module data
        data = load_module_data()
        logger.info(f"[{MODULE_NAME}] Data loaded - {data.get('api_keys_validated', 0)} keys validated")
        
        # Test configuration loading
        connector = APIConnect()
        if connector.config:
            logger.info(f"[{MODULE_NAME}] Configuration loaded successfully")
        else:
            logger.warning(f"[{MODULE_NAME}] Configuration failed to load")
        
        logger.info(f"[{MODULE_NAME}] Module initialization completed successfully")
        log_operation("Module initialized", True, f"Version {MODULE_VERSION}")
        return True
    except Exception as e:
        logger.error(f"[{MODULE_NAME}] Module initialization failed: {e}")
        log_operation("Initialization failed", False, error=str(e))
        return False

# Initialize on import
initialize_module()

# =============================================
# CLI INTERFACE
# =============================================

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description='AIPass API Key Provider with Validation',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
COMMANDS:
  Commands: get-key, get-config, validate, init, test, --provider, --list-providers

OPERATIONS:
  get-key      - Retrieve validated API key for a provider
  get-config   - Get full provider configuration
  validate     - Validate API key format and completeness
  init         - Initialize module and create default config
  test         - Run module tests and connectivity checks

OPTIONS:
  --provider   - Specify API provider (default: openrouter)
  --list-providers - List all available providers

EXAMPLES:
  python api_connect.py get-key
  python api_connect.py get-key --provider openrouter
  python api_connect.py get-config --provider openrouter
  python api_connect.py validate
  python api_connect.py init
  python api_connect.py test
  python api_connect.py --list-providers
        """
    )

    parser.add_argument('command',
                       nargs='?',
                       choices=['get-key', 'get-config', 'validate', 'init', 'test'],
                       help='Command to execute')
    
    parser.add_argument('--provider',
                       type=str,
                       default='openrouter',
                       help='API provider name (default: openrouter)')
    
    parser.add_argument('--list-providers',
                       action='store_true',
                       help='List all available providers')

    args = parser.parse_args()

    # Handle list-providers flag
    if args.list_providers:
        connector = APIConnect()
        if connector.config and "config" in connector.config:
            providers = connector.config["config"].get("providers", {})
            print("Available providers:")
            for provider in providers.keys():
                print(f"  - {provider}")
        return 0

    # Handle commands
    if not args.command:
        parser.print_help()
        return 0

    connector = APIConnect()

    if args.command == 'get-key':
        key = connector.get_api_key(args.provider)
        if key:
            print(f"✓ API key retrieved for {args.provider}")
            print(f"  Key (first 20 chars): {key[:20]}...")
        else:
            print(f"✗ Failed to retrieve API key for {args.provider}")
            return 1

    elif args.command == 'get-config':
        config = connector.get_provider_config(args.provider)
        if config:
            print(f"Provider configuration for {args.provider}:")
            print(json.dumps(config, indent=2))
        else:
            print(f"✗ No configuration found for {args.provider}")
            return 1

    elif args.command == 'validate':
        key = os.getenv(f"{args.provider.upper()}_API_KEY")
        if not key:
            key = connector._read_env_file(f"{args.provider.upper()}_API_KEY")
        
        if key:
            is_valid = connector._validate_key(key, args.provider)
            if is_valid:
                print(f"✓ API key for {args.provider} is valid")
            else:
                print(f"✗ API key for {args.provider} is invalid")
                return 1
        else:
            print(f"✗ No API key found for {args.provider}")
            return 1

    elif args.command == 'init':
        connector._create_default_config()
        print("✓ Module initialized successfully")
        print(f"  Config file: {connector.config_path}")
        print(f"  .env file: {connector.env_path}")

    elif args.command == 'test':
        print("Running API Connect tests...")
        print(f"✓ Configuration loaded: {bool(connector.config)}")
        print(f"✓ Config file exists: {connector.config_path.exists()}")
        print(f"✓ .env file exists: {connector.env_path.exists()}")
        
        # Test key retrieval
        key = connector.get_api_key(args.provider)
        print(f"✓ Key retrieval: {'Success' if key else 'No key configured'}")
        
        print("\n✓ All tests completed")

    return 0


if __name__ == "__main__":
    sys.exit(main())