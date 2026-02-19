#!/home/aipass/.venv/bin/python3
# -*- coding: utf-8 -*-
"""
META:
  app: Nexus
  layer: handlers/system
  purpose: Multi-provider LLM client with unified chat interface
  status: Active
  version: 2.1
  v1_ref: .archive/nexus_v1_original/a.i_core/a.i_profiles/Nexus/llm_client.py
  providers: openai, anthropic, mistral, google
"""

import sys
import os
import logging
from pathlib import Path
from typing import Optional, Any

AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))

from dotenv import load_dotenv

# Load .env from home directory
load_dotenv(Path.home() / ".env")

logger = logging.getLogger("nexus.llm_client")

# ---------------------------------------------------------------------------
# Provider availability flags - graceful degradation per provider
# ---------------------------------------------------------------------------

# OpenAI
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    OpenAI = None  # type: ignore
    logger.warning("OpenAI SDK not installed - openai provider unavailable")

# Anthropic
try:
    import anthropic as _anthropic_module
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    _anthropic_module = None  # type: ignore
    logger.warning("Anthropic SDK not installed - anthropic provider unavailable")

# Mistral
try:
    from mistralai import Mistral as _MistralClient
    MISTRAL_AVAILABLE = True
except ImportError:
    MISTRAL_AVAILABLE = False
    _MistralClient = None  # type: ignore
    logger.warning("Mistral SDK not installed - mistral provider unavailable")

# Google Gemini
try:
    import google.generativeai as _genai
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False
    _genai = None  # type: ignore
    logger.warning("Google Generative AI SDK not installed - google provider unavailable")

# ---------------------------------------------------------------------------
# Supported providers registry
# ---------------------------------------------------------------------------

SUPPORTED_PROVIDERS = {"openai", "anthropic", "mistral", "google"}

PROVIDER_AVAILABILITY = {
    "openai": OPENAI_AVAILABLE,
    "anthropic": ANTHROPIC_AVAILABLE,
    "mistral": MISTRAL_AVAILABLE,
    "google": GOOGLE_AVAILABLE,
}

# ---------------------------------------------------------------------------
# Provider detection from model name
# ---------------------------------------------------------------------------

_MODEL_PREFIX_MAP = {
    "gpt-": "openai",
    "o1-": "openai",
    "o3-": "openai",
    "o4-": "openai",
    "claude-": "anthropic",
    "mistral-": "mistral",
    "codestral-": "mistral",
    "pixtral-": "mistral",
    "gemini-": "google",
}


def detect_provider(model: str) -> Optional[str]:
    """Detect provider from model name prefix.

    Returns provider string or None if unrecognized.
    """
    model_lower = model.lower()
    for prefix, provider in _MODEL_PREFIX_MAP.items():
        if model_lower.startswith(prefix):
            return provider
    return None


# ---------------------------------------------------------------------------
# Client factory
# ---------------------------------------------------------------------------

def make_client(
    provider: str = "openai",
    api_key: Optional[str] = None,
    model: Optional[str] = None,
) -> Any:
    """Create an SDK client for the given provider.

    Backward compatible: make_client() with no args returns an OpenAI client
    using OPENAI_API_KEY from the environment, exactly as v2.0 did.

    Args:
        provider: One of 'openai', 'anthropic', 'mistral', 'google'.
        api_key:  API key. If None, reads from environment
                  (OPENAI_API_KEY, ANTHROPIC_API_KEY, etc.)
        model:    Optional model name. If provided and provider is default,
                  attempts to auto-detect provider from model prefix.
    """
    # Auto-detect provider from model name when provider is default
    if model and provider == "openai":
        detected = detect_provider(model)
        if detected:
            provider = detected

    # Resolve API key from environment if not provided
    if api_key is None:
        env_key_map = {
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "mistral": "MISTRAL_API_KEY",
            "google": "GOOGLE_API_KEY",
        }
        env_var = env_key_map.get(provider)
        if not env_var:
            raise ValueError(f"Unknown provider: {provider}")
        api_key = os.getenv(env_var)
        if not api_key:
            raise ValueError(f"{env_var} not found in environment")

    # Validate provider is known
    if provider not in SUPPORTED_PROVIDERS:
        raise ValueError(f"Unknown provider: {provider}. Supported: {sorted(SUPPORTED_PROVIDERS)}")

    # Check SDK availability
    if not PROVIDER_AVAILABILITY.get(provider, False):
        raise NotImplementedError(
            f"{provider} SDK not installed. Install the required package to use this provider."
        )

    # --- Build client per provider ---

    if provider == "openai":
        return OpenAI(api_key=api_key)  # type: ignore[misc]

    if provider == "anthropic":
        return _anthropic_module.Anthropic(api_key=api_key)  # type: ignore[union-attr]

    if provider == "mistral":
        return _MistralClient(api_key=api_key)  # type: ignore[misc]

    if provider == "google":
        _genai.configure(api_key=api_key)  # type: ignore[union-attr]
        return _genai

    # Unreachable but satisfies linters
    raise ValueError(f"Unhandled provider: {provider}")


# ---------------------------------------------------------------------------
# Unified chat interface
# ---------------------------------------------------------------------------

def chat(
    client: Any,
    messages: list,
    model: str = "gpt-4.1",
    temperature: float = 0.7,
    provider: Optional[str] = None,
) -> str:
    """Send messages to an LLM and return the response text.

    Backward compatible: chat(client, messages) works exactly as v2.0 for
    OpenAI clients. The provider is auto-detected from the client type when
    not specified.

    Args:
        client:      SDK client returned by make_client().
        messages:    List of {"role": ..., "content": ...} dicts.
        model:       Model identifier.
        temperature: Sampling temperature.
        provider:    Explicit provider name. Auto-detected if None.
    """
    # Auto-detect provider from client type
    if provider is None:
        provider = _detect_provider_from_client(client)

    # --- OpenAI ---
    if provider == "openai":
        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
        )
        return resp.choices[0].message.content.strip()

    # --- Anthropic ---
    if provider == "anthropic":
        # Anthropic expects system message separately
        system_msg = None
        chat_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system_msg = msg["content"]
            else:
                chat_messages.append(msg)

        kwargs = {
            "model": model,
            "messages": chat_messages,
            "temperature": temperature,
            "max_tokens": 4096,
        }
        if system_msg:
            kwargs["system"] = system_msg

        resp = client.messages.create(**kwargs)
        return resp.content[0].text

    # --- Mistral ---
    if provider == "mistral":
        resp = client.chat.complete(
            model=model,
            messages=messages,
            temperature=temperature,
        )
        return resp.choices[0].message.content.strip()

    # --- Google Gemini ---
    if provider == "google":
        mdl = client.GenerativeModel(model)
        # Convert messages: Gemini expects a different format
        history = []
        last_content = ""
        for msg in messages:
            role = "user" if msg["role"] in ("user", "system") else "model"
            if msg == messages[-1]:
                last_content = msg["content"]
            else:
                history.append({"role": role, "parts": [msg["content"]]})
        chat_session = mdl.start_chat(history=history)
        reply = chat_session.send_message(last_content)
        return reply.text.strip()

    raise ValueError(f"Unknown provider: {provider}")


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _detect_provider_from_client(client: Any) -> str:
    """Detect provider from client instance type."""
    client_type = type(client).__module__ + "." + type(client).__qualname__

    if "openai" in client_type.lower():
        return "openai"
    if "anthropic" in client_type.lower():
        return "anthropic"
    if "mistral" in client_type.lower():
        return "mistral"
    # Google genai is a module, not an instance
    if hasattr(client, "GenerativeModel"):
        return "google"

    logger.warning("Could not detect provider from client type: %s, defaulting to openai", client_type)
    return "openai"


def get_available_providers() -> list:
    """Return list of providers whose SDKs are installed."""
    return [p for p, available in PROVIDER_AVAILABILITY.items() if available]
