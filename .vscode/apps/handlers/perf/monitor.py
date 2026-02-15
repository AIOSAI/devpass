#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: monitor.py - Performance Monitoring Handler
# Date: 2025-11-23
# Version: 1.0.1
# Category: vscode/perf
# Branch: .vscode
#
# CHANGELOG (Max 5 entries):
#   - v1.0.1 (2025-11-29): Fixed type errors and added infrastructure imports
#   - v1.0.0 (2025-11-23): Migrated from .local/bin/pylance-monitor to AIPass standards
#
# CODE STANDARDS:
#   - Handler implements logic, module orchestrates
#   - Pure functions where possible
# =============================================

"""
Performance Monitoring Handler

Core logic for monitoring Pylance and VS Code memory usage.
Provides data collection functions for module orchestration.
"""

import subprocess
from pathlib import Path
from typing import Tuple, Dict, Any


def get_process_memory(pattern: str) -> Tuple[float, int]:
    """
    Get memory usage for processes matching pattern

    Args:
        pattern: Process name pattern to search for

    Returns:
        Tuple of (total_mb, process_count)
    """
    try:
        result = subprocess.run(
            ["ps", "aux"],
            capture_output=True,
            text=True,
            check=False
        )

        total_mb = 0
        count = 0

        for line in result.stdout.split('\n'):
            if pattern in line and 'grep' not in line:
                parts = line.split()
                if len(parts) >= 6:
                    rss_kb = int(parts[5])
                    total_mb += rss_kb / 1024
                    count += 1

        return total_mb, count

    except Exception:
        return 0.0, 0


def get_system_memory() -> Tuple[int, int, float]:
    """
    Get total system memory usage

    Returns:
        Tuple of (used_mb, total_mb, percent)
    """
    try:
        result = subprocess.run(
            ["free", "-m"],
            capture_output=True,
            text=True,
            check=False
        )

        for line in result.stdout.split('\n'):
            if line.startswith('Mem:'):
                parts = line.split()
                total = int(parts[1])
                used = int(parts[2])
                percent = (used / total) * 100
                return used, total, percent

        return 0, 0, 0.0

    except Exception:
        return 0, 0, 0.0


def count_python_files() -> int:
    """
    Count accessible Python files based on pyrightconfig.json exclusions

    Returns:
        Count of Python files
    """
    excludes = [
        ".venv", "venv", "env", "node_modules", "__pycache__",
        ".git", ".archive", ".backup", "MEMORY_BANK", "system_logs",
        "logs", ".cache", ".local", ".claude", "mcp_servers",
        "speakeasy", "Nexus", "backup_system", "void", "workshop",
        ".config", ".gemini", "input_x", "extensions"
    ]

    count = 0
    base = Path("/home/aipass")

    for py_file in base.rglob("*.py"):
        if not any(excl in py_file.parts for excl in excludes):
            count += 1

    return count


def gather_stats(include_file_count: bool = False) -> Dict[str, Any]:
    """
    Gather all performance statistics

    Args:
        include_file_count: Whether to scan and count Python files

    Returns:
        Dictionary with all stats
    """
    pylance_mb, pylance_count = get_process_memory("pylance")
    vscode_mb, vscode_count = get_process_memory("/usr/share/code/code")
    used_mb, total_mb, percent = get_system_memory()

    stats: Dict[str, Any] = {
        "system": {
            "used_mb": used_mb,
            "total_mb": total_mb,
            "percent": percent
        },
        "pylance": {
            "memory_mb": pylance_mb,
            "process_count": pylance_count
        },
        "vscode": {
            "memory_mb": vscode_mb,
            "process_count": vscode_count
        }
    }

    if include_file_count:
        stats["python_files"] = count_python_files()

    return stats


def get_health_status(memory_mb: float) -> str:
    """
    Get health status for Pylance memory usage

    Args:
        memory_mb: Pylance memory in MB

    Returns:
        Status string: 'healthy', 'normal', 'warning', or 'critical'
    """
    if memory_mb < 400:
        return "healthy"
    elif memory_mb < 600:
        return "normal"
    elif memory_mb < 700:
        return "warning"
    else:
        return "critical"


def get_recommendation(stats: Dict[str, Any]) -> str:
    """
    Get recommendation based on current stats

    Args:
        stats: Statistics dictionary from gather_stats()

    Returns:
        Recommendation string or empty string
    """
    pylance_mb = stats["pylance"]["memory_mb"]
    system_percent = stats["system"]["percent"]

    if pylance_mb > 700:
        return "Restart VS Code to reset Pylance memory"
    elif system_percent > 70:
        return "System memory high - close unused apps"
    else:
        return ""
