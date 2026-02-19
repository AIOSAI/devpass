#!/home/aipass/.venv/bin/python3
# -*- coding: utf-8 -*-
"""
META:
  app: Nexus
  layer: handlers
  purpose: Persistent execution context for Natural Flow
  status: Active

Persistent execution context for Nexus Natural Flow.

Maintains a Python namespace across conversation turns so variables,
imports, and state survive between code blocks.  Tracks files created /
modified, keeps an operation history, and provides a small file cache.

Rebuilt from v1 natural_flow.py ExecutionContext into Nexus v2.
"""

import io
import os
import re
import sys
import json
import signal
import contextlib
import subprocess
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))

import logging

logger = logging.getLogger(__name__)


class ExecutionTimeout(Exception):
    """Raised when code execution exceeds the allowed time."""


def _timeout_handler(_signum, _frame):
    """SIGALRM handler that raises ExecutionTimeout."""
    raise ExecutionTimeout("Code execution timed out")


class ExecutionContext:
    """Persistent Python execution environment across conversation turns.

    Pre-loads Path, os, json, subprocess, etc. into the namespace so
    generated code can use them immediately.
    """

    DEFAULT_TIMEOUT = 30  # seconds
    MAX_CACHE_ENTRIES = 5

    def __init__(self, working_dir: Optional[Path] = None,
                 nexus_dir: Optional[Path] = None):
        """Create a fresh execution context."""
        _nexus_dir = nexus_dir or Path(__file__).resolve().parent.parent.parent
        _working_dir = working_dir or Path.cwd()

        self.globals: Dict[str, Any] = {
            "Path": Path, "os": os, "json": json,
            "subprocess": subprocess, "datetime": datetime,
            "sys": sys, "re": re,
            "created_files": [], "modified_files": [],
            "executed_scripts": [],
            "last_result": None, "last_output": "",
            "working_dir": _working_dir, "nexus_dir": _nexus_dir,
        }
        self.operation_history: List[Dict[str, Any]] = []
        self.session_start: datetime = datetime.now()
        self.file_cache: List[Dict[str, Any]] = []
        self.loaded_files: Dict[str, str] = {}

    def execute(self, code: str, timeout: int = DEFAULT_TIMEOUT) -> Dict[str, Any]:
        """Execute *code* in the persistent namespace with stdout capture.

        Returns dict with success, output, result, error, code_executed.
        """
        code = code.strip()
        if not code:
            return {"success": False, "error": "Empty code block", "output": ""}

        self.globals["last_result"] = None
        output_buffer = io.StringIO()
        old_handler = None

        try:
            if hasattr(signal, "SIGALRM"):
                old_handler = signal.signal(signal.SIGALRM, _timeout_handler)
                signal.alarm(timeout)

            with contextlib.redirect_stdout(output_buffer):
                exec(code, self.globals)  # noqa: S102

            if hasattr(signal, "SIGALRM"):
                signal.alarm(0)

            captured = output_buffer.getvalue()
            result_value = self.globals.get("last_result")
            full_output = captured
            if result_value is not None and str(result_value) not in captured:
                full_output += f"\nResult: {result_value}"

            self._record(code, True, output=full_output, result=result_value)
            self.globals["last_output"] = full_output
            return {"success": True, "output": full_output.strip(),
                    "result": result_value, "code_executed": code}

        except ExecutionTimeout:
            self._record(code, False, error=f"Timed out after {timeout}s")
            return {"success": False,
                    "error": f"Execution timed out after {timeout} seconds",
                    "output": output_buffer.getvalue().strip(),
                    "code_executed": code}

        except Exception as exc:
            error_msg = f"{type(exc).__name__}: {exc}"
            self._record(code, False, error=error_msg)
            return {"success": False, "error": error_msg,
                    "output": output_buffer.getvalue().strip(),
                    "code_executed": code}

        finally:
            if hasattr(signal, "SIGALRM"):
                signal.alarm(0)
                if old_handler is not None:
                    signal.signal(signal.SIGALRM, old_handler)

    def load_file(self, file_path: str) -> Dict[str, Any]:
        """Load a file into the cache for analysis.

        Tries absolute path first, then CWD / nexus_dir / working_dir.
        """
        try:
            resolved = self._resolve_path(file_path)
            if resolved is None:
                return {"success": False, "error": f"File not found: {file_path}"}

            content = resolved.read_text(encoding="utf-8", errors="replace")
            entry = {
                "path": str(resolved), "relative_path": file_path,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "content": content, "size": len(content),
            }
            self.file_cache.insert(0, entry)
            self.loaded_files[file_path] = content

            while len(self.file_cache) > self.MAX_CACHE_ENTRIES:
                removed = self.file_cache.pop()
                self.loaded_files.pop(removed["relative_path"], None)

            return {"success": True, "content": content,
                    "file_path": str(resolved), "size": len(content),
                    "cache_entries": len(self.file_cache)}
        except Exception as exc:
            return {"success": False, "error": f"Error loading file: {exc}"}

    def clear_file_cache(self) -> str:
        """Drop all cached files."""
        self.file_cache.clear()
        self.loaded_files.clear()
        return "File cache cleared"

    def get_loaded_files_summary(self) -> str:
        """Human-readable summary of cache contents."""
        if not self.file_cache:
            return "No files currently loaded"
        lines = [f"Loaded files ({len(self.file_cache)}/{self.MAX_CACHE_ENTRIES}):"]
        for entry in self.file_cache:
            size_kb = entry["size"] / 1024
            lines.append(f"  - {entry['relative_path']} ({size_kb:.1f} KB)")
        return "\n".join(lines)

    def get_context_summary(self) -> str:
        """One-line summary of session activity."""
        parts: List[str] = []
        created = len(self.globals.get("created_files", []))
        modified = len(self.globals.get("modified_files", []))
        executed = len(self.globals.get("executed_scripts", []))
        total = len(self.operation_history)
        if created:
            parts.append(f"{created} files created")
        if modified:
            parts.append(f"{modified} files modified")
        if executed:
            parts.append(f"{executed} scripts executed")
        if total:
            parts.append(f"{total} total operations")
        return " | ".join(parts) if parts else "Clean execution context"

    def get_stats(self) -> Dict[str, Any]:
        """Detailed statistics about the execution context."""
        return {
            "session_duration": str(datetime.now() - self.session_start),
            "total_operations": len(self.operation_history),
            "successful": sum(1 for op in self.operation_history if op.get("success")),
            "failed": sum(1 for op in self.operation_history if not op.get("success")),
            "files_created": len(self.globals.get("created_files", [])),
            "files_modified": len(self.globals.get("modified_files", [])),
            "cached_files": len(self.file_cache),
            "context_summary": self.get_context_summary(),
            "recent_operations": self.operation_history[-5:],
        }

    def _record(self, code: str, success: bool, **kwargs) -> None:
        """Append an entry to the operation history."""
        entry: Dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "code": code, "success": success,
        }
        entry.update(kwargs)
        self.operation_history.append(entry)

    def _resolve_path(self, file_path: str) -> Optional[Path]:
        """Resolve *file_path* to an existing file or return None."""
        p = Path(file_path)
        if p.is_absolute():
            return p if p.is_file() else None
        candidates = [
            Path.cwd() / p,
            self.globals["nexus_dir"] / p,
            self.globals["working_dir"] / p,
        ]
        for candidate in candidates:
            if candidate.is_file():
                return candidate.resolve()
        return None
