"""
Lightweight Prax bootstrap fallback for devepulse.

This module installs minimal stub implementations of the Prax logging
stack so that downstream imports keep working if Prax is missing or
broken. It is intentionally small so the same file can be copied into
other branches while the real Prax system is still under development.
"""

from __future__ import annotations

import logging
import sys
import types
from pathlib import Path
from typing import Any, Dict


_LOGGER = logging.getLogger("devepulse.prax_fallback")


class _FallbackSystemLogger:
    """Simple stand-in that prefixes messages so we notice Prax is offline."""

    def __init__(self, base_logger: logging.Logger | None = None) -> None:
        self._logger = base_logger or logging.getLogger("prax-fallback")

    def info(self, message: str, *args: Any, **kwargs: Any) -> None:  # noqa: D401 - mirror logging API
        self._logger.info("[Prax offline] " + message, *args, **kwargs)

    def warning(self, message: str, *args: Any, **kwargs: Any) -> None:
        self._logger.warning("[Prax offline] " + message, *args, **kwargs)

    def error(self, message: str, *args: Any, **kwargs: Any) -> None:
        self._logger.error("[Prax offline] " + message, *args, **kwargs)


def _ensure_package(fullname: str) -> None:
    """
    Ensure parent packages exist in sys.modules so that a stub module
    can be registered under ``fullname``.
    """
    parts = fullname.split(".")
    for idx in range(1, len(parts)):
        prefix = ".".join(parts[:idx])
        if prefix not in sys.modules:
            pkg = types.ModuleType(prefix)
            pkg.__path__ = []  # type: ignore[attr-defined]
            sys.modules[prefix] = pkg


def _install_stub(fullname: str, attributes: Dict[str, Any]) -> None:
    """Register a stub module in ``sys.modules`` if it is missing."""
    _ensure_package(fullname)
    sys.modules.pop(fullname, None)  # remove partially imported modules
    module = types.ModuleType(fullname)
    for key, value in attributes.items():
        setattr(module, key, value)
    sys.modules[fullname] = module


def install_prax_fallback() -> bool:
    """
    Install stub modules if Prax cannot be imported.

    Returns ``True`` when the fallback was needed, ``False`` otherwise.
    """
    try:
        import prax.apps.prax_logger  # type: ignore  # noqa: F401
        return False
    except Exception as exc:  # pragma: no cover - we only run this in failure scenarios
        _LOGGER.warning("Prax logger unavailable (%s); enabling fallback.", exc, exc_info=True)

    fallback_logger = _FallbackSystemLogger()

    _install_stub(
        "prax.apps.prax_logger",
        {
            "system_logger": fallback_logger,
            "setup_system_logger": lambda: fallback_logger,
            "log_operation": lambda *args, **kwargs: None,
        },
    )

    base_path = Path.home() / "aipass_core"
    _install_stub(
        "prax.apps.prax_config",
        {
            "AIPASS_ROOT": base_path,
            "PRAX_ROOT": base_path / "prax",
            "ECOSYSTEM_ROOT": base_path,
            "SYSTEM_LOGS_DIR": base_path / "logs",
            "PRAX_JSON_DIR": base_path / "prax" / "prax_json",
            "DEFAULT_LOG_LEVEL": logging.INFO,
            "lines_to_bytes": lambda lines, avg_bytes_per_line=150: lines * avg_bytes_per_line,
            "load_ignore_patterns_from_config": lambda: [],
            "ensure_prax_logger_config": lambda: {},
        },
    )

    _install_stub(
        "prax.apps.prax_registry",
        {
            "save_module_registry": lambda *args, **kwargs: None,
            "load_module_registry": lambda *args, **kwargs: {},
        },
    )

    _install_stub(
        "prax.apps.prax_handlers",
        {
            "system_logger": fallback_logger,
            "get_system_logger": lambda: fallback_logger,
        },
    )

    _install_stub(
        "prax.apps.prax_discovery",
        {
            "discover_python_modules": lambda: {},
            "scan_directory_safely": lambda *args, **kwargs: None,
            "start_file_watcher": lambda: None,
            "stop_file_watcher": lambda: None,
            "is_file_watcher_active": lambda: False,
        },
    )

    _LOGGER.info("Prax fallback installed; continuing with degraded logging.")
    return True


__all__ = ["install_prax_fallback"]
