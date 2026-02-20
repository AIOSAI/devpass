#!/home/aipass/.venv/bin/python3
# -*- coding: utf-8 -*-

# ===================AIPASS====================
# META DATA HEADER
# Name: langchain_interface.py - LangChain enhanced chat wrapper
# Date: 2026-02-18
# Version: 1.0.0
# Category: Nexus/handlers/system
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2026-02-18): Initial build with LangChain OpenAI wrapper
#
# CODE STANDARDS:
#   - Graceful fallback: returns None when LangChain unavailable
#   - Token estimation with actual usage logging when available
# =============================================

"""
LangChain enhanced chat wrapper with graceful fallback.

Provides LangChain-based chat with message conversion, token estimation,
and actual usage logging. Returns None on failure so callers can fall
back to the direct LLM client.
"""

import sys
import logging
from pathlib import Path
from typing import Optional, Any

AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))

logger = logging.getLogger("nexus.langchain_interface")

# ---------------------------------------------------------------------------
# LangChain availability - graceful degradation
# ---------------------------------------------------------------------------

LANGCHAIN_AVAILABLE = False
LANGCHAIN_MESSAGES_AVAILABLE = False

try:
    from langchain_openai import ChatOpenAI
    LANGCHAIN_AVAILABLE = True
except ImportError:
    ChatOpenAI = None  # type: ignore
    logger.warning("langchain_openai not installed - LangChain enhanced chat unavailable")

try:
    from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
    LANGCHAIN_MESSAGES_AVAILABLE = True
except ImportError:
    HumanMessage = None  # type: ignore
    SystemMessage = None  # type: ignore
    AIMessage = None  # type: ignore
    if LANGCHAIN_AVAILABLE:
        logger.warning("langchain_core not installed - message conversion unavailable")
        LANGCHAIN_AVAILABLE = False


# ---------------------------------------------------------------------------
# Client factory
# ---------------------------------------------------------------------------

def make_langchain_client(
    provider: str = "openai",
    api_key: Optional[str] = None,
    model: str = "gpt-4.1",
    temperature: float = 0.7,
) -> Optional[Any]:
    """Create a LangChain chat client for the given provider.

    Returns None if LangChain is not installed (graceful fallback).

    Args:
        provider:    Provider name. Currently only 'openai' is supported
                     via LangChain wrappers.
        api_key:     API key string. Required for client creation.
        model:       Model identifier.
        temperature: Sampling temperature.

    Returns:
        LangChain ChatOpenAI instance, or None if unavailable.
    """
    if not LANGCHAIN_AVAILABLE:
        logger.info("LangChain not available, returning None (caller should fallback)")
        return None

    if provider != "openai":
        logger.warning(
            "LangChain wrapper only supports openai provider currently, got '%s'",
            provider,
        )
        return None

    if api_key is None:
        logger.error("api_key is required to create LangChain client")
        return None

    try:
        from pydantic import SecretStr

        client = ChatOpenAI(  # type: ignore[misc]
            api_key=SecretStr(api_key),
            model=model,
            temperature=temperature,
        )
        logger.info("LangChain client created: model=%s, temperature=%s", model, temperature)
        return client
    except Exception as exc:
        logger.error("Failed to create LangChain client: %s", exc)
        return None


# ---------------------------------------------------------------------------
# Enhanced chat
# ---------------------------------------------------------------------------

def langchain_enhanced_chat(  # noqa: ARG001 - temperature kept for API consistency
    provider: str,
    client: Any,
    model: str,
    messages: list,
    temperature: float = 0.7,  # used by callers for config passthrough
) -> Optional[str]:
    """Send messages through LangChain enhanced pipeline.

    Converts standard message dicts to LangChain message objects,
    invokes the client, and returns the response text.

    Returns None if LangChain is not available or if the call fails,
    allowing the caller to fall back to the direct LLM client.

    Args:
        provider:    Provider name (currently only 'openai').
        client:      LangChain client from make_langchain_client().
        model:       Model identifier (for logging).
        messages:    List of {"role": ..., "content": ...} dicts.
        temperature: Sampling temperature (for logging).

    Returns:
        Response text string, or None on failure.
    """
    if not LANGCHAIN_AVAILABLE or not LANGCHAIN_MESSAGES_AVAILABLE:
        return None

    if client is None:
        logger.warning("LangChain client is None, cannot chat")
        return None

    if provider != "openai":
        logger.warning("LangChain enhanced chat only supports openai, got '%s'", provider)
        return None

    try:
        # Convert message dicts to LangChain message objects
        lc_messages = _convert_messages(messages)

        # Invoke the LangChain client
        response = client.invoke(lc_messages)

        # Estimate and log token usage
        _log_token_estimate(model, messages, response)

        # Extract text content
        if hasattr(response, "content") and isinstance(response.content, str):
            return response.content.strip()

        logger.warning("Unexpected response format from LangChain: %s", type(response))
        return str(response).strip()

    except Exception as exc:
        logger.error("LangChain enhanced chat failed: %s", exc)
        return None


# ---------------------------------------------------------------------------
# Message conversion
# ---------------------------------------------------------------------------

def _convert_messages(messages: list) -> list:
    """Convert standard message dicts to LangChain message objects.

    Args:
        messages: List of {"role": "system"|"user"|"assistant", "content": str}

    Returns:
        List of LangChain message objects (SystemMessage, HumanMessage, AIMessage)
    """
    lc_messages = []
    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")

        if role == "system":
            lc_messages.append(SystemMessage(content=content))  # type: ignore[misc]
        elif role == "user":
            lc_messages.append(HumanMessage(content=content))  # type: ignore[misc]
        elif role == "assistant":
            lc_messages.append(AIMessage(content=content))  # type: ignore[misc]
        else:
            # Default unknown roles to HumanMessage
            logger.warning("Unknown message role '%s', treating as user", role)
            lc_messages.append(HumanMessage(content=content))  # type: ignore[misc]

    return lc_messages


# ---------------------------------------------------------------------------
# Token estimation and logging
# ---------------------------------------------------------------------------

# Rough multiplier: average English word is ~1.3 tokens
TOKENS_PER_WORD = 1.3


def _log_token_estimate(model: str, messages: list, response: Any) -> None:
    """Estimate and log token usage for a LangChain call.

    This is a rough approximation based on word count. Actual token
    counts vary by model and tokenizer.

    Args:
        model:    Model name (for log context).
        messages: Input messages.
        response: LangChain response object.
    """
    try:
        # Estimate input tokens from message content
        input_words = sum(
            len(msg.get("content", "").split())
            for msg in messages
        )
        input_tokens = int(input_words * TOKENS_PER_WORD)

        # Estimate output tokens from response
        output_text = ""
        if hasattr(response, "content") and isinstance(response.content, str):
            output_text = response.content
        output_words = len(output_text.split()) if output_text else 0
        output_tokens = int(output_words * TOKENS_PER_WORD)

        total_tokens = input_tokens + output_tokens

        logger.info(
            "LangChain token estimate [%s]: ~%d input, ~%d output, ~%d total",
            model,
            input_tokens,
            output_tokens,
            total_tokens,
        )

        # Check for actual usage metadata from LangChain response
        if hasattr(response, "response_metadata"):
            metadata = response.response_metadata
            if isinstance(metadata, dict) and "token_usage" in metadata:
                usage = metadata["token_usage"]
                logger.info(
                    "LangChain actual usage [%s]: %d input, %d output, %d total",
                    model,
                    usage.get("prompt_tokens", 0),
                    usage.get("completion_tokens", 0),
                    usage.get("total_tokens", 0),
                )

    except Exception as exc:
        logger.info("Token estimation failed (non-critical): %s", exc)


# ---------------------------------------------------------------------------
# Availability check
# ---------------------------------------------------------------------------

def is_available() -> bool:
    """Return True if LangChain enhanced chat is fully available."""
    return LANGCHAIN_AVAILABLE and LANGCHAIN_MESSAGES_AVAILABLE
