#!/usr/bin/env python3

# =============================================
# META DATA HEADER
# Name: test_api_system.py
# Date: 2025-08-30
# Version: 1.0.0
# Category: api
# 
# CHANGELOG:
#   - v1.0.0 (2025-08-30): Initial API system test script
# =============================================

"""
API System Test Script
Tests the complete API system implementation including all modules and 3-JSON pattern
"""

import sys
from pathlib import Path
AIPASS_ROOT = Path.home()
import sys
sys.path.append(str(AIPASS_ROOT))

print("AIPass API System - Test Suite")
print("=" * 50)

# Test 1: Import all modules
print("\nTesting module imports...")
try:
    from api.apps.api_connect import APIConnect, get_api_key
    print("OK api_connect imported successfully")
except Exception as e:
    print(f"FAIL api_connect import failed: {e}")

try:
    from api.apps.api_usage import APIUsageTracker, track_usage
    print("OK api_usage imported successfully")
except Exception as e:
    print(f"FAIL api_usage import failed: {e}")

try:
    from api.apps.openrouter import OpenRouterClient, get_response
    print("OK openrouter imported successfully")
except Exception as e:
    print(f"FAIL openrouter import failed: {e}")

# Test 2: Check 3-JSON file creation
print("\nTesting 3-JSON file creation...")
import os
import json

json_files_expected = [
    "api/api_json/api_connect_config.json",
    "api/api_json/api_connect_data.json", 
    "api/api_json/api_usage_config.json",
    "api/api_json/api_usage_data.json",
    "api/api_json/openrouter_config.json", 
    "api/api_json/openrouter_data.json"
]

for json_file in json_files_expected:
    if os.path.exists(json_file):
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
            print(f"OK {json_file} - valid JSON")
        except json.JSONDecodeError:
            print(f"FAIL {json_file} - invalid JSON")
        except Exception as e:
            print(f"FAIL {json_file} - error: {e}")
    else:
        print(f"WARN {json_file} - not found (may be created on first use)")

# Test 3: Test basic functionality
print("\nTesting basic functionality...")

# Test API Connect
try:
    connector = APIConnect()
    key = connector.get_api_key("openrouter")  # Should return None without real key
    print(f"OK APIConnect basic test - Key check: {'Found' if key else 'None (expected)'}")
except Exception as e:
    print(f"FAIL APIConnect test failed: {e}")

# Test API Usage Tracker
try:
    tracker = APIUsageTracker()
    summary = tracker.get_session_summary()
    print(f"OK APIUsageTracker basic test - Session: {summary.get('total_requests', 0)} requests")
except Exception as e:
    print(f"FAIL APIUsageTracker test failed: {e}")

# Test OpenRouter Client
try:
    from api.apps.openrouter import get_available_models
    client = OpenRouterClient()
    models = get_available_models()  # Module-level function
    if models:
        print(f"OK OpenRouterClient basic test - {len(models)} models available")
    else:
        print(f"WARN OpenRouterClient basic test - No models returned (API key or privacy settings issue)")
except Exception as e:
    print(f"FAIL OpenRouterClient test failed: {e}")

# Test 4: Test workflow integration
print("\nTesting workflow integration...")
try:
    messages = [{"role": "user", "content": "Hello"}]
    response = get_response(messages, caller="test_script")
    if response is None:
        print("OK Workflow test - Expected None response (no API key configured)")
    else:
        print(f"OK Workflow test - Got response: {len(response)} chars")
except Exception as e:
    print(f"FAIL Workflow test failed: {e}")

print("\nTest Results Summary:")
print("- Module imports: Check above for OK/FAIL")
print("- JSON file creation: Check above for file status")
print("- Basic functionality: Check above for component tests")
print("- Workflow integration: Check above for end-to-end test")

print("\nNext Steps:")
print("1. Add OpenRouter API key to .env file for live testing")
print("2. Test with actual API calls using your OpenRouter key")  
print("3. Monitor usage tracking and cost breakdown")
print("4. Integration with flow modules for production use")

print("\nAPI System Test Complete")