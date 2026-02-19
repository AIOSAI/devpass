#!/home/aipass/.venv/bin/python3
# -*- coding: utf-8 -*-
"""
META:
  app: Nexus
  layer: handlers/system
  purpose: Load provider configuration and resolve API keys
  status: Active
  version: 1.0
  v1_ref: .archive/nexus_v1_original/a.i_core/a.i_profiles/Nexus/config_loader.py
"""

import sys
import os
import json
import logging
from pathlib import Path
from typing import Optional, Tuple

AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))

from dotenv import load_dotenv

# Load .env from home directory
load_dotenv(Path.home() / ".env")

logger = logging.getLogger("nexus.config_loader")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

NEXUS_ROOT = Path(__file__).resolve().parent.parent.parent
CONFIG_DIR = NEXUS_ROOT / "config"
API_CONFIG_PATH = CONFIG_DIR / "api_config.json"

# ---------------------------------------------------------------------------
# Known providers and their env var names
# ---------------------------------------------------------------------------

ALLOWED_PROVIDERS = {"openai", "anthropic", "mistral", "google"}

ENV_KEY_MAP = {
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "mistral": "MISTRAL_API_KEY",
    "google": "GOOGLE_API_KEY",
}

# ---------------------------------------------------------------------------
# Config loading
# ---------------------------------------------------------------------------

_CACHED_CONFIG: Optional[dict] = None


def load_api_config(force_reload: bool = False) -> dict:
    """Load and validate config/api_config.json.

    Caches the result after first load. Pass force_reload=True to re-read
    from disk.

    Returns:
        Parsed config dict with keys: active_provider, providers, use_langchain
    """
    global _CACHED_CONFIG

    if _CACHED_CONFIG is not None and not force_reload:
        return _CACHED_CONFIG

    if not API_CONFIG_PATH.exists():
        logger.error("api_config.json not found at %s", API_CONFIG_PATH)
        raise FileNotFoundError(f"api_config.json not found at {API_CONFIG_PATH}")

    with API_CONFIG_PATH.open(encoding="utf-8") as fh:
        cfg = json.load(fh)

    _validate_config(cfg)
    _CACHED_CONFIG = cfg
    logger.info("Loaded API config: active_provider=%s", cfg.get("active_provider"))
    return cfg


def _validate_config(cfg: dict) -> None:
    """Validate config structure and values."""
    # Must have active_provider
    active = cfg.get("active_provider")
    if not active:
        raise ValueError("api_config.json missing 'active_provider'")

    if active not in ALLOWED_PROVIDERS:
        raise ValueError(
            f"Unknown active_provider '{active}'. Allowed: {sorted(ALLOWED_PROVIDERS)}"
        )

    # Must have providers section
    providers = cfg.get("providers")
    if not providers or not isinstance(providers, dict):
        raise ValueError("api_config.json missing or empty 'providers' section")

    # Active provider must exist in providers
    if active not in providers:
        raise ValueError(
            f"Active provider '{active}' not found in providers section"
        )

    # Check for unknown providers
    unknown = set(providers.keys()) - ALLOWED_PROVIDERS
    if unknown:
        logger.warning("Unknown providers in config (ignored): %s", sorted(unknown))


# ---------------------------------------------------------------------------
# Provider accessors
# ---------------------------------------------------------------------------

def get_active_provider() -> Tuple[str, dict]:
    """Return the active provider name and its settings dict.

    Returns:
        Tuple of (provider_name, settings_dict) where settings_dict
        contains 'model', 'temperature', etc.
    """
    cfg = load_api_config()
    provider_name = cfg["active_provider"]
    settings = cfg["providers"].get(provider_name, {})
    return provider_name, settings


def get_provider_settings(provider: str) -> dict:
    """Return settings dict for a specific provider.

    Args:
        provider: Provider name (openai, anthropic, mistral, google)

    Returns:
        Settings dict with model, temperature, etc.
    """
    cfg = load_api_config()
    providers = cfg.get("providers", {})
    if provider not in providers:
        raise ValueError(f"Provider '{provider}' not found in config")
    return providers[provider]


def get_api_key(provider: str) -> str:
    """Load API key for a provider from environment variables.

    Checks both .env file (already loaded via dotenv) and system env vars.

    Args:
        provider: Provider name (openai, anthropic, mistral, google)

    Returns:
        API key string

    Raises:
        ValueError: If provider unknown or key not found
    """
    env_var = ENV_KEY_MAP.get(provider)
    if not env_var:
        raise ValueError(
            f"Unknown provider '{provider}'. Known: {sorted(ENV_KEY_MAP.keys())}"
        )

    api_key = os.getenv(env_var)
    if not api_key:
        raise ValueError(
            f"{env_var} not found in environment. "
            f"Set it in ~/.env or export it as an environment variable."
        )

    return api_key


def use_langchain() -> bool:
    """Return whether LangChain enhanced mode is enabled in config."""
    cfg = load_api_config()
    return bool(cfg.get("use_langchain", False))


# ---------------------------------------------------------------------------
# Convenience: full initialization helper
# ---------------------------------------------------------------------------

def get_ready_config() -> dict:
    """Load config and resolve the active provider's API key.

    Returns a dict with:
        provider: str
        model: str
        temperature: float
        api_key: str
        use_langchain: bool
    """
    provider_name, settings = get_active_provider()
    api_key = get_api_key(provider_name)

    return {
        "provider": provider_name,
        "model": settings.get("model", "gpt-4.1"),
        "temperature": settings.get("temperature", 0.7),
        "api_key": api_key,
        "use_langchain": use_langchain(),
    }
