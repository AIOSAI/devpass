#!/home/aipass/.venv/bin/python3
# -*- coding: utf-8 -*-
"""Tests for the cortex file awareness system (handlers/cortex/)."""

import sys
import tempfile
from pathlib import Path

AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))

NEXUS_DIR = Path(__file__).resolve().parent.parent
if str(NEXUS_DIR) not in sys.path:
    sys.path.insert(0, str(NEXUS_DIR))


def test_cortex_watcher_creation():
    """CortexFileWatcher initializes without errors."""
    from handlers.cortex.watcher import CortexFileWatcher

    watcher = CortexFileWatcher(watch_dir=NEXUS_DIR)
    assert watcher.watch_dir == NEXUS_DIR
    assert len(watcher.changes) == 0


def test_cortex_watcher_valid_file_check():
    """Watcher correctly filters valid and invalid files."""
    from handlers.cortex.watcher import CortexFileWatcher

    watcher = CortexFileWatcher()

    # Valid files
    assert watcher._is_valid_file(Path("/tmp/test.py")) is True
    assert watcher._is_valid_file(Path("/tmp/test.json")) is True
    assert watcher._is_valid_file(Path("/tmp/test.md")) is True

    # Invalid: wrong extension
    assert watcher._is_valid_file(Path("/tmp/test.txt")) is False
    assert watcher._is_valid_file(Path("/tmp/test.log")) is False

    # Invalid: ignored directories
    assert watcher._is_valid_file(Path("/tmp/.venv/test.py")) is False
    assert watcher._is_valid_file(Path("/tmp/__pycache__/test.py")) is False
    assert watcher._is_valid_file(Path("/tmp/.git/test.py")) is False

    # Invalid: ignored files
    assert watcher._is_valid_file(Path("/tmp/cortex.json")) is False
    assert watcher._is_valid_file(Path("/tmp/pulse.json")) is False


def test_cortex_watcher_get_recent_empty():
    """get_recent_changes returns empty list on fresh watcher."""
    from handlers.cortex.watcher import CortexFileWatcher

    watcher = CortexFileWatcher()
    recent = watcher.get_recent_changes()
    assert recent == []


def test_cortex_summarizer_load_save():
    """Cortex data can be loaded and saved."""
    from handlers.cortex.summarizer import load_cortex_data, save_cortex_data

    # Load (creates defaults if missing)
    data = load_cortex_data()
    assert "files" in data

    # Save should not error
    save_cortex_data(data)


def test_cortex_summarizer_simple_summary():
    """_simple_summarize generates basic file descriptions."""
    from handlers.cortex.summarizer import _simple_summarize

    # Create a temp Python file
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
        f.write("class TestClass:\n    pass\n")
        temp_path = Path(f.name)

    try:
        summary = _simple_summarize(temp_path)
        assert "Python module" in summary
    finally:
        temp_path.unlink(missing_ok=True)


def test_cortex_block_format():
    """get_cortex_block returns formatted text block."""
    from handlers.cortex.summarizer import get_cortex_block

    block = get_cortex_block()
    assert block.startswith("File Awareness:")


def test_cortex_time_ago():
    """_format_time_ago produces readable relative times."""
    from handlers.cortex.summarizer import _format_time_ago
    from datetime import datetime, timedelta

    now = datetime.now()

    # Just now (10 seconds ago)
    recent = (now - timedelta(seconds=10)).isoformat()
    assert _format_time_ago(recent, now) == "just now"

    # Minutes ago
    minutes = (now - timedelta(minutes=5)).isoformat()
    assert "min ago" in _format_time_ago(minutes, now)

    # Hours ago
    hours = (now - timedelta(hours=3)).isoformat()
    assert "hr ago" in _format_time_ago(hours, now)

    # Days ago
    days = (now - timedelta(days=2)).isoformat()
    assert "d ago" in _format_time_ago(days, now)


def test_cortex_session_reset():
    """reset_session_counters clears change counts."""
    from handlers.cortex.summarizer import reset_session_counters, load_cortex_data

    reset_session_counters()
    data = load_cortex_data()
    for entry in data.get("files", {}).values():
        assert entry.get("changes_this_session", 0) == 0
