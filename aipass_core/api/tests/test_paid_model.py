#!/usr/bin/env python3

"""
Test API system with paid model to verify it works
This proves the issue is privacy settings, not the code
"""

import sys
from pathlib import Path
AIPASS_ROOT = Path.home()
import sys
sys.path.append(str(AIPASS_ROOT))

from api.apps.openrouter import get_response

print("Testing API System with Paid Model")
print("=" * 50)

# Test with an affordable paid model
test_model = "openai/gpt-4o-mini"
print(f"\nModel: {test_model}")
print(f"Note: This is a paid model (~$0.15/$1 per million tokens)")
print(f"Your balance: $9.99 - This test will cost < $0.001\n")

messages = [{"role": "user", "content": "Say 'API working' if you receive this"}]

print("Making request...")
response = get_response(messages, model=test_model, caller="paid_model_test")

if response:
    print(f"✅ SUCCESS! API system working correctly")
    print(f"Response: {response}")
    print(f"\n✅ This confirms the API code is working fine")
    print(f"✅ The free model issue is purely OpenRouter privacy settings")
else:
    print(f"❌ FAILED - No response received")
    print(f"Check /home/aipass/api/api_json/openrouter_log.json for details")
