#!/usr/bin/env python3

"""
Quick test of top 3 free models to find one that works
"""

import sys
from pathlib import Path
AIPASS_ROOT = Path.home()
import sys
sys.path.append(str(AIPASS_ROOT))

from api.apps.openrouter import get_response

print("Testing Top 3 Free Models")
print("=" * 60)

# Top 3 candidates
models_to_test = [
    ("google/gemini-2.0-flash-exp:free", "Gemini 2.0 Flash (1M context)"),
    ("meta-llama/llama-3.3-70b-instruct:free", "Llama 3.3 70B"),
    ("mistralai/mistral-small-3.2-24b-instruct:free", "Mistral Small 3.2"),
]

test_message = [{"role": "user", "content": "Reply with just 'OK' if you receive this"}]

working_models = []

for model_id, model_name in models_to_test:
    print(f"\nTesting: {model_name}")
    print(f"Model ID: {model_id}")

    response = get_response(test_message, model=model_id, caller="model_test")

    if response:
        print(f"✅ SUCCESS - Model works!")
        print(f"Response: {response}")
        working_models.append((model_id, model_name))
    else:
        print(f"❌ FAILED - Model blocked or unavailable")

print("\n" + "=" * 60)
print("RESULTS:")
print("=" * 60)

if working_models:
    print(f"\n✅ Found {len(working_models)} working free model(s):\n")
    for i, (model_id, model_name) in enumerate(working_models, 1):
        print(f"{i}. {model_name}")
        print(f"   ID: {model_id}\n")

    print(f"RECOMMENDED DEFAULT: {working_models[0][0]}")
else:
    print("\n❌ No free models working with current privacy settings")
    print("   You may need to adjust OpenRouter privacy settings")
    print("   Or use a paid model like: openai/gpt-4o-mini")
