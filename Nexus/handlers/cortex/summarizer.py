#!/home/aipass/.venv/bin/python3
# -*- coding: utf-8 -*-

# ===================AIPASS====================
# META DATA HEADER
# Name: summarizer.py - File change summarization
# Date: 2026-02-18
# Version: 1.0.0
# Category: Nexus/handlers/cortex
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2026-02-18): Initial build from v1 cortex_module.py
#
# CODE STANDARDS:
#   - Error handling: graceful LLM fallback
# =============================================

"""
Cortex Summarizer - File Change Summarization

Manages cortex.json - persistent file awareness state across sessions.
Provides LLM-powered summarization with simple fallback. The cortex block
gets injected into the system prompt for real-time workspace awareness.
"""

import sys
import json
import logging
from datetime import datetime
from pathlib import Path

AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))

logger = logging.getLogger(__name__)

NEXUS_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = NEXUS_DIR / "data"
CORTEX_PATH = DATA_DIR / "cortex.json"
MAX_SUMMARY_WORDS = 20
MAX_BLOCK_FILES = 30


def load_cortex_data() -> dict:
    """Load cortex state from data/cortex.json. Returns defaults if missing."""
    if CORTEX_PATH.exists():
        try:
            with open(CORTEX_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            if "files" not in data:
                data["files"] = {}
            return data
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to load cortex.json: {e}")
    return {"files": {}, "last_refresh": None}


def save_cortex_data(data: dict):
    """Save cortex state to data/cortex.json."""
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(CORTEX_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except IOError as e:
        logger.error(f"Failed to save cortex.json: {e}")


def _update_file_entry(files: dict, filepath: str, change_type: str,
                       abs_path: Path, timestamp: str, llm_client=None):
    """Update a single file entry in the cortex files dict (shared logic)."""
    if change_type == "deleted":
        entry = files.get(filepath, {"changes_this_session": 0, "summary": ""})
        entry.update({
            "last_change_type": "deleted",
            "last_change_time": timestamp,
            "file_exists": False,
            "changes_this_session": entry.get("changes_this_session", 0) + 1,
        })
        files[filepath] = entry
    else:
        summary = _generate_summary(abs_path, llm_client)
        if filepath not in files:
            files[filepath] = {"changes_this_session": 0}
        entry = files[filepath]
        entry.update({
            "summary": summary,
            "last_change_type": change_type,
            "last_change_time": timestamp,
            "file_exists": True,
            "changes_this_session": entry.get("changes_this_session", 0) + 1,
        })
        try:
            if abs_path.exists():
                entry["size_bytes"] = abs_path.stat().st_size
        except OSError as e:
            logger.warning("Could not stat %s: %s", abs_path, e)


def refresh_summary(filepath: str, change_type: str, llm_client=None,
                    watch_dir: "Path | None" = None) -> dict:
    """Summarize a single file change and persist to cortex.json."""
    watch_dir = watch_dir or NEXUS_DIR
    cortex = load_cortex_data()
    timestamp = datetime.now().isoformat()
    _update_file_entry(cortex["files"], filepath, change_type,
                       watch_dir / filepath, timestamp, llm_client)
    cortex["last_refresh"] = timestamp
    save_cortex_data(cortex)
    return cortex["files"].get(filepath, {})


def batch_refresh(changes: dict, llm_client=None, watch_dir: "Path | None" = None):
    """Refresh summaries for multiple changes (single load/save cycle)."""
    if not changes:
        return
    watch_dir = watch_dir or NEXUS_DIR
    cortex = load_cortex_data()
    timestamp = datetime.now().isoformat()
    for filepath, info in changes.items():
        _update_file_entry(cortex["files"], filepath,
                           info.get("change_type", "modified"),
                           watch_dir / filepath, timestamp, llm_client)
    cortex["last_refresh"] = timestamp
    save_cortex_data(cortex)
    logger.info(f"Batch refreshed {len(changes)} file summaries")


def get_cortex_block() -> str:
    """Format cortex state as text block for system prompt injection.

    Returns a string like:
        File Awareness:
        - watcher.py: Filesystem watcher (modified 2min ago)
    """
    cortex = load_cortex_data()
    files = cortex.get("files", {})
    if not files:
        return "File Awareness:\n- No files tracked yet"

    lines = ["File Awareness:"]
    now = datetime.now()

    # Split into changed vs unchanged, sort changed by recency
    changed, unchanged = [], []
    for fp, meta in files.items():
        (changed if meta.get("last_change_type", "existing") != "existing"
         else unchanged).append((fp, meta))
    changed.sort(key=lambda x: x[1].get("last_change_time", ""), reverse=True)

    display = (changed + unchanged)[:MAX_BLOCK_FILES]
    truncated = len(files) > MAX_BLOCK_FILES

    for filepath, meta in display:
        summary = meta.get("summary", "").strip()
        if summary and len(summary) > 80:
            summary = summary[:77] + "..."

        status_parts = []
        if not meta.get("file_exists", True):
            status_parts.append("DELETED")
        elif meta.get("last_change_type", "existing") != "existing":
            status_parts.append(
                f"{meta['last_change_type']} "
                f"{_format_time_ago(meta.get('last_change_time', ''), now)}"
            )
            if meta.get("changes_this_session", 0) > 1:
                status_parts.append(f"{meta['changes_this_session']}x this session")

        status = f" ({', '.join(status_parts)})" if status_parts else ""
        line = f"- {filepath}: {summary}{status}" if summary else f"- {filepath}{status}"
        lines.append(line)

    if truncated:
        lines.append(f"  ... and {len(files) - MAX_BLOCK_FILES} more tracked files")
    return "\n".join(lines)


def reset_session_counters():
    """Reset changes_this_session for all files. Called at session start."""
    cortex = load_cortex_data()
    files = cortex.get("files", {})
    reset_count = 0
    for entry in files.values():
        if entry.get("changes_this_session", 0) > 0:
            reset_count += 1
        entry["changes_this_session"] = 0
        entry.setdefault("last_change_type", "existing")
        entry.setdefault("last_change_time", datetime.now().isoformat())
        entry.setdefault("file_exists", True)
    save_cortex_data(cortex)
    if reset_count > 0:
        logger.info(f"Session reset: cleared counters for {reset_count} files")
    else:
        logger.info(f"Session initialized: {len(files)} files tracked")


def _generate_summary(filepath: Path, llm_client=None) -> str:
    """Generate summary via LLM or simple fallback."""
    if not filepath.exists():
        return "[file not found]"
    if llm_client is not None:
        try:
            return _llm_summarize(filepath, llm_client)
        except Exception as e:
            logger.warning(f"LLM summary failed for {filepath.name}: {e}")
    return _simple_summarize(filepath)


def _llm_summarize(filepath: Path, llm_client) -> str:
    """Summarize file content using an LLM client."""
    try:
        content = filepath.read_text(encoding="utf-8")
    except (IOError, UnicodeDecodeError) as e:
        return f"[unreadable: {e}]"

    if len(content) > 4000:
        content = content[:4000] + "\n... (truncated)"

    messages = [
        {"role": "system", "content": "Summarize this file in 1 sentence. "
         "Focus on purpose and key functionality. Max 15 words."},
        {"role": "user", "content": content},
    ]

    if hasattr(llm_client, "chat") and hasattr(llm_client.chat, "completions"):
        resp = llm_client.chat.completions.create(
            model="gpt-4.1-mini", messages=messages, temperature=0.3, max_tokens=60)
        summary = resp.choices[0].message.content.strip()
    elif callable(llm_client):
        summary = llm_client(messages)
    else:
        return _simple_summarize(filepath)

    summary_str = str(summary)
    words = summary_str.split()
    return " ".join(words[:MAX_SUMMARY_WORDS]) if len(words) > MAX_SUMMARY_WORDS else summary_str


def _simple_summarize(filepath: Path) -> str:
    """Generate basic summary from file metadata (no LLM needed)."""
    try:
        size = filepath.stat().st_size
    except OSError:
        return "[cannot stat file]"

    ext = filepath.suffix.lower()
    size_desc = ("tiny" if size < 100 else "small" if size < 1000
                 else "medium" if size < 10000 else f"{size // 1000}KB")
    type_map = {".py": "Python module", ".json": "JSON data", ".md": "Markdown doc"}
    type_desc = type_map.get(ext, f"{ext} file")

    hint = ""
    if ext == ".py":
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                for raw_line in f:
                    line = raw_line.strip()
                    if line and not line.startswith("#") and not line.startswith('"""'):
                        if line.startswith(("class ", "def ")):
                            hint = f" - {line.split('(')[0]}"
                        break
        except (IOError, UnicodeDecodeError):
            pass
    return f"{type_desc} ({size_desc}){hint}"


def _format_time_ago(iso_timestamp: str, now: "datetime | None" = None) -> str:
    """Format ISO timestamp as relative time (e.g. '2min ago')."""
    if not iso_timestamp:
        return ""
    now = now or datetime.now()
    try:
        dt = datetime.fromisoformat(iso_timestamp.replace("Z", "+00:00"))
        if dt.tzinfo and not now.tzinfo:
            dt = dt.replace(tzinfo=None)
        secs = int((now - dt).total_seconds())
        if secs < 60:
            return "just now"
        if secs < 3600:
            return f"{secs // 60}min ago"
        if secs < 86400:
            return f"{secs // 3600}hr ago"
        return f"{secs // 86400}d ago"
    except (ValueError, TypeError):
        return ""
