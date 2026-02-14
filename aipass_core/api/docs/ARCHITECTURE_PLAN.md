# AIPass API System - Modular Architecture Plan

*Updated: 2025-08-30 - Following AIPass Standards & Modular Principles*

## 📋 META DATA

- **Status**: Planning → Implementation
- **Priority**: High - Foundation for all API operations  
- **Dependencies**: OpenRouter API key, AIPass 3-JSON pattern
- **Timeline**: Phase 1 immediate start

## 🎯 Mission Statement

Build a production-ready, modular API system that:

1. Provides API keys to calling modules
2. Tracks REAL usage per module (no estimates, actual API metrics)
3. Uses OpenRouter as primary provider (323 models via single API)
4. Follows ALL AIPass standards (3-JSON, logging, error handling)
5. Respects each caller's independent configuration
6. Scales properly from day one

## 📂 Directory Structure (AIPass Standards)

```
api/
├── ARCHITECTURE_PLAN.md      # This document
├── api_connect.py            # Key provider with validation
├── api_usage.py              # Real usage tracking
├── openrouter.py             # OpenRouter client
├── api_json/                 # 3-JSON pattern storage
│   ├── api_config.json       # API keys and settings
│   ├── api_data.json         # Usage tracking data
│   └── api_log.json          # Request/response logs
└── system_logs/             (Comment, no prax-logger deals with this)
    └── api_system.log       (comment,  no prax-logger deals with this)
```

## 🔄 Simple Workflow

### How an API Call Flows (with Auto-Provisioning)

```
1. Module (e.g., flow_mbank.py) needs AI response
   ↓
2. Module imports: from api.openrouter import get_response
   ↓
3. Module loads its config (may not exist yet):
   - Tries to load flow_json/flow_mbank_config.json
   - If missing, continues with model=None
   ↓
4. Module calls: response = get_response(messages, model=model, caller="flow_mbank")
   ↓
5. openrouter.py receives the call:
   ↓
6. FIRST TIME (no config):
   - Detects caller: "flow_mbank" from "flow/flow_json/"
   - Checks if flow_json/flow_mbank_config.json exists
   - NOT FOUND: Creates it from template (same for all modules)
   - Returns error: "Config created, please reload and try again"
   ↓
7. SUBSEQUENT CALLS (config exists):
   - Module loads config with ai_model
   - Passes model to openrouter
   - openrouter makes API call
   - Returns response
```

### The Magic: Zero Configuration Required

- **Caller doesn't implement JSON creation** - Too error-prone
- **openrouter maintains templates** - Single source of truth
- **Auto-provisioning on first use** - Just works
- **Each module still controls its config** - Can edit after creation

### Where Prompts Live

- **System prompts**: In the calling module (sets AI behavior/role)
- **Module prompts**: In the calling module (specific task instructions)
- **API system**: Just a conduit - passes messages unchanged

**Note on Multi-Tool Calls:**

- For flow modules (Phase 1): Single request/response is fine
- For future multi-skill: System prompt should be broad enough to handle all tools in one call

## 🛠️ Core Components (Phase 1)

### 1. api_connect.py - Key Provider with Validation

```python
"""
API key provider following AIPass standards
- Reads keys from api_json/api_config.json or .env
- Auto-creates .env template if missing
- Validates key format and completeness
- Integrates with prax logging
"""

import json
import os
from pathlib import Path
from prax.prax_logger import system_logger as logger

class APIConnect:
    def __init__(self):
        # Use the imported system_logger function directly
        self.config_path = Path("api/api_json/api_config.json")
        self._load_config()
    
    def get_api_key(self, provider="openrouter"):
        """Get validated API key for provider"""
        # Check config file first
        # Fall back to .env
        # Validate format (e.g., sk-or-v1- for OpenRouter)
        # Log access for security
        return api_key
```

### 2. api_usage.py - Real Usage Monitor

```python
"""
Track REAL API usage per module (based on prax_usage_monitor patterns)
- Store generation_id from each request
- Query OpenRouter's /generation endpoint for exact metrics
- Log: caller, model, actual tokens, real cost, generation time
- Follow AIPass 3-JSON pattern
- No fake estimates or token counting libraries!
"""

import json
import requests
from datetime import datetime
from prax.prax_logger import system_logger as logger

class APIUsageTracker:
    def __init__(self):
        # Use the imported system_logger function directly
        self.data_path = Path("api/api_json/api_data.json")
        self.log_path = Path("api/api_json/api_log.json")
    
    def track_usage(self, caller, generation_id, model):
        """Get REAL metrics from OpenRouter and log them"""
        # Query /generation endpoint with generation_id
        # Get actual: total_cost, tokens_prompt, tokens_completion, latency
        # Store with caller context (e.g., "flow_mbank")
        # Update daily/monthly totals
        # Log to both JSON and system_logs
```

### 3. openrouter.py - OpenRouter Client

```python
"""
OpenRouter client using OpenAI SDK - AIPass standards compliant
- Uses OpenRouter base URL
- Handles all 323 available models
- Proper error handling and logging
- Returns response or explicit error
"""

from openai import OpenAI
from api.api_connect import APIConnect
from api.api_usage import APIUsageTracker
from prax.prax_logger import system_logger as logger

class OpenRouterClient:
    def __init__(self):
        # Use the imported system_logger function directly
        self.api_connect = APIConnect()
        self.usage_tracker = APIUsageTracker()
        
    def get_response(self, messages, model="openai/gpt-4", caller=None):
        """Get AI response via OpenRouter with full tracking"""
        
        try:
            # Get and validate API key
            api_key = self.api_connect.get_api_key("openrouter")
            
            # Create client with OpenRouter URL
            client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=api_key
            )
            
            # Log the request
            logger(f"api_request: {caller} using {model}")
            
            # Make the request
            response = client.chat.completions.create(
                model=model,
                messages=messages
            )
            
            # Track REAL usage via generation_id
            if response.id:
                self.usage_tracker.track_usage(
                    caller=caller,  # e.g., "flow_mbank" 
                    generation_id=response.id,
                    model=model
                )
            
            return response.choices[0].message.content
            
        except Exception as e:
            # Log error with full context
            logger(f"api_error: {caller} {model} - {str(e)}")
            return None  # Explicit failure, no retry loops!

# Module-level function for simple imports
_client = OpenRouterClient()
get_response = _client.get_response
```

## 📊 Real Metrics from OpenRouter

Based on `tests/test_openrouter_key.py`, OpenRouter provides REAL usage data:

### Generation Tracking (`/generation` endpoint)

- **total_cost**: Exact cost in dollars (e.g., $0.00001060 = $10.60 per million)
- **tokens_prompt**: Actual prompt tokens used
- **tokens_completion**: Actual completion tokens
- **generation_time**: Processing time in ms
- **latency**: Network latency in ms
- **provider_name**: Which provider handled the request

### Account Monitoring (`/credits` endpoint)

- **total_credits**: Amount purchased
- **total_usage**: Amount spent
- **remaining**: Current balance

**Key Point**: No token counting libraries or estimates - all metrics come from the API!

## 🔐 AIPass Standards Compliance

### 3-JSON Pattern

Each module maintains three JSON files:

**api_config.json** - Configuration

```json
{
    "skill_name": "api_system",
    "timestamp": "2025-08-30T10:00:00Z",
    "version": "1.0.0",
    "config": {
        "enabled": true,
        "providers": {
            "openrouter": {
                "api_key": "sk-or-v1-...",
                "base_url": "https://openrouter.ai/api/v1"
            }
        },
        "default_provider": "openrouter",
        "timeout_seconds": 30
    }
}
```

**api_data.json** - Runtime Data

```json
{
    "current_session": {
        "start_time": "2025-08-30T10:00:00Z",
        "total_requests": 0,
        "total_cost": 0.0
    },
    "usage_by_caller": {
        "flow_mbank": {
            "requests": 0,
            "total_cost": 0.0,
            "total_tokens": 0
        }
    },
    "daily_totals": {}
}
```

**api_log.json** - Request Logs

```json
{
    "logs": [
        {
            "timestamp": "2025-08-30T10:00:00Z",
            "caller": "flow_mbank",
            "model": "openai/gpt-4",
            "generation_id": "gen-xxx",
            "status": "success",
            "tokens": 150,
            "cost": 0.00015,
            "latency_ms": 420
        }
    ]
}
```

### System Logger Integration

- All modules use `prax.prax_logger.system_logger`
- Logs go to both JSON files and `system_logs/`
- Error tracking with full context
- Performance metrics tracked

### Error Handling

- Explicit errors, no silent failures
- Full context logging (caller, model, error details)
- No retry loops - fail fast and clear
- Errors returned to caller for handling

## 🔗 Reference Code

### Existing Patterns to Build On

- **prax/prax_usage_monitor.py** - Usage tracking patterns (retire after api_usage.py, already archived)
- **prax/prax_logger.py** - System logging integration
- **tests/test_openrouter_key.py** - Shows exact API responses
- **Versioned backups** - Previous attempts available in backup_system/backups/
  - Old OpenAI skill implementations
  - Previous API connect patterns
  - Lessons learned from past iterations

**Note**: Archive.local may be cleared periodically. Check versioned backups for historical code.

### Caller Context Patterns

**Simple (Phase 1 - Flow modules):**

```python
# Direct module calls
get_response(messages, model="...", caller="flow_mbank")
get_response(messages, model="...", caller="live_chat_context")
```

**Complex (Future - Multi-skill scenarios):**

```python
# When skills call other skills (track the chain)
caller="multi_skill:orchestrator->skill1->skill2"

# Example: read_file_skill provides context for AI response
# The OpenAI skill (now OpenRouter) had handlers to keep file content in context
# This pattern needs to be preserved in the new architecture
# Check versioned backups for openai_skill.py to see the context retention logic. read the skill files to confirm this. 
```

**Context Retention Pattern** (from previous OpenAI skill):

- Skills like read_file_skill add content to message context
- API module maintains conversation history for multi-turn interactions
- File contents stay in the message chain for AI to reference
- Handler pattern allowed skills to modify context before API calls

## 📦 Implementation Phases

### Phase 1: Foundation (Immediate)

**Goal**: Get basic API calls working with AIPass standards

1. **api_connect.py**
   - [ ] Read API keys from config/env
   - [ ] Validate key format
   - [ ] Auto-create .env template if missing
   - [ ] Integrate prax logging

2. **api_usage.py**  
   - [ ] Query generation endpoint for real metrics
   - [ ] Store in api_data.json (3-JSON pattern)
   - [ ] Track by caller module
   - [ ] Daily/monthly aggregation

3. **openrouter.py**
   - [ ] Set up OpenAI SDK with OpenRouter URL
   - [ ] Full error handling and logging
   - [ ] Integration with api_connect and api_usage
   - [ ] Return responses or explicit errors

### Phase 2: Integration (After Phase 1 Works)

**Goal**: Connect to existing modules

- [ ] Update flow_mbank.py to use new API
- [ ] Update live_chat_context_skill.py
- [ ] Remove old OpenAI skill dependencies
- [ ] Test with real workflows

### Phase 3: Enhancement (After Stable)

**Goal**: Add advanced features

- [ ] Usage reports and summaries
- [ ] Cost alerts and limits
- [ ] Model recommendation based on task
- [ ] Performance optimization

## 🧪 Testing Approach

### Tests Location

All tests in: `C:\Aipass-Ecosystem\tests\api\`

### Test Categories

1. **Unit Tests** - Each function works correctly
2. **Integration Tests** - Components work together
3. **Live Tests** - Real API calls (use sparingly)
4. **Standards Tests** - AIPass compliance verification

### Test Example

```python
# tests/api/test_openrouter.py
def test_aipass_standards():
    """Verify AIPass standards compliance"""
    # Check 3-JSON files exist
    # Verify logger integration
    # Test error handling
    # Validate configuration structure
```

## 🎯 Success Criteria

### Phase 1 Complete When

- [ ] Can make API call via openrouter.py
- [ ] API keys auto-load and validate
- [ ] Real usage tracked in api_data.json
- [ ] Errors logged properly via prax
- [ ] 3-JSON pattern fully implemented

### System Success When

- [ ] All modules use central API
- [ ] Zero OpenAI skill dependencies
- [ ] Real usage tracking accurate
- [ ] Cost transparency achieved
- [ ] Full AIPass standards compliance

## 🐛 Bug Discovery (2025-08-30)

### Issue Identified

Testing revealed that flow_mbank was using the API system's hardcoded DEFAULT_MODEL instead of its own model selection. This violates the core principle of module independence.

### Root Cause Analysis

1. **flow_mbank.py** calls `get_response(messages=messages, caller="flow_mbank")` with NO model parameter
2. **openrouter.py** had fallback logic: `model = model or DEFAULT_MODEL`
3. **Result**: All callers used the same hardcoded model instead of their own preferences

### Testing Methodology

Commented out sections one by one to isolate dependencies:

- Line 71: `OPENROUTER_BASE_URL` - Error: "name 'OPENROUTER_BASE_URL' is not defined"
- Line 72: `DEFAULT_MODEL` - Error: "name 'DEFAULT_MODEL' is not defined"  
- Line 73: `DEFAULT_TIMEOUT` - Error: "name 'DEFAULT_TIMEOUT' is not defined"
- Line 262: `model = model or DEFAULT_MODEL` - Error: "API CONNECTION ERROR"

This proved the system was relying on hardcoded fallbacks instead of caller configs.

## ✅ Correct Implementation Plan

### Core Architecture Principle

**openrouter.py = Infrastructure + JSON Provisioning** (creates configs for callers, but doesn't choose models)
**Callers = Model Selection** (each loads their config and decides what model to use)

### Key Design Decision: Separation of Concerns

Following AIPass STANDARDS.md architecture:

1. **Modules manage their OWN 3-JSON files** - Each module creates/manages its own config, data, log
2. **openrouter ONLY provides API configs** - Creates API-specific config when missing (like old openai_skill)
3. **Clear separation** - Module logic stays with module, API config comes from API system
4. **No duplication** - openrouter doesn't recreate what modules already do

### Phase 1A: Fix openrouter.py (Infrastructure + Provisioning)

1. **Add Caller Detection** (based on old openai_skill pattern)

   ```python
   def get_caller_info():
       """Detect caller module and determine JSON folder location"""
       # Check stack trace to find caller
       # Look for patterns: flow/, prax/, skills/skills_*/
       # Return: (module_name, json_folder_path)
       
       # Example detection:
       # If called from flow/flow_mbank.py:
       #   return ("flow_mbank", Path("flow/flow_json"))
       # If called from prax/prax_logger.py:
       #   return ("prax_logger", Path("prax/prax_json"))
   ```

2. **Single Universal Template** (same for ALL modules)

   ```python
   # One template to rule them all - modules customize after creation
   DEFAULT_CONFIG_TEMPLATE = {
       "config": {
           "ai_model": "deepseek/deepseek-chat-v3.1:free",  # Default free model
           "ai_temperature": 0.5,
           "ai_max_tokens": 1500,
           "enabled": True
       }
   }
   ```

3. **Auto-provision API Config ONLY** (not full module config)

   ```python
   def ensure_caller_api_config(caller_name, json_folder_path):
       """Create ONLY API config for caller (following openai_skill pattern)"""
       # API config file - separate from module's main config
       api_config_file = json_folder_path / f"openrouter_skill_config.json"
       
       if not api_config_file.exists():
           # Create ONLY API-related config
           api_config = {
               "skill_name": "openrouter",
               "timestamp": datetime.now().isoformat(),
               "config": {
                   "ai_model": "deepseek/deepseek-chat-v3.1:free",
                   "ai_temperature": 0.5,
                   "ai_max_tokens": 1500,
                   "enabled": True
               }
           }
           
           # Create the API config file
           json_folder_path.mkdir(parents=True, exist_ok=True)
           with open(api_config_file, 'w') as f:
               json.dump(api_config, f, indent=2)
           
           logger.info(f"Created API config for {caller_name} at {api_config_file}")
           
           # Also create API-specific data and log files
           api_data_file = json_folder_path / f"openrouter_skill_data.json"
           api_log_file = json_folder_path / f"openrouter_skill_log.json"
           
           # These track API usage, not module operations
           if not api_data_file.exists():
               with open(api_data_file, 'w') as f:
                   json.dump({"skill_name": "openrouter", "data": {}}, f, indent=2)
           
           if not api_log_file.exists():
               with open(api_log_file, 'w') as f:
                   json.dump({"skill_name": "openrouter", "logs": []}, f, indent=2)
   ```

4. **openrouter's OWN 3-JSON files** (`api/api_json/`)

   **openrouter_config.json** (Infrastructure settings)

   ```json
   {
     "module_name": "openrouter",
     "timestamp": "2025-08-30T...",
     "config": {
       "base_url": "https://openrouter.ai/api/v1",
       "timeout_seconds": 30,
       "enabled": true,
       "log_requests": true,
       "log_responses": false,
       "auto_provision": true
     }
   }
   ```

   **openrouter_data.json** (Runtime tracking)

   ```json
   {
     "module_name": "openrouter",
     "data": {
       "total_requests": 0,
       "successful_requests": 0,
       "failed_requests": 0,
       "provisioned_configs": {
         "flow_mbank": "2025-08-30T...",
         "prax_logger": "2025-08-30T..."
       },
       "callers_tracked": ["flow_mbank", "prax_logger"]
     }
   }
   ```

   **openrouter_log.json** (Operation history)

   ```json
   {
     "module_name": "openrouter",
     "logs": [
       {
         "timestamp": "2025-08-30T...",
         "operation": "provision_config",
         "caller": "flow_mbank",
         "success": true,
         "details": "Created API config at flow/flow_json/"
       }
     ]
   }
   ```

5. **Modified get_response flow**

   ```python
   def get_response(messages, model=None, caller=None):
       # Step 1: Detect caller if not provided
       if not caller:
           caller_name, json_folder = get_caller_info()
           caller = caller_name
       
       # Step 2: Ensure caller has config (auto-create if missing)
       if caller:
           caller_name, json_folder = get_caller_info()
           ensure_caller_config(caller_name, json_folder)
       
       # Step 3: Validate model was provided
       if not model:
           error_msg = f"Caller '{caller}' must specify a model from their config"
           log_operation("Request failed", False, error_msg)
           return None
       
       # Step 4: Make API call with provided model
       # ... rest of API call logic
   ```

6. **Fix type issues**

   ```python
   # After validation, model and caller are guaranteed to be strings
   if not model or not caller:
       return None  # Already logged error above
   
   # Now safe to call functions that require str
   update_request_stats(caller, model, False)

### Phase 1B: Fix flow_mbank.py (Proper Separation)

1. **flow_mbank manages its OWN config** (per STANDARDS.md)

   ```python
   # flow_mbank already has its own config management for TRL mapping
   # It creates/manages flow_json/flow_mbank_config.json itself
   ```

2. **Load API config from openrouter's file**

   ```python
   def get_ai_model():
       """Get AI model from openrouter's API config"""
       # First check if openrouter API config exists
       api_config_file = FLOW_JSON_DIR / "openrouter_skill_config.json"
       
       if api_config_file.exists():
           with open(api_config_file, 'r') as f:
               api_config = json.load(f)
               return api_config.get("config", {}).get("ai_model")
       
       # No API config yet - openrouter will create on first call
       return None
   ```

3. **Load model and call API**

   ```python
   # In analyze_plan_content():
   # Get AI model from openrouter's API config
   model = get_ai_model()
   
   # Call with model (None triggers provisioning)
   response = get_response(
       messages=messages,
       model=model,
       caller="flow_mbank"
   )
   
   # If no API config existed:
   # 1. openrouter creates openrouter_skill_config.json
   # 2. Returns error asking to retry
   # 3. Next call loads model from the created config
   ```

4. **Result: Clean separation**

   ```
   flow/flow_json/
   ├── flow_mbank_config.json         # Module's own config (TRL mapping, etc)
   ├── flow_mbank_data.json           # Module's runtime data
   ├── flow_mbank_log.json            # Module's operation logs
   ├── openrouter_skill_config.json   # API config from openrouter
   ├── openrouter_skill_data.json     # API usage tracking
   └── openrouter_skill_log.json      # API call logs
   ```

### Complete JSON Structure Overview

**openrouter.py creates TWO sets of JSON files:**

1. **Its OWN 3-JSON files** in `api/api_json/`:

   ```
   api/api_json/
   ├── openrouter_config.json    # openrouter's infrastructure settings
   ├── openrouter_data.json      # openrouter's runtime tracking
   └── openrouter_log.json       # openrouter's operation logs
   ```

2. **API configs for CALLERS** in their directories:

   ```
   flow/flow_json/
   ├── openrouter_skill_config.json    # API settings for flow modules
   ├── openrouter_skill_data.json      # API usage by flow modules
   └── openrouter_skill_log.json       # API calls from flow modules
   
   prax/prax_json/
   ├── openrouter_skill_config.json    # API settings for prax modules
   ├── openrouter_skill_data.json      # API usage by prax modules
   └── openrouter_skill_log.json       # API calls from prax modules
   ```

**Each module ALSO has its OWN 3-JSON files:**

```
flow/flow_json/
├── flow_mbank_config.json    # flow_mbank's own settings (TRL, etc)
├── flow_mbank_data.json      # flow_mbank's runtime data
└── flow_mbank_log.json       # flow_mbank's operation logs
```

### Phase 1C: Caller Customization (After Auto-Creation)

**All modules start with the same template:**

```json
{
  "module_name": "[caller_name]",
  "timestamp": "2025-08-30T...",
  "config": {
    "ai_model": "deepseek/deepseek-chat-v3.1:free",
    "ai_temperature": 0.5,
    "ai_max_tokens": 1500,
    "enabled": true
  }
}
```

**Modules can edit their config after creation:**

- flow_mbank might keep the free model for batch processing
- conversational_ai might change to `"anthropic/claude-3.5-sonnet"` for quality
- code_analysis might use `"openai/gpt-4o-mini"` with temperature 0.1

**The key: ONE template, then modules customize as needed**

### Phase 1D: Testing & Verification

1. **Test with missing model**
   - flow_mbank calls without model parameter
   - Should get: "Caller 'flow_mbank' must specify a model"
   - Plan should stay open with clear error

2. **Test with invalid model**
   - Pass `model="invalid/model"`  
   - Should get OpenRouter API error
   - Proper error logging and tracking

3. **Test with missing config**
   - Delete flow_mbank_config.json
   - Should auto-create with defaults on init
   - System should work immediately

4. **Test different callers with different models**
   - flow_mbank uses free model
   - Another module uses premium model
   - Verify each uses their own selection

## 💡 Key Principles

1. **Start Simple, Build Right** - Basic functionality with proper standards
2. **Module Independence** - Each module owns its config AND MUST SPECIFY ITS MODEL
3. **Explicit Errors** - Fail fast, log clearly, NO SILENT FALLBACKS
4. **OpenRouter First** - 323 models via one API
5. **AIPass Standards** - 3-JSON pattern, prax logging, proper structure
6. **Real Metrics Only** - No estimates, only actual API data
7. **Scale from Day One** - Build it right the first time
8. **No Magic Defaults** - Every parameter must be explicit

## 🚫 What We're NOT Building (Yet)

- Complex retry logic (fallback to errors for now)
- Multiple provider support (OpenRouter handles that)
- Monitoring dashboards (logs are enough initially)
- Advanced routing logic (keep it simple)

## 📝 Next Steps

1. Start with `api_connect.py` - keys with validation
2. Build `api_usage.py` - real metrics tracking
3. Create `openrouter.py` - API calls with standards
4. Set up 3-JSON files properly
5. Test with simple script
6. Integrate with one module
7. Expand systematically

---

**Remember**: Code is truth. Follow standards, track everything, build to scale.
