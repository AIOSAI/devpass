#!/usr/bin/env python3

"""
Find available free models from OpenRouter
"""

import sys
from pathlib import Path
AIPASS_ROOT = Path.home()
import sys
sys.path.append(str(AIPASS_ROOT))

import requests
import os

# Load env
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    with open(env_path, 'r') as f:
        for line in f:
            if '=' in line and not line.strip().startswith('#'):
                key, value = line.strip().split('=', 1)
                os.environ[key] = value

OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")

print("Searching for FREE models on OpenRouter...")
print("=" * 60)

headers = {
    "Authorization": f"Bearer {OPENROUTER_KEY}",
    "Content-Type": "application/json"
}

try:
    response = requests.get(
        "https://openrouter.ai/api/v1/models",
        headers=headers,
        timeout=10
    )

    if response.status_code == 200:
        data = response.json()

        free_models = []
        for model in data.get('data', []):
            model_id = model.get('id', '')
            pricing = model.get('pricing', {})

            # Check if free (pricing is 0)
            prompt_cost = float(pricing.get('prompt', '0'))
            completion_cost = float(pricing.get('completion', '0'))

            if prompt_cost == 0 and completion_cost == 0:
                free_models.append({
                    'id': model_id,
                    'name': model.get('name', ''),
                    'context': model.get('context_length', 0)
                })

        print(f"Found {len(free_models)} FREE models:\n")

        for i, model in enumerate(free_models, 1):
            print(f"{i}. {model['id']}")
            print(f"   Name: {model['name']}")
            print(f"   Context: {model['context']:,} tokens")
            print()

        if free_models:
            print("\nRECOMMENDED FREE MODELS TO TRY:")
            print("-" * 60)
            for model in free_models[:5]:  # Top 5
                print(f"  - {model['id']}")
        else:
            print("⚠️ No free models found. OpenRouter may have changed pricing.")
            print("   Alternative: Use very cheap models like openai/gpt-4o-mini")

    else:
        print(f"❌ Failed to fetch models: {response.status_code}")
        print(response.text[:200])

except Exception as e:
    print(f"❌ Error: {e}")
