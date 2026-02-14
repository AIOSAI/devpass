import sys
import os
import json
import logging
from pathlib import Path
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from pydantic import SecretStr

# Usage monitor dynamic import
try:
    from usage_monitor import get_usage_monitor
    usage_monitor = get_usage_monitor()
    USAGE_MONITORING_ENABLED = True
    print(f"[INFO] Usage monitoring enabled")
except Exception as e:
    print(f"[WARN] Usage monitoring unavailable: {e}")
    usage_monitor = None
    USAGE_MONITORING_ENABLED = False

logger = logging.getLogger("seed")

# --- API key retrieval from config.json ---
def get_openai_api_key():
    config_path = Path(__file__).parent / "config.json"
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        return config.get("openai", {}).get("api_key")
    except Exception as e:
        logger.warning(f"Could not read API key from {config_path}: {e}")
        return None

LANGCHAIN_AVAILABLE = True
ChatOpenAI_AVAILABLE = True


def make_langchain_client(provider: str, api_key: str, model: str = "gpt-4.1-nano", temperature: float = 0.7):
    """Create a LangChain client for the given provider."""
    if not LANGCHAIN_AVAILABLE:
        raise ValueError("LangChain not available")
    if provider == "openai":
        if not ChatOpenAI_AVAILABLE:
            raise ValueError("LangChain OpenAI not available")
        return ChatOpenAI(
            api_key=SecretStr(api_key),
            model=model,
            temperature=temperature
        )
    raise ValueError(f"LangChain provider '{provider}' not supported yet")


def langchain_enhanced_chat(provider: str, client, model: str, messages: list, temperature: float, breakdown=None, token_contributions=None) -> str:
    """Send an enhanced chat request using LangChain."""
    if provider == "openai":
        lc_messages = []
        for msg in messages:
            if msg["role"] == "system":
                lc_messages.append(SystemMessage(content=msg["content"]))
            elif msg["role"] == "user":
                lc_messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                lc_messages.append(AIMessage(content=msg["content"]))
        response = client.invoke(lc_messages)
        # Log usage if available
        if USAGE_MONITORING_ENABLED and usage_monitor:
            try:
                try:
                    input_tokens = sum(len(msg["content"].split()) * 1.3 for msg in messages)
                    output_tokens = len(response.content.split()) * 1.3 if isinstance(response.content, str) else 0
                except Exception as e:
                    logger.warning(f"Error estimating token count: {e}")
                    input_tokens = 0
                    output_tokens = 0
                usage_monitor.log_usage(
                    provider="openai",
                    model=model,
                    input_tokens=int(input_tokens),
                    output_tokens=int(output_tokens),
                    system="langchain_enhancer",
                    breakdown=breakdown,
                    token_contributions=token_contributions
                )
            except Exception as e:
                logger.warning(f"Failed to log LangChain token usage: {e}")
        return response.content.strip()
    raise ValueError(f"LangChain provider '{provider}' not supported")


def test_langchain_connection():
    """Test the LangChain connection to ensure it works."""
    print("Testing LangChain interface...")
    try:
        api_key = get_openai_api_key()
        if not api_key:
            print("No API key found in config.json")
            return False
        client = make_langchain_client("openai", api_key)
        response = langchain_enhanced_chat(
            "openai", 
            client, 
            "gpt-3.5-turbo", 
            [{"role": "user", "content": "Hello, are you working?"}],
            0.7
        )
        print(f"LangChain test response: {response}")
        return True
    except Exception as e:
        print(f"LangChain test failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing LangChain interface...")
    test_langchain_connection()
