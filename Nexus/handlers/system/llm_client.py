#!/usr/bin/env python3.12
"""OpenAI LLM client for Nexus v2"""

import sys
from pathlib import Path

AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))

from openai import OpenAI
import os
from dotenv import load_dotenv

# Load .env from home directory
load_dotenv(Path.home() / ".env")

def make_client() -> OpenAI:
    """Create OpenAI client using API key from environment"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in environment")
    return OpenAI(api_key=api_key)

def chat(client: OpenAI, messages: list, model: str = "gpt-4.1", temperature: float = 0.7) -> str:
    """Send messages to OpenAI and return response text"""
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature
    )
    return response.choices[0].message.content.strip()
