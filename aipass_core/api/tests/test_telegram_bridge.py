#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: test_telegram_bridge.py - Telegram Bridge v4 Test Suite
# Date: 2026-02-12
# Version: 2.0.0
# Category: api/tests
#
# CHANGELOG (Max 5 entries):
#   - v2.0.0 (2026-02-12): Complete rewrite for v4 tmux architecture (FPLAN-0317)
#   - v1.4.0 (2026-02-10): Add file_handler and raw_prompt tests (Phase 5 FPLAN-0312)
#
# CODE STANDARDS:
#   - Pure pytest with monkeypatch/tmp_path fixtures
#   - No real Telegram API connections
#   - No real tmux sessions
#   - No Prax imports (handler tier 3)
# =============================================

"""
Telegram Bridge v4 Test Suite

Covers:
- Config loading (config.py)
- Rate limiting and user allowlist (bridge.py)
- Branch targeting (bridge.py)
- Pending file coordination (bridge.py)
- Response chunking (bridge.py)
- tmux session manager (tmux_manager.py)
- Session store v2 (session_store.py)
- Stop hook response extraction (telegram_response.py)
- File handler (file_handler.py)
- Session commands (bridge.py)
"""

import sys
import asyncio
import json
import time
from pathlib import Path
from typing import Generator
from unittest.mock import AsyncMock, patch, MagicMock

import pytest
from telegram import Update

# ---------------------------------------------------------------------------
# Infrastructure
# ---------------------------------------------------------------------------
AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))

# Modules under test
from api.apps.handlers.telegram import config as tg_config
from api.apps.handlers.telegram import bridge as tg_bridge
from api.apps.handlers.telegram import session_store as tg_session_store
from api.apps.handlers.telegram import tmux_manager as tg_tmux
from api.apps.handlers.telegram.file_handler import (
    detect_file_type, build_file_prompt, cleanup_file,
    MAX_FILE_SIZE, SUPPORTED_TEXT_EXTENSIONS,
)

# Stop hook module (lives outside the api package)
sys.path.insert(0, str(Path.home() / ".claude" / "hooks"))
import telegram_response as tg_hook


# =============================================
# FIXTURES
# =============================================

@pytest.fixture
def valid_config_file(tmp_path: Path) -> Path:
    """Write a valid Telegram config JSON and return its path."""
    cfg = {
        "telegram_bot_token": "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11",
        "telegram_bot_username": "test_bridge_bot",
        "allowed_user_ids": [111111, 222222]
    }
    cfg_path = tmp_path / "telegram_config.json"
    cfg_path.write_text(json.dumps(cfg), encoding="utf-8")
    return cfg_path


@pytest.fixture
def empty_allowlist_config_file(tmp_path: Path) -> Path:
    """Config with empty allowed_user_ids list (allow all)."""
    cfg = {
        "telegram_bot_token": "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11",
        "telegram_bot_username": "test_bridge_bot",
        "allowed_user_ids": []
    }
    cfg_path = tmp_path / "telegram_config.json"
    cfg_path.write_text(json.dumps(cfg), encoding="utf-8")
    return cfg_path


@pytest.fixture
def no_token_config_file(tmp_path: Path) -> Path:
    """Config with missing bot token."""
    cfg = {"telegram_bot_username": "test_bridge_bot"}
    cfg_path = tmp_path / "telegram_config.json"
    cfg_path.write_text(json.dumps(cfg), encoding="utf-8")
    return cfg_path


@pytest.fixture
def invalid_json_file(tmp_path: Path) -> Path:
    """File containing invalid JSON."""
    cfg_path = tmp_path / "telegram_config.json"
    cfg_path.write_text("{not valid json!!!", encoding="utf-8")
    return cfg_path


@pytest.fixture(autouse=True)
def _clear_rate_limiter():
    """Clear the in-memory rate limit tracker before every test."""
    tg_bridge._rate_limit_tracker.clear()
    yield
    tg_bridge._rate_limit_tracker.clear()


@pytest.fixture
def session_file(tmp_path: Path) -> Path:
    """Provide a temporary session file."""
    return tmp_path / "telegram_sessions.json"


@pytest.fixture
def pending_dir(tmp_path: Path) -> Path:
    """Provide a temporary pending directory."""
    d = tmp_path / "telegram_pending"
    d.mkdir()
    return d


# =============================================
# 1. CONFIG TESTS
# =============================================

class TestLoadConfig:
    """Tests for config.load_telegram_config."""

    def test_load_config_valid(self, monkeypatch: pytest.MonkeyPatch, valid_config_file: Path) -> None:
        """Valid JSON loads correctly."""
        monkeypatch.setattr(tg_config, "CONFIG_PATH", valid_config_file)
        result = tg_config.load_telegram_config()
        assert result is not None
        assert result["telegram_bot_token"] == "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"

    def test_load_config_missing_file(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        """Returns None when config file does not exist."""
        monkeypatch.setattr(tg_config, "CONFIG_PATH", tmp_path / "nonexistent.json")
        assert tg_config.load_telegram_config() is None

    def test_load_config_invalid_json(self, monkeypatch: pytest.MonkeyPatch, invalid_json_file: Path) -> None:
        """Returns None for malformed JSON."""
        monkeypatch.setattr(tg_config, "CONFIG_PATH", invalid_json_file)
        assert tg_config.load_telegram_config() is None


class TestGetBotToken:
    """Tests for config.get_bot_token."""

    def test_get_bot_token(self, monkeypatch: pytest.MonkeyPatch, valid_config_file: Path) -> None:
        """Extracts token from valid config."""
        monkeypatch.setattr(tg_config, "CONFIG_PATH", valid_config_file)
        assert tg_config.get_bot_token() == "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"

    def test_get_bot_token_missing(self, monkeypatch: pytest.MonkeyPatch, no_token_config_file: Path) -> None:
        """Returns None when token key absent."""
        monkeypatch.setattr(tg_config, "CONFIG_PATH", no_token_config_file)
        assert tg_config.get_bot_token() is None


class TestGetAllowedUserIds:
    """Tests for config.get_allowed_user_ids."""

    def test_get_allowed_user_ids(self, monkeypatch: pytest.MonkeyPatch, valid_config_file: Path) -> None:
        """Returns list of ints from config."""
        monkeypatch.setattr(tg_config, "CONFIG_PATH", valid_config_file)
        ids = tg_config.get_allowed_user_ids()
        assert ids == [111111, 222222]

    def test_get_allowed_user_ids_empty(self, monkeypatch: pytest.MonkeyPatch, empty_allowlist_config_file: Path) -> None:
        """Returns empty list (allow all)."""
        monkeypatch.setattr(tg_config, "CONFIG_PATH", empty_allowlist_config_file)
        assert tg_config.get_allowed_user_ids() == []


# =============================================
# 2. RATE LIMITING TESTS
# =============================================

class TestCheckRateLimit:
    """Tests for bridge.check_rate_limit."""

    def test_rate_limit_allows_within_limit(self) -> None:
        """5 messages within window should be allowed."""
        for _ in range(5):
            assert tg_bridge.check_rate_limit(1001) is True

    def test_rate_limit_blocks_over_limit(self) -> None:
        """6th message should be blocked."""
        for _ in range(5):
            tg_bridge.check_rate_limit(2002)
        assert tg_bridge.check_rate_limit(2002) is False

    def test_rate_limit_window_expires(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """After window expires, messages allowed again."""
        fake_time = 1000000.0
        monkeypatch.setattr(time, "time", lambda: fake_time)

        for _ in range(5):
            tg_bridge.check_rate_limit(3003)
        assert tg_bridge.check_rate_limit(3003) is False

        fake_time += 61.0
        monkeypatch.setattr(time, "time", lambda: fake_time)
        assert tg_bridge.check_rate_limit(3003) is True

    def test_rate_limit_per_user(self) -> None:
        """Rate limits tracked independently per user."""
        for _ in range(5):
            tg_bridge.check_rate_limit(4001)
        assert tg_bridge.check_rate_limit(4001) is False
        assert tg_bridge.check_rate_limit(4002) is True


# =============================================
# 3. USER ALLOWLIST TESTS
# =============================================

class TestIsUserAllowed:
    """Tests for bridge.is_user_allowed."""

    def test_empty_allowlist_allows_all(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Empty allowlist means allow everyone."""
        monkeypatch.setattr("api.apps.handlers.telegram.bridge.get_allowed_user_ids", lambda: [])
        assert tg_bridge.is_user_allowed(999999) is True

    def test_user_in_allowlist(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """User in allowlist returns True."""
        monkeypatch.setattr("api.apps.handlers.telegram.bridge.get_allowed_user_ids", lambda: [111, 222])
        assert tg_bridge.is_user_allowed(222) is True

    def test_user_not_in_allowlist(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """User NOT in allowlist returns False."""
        monkeypatch.setattr("api.apps.handlers.telegram.bridge.get_allowed_user_ids", lambda: [111, 222])
        assert tg_bridge.is_user_allowed(444) is False


# =============================================
# 4. BRANCH TARGETING TESTS
# =============================================

class TestResolveBranchTarget:
    """Tests for bridge.resolve_branch_target."""

    def test_no_branch_prefix(self) -> None:
        """Message without @prefix uses default branch."""
        msg, branch, path = tg_bridge.resolve_branch_target("hello world")
        assert msg == "hello world"
        assert branch == tg_bridge.DEFAULT_BRANCH

    def test_branch_prefix_not_in_registry(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        """Unknown @branch falls back to default."""
        registry = {"branches": []}
        reg_file = tmp_path / "registry.json"
        reg_file.write_text(json.dumps(registry))
        monkeypatch.setattr(tg_bridge, "BRANCH_REGISTRY_PATH", reg_file)

        msg, branch, path = tg_bridge.resolve_branch_target("@nonexistent hello")
        assert branch == tg_bridge.DEFAULT_BRANCH

    def test_branch_prefix_resolved(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        """Valid @branch resolves to branch path."""
        branch_dir = tmp_path / "test_branch"
        branch_dir.mkdir()
        registry = {"branches": [{"email": "@test_branch", "path": str(branch_dir)}]}
        reg_file = tmp_path / "registry.json"
        reg_file.write_text(json.dumps(registry))
        monkeypatch.setattr(tg_bridge, "BRANCH_REGISTRY_PATH", reg_file)

        msg, branch, path = tg_bridge.resolve_branch_target("@test_branch hello world")
        assert msg == "hello world"
        assert branch == "test_branch"
        assert path == branch_dir


# =============================================
# 5. RESPONSE CHUNKING TESTS
# =============================================

class TestChunkResponse:
    """Tests for bridge.chunk_response."""

    def test_chunk_short_message(self) -> None:
        """Short message returns single chunk."""
        chunks = tg_bridge.chunk_response("Hello!")
        assert len(chunks) == 1

    def test_chunk_at_limit(self) -> None:
        """Message at limit returns single chunk."""
        text = "a" * 4096
        chunks = tg_bridge.chunk_response(text)
        assert len(chunks) == 1

    def test_chunk_long_message(self) -> None:
        """Message over limit is split."""
        text = "This is a test sentence. " * 300
        chunks = tg_bridge.chunk_response(text)
        assert len(chunks) >= 2
        for chunk in chunks:
            assert len(chunk) <= 4096

    def test_chunk_no_good_break(self) -> None:
        """Hard-breaks at limit with no break points."""
        text = "x" * 8000
        chunks = tg_bridge.chunk_response(text, limit=4096)
        assert len(chunks) == 2
        assert len(chunks[0]) == 4096


# =============================================
# 6. PENDING FILE TESTS
# =============================================

class TestWritePendingFile:
    """Tests for bridge.write_pending_file."""

    def test_write_pending_file(self, monkeypatch: pytest.MonkeyPatch, pending_dir: Path) -> None:
        """Pending file is created with correct data."""
        monkeypatch.setattr(tg_bridge, "PENDING_DIR", pending_dir)

        result = tg_bridge.write_pending_file(
            branch_name="dev_central",
            chat_id=12345,
            message_id=100,
            bot_token="test-token",
            session_id="test-session-id",
            processing_message_id=101,
        )

        assert result is True
        pending_path = pending_dir / "telegram-dev_central.json"
        assert pending_path.exists()

        data = json.loads(pending_path.read_text())
        assert data["chat_id"] == 12345
        assert data["bot_token"] == "test-token"
        assert data["session_id"] == "test-session-id"
        assert data["processing_message_id"] == 101

    def test_write_pending_file_creates_dir(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        """Pending file creation creates parent directory."""
        deep_dir = tmp_path / "a" / "b" / "pending"
        monkeypatch.setattr(tg_bridge, "PENDING_DIR", deep_dir)

        result = tg_bridge.write_pending_file(
            branch_name="test",
            chat_id=1,
            message_id=1,
            bot_token="tok",
            session_id="sid",
        )

        assert result is True
        assert (deep_dir / "telegram-test.json").exists()


# =============================================
# 7. SESSION STORE v2 TESTS
# =============================================

class TestSessionStoreCRUD:
    """Tests for session_store save, get, clear with branch_name."""

    def test_save_and_get_session(self, monkeypatch: pytest.MonkeyPatch, session_file: Path) -> None:
        """Saving with branch_name and retrieving returns correct data."""
        monkeypatch.setattr(tg_session_store, "SESSION_FILE", session_file)

        tg_session_store.save_session(12345, "dev_central")
        result = tg_session_store.get_session(12345)

        assert result is not None
        assert result["branch_name"] == "dev_central"
        assert result["message_count"] == 1

    def test_save_session_increments_count(self, monkeypatch: pytest.MonkeyPatch, session_file: Path) -> None:
        """Same branch_name increments message_count."""
        monkeypatch.setattr(tg_session_store, "SESSION_FILE", session_file)

        tg_session_store.save_session(12345, "dev_central")
        tg_session_store.save_session(12345, "dev_central")
        tg_session_store.save_session(12345, "dev_central")

        result = tg_session_store.get_session(12345)
        assert result["message_count"] == 3

    def test_save_new_branch_resets(self, monkeypatch: pytest.MonkeyPatch, session_file: Path) -> None:
        """Different branch_name replaces entry."""
        monkeypatch.setattr(tg_session_store, "SESSION_FILE", session_file)

        tg_session_store.save_session(12345, "dev_central")
        tg_session_store.save_session(12345, "dev_central")
        tg_session_store.save_session(12345, "projects")

        result = tg_session_store.get_session(12345)
        assert result["branch_name"] == "projects"
        assert result["message_count"] == 1

    def test_clear_session(self, monkeypatch: pytest.MonkeyPatch, session_file: Path) -> None:
        """Clearing removes the session."""
        monkeypatch.setattr(tg_session_store, "SESSION_FILE", session_file)

        tg_session_store.save_session(12345, "dev_central")
        tg_session_store.clear_session(12345)
        assert tg_session_store.get_session(12345) is None

    def test_get_session_nonexistent(self, monkeypatch: pytest.MonkeyPatch, session_file: Path) -> None:
        """Getting nonexistent session returns None."""
        monkeypatch.setattr(tg_session_store, "SESSION_FILE", session_file)
        assert tg_session_store.get_session(99999) is None

    def test_multiple_chats_independent(self, monkeypatch: pytest.MonkeyPatch, session_file: Path) -> None:
        """Sessions for different chats are independent."""
        monkeypatch.setattr(tg_session_store, "SESSION_FILE", session_file)

        tg_session_store.save_session(111, "dev_central")
        tg_session_store.save_session(222, "projects")

        assert tg_session_store.get_session(111)["branch_name"] == "dev_central"
        assert tg_session_store.get_session(222)["branch_name"] == "projects"


class TestGetSessionByBranch:
    """Tests for session_store.get_session_by_branch."""

    def test_find_by_branch(self, monkeypatch: pytest.MonkeyPatch, session_file: Path) -> None:
        """Find session entry by branch name."""
        monkeypatch.setattr(tg_session_store, "SESSION_FILE", session_file)

        tg_session_store.save_session(12345, "dev_central")
        result = tg_session_store.get_session_by_branch("dev_central")
        assert result is not None
        assert result["branch_name"] == "dev_central"

    def test_not_found(self, monkeypatch: pytest.MonkeyPatch, session_file: Path) -> None:
        """Returns None when branch not in store."""
        monkeypatch.setattr(tg_session_store, "SESSION_FILE", session_file)
        assert tg_session_store.get_session_by_branch("nonexistent") is None


class TestGetSessionInfo:
    """Tests for session_store.get_session_info."""

    def test_with_session(self, monkeypatch: pytest.MonkeyPatch, session_file: Path) -> None:
        """Returns formatted info when session exists."""
        monkeypatch.setattr(tg_session_store, "SESSION_FILE", session_file)
        tg_session_store.save_session(12345, "dev_central")
        info = tg_session_store.get_session_info(12345)
        assert "dev_central" in info
        assert "Messages: 1" in info

    def test_no_session(self, monkeypatch: pytest.MonkeyPatch, session_file: Path) -> None:
        """Returns 'no active session' when none exists."""
        monkeypatch.setattr(tg_session_store, "SESSION_FILE", session_file)
        info = tg_session_store.get_session_info(99999)
        assert "No active session" in info


class TestSessionStoreRobustness:
    """Tests for session_store handling edge cases."""

    def test_missing_file_returns_none(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        """Reading from nonexistent file returns None."""
        monkeypatch.setattr(tg_session_store, "SESSION_FILE", tmp_path / "nonexistent.json")
        assert tg_session_store.get_session(12345) is None

    def test_corrupt_json(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        """Corrupt JSON handled gracefully."""
        corrupt = tmp_path / "sessions.json"
        corrupt.write_text("{not valid!!!")
        monkeypatch.setattr(tg_session_store, "SESSION_FILE", corrupt)
        assert tg_session_store.get_session(12345) is None

    def test_save_creates_parent_dir(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        """save_session creates parent dirs."""
        deep = tmp_path / "a" / "b" / "sessions.json"
        monkeypatch.setattr(tg_session_store, "SESSION_FILE", deep)
        tg_session_store.save_session(12345, "test")
        assert deep.exists()


# =============================================
# 8. TMUX MANAGER TESTS
# =============================================

class TestTmuxManagerSessionName:
    """Tests for tmux_manager._session_name."""

    def test_session_name_format(self) -> None:
        """Session name is telegram-{branch}."""
        assert tg_tmux._session_name("dev_central") == "telegram-dev_central"

    def test_session_name_prefix(self) -> None:
        """All session names start with prefix."""
        assert tg_tmux._session_name("test").startswith(tg_tmux.SESSION_PREFIX)


class TestTmuxManagerListSessions:
    """Tests for tmux_manager.list_sessions."""

    def test_list_sessions_parses_output(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Parses tmux list-sessions output correctly."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "telegram-dev_central\ntelegram-projects\nother-session\n"
        monkeypatch.setattr("subprocess.run", lambda *a, **kw: mock_result)

        sessions = tg_tmux.list_sessions()
        assert "dev_central" in sessions
        assert "projects" in sessions
        assert len(sessions) == 2  # 'other-session' filtered out

    def test_list_sessions_empty(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Returns empty list when no tmux sessions."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        monkeypatch.setattr("subprocess.run", lambda *a, **kw: mock_result)

        assert tg_tmux.list_sessions() == []


class TestTmuxManagerSessionExists:
    """Tests for tmux_manager.session_exists."""

    def test_session_exists_true(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Returns True when tmux has-session succeeds."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        monkeypatch.setattr("subprocess.run", lambda *a, **kw: mock_result)

        assert tg_tmux.session_exists("dev_central") is True

    def test_session_exists_false(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Returns False when tmux has-session fails."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        monkeypatch.setattr("subprocess.run", lambda *a, **kw: mock_result)

        assert tg_tmux.session_exists("dev_central") is False


class TestTmuxManagerCreateSession:
    """Tests for tmux_manager.create_session."""

    def test_create_session_success(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        """Successful session creation returns True."""
        call_count = {"n": 0}

        def mock_run(*args, **kwargs):
            call_count["n"] += 1
            result = MagicMock()
            if call_count["n"] == 1:
                # has-session check - session doesn't exist
                result.returncode = 1
            else:
                # new-session or send-keys
                result.returncode = 0
                result.stderr = ""
            return result

        monkeypatch.setattr("subprocess.run", mock_run)

        assert tg_tmux.create_session("test", tmp_path) is True

    def test_create_session_already_exists(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        """Returns True when session already exists."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        monkeypatch.setattr("subprocess.run", lambda *a, **kw: mock_result)

        assert tg_tmux.create_session("test", tmp_path) is True

    def test_create_session_invalid_path(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        """Returns False when path doesn't exist."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        monkeypatch.setattr("subprocess.run", lambda *a, **kw: mock_result)

        assert tg_tmux.create_session("test", tmp_path / "nonexistent") is False


class TestTmuxManagerSendMessage:
    """Tests for tmux_manager.send_message."""

    def test_send_message_success(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Successful send returns True."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stderr = ""
        monkeypatch.setattr("subprocess.run", lambda *a, **kw: mock_result)

        result = asyncio.run(tg_tmux.send_message("dev_central", "hello"))
        assert result is True

    def test_send_message_no_session(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Returns False when session doesn't exist."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        monkeypatch.setattr("subprocess.run", lambda *a, **kw: mock_result)

        result = asyncio.run(tg_tmux.send_message("nonexistent", "hello"))
        assert result is False


class TestTmuxManagerKillSession:
    """Tests for tmux_manager.kill_session."""

    def test_kill_session_success(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Successful kill returns True."""
        call_count = {"n": 0}

        def mock_run(*args, **kwargs):
            call_count["n"] += 1
            result = MagicMock()
            result.returncode = 0
            result.stderr = ""
            return result

        monkeypatch.setattr("subprocess.run", mock_run)

        assert tg_tmux.kill_session("dev_central") is True

    def test_kill_nonexistent_session(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Killing nonexistent session returns True (idempotent)."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        monkeypatch.setattr("subprocess.run", lambda *a, **kw: mock_result)

        assert tg_tmux.kill_session("nonexistent") is True


# =============================================
# 9. STOP HOOK TESTS
# =============================================

class TestStopHookFindPendingFile:
    """Tests for telegram_response.find_pending_file."""

    def test_find_matching_pending(self, monkeypatch: pytest.MonkeyPatch, pending_dir: Path) -> None:
        """Finds pending file with matching session_id."""
        monkeypatch.setattr(tg_hook, "PENDING_DIR", pending_dir)

        data = {
            "session_id": "test-session-123",
            "chat_id": 12345,
            "bot_token": "tok",
            "timestamp": time.time(),
        }
        (pending_dir / "telegram-dev_central.json").write_text(json.dumps(data))

        result = tg_hook.find_pending_file("test-session-123")
        assert result is not None
        assert result.name == "telegram-dev_central.json"

    def test_no_matching_pending(self, monkeypatch: pytest.MonkeyPatch, pending_dir: Path) -> None:
        """Returns None when no pending file matches."""
        monkeypatch.setattr(tg_hook, "PENDING_DIR", pending_dir)
        assert tg_hook.find_pending_file("nonexistent-session") is None

    def test_stale_pending_file_removed(self, monkeypatch: pytest.MonkeyPatch, pending_dir: Path) -> None:
        """Stale pending files (>TTL) are removed."""
        monkeypatch.setattr(tg_hook, "PENDING_DIR", pending_dir)

        data = {
            "session_id": "stale-session",
            "timestamp": time.time() - 700,  # 700s > 600s TTL
        }
        stale_file = pending_dir / "telegram-stale.json"
        stale_file.write_text(json.dumps(data))

        result = tg_hook.find_pending_file("stale-session")
        assert result is None
        assert not stale_file.exists()

    def test_no_pending_dir(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        """Returns None when pending dir doesn't exist."""
        monkeypatch.setattr(tg_hook, "PENDING_DIR", tmp_path / "nonexistent")
        assert tg_hook.find_pending_file("any") is None


class TestStopHookExtractResponse:
    """Tests for telegram_response.extract_assistant_response."""

    def test_extract_simple_response(self, tmp_path: Path) -> None:
        """Extracts text from simple JSONL transcript."""
        transcript = tmp_path / "session.jsonl"
        lines = [
            json.dumps({"type": "user", "message": {"content": [{"type": "text", "text": "hello"}]}}),
            json.dumps({"type": "assistant", "message": {"content": [{"type": "text", "text": "Hi there!"}]}}),
        ]
        transcript.write_text("\n".join(lines))

        result = tg_hook.extract_assistant_response(str(transcript))
        assert result == "Hi there!"

    def test_extract_multi_block_response(self, tmp_path: Path) -> None:
        """Extracts and joins multiple text blocks."""
        transcript = tmp_path / "session.jsonl"
        lines = [
            json.dumps({"type": "user", "message": {"content": [{"type": "text", "text": "hello"}]}}),
            json.dumps({"type": "assistant", "message": {"content": [
                {"type": "text", "text": "Part 1"},
                {"type": "tool_use", "id": "t1", "name": "bash"},
                {"type": "text", "text": "Part 2"},
            ]}}),
        ]
        transcript.write_text("\n".join(lines))

        result = tg_hook.extract_assistant_response(str(transcript))
        assert "Part 1" in result
        assert "Part 2" in result
        assert "tool_use" not in result

    def test_extract_last_user_message(self, tmp_path: Path) -> None:
        """Only extracts response after the LAST user message."""
        transcript = tmp_path / "session.jsonl"
        lines = [
            json.dumps({"type": "user", "message": {"content": [{"type": "text", "text": "first"}]}}),
            json.dumps({"type": "assistant", "message": {"content": [{"type": "text", "text": "Old response"}]}}),
            json.dumps({"type": "user", "message": {"content": [{"type": "text", "text": "second"}]}}),
            json.dumps({"type": "assistant", "message": {"content": [{"type": "text", "text": "New response"}]}}),
        ]
        transcript.write_text("\n".join(lines))

        result = tg_hook.extract_assistant_response(str(transcript))
        assert result == "New response"

    def test_extract_no_transcript(self, tmp_path: Path) -> None:
        """Returns None when transcript doesn't exist."""
        result = tg_hook.extract_assistant_response(str(tmp_path / "missing.jsonl"))
        assert result is None

    def test_extract_no_assistant_response(self, tmp_path: Path) -> None:
        """Returns None when no assistant message found."""
        transcript = tmp_path / "session.jsonl"
        lines = [
            json.dumps({"type": "user", "message": {"content": [{"type": "text", "text": "hello"}]}}),
        ]
        transcript.write_text("\n".join(lines))

        result = tg_hook.extract_assistant_response(str(transcript))
        assert result is None


class TestStopHookChunkText:
    """Tests for telegram_response.chunk_text."""

    def test_short_text_no_chunking(self) -> None:
        """Short text returns single chunk."""
        assert tg_hook.chunk_text("hello") == ["hello"]

    def test_long_text_chunked(self) -> None:
        """Long text is chunked at limit."""
        text = "a" * 8000
        chunks = tg_hook.chunk_text(text)
        assert len(chunks) == 2
        for chunk in chunks:
            assert len(chunk) <= 4096


# =============================================
# 10. FILE HANDLER TESTS
# =============================================

class TestDetectFileType:
    """Tests for file_handler.detect_file_type."""

    def test_detect_text(self, tmp_path: Path) -> None:
        """Python/JS/TXT files return 'text'."""
        for ext in ('.py', '.js', '.txt'):
            f = tmp_path / f"test{ext}"
            f.write_text("hello")
            assert detect_file_type(f) == 'text'

    def test_detect_image(self, tmp_path: Path) -> None:
        """JPG/PNG files return 'image'."""
        for ext in ('.jpg', '.png'):
            f = tmp_path / f"test{ext}"
            f.write_bytes(b'\x00')
            assert detect_file_type(f) == 'image'

    def test_detect_pdf(self, tmp_path: Path) -> None:
        """PDF files return 'pdf'."""
        f = tmp_path / "test.pdf"
        f.write_bytes(b'%PDF')
        assert detect_file_type(f) == 'pdf'

    def test_detect_binary(self, tmp_path: Path) -> None:
        """Binary files return 'binary'."""
        f = tmp_path / "test.exe"
        f.write_bytes(b'\x00\x01\xff\xfe')
        assert detect_file_type(f) == 'binary'


class TestBuildFilePrompt:
    """Tests for file_handler.build_file_prompt."""

    def test_text_prompt(self, tmp_path: Path) -> None:
        """Text prompt includes code block."""
        f = tmp_path / "hello.py"
        f.write_text("print('hello')")
        result = build_file_prompt(f, 'text')
        assert "```python" in result
        assert "print('hello')" in result

    def test_image_prompt(self, tmp_path: Path) -> None:
        """Image prompt references file path."""
        f = tmp_path / "photo.jpg"
        f.write_bytes(b'\xff')
        result = build_file_prompt(f, 'image')
        assert str(f) in result


class TestCleanupFile:
    """Tests for file_handler.cleanup_file."""

    def test_cleanup(self, tmp_path: Path) -> None:
        """File is deleted."""
        f = tmp_path / "temp.txt"
        f.write_text("data")
        cleanup_file(f)
        assert not f.exists()

    def test_cleanup_missing(self, tmp_path: Path) -> None:
        """No error on missing file."""
        cleanup_file(tmp_path / "nonexistent.txt")


# =============================================
# 11. CHAT LOGGING TESTS
# =============================================

class TestLogChat:
    """Tests for bridge.log_chat."""

    def test_log_creates_file(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        """log_chat creates log file."""
        log_file = tmp_path / "chats" / "telegram_chats.log"
        monkeypatch.setattr(tg_bridge, "CHAT_LOG_FILE", log_file)
        tg_bridge.log_chat("@alice", "Hello Claude")
        assert log_file.exists()
        assert "@alice" in log_file.read_text()

    def test_log_format(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        """Log entries have correct format."""
        log_file = tmp_path / "telegram_chats.log"
        monkeypatch.setattr(tg_bridge, "CHAT_LOG_FILE", log_file)
        tg_bridge.log_chat("@bob", "question", response="answer")
        content = log_file.read_text()
        assert "SENDER: @bob" in content
        assert "RESPONSE:" in content


# =============================================
# 12. SESSION COMMAND HANDLER TESTS
# =============================================

def _build_command_mocks(
    monkeypatch: pytest.MonkeyPatch,
    chat_id: int = 12345,
    text: str = "/cmd",
) -> tuple:
    """Build mock update/context for command handler tests."""
    mock_message = AsyncMock()
    mock_message.text = text
    mock_message.reply_text = AsyncMock(return_value=AsyncMock())

    mock_chat = AsyncMock()
    mock_chat.id = chat_id

    mock_user = AsyncMock()
    mock_user.username = "testuser"
    mock_user.id = 111111
    mock_user.first_name = "Test"

    mock_update = AsyncMock(spec=Update)
    mock_update.message = mock_message
    mock_update.effective_chat = mock_chat
    mock_update.effective_user = mock_user

    mock_context = AsyncMock()

    return mock_update, mock_context


class TestHandleNew:
    """Tests for bridge.handle_new command."""

    def test_handle_new_kills_and_clears(self, monkeypatch: pytest.MonkeyPatch, session_file: Path) -> None:
        """The /new command kills session and clears store."""
        monkeypatch.setattr(tg_session_store, "SESSION_FILE", session_file)
        monkeypatch.setattr("api.apps.handlers.telegram.bridge.get_session", tg_session_store.get_session)
        monkeypatch.setattr("api.apps.handlers.telegram.bridge.clear_session", tg_session_store.clear_session)
        monkeypatch.setattr("api.apps.handlers.telegram.bridge.kill_session", lambda b: True)

        tg_session_store.save_session(12345, "dev_central")
        mock_update, mock_context = _build_command_mocks(monkeypatch)

        asyncio.run(tg_bridge.handle_new(mock_update, mock_context))

        assert tg_session_store.get_session(12345) is None
        mock_update.message.reply_text.assert_called_once()


class TestHandleStatus:
    """Tests for bridge.handle_status command."""

    def test_handle_status_shows_info(self, monkeypatch: pytest.MonkeyPatch, session_file: Path) -> None:
        """The /status command returns session info."""
        monkeypatch.setattr(tg_session_store, "SESSION_FILE", session_file)
        monkeypatch.setattr("api.apps.handlers.telegram.bridge.get_session", tg_session_store.get_session)
        monkeypatch.setattr("api.apps.handlers.telegram.bridge.get_session_info", tg_session_store.get_session_info)
        monkeypatch.setattr("api.apps.handlers.telegram.bridge.session_exists", lambda b: True)
        monkeypatch.setattr("api.apps.handlers.telegram.bridge.list_sessions", lambda: ["dev_central"])

        tg_session_store.save_session(12345, "dev_central")
        mock_update, mock_context = _build_command_mocks(monkeypatch)

        asyncio.run(tg_bridge.handle_status(mock_update, mock_context))

        call_text = mock_update.message.reply_text.call_args[0][0]
        assert "dev_central" in call_text
        assert "Active" in call_text


class TestHandleList:
    """Tests for bridge.handle_list command."""

    def test_handle_list_shows_sessions(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The /list command shows active sessions."""
        monkeypatch.setattr("api.apps.handlers.telegram.bridge.list_sessions", lambda: ["dev_central", "projects"])

        mock_update, mock_context = _build_command_mocks(monkeypatch)
        asyncio.run(tg_bridge.handle_list(mock_update, mock_context))

        call_text = mock_update.message.reply_text.call_args[0][0]
        assert "telegram-dev_central" in call_text
        assert "telegram-projects" in call_text
        assert "Total: 2" in call_text

    def test_handle_list_empty(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The /list command handles no sessions."""
        monkeypatch.setattr("api.apps.handlers.telegram.bridge.list_sessions", lambda: [])

        mock_update, mock_context = _build_command_mocks(monkeypatch)
        asyncio.run(tg_bridge.handle_list(mock_update, mock_context))

        call_text = mock_update.message.reply_text.call_args[0][0]
        assert "No active" in call_text


class TestHandleEnd:
    """Tests for bridge.handle_end command."""

    def test_handle_end_kills_session(self, monkeypatch: pytest.MonkeyPatch, session_file: Path) -> None:
        """The /end command kills the tmux session."""
        monkeypatch.setattr(tg_session_store, "SESSION_FILE", session_file)
        monkeypatch.setattr("api.apps.handlers.telegram.bridge.get_session", tg_session_store.get_session)
        monkeypatch.setattr("api.apps.handlers.telegram.bridge.session_exists", lambda b: True)

        killed = {"branch": None}
        monkeypatch.setattr("api.apps.handlers.telegram.bridge.kill_session", lambda b: (killed.update({"branch": b}) or True))

        tg_session_store.save_session(12345, "dev_central")
        mock_update, mock_context = _build_command_mocks(monkeypatch)

        asyncio.run(tg_bridge.handle_end(mock_update, mock_context))

        assert killed["branch"] == "dev_central"
        call_text = mock_update.message.reply_text.call_args[0][0]
        assert "ended" in call_text


class TestHandleBranch:
    """Tests for bridge.handle_branch command."""

    def test_handle_branch_shows_current(self, monkeypatch: pytest.MonkeyPatch, session_file: Path) -> None:
        """The /branch command shows current branch."""
        monkeypatch.setattr(tg_session_store, "SESSION_FILE", session_file)
        monkeypatch.setattr("api.apps.handlers.telegram.bridge.get_session", tg_session_store.get_session)

        tg_session_store.save_session(12345, "projects")
        mock_update, mock_context = _build_command_mocks(monkeypatch)

        asyncio.run(tg_bridge.handle_branch(mock_update, mock_context))

        call_text = mock_update.message.reply_text.call_args[0][0]
        assert "@projects" in call_text


class TestHandleSwitch:
    """Tests for bridge.handle_switch command."""

    def test_handle_switch_updates_branch(self, monkeypatch: pytest.MonkeyPatch, session_file: Path, tmp_path: Path) -> None:
        """The /switch command updates the session branch."""
        monkeypatch.setattr(tg_session_store, "SESSION_FILE", session_file)
        monkeypatch.setattr("api.apps.handlers.telegram.bridge.save_session", tg_session_store.save_session)
        monkeypatch.setattr("api.apps.handlers.telegram.bridge.session_exists", lambda b: False)

        # Create a valid branch path
        branch_dir = tmp_path / "projects"
        branch_dir.mkdir()
        monkeypatch.setattr(
            "api.apps.handlers.telegram.bridge._resolve_branch_path",
            lambda b: branch_dir if b == "projects" else tg_bridge.DEFAULT_SESSION_PATH,
        )

        mock_update, mock_context = _build_command_mocks(monkeypatch, text="/switch @projects")
        asyncio.run(tg_bridge.handle_switch(mock_update, mock_context))

        result = tg_session_store.get_session(12345)
        assert result is not None
        assert result["branch_name"] == "projects"

    def test_handle_switch_no_args(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The /switch command without args shows usage."""
        mock_update, mock_context = _build_command_mocks(monkeypatch, text="/switch")
        asyncio.run(tg_bridge.handle_switch(mock_update, mock_context))

        call_text = mock_update.message.reply_text.call_args[0][0]
        assert "Usage" in call_text
