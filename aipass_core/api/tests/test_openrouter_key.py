#!/usr/bin/env python3

# =============================================
# META DATA HEADER
# Name: test_openrouter_key.py
# Date: 2025-08-29
# Version: 1.0.0
# 
# CHANGELOG:
#   - v1.0.0 (2025-08-29): Production-ready OpenRouter API test tool
#     * Feature: Comprehensive API testing with real usage metrics
#     * Feature: Account balance and credit monitoring
#     * Feature: Detailed generation tracking with cost analysis
#     * Feature: Robust error handling (network, auth, format validation)
#     * Feature: AIPass standards compliance with proper sections
#     * Fix: Scientific notation cost display with readable format
#     * Fix: DNS/connection error detection and reporting
# =============================================

"""
OpenRouter API Test Tool

Comprehensive testing tool for OpenRouter API functionality with detailed
usage tracking, account monitoring, and error detection.

Status: Production Ready

Key Features:
- Real-time usage tracking with exact costs
- Account balance monitoring
- API key validation and format checking
- Network connectivity testing
- Generation performance metrics
- Comprehensive error handling
"""

# Standard imports
import requests
import json
import time
import os
from datetime import datetime
from pathlib import Path

# =============================================
# CONFIGURATION SECTION
# =============================================

# Test model configuration - EDIT HERE TO CHANGE MODEL
TEST_MODEL = "deepseek/deepseek-chat-v3.1:free"

# Alternative models to try:
# TEST_MODEL = "openai/gpt-4o-mini"                    # OpenAI GPT-4o Mini
# TEST_MODEL = "anthropic/claude-3.5-sonnet"          # Anthropic Claude
# TEST_MODEL = "google/gemini-flash-1.5"              # Google Gemini
# TEST_MODEL = "meta-llama/llama-3.1-8b-instruct:free" # Meta Llama (free)

# Request headers configuration
REQUEST_HEADERS = {
    "Content-Type": "application/json",
    "HTTP-Referer": "https://aipass-ecosystem.local",
    "X-Title": "AIPass OpenRouter Test Tool"
}

# Test configuration
TEST_MESSAGE = "Hello, test message for usage tracking"
API_TIMEOUT = 30
KEY_MIN_LENGTH = 60  # Minimum expected key length

# =============================================
# ENVIRONMENT LOADING
# =============================================

# Load environment variables
def load_env():
    env_path = Path(__file__).parent.parent / '.env'
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                if '=' in line and not line.strip().startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value

load_env()
OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")

# =============================================
# CORE TESTING FUNCTIONS
# =============================================

def test_openrouter_key():
    """Test OpenRouter key capabilities"""
    if not OPENROUTER_KEY:
        print("❌ OPENROUTER_API_KEY not found in .env file")
        return False
    
    # Validate OpenRouter key format
    if not OPENROUTER_KEY.startswith("sk-or-v1-"):
        print(f"❌ Invalid OpenRouter API key format. Should start with 'sk-or-v1-'")
        print(f"   Your key starts with: '{OPENROUTER_KEY[:10]}...'")
        return False
    
    # Check if key looks complete (OpenRouter keys are typically ~70 characters)
    if len(OPENROUTER_KEY) < KEY_MIN_LENGTH:
        print(f"❌ OpenRouter API key appears incomplete")
        print(f"   Key length: {len(OPENROUTER_KEY)} characters (expected ~70)")
        print(f"   Key: {OPENROUTER_KEY}")
        return False
        
    print("Testing OpenRouter API Key...")
    print(f"Key: {OPENROUTER_KEY[:15]}...{OPENROUTER_KEY[-8:]}")
    print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Build headers with API key
    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        **REQUEST_HEADERS
    }
    
    # Test 1: Basic API call with usage tracking
    print(f"\n1. Testing basic API call with usage tracking...")
    print(f"  Model: {TEST_MODEL}")
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json={
                "model": TEST_MODEL,
                "messages": [{"role": "user", "content": TEST_MESSAGE}],
                "usage_tracking": True  # Enable detailed usage tracking
            },
            timeout=API_TIMEOUT
        )
        
        print(f"  Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("  SUCCESS! OpenRouter API call working")
            
            # Check for usage data in response
            if 'usage' in data:
                usage = data['usage']
                print(f"  Token Usage:")
                print(f"    - Prompt Tokens: {usage.get('prompt_tokens', 'N/A')}")
                print(f"    - Completion Tokens: {usage.get('completion_tokens', 'N/A')}")
                print(f"    - Total Tokens: {usage.get('total_tokens', 'N/A')}")
                
            # Check for generation ID (for detailed tracking)
            if 'id' in data:
                generation_id = data['id']
                print(f"  Generation ID: {generation_id}")
                
                # Try to get detailed generation stats
                print("\n2. Testing detailed generation tracking...")
                time.sleep(2)  # Brief pause for data processing
                
                gen_response = requests.get(
                    f"https://openrouter.ai/api/v1/generation?id={generation_id}",
                    headers=headers,
                    timeout=10
                )
                
                print(f"  Generation API Status: {gen_response.status_code}")
                if gen_response.status_code == 200:
                    gen_data = gen_response.json()
                    print("  SUCCESS! Detailed generation tracking working")
                    if 'data' in gen_data:
                        data = gen_data['data']
                        print(f"    - Model: {data.get('model', 'N/A')}")
                        print(f"    - Provider: {data.get('provider_name', 'N/A')}")
                        cost = data.get('total_cost', 0)
                        if isinstance(cost, (int, float)) and cost > 0:
                            print(f"    - Total Cost: ${cost:.8f} (${cost*1000000:.2f} per million calls)")
                        else:
                            print(f"    - Total Cost: ${cost}")
                        print(f"    - Tokens: {data.get('tokens_prompt', 'N/A')} prompt + {data.get('tokens_completion', 'N/A')} completion")
                        print(f"    - Generation Time: {data.get('generation_time', 'N/A')}ms")
                        print(f"    - Latency: {data.get('latency', 'N/A')}ms")
                else:
                    print(f"  Generation tracking failed: {gen_response.text[:100]}")
                
        else:
            print(f"  FAILED: {response.status_code}")
            print(f"  Error: {response.text[:200]}")
            
    except requests.exceptions.ConnectionError as e:
        if "Failed to resolve" in str(e) or "getaddrinfo failed" in str(e):
            print(f"  ❌ NO INTERNET CONNECTION: Cannot reach openrouter.ai")
        else:
            print(f"  ❌ CONNECTION ERROR: {e}")
    except requests.exceptions.Timeout:
        print(f"  ❌ TIMEOUT: OpenRouter took too long to respond")
    except Exception as e:
        print(f"  ❌ ERROR: {e}")
    
    # Test 3: Check account balance and credits
    print("\n3. Testing account balance information...")
    try:
        balance_response = requests.get(
            "https://openrouter.ai/api/v1/credits",
            headers=headers,
            timeout=10
        )
        
        print(f"  Balance API Status: {balance_response.status_code}")
        if balance_response.status_code == 200:
            balance_data = balance_response.json()
            print("  SUCCESS! Account balance accessible")
            if 'data' in balance_data:
                data = balance_data['data']
                total_credits = data.get('total_credits', 0)
                total_usage = data.get('total_usage', 0)
                remaining = total_credits - total_usage
                print(f"    - Total Credits Purchased: ${total_credits:.6f}")
                print(f"    - Total Usage: ${total_usage:.6f}")
                print(f"    - Remaining Balance: ${remaining:.6f}")
        else:
            print(f"  Balance check failed: {balance_response.text[:100]}")
            
    except requests.exceptions.ConnectionError as e:
        if "Failed to resolve" in str(e) or "getaddrinfo failed" in str(e):
            print(f"  ❌ NO INTERNET CONNECTION: Cannot reach openrouter.ai")
        else:
            print(f"  ❌ CONNECTION ERROR: {e}")
    except requests.exceptions.Timeout:
        print(f"  ❌ TIMEOUT: OpenRouter took too long to respond")
    except Exception as e:
        print(f"  ❌ Balance check error: {e}")
    
    # Test 4: Check key information (rate limits, etc.)
    print("\n4. Testing API key information...")
    try:
        key_response = requests.get(
            "https://openrouter.ai/api/v1/auth/key",
            headers=headers,
            timeout=10
        )
        
        print(f"  Key API Status: {key_response.status_code}")
        if key_response.status_code == 200:
            key_data = key_response.json()
            print("  SUCCESS! Key information accessible")
            if 'data' in key_data:
                data = key_data['data']
                print(f"    - Key Label: {data.get('label', 'N/A')}")
                print(f"    - Rate Limit: {data.get('limit', 'N/A')} requests")
        else:
            print(f"  Key info check failed: {key_response.text[:100]}")
            
    except requests.exceptions.ConnectionError as e:
        if "Failed to resolve" in str(e) or "getaddrinfo failed" in str(e):
            print(f"  ❌ NO INTERNET CONNECTION: Cannot reach openrouter.ai")
        else:
            print(f"  ❌ CONNECTION ERROR: {e}")
    except requests.exceptions.Timeout:
        print(f"  ❌ TIMEOUT: OpenRouter took too long to respond")
    except Exception as e:
        print(f"  ❌ Key info error: {e}")
    
    return True

# =============================================
# MAIN EXECUTION
# =============================================

if __name__ == "__main__":
    """
    Run OpenRouter API tests with comprehensive error handling and reporting.
    """
    test_openrouter_key()