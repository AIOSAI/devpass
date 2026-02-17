#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: direct_chat.py - Config-Driven Telegram Direct Chat
# Date: 2026-02-15
# Version: 1.0.0
# Category: api/handlers/telegram
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2026-02-15): Initial - extracted from assistant_chat.py, config-driven with standards integration
#
# CODE STANDARDS:
#   - stdlib ONLY (no external dependencies)
#   - Config-driven: all bot-specific values passed as parameters
#   - Imports standard commands from telegram_standards.py
# =============================================

"""
Config-Driven Telegram Direct Chat Handler

Reusable long-polling chat module that replaces duplicated per-bot scripts
(assistant_chat.py, test_chat.py). All bot-specific values are passed via
the run() function - no hardcoded constants.

Integrates telegram_standards.py for shared /start, /help, /status, /new
commands. Any message that is NOT a standard command flows through as a
regular message injected into a Claude tmux session.

Flow:
  Patrick sends Telegram message
  -> This module receives it via getUpdates long-polling
  -> If /command -> handle via telegram_standards, reply, return
  -> If /new -> kill tmux session, reply, return
  -> Else -> ensure tmux session exists (running Claude)
  -> Write pending file for Stop hook coordination
  -> Inject message into tmux session via send-keys
  -> Claude processes and hits Stop event
  -> Stop hook reads pending file, extracts response, sends to Telegram
  -> Stop hook deletes pending file
  -> Continue polling for next message

Usage:
    from api.apps.handlers.telegram.direct_chat import run

    run(
        branch_name="assistant",
        session_name="telegram-assistant",
        config_path=Path.home() / ".aipass" / "assistant_bot_config.json",
        work_dir=Path("/home/aipass/aipass_os/dev_central/assistant"),
        log_dir=Path("/home/aipass/aipass_os/dev_central/assistant/logs"),
        data_dir=Path("/home/aipass/aipass_os/dev_central/assistant/assistant_json"),
        bot_name="AIPass Assistant Bot",
    )
"""

# =============================================
# IMPORTS (stdlib only)
# =============================================

import atexit
import json
import logging
import os
import signal
import subprocess
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib.error import URLError
from urllib.request import Request, urlopen

# =============================================
# SIBLING IMPORT - telegram_standards
# =============================================

# Allow import whether running as a package or standalone script
try:
    from api.apps.handlers.telegram.telegram_standards import (
        parse_command,
        handle_standard_command,
    )
except ImportError:
    # Fallback: import from same directory when running standalone
    _this_dir = Path(__file__).resolve().parent
    if str(_this_dir) not in sys.path:
        sys.path.insert(0, str(_this_dir))
    from telegram_standards import parse_command, handle_standard_command


# =============================================
# SHARED CONSTANTS
# =============================================

# Security
PATRICK_CHAT_ID = "7235222625"

# Rate limiting
RATE_LIMIT_COOLDOWN = 1.0  # Minimum seconds between messages

# Telegram API
POLL_TIMEOUT = 30  # Long-poll timeout in seconds

# Pending file coordination
PENDING_DIR = Path.home() / ".aipass" / "telegram_pending"
PENDING_TTL = 300  # 5 minutes - clean stale pending files on startup

# File handling
TEMP_DIR = Path("/tmp/telegram_uploads")
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


# =============================================
# LOGGING SETUP
# =============================================

def _setup_logger(branch_name: str, log_dir: Path) -> logging.Logger:
    """
    Create and configure a logger for a specific branch.

    Creates a file handler writing to log_dir/{branch_name}_chat.log
    and a stdout handler for interactive use.

    Args:
        branch_name: Branch identifier (used in logger name and log filename)
        log_dir: Directory to write log files into

    Returns:
        Configured logger instance
    """
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"{branch_name}_chat.log"

    _logger = logging.getLogger(f"{branch_name}_chat")
    _logger.setLevel(logging.INFO)

    if not _logger.handlers:
        file_handler = logging.FileHandler(str(log_file))
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        )
        _logger.addHandler(file_handler)

        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        )
        _logger.addHandler(stdout_handler)

    return _logger


# =============================================
# CONFIG
# =============================================

def load_config(config_path: Path, logger: logging.Logger) -> dict:
    """
    Load bot configuration from a JSON file.

    Args:
        config_path: Path to the bot config JSON file
        logger: Logger instance for error reporting

    Returns:
        Dict with telegram_bot_token, telegram_chat_id, etc.

    Raises:
        FileNotFoundError: If config file is missing
        json.JSONDecodeError: If config is invalid JSON
    """
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


# =============================================
# OFFSET TRACKING
# =============================================

def load_offset(offset_file: Path, logger: logging.Logger) -> int:
    """
    Load the last processed Telegram update offset.

    Args:
        offset_file: Path to the offset JSON file
        logger: Logger instance

    Returns:
        The offset integer, or 0 if no offset saved
    """
    if not offset_file.exists():
        return 0
    try:
        with open(offset_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("offset", 0)
    except (json.JSONDecodeError, OSError):
        return 0


def save_offset(offset: int, offset_file: Path, logger: logging.Logger) -> None:
    """
    Persist the current update offset.

    Args:
        offset: The update_id + 1 of the last processed update
        offset_file: Path to the offset JSON file
        logger: Logger instance
    """
    offset_file.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(offset_file, "w", encoding="utf-8") as f:
            json.dump({"offset": offset, "updated": datetime.now().isoformat()}, f)
    except OSError as e:
        logger.error("Failed to save offset: %s", e)


# =============================================
# LOCK FILE MANAGEMENT
# =============================================

def create_lock(
    lock_file: Path,
    session_name: str,
    logger: logging.Logger,
) -> None:
    """
    Create the chat lock file to signal an active chat session.

    Args:
        lock_file: Path to the lock file
        session_name: tmux session name for the lock metadata
        logger: Logger instance
    """
    lock_file.parent.mkdir(parents=True, exist_ok=True)
    try:
        lock_file.write_text(
            json.dumps({
                "pid": os.getpid(),
                "started": datetime.now().isoformat(),
                "session": session_name,
            }),
            encoding="utf-8",
        )
        logger.info("Chat lock created: %s", lock_file)
    except OSError as e:
        logger.error("Failed to create lock file: %s", e)


def remove_lock(lock_file: Path, logger: logging.Logger) -> None:
    """
    Remove the chat lock file on exit.

    Args:
        lock_file: Path to the lock file
        logger: Logger instance
    """
    try:
        if lock_file.exists():
            lock_file.unlink()
            logger.info("Chat lock removed")
    except OSError as e:
        logger.error("Failed to remove lock file: %s", e)


# =============================================
# PENDING FILE MANAGEMENT
# =============================================

def ensure_pending_dir() -> None:
    """Create the pending directory if it doesn't exist."""
    PENDING_DIR.mkdir(parents=True, exist_ok=True)


def clean_stale_pending(pending_file: Path, logger: logging.Logger) -> None:
    """
    Remove stale pending file on startup (older than PENDING_TTL).

    Args:
        pending_file: Path to this bot's pending file
        logger: Logger instance
    """
    if not pending_file.exists():
        return
    try:
        age = time.time() - pending_file.stat().st_mtime
        if age > PENDING_TTL:
            pending_file.unlink()
            logger.info("Cleaned stale pending file (%.0fs old)", age)
    except OSError:
        pass


def write_pending_file(
    chat_id: str,
    message_id: int,
    bot_token: str,
    branch_name: str,
    pending_file: Path,
    logger: logging.Logger,
) -> bool:
    """
    Write the pending file for Stop hook coordination.

    The Stop hook (telegram_response.py) checks this file to know that
    a response should be sent to Telegram. It matches by CWD-derived
    branch name: the tmux session runs in the branch directory,
    so CWD.name = branch_name, and it looks for 'telegram-{branch_name}.json'.

    Args:
        chat_id: Patrick's Telegram chat ID (string)
        message_id: The original message's Telegram message ID
        bot_token: Bot token for the Stop hook to use for sending
        branch_name: Branch identifier
        pending_file: Path to the pending JSON file
        logger: Logger instance

    Returns:
        True if written successfully
    """
    ensure_pending_dir()

    pending_data = {
        "chat_id": int(chat_id),
        "message_id": message_id,
        "bot_token": bot_token,
        "session_id": f"tmux-{branch_name}",
        "processing_message_id": None,
        "timestamp": time.time(),
        "branch_name": branch_name,
    }

    try:
        pending_file.write_text(
            json.dumps(pending_data, indent=2),
            encoding="utf-8",
        )
        logger.info("Pending file written for message %d", message_id)
        return True
    except OSError as e:
        logger.error("Failed to write pending file: %s", e)
        return False


# =============================================
# TMUX SESSION MANAGEMENT
# =============================================

def session_exists(session_name: str) -> bool:
    """
    Check if a tmux session exists.

    Args:
        session_name: tmux session name to check

    Returns:
        True if the session is running
    """
    result = subprocess.run(
        ["tmux", "has-session", "-t", session_name],
        capture_output=True,
    )
    return result.returncode == 0


def kill_tmux_session(session_name: str, logger: logging.Logger) -> bool:
    """
    Kill a tmux session by name.

    Used by the /new command to start a fresh Claude context.

    Args:
        session_name: tmux session name to kill
        logger: Logger instance

    Returns:
        True if killed successfully (or didn't exist)
    """
    if not session_exists(session_name):
        logger.info("tmux session '%s' not running, nothing to kill", session_name)
        return True

    try:
        subprocess.run(
            ["tmux", "kill-session", "-t", session_name],
            check=True,
            capture_output=True,
        )
        logger.info("Killed tmux session '%s'", session_name)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(
            "Failed to kill tmux session '%s': %s",
            session_name,
            e.stderr.decode() if e.stderr else str(e),
        )
        return False


def ensure_tmux_session(
    session_name: str,
    work_dir: Path,
    logger: logging.Logger,
) -> bool:
    """
    Create the tmux session if it doesn't exist.

    Creates a detached tmux session running 'claude --permission-mode bypassPermissions'
    in the specified working directory.

    Args:
        session_name: tmux session name
        work_dir: Working directory for the tmux session
        logger: Logger instance

    Returns:
        True if session is ready (created or already existed)
    """
    if session_exists(session_name):
        logger.info("tmux session '%s' already exists", session_name)
        return True

    logger.info("Creating tmux session '%s' at %s", session_name, work_dir)

    try:
        # env -u CLAUDECODE prevents "cannot run inside another Claude" error
        # when this script is launched from within a Claude Code session
        env = os.environ.copy()
        env.pop("CLAUDECODE", None)
        subprocess.run(
            [
                "tmux", "new-session", "-d",
                "-s", session_name,
                "-c", str(work_dir),
                "claude", "--permission-mode", "bypassPermissions",
            ],
            check=True,
            capture_output=True,
            env=env,
        )
        # Give Claude a moment to start up
        logger.info("tmux session created, waiting 5s for Claude to initialize...")
        time.sleep(5)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(
            "Failed to create tmux session: %s",
            e.stderr.decode() if e.stderr else str(e),
        )
        return False
    except FileNotFoundError:
        logger.error("tmux not found - is it installed?")
        return False


def inject_message(
    text: str,
    session_name: str,
    logger: logging.Logger,
) -> bool:
    """
    Send a message to Claude via tmux send-keys.

    Uses send-keys -l for literal text (no shell interpretation of
    special characters), followed by Enter to submit.

    Args:
        text: The message text to inject
        session_name: tmux session name
        logger: Logger instance

    Returns:
        True if injection succeeded
    """
    try:
        # Send the text literally (no interpretation of special chars)
        subprocess.run(
            ["tmux", "send-keys", "-t", session_name, "-l", text],
            check=True,
            capture_output=True,
        )
        # Brief pause then press Enter
        time.sleep(0.5)
        subprocess.run(
            ["tmux", "send-keys", "-t", session_name, "Enter"],
            check=True,
            capture_output=True,
        )
        logger.info("Message injected into tmux session")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(
            "Failed to inject message: %s",
            e.stderr.decode() if e.stderr else str(e),
        )
        return False


# =============================================
# TELEGRAM API (stdlib urllib)
# =============================================

def poll_updates(bot_token: str, offset: int, logger: logging.Logger) -> list:
    """
    Long-poll Telegram for new updates using getUpdates API.

    Uses urllib (stdlib) with a 30-second long-poll timeout.
    Telegram holds the connection open until there's an update
    or the timeout expires.

    Args:
        bot_token: Telegram bot token
        offset: Update offset to avoid reprocessing
        logger: Logger instance

    Returns:
        List of update dicts from Telegram API
    """
    url = (
        f"https://api.telegram.org/bot{bot_token}/getUpdates"
        f"?offset={offset}&timeout={POLL_TIMEOUT}"
    )

    try:
        # timeout = poll_timeout + buffer for network latency
        req = Request(url)
        with urlopen(req, timeout=POLL_TIMEOUT + 10) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        if not data.get("ok"):
            logger.error("Telegram API error: %s", data.get("description", "unknown"))
            return []

        return data.get("result", [])
    except URLError as e:
        logger.error("Poll error: %s", e)
        return []
    except Exception as e:
        logger.error("Unexpected poll error: %s", e)
        return []


def send_telegram_message(bot_token: str, chat_id: str, text: str, logger: logging.Logger) -> bool:
    """
    Send a message to Telegram (used for status/error messages from this script).

    Args:
        bot_token: Telegram bot token
        chat_id: Target chat ID
        text: Message text
        logger: Logger instance

    Returns:
        True if sent successfully
    """
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    payload = {
        "chat_id": int(chat_id),
        "text": text,
    }

    data = json.dumps(payload).encode("utf-8")
    req = Request(url, data=data, headers={"Content-Type": "application/json"})

    try:
        with urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read())
            return result.get("ok", False)
    except Exception as e:
        logger.error("Failed to send Telegram message: %s", e)
        return False


# =============================================
# FILE HANDLING (stdlib only)
# =============================================

def download_telegram_file(
    bot_token: str,
    file_id: str,
    logger: logging.Logger,
    filename: Optional[str] = None,
) -> Optional[Path]:
    """
    Download a file from Telegram via getFile API + urllib.

    1. Calls getFile to get the file_path on Telegram's servers
    2. Downloads the file binary to /tmp/telegram_uploads/

    Args:
        bot_token: Telegram bot token
        file_id: Telegram file_id from the message
        logger: Logger instance
        filename: Optional original filename (used for extension)

    Returns:
        Path to the downloaded file, or None on failure
    """
    # Step 1: Get file info from Telegram
    url = f"https://api.telegram.org/bot{bot_token}/getFile?file_id={file_id}"
    try:
        with urlopen(Request(url), timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        logger.error("getFile API failed: %s", e)
        return None

    if not data.get("ok"):
        logger.error("getFile error: %s", data.get("description", "unknown"))
        return None

    file_info = data.get("result", {})
    file_path = file_info.get("file_path", "")
    file_size = file_info.get("file_size", 0)

    if not file_path:
        logger.error("No file_path in getFile response")
        return None

    if file_size > MAX_FILE_SIZE:
        logger.warning("File too large: %d bytes (max %d)", file_size, MAX_FILE_SIZE)
        return None

    # Step 2: Download the file
    download_url = f"https://api.telegram.org/file/bot{bot_token}/{file_path}"

    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    # Determine local filename
    if filename:
        safe_name = "".join(c if c.isalnum() or c in ".-_" else "_" for c in Path(filename).name)
    else:
        ext = Path(file_path).suffix or ".jpg"
        safe_name = f"{uuid.uuid4()}{ext}"

    dest = TEMP_DIR / safe_name

    try:
        with urlopen(Request(download_url), timeout=30) as resp:
            dest.write_bytes(resp.read())
        logger.info("Downloaded file to %s (%d bytes)", dest, file_size)
        return dest
    except Exception as e:
        logger.error("File download failed: %s", e)
        return None


def build_file_prompt(file_path: Path, caption: Optional[str] = None, is_image: bool = True) -> str:
    """
    Build a Claude prompt that references a downloaded file.

    For images: tells Claude to use Read tool to view the image.
    For documents: tells Claude to use Read tool to view the file.

    Args:
        file_path: Path to the downloaded file
        caption: Optional caption from the Telegram message
        is_image: True for photos, False for documents

    Returns:
        Formatted prompt string for Claude
    """
    if is_image:
        desc = caption or "What do you see in this image?"
        return (
            f"Patrick via Telegram: {desc}\n\n"
            f"[Image attached at: {file_path}]\n"
            f"Please use the Read tool to view the image file at the path above."
        )
    else:
        desc = caption or "Review this file"
        suffix = file_path.suffix.lower()
        if suffix == ".pdf":
            file_type = "PDF document"
        else:
            file_type = "File"
        return (
            f"Patrick via Telegram: {desc}\n\n"
            f"[{file_type} at: {file_path}]\n"
            f"Please use the Read tool to view the file at the path above."
        )


# =============================================
# MESSAGE PROCESSING
# =============================================

def process_update(
    update: dict,
    bot_token: str,
    branch_name: str,
    session_name: str,
    work_dir: Path,
    pending_file: Path,
    bot_name: str,
    custom_commands: Optional[dict],
    state: dict,
    logger: logging.Logger,
) -> None:
    """
    Process a single Telegram update.

    Command flow:
      1. Check if message is a /command via parse_command()
      2. If standard command -> handle via handle_standard_command(), reply, return
      3. If /new -> kill tmux session, reply, return
      4. Else -> regular message flow (tmux injection + pending file)

    Security: only accepts messages from Patrick's chat_id.
    Rate limit: enforces minimum 1-second cooldown between messages.

    Args:
        update: Telegram update dict
        bot_token: Bot token for pending file and status messages
        branch_name: Branch identifier
        session_name: tmux session name
        work_dir: Working directory for tmux session
        pending_file: Path to the pending JSON file
        bot_name: Display name for the bot
        custom_commands: Optional bot-specific commands dict
        state: Mutable state dict (last_message_time, running, message_count)
        logger: Logger instance
    """
    message = update.get("message")
    if not message:
        return

    # Extract message details
    text = message.get("text", "")
    chat = message.get("chat", {})
    chat_id = str(chat.get("id", ""))
    message_id = message.get("message_id", 0)
    from_user = message.get("from", {})
    username = from_user.get("username", "unknown")

    # Security: only accept from Patrick
    if chat_id != PATRICK_CHAT_ID:
        logger.warning("Blocked message from unauthorized chat_id: %s (@%s)", chat_id, username)
        return

    # ---- Command handling (NEW: via telegram_standards) ----
    if text:
        parsed = parse_command(text)
        if parsed is not None:
            cmd_name, cmd_args = parsed
            result = handle_standard_command(
                command=cmd_name,
                session_name=session_name,
                branch_name=branch_name,
                bot_name=bot_name,
                custom_commands=custom_commands,
                chat_id=chat_id,
                message_count=state.get("message_count"),
                uptime=state.get("uptime"),
            )

            if result is not None:
                if isinstance(result, tuple):
                    # ("new", response_text) -> kill tmux session, send text
                    action, response_text = result
                    if action == "new":
                        kill_tmux_session(session_name, logger)
                        send_telegram_message(bot_token, chat_id, response_text, logger)
                        logger.info("Handled /new command - session killed")
                    return
                else:
                    # str -> send the response text directly
                    send_telegram_message(bot_token, chat_id, result, logger)
                    logger.info("Handled /%s command", cmd_name)
                    return

            # result is None -> not a standard command, fall through to regular processing
            # (the /command text itself will be injected as a regular message)

    # ---- Regular message processing ----

    # Determine message type and build prompt
    prompt = None
    photo_list = message.get("photo")
    document = message.get("document")
    caption = message.get("caption", "")

    if photo_list:
        # Photo message - download highest quality version (last in array)
        best_photo = photo_list[-1]
        file_id = best_photo.get("file_id", "")
        logger.info(
            "Photo from Patrick (file_id=%s, caption=%s)",
            file_id[:20],
            caption[:50] if caption else "none",
        )

        file_path = download_telegram_file(bot_token, file_id, logger)
        if file_path:
            prompt = build_file_prompt(file_path, caption=caption or None, is_image=True)
        else:
            send_telegram_message(bot_token, chat_id, "Failed to download image. Try again?", logger)
            return

    elif document:
        # Document message - download the file
        file_id = document.get("file_id", "")
        file_name = document.get("file_name", "")
        file_size = document.get("file_size", 0)
        logger.info("Document from Patrick: %s (%d bytes)", file_name, file_size)

        if file_size > MAX_FILE_SIZE:
            send_telegram_message(
                bot_token, chat_id,
                f"File too large ({file_size // 1024}KB). Max is 10MB.",
                logger,
            )
            return

        file_path = download_telegram_file(bot_token, file_id, logger, filename=file_name)
        if file_path:
            prompt = build_file_prompt(file_path, caption=caption or None, is_image=False)
        else:
            send_telegram_message(bot_token, chat_id, "Failed to download file. Try again?", logger)
            return

    elif text:
        # Regular text message
        prompt = f"Patrick via Telegram: {text}"

    else:
        logger.info("Ignoring unsupported message type from Patrick")
        return

    # Rate limiting
    now = time.time()
    if now - state["last_message_time"] < RATE_LIMIT_COOLDOWN:
        logger.warning("Rate limited - message too soon (%.1fs)", now - state["last_message_time"])
        return
    state["last_message_time"] = now

    # Track message count
    state["message_count"] = state.get("message_count", 0) + 1

    logger.info("Processing message (msg_id=%d)", message_id)

    # Ensure tmux session exists
    if not ensure_tmux_session(session_name, work_dir, logger):
        logger.error("Cannot process message - tmux session unavailable")
        send_telegram_message(bot_token, chat_id, "Failed to start Claude session. Check logs.", logger)
        return

    # Write pending file BEFORE injecting (Stop hook needs it ready)
    if not write_pending_file(chat_id, message_id, bot_token, branch_name, pending_file, logger):
        logger.error("Failed to write pending file")
        send_telegram_message(bot_token, chat_id, "Internal error writing pending file.", logger)
        return

    # Inject into tmux
    if not inject_message(prompt, session_name, logger):
        logger.error("Failed to inject message into tmux")
        pending_file.unlink(missing_ok=True)
        send_telegram_message(bot_token, chat_id, "Failed to send message to Claude session.", logger)
        return

    logger.info("Message processed successfully (msg_id=%d)", message_id)


# =============================================
# RUN - CONFIG-DRIVEN ENTRY POINT
# =============================================

def run(
    branch_name: str,
    session_name: str,
    config_path: Path,
    work_dir: Path,
    log_dir: Path,
    data_dir: Path,
    bot_name: str = "AIPass Bot",
    custom_commands: Optional[dict] = None,
) -> int:
    """
    Run the Telegram direct chat polling loop.

    This is the single entry point that replaces per-bot scripts like
    assistant_chat.py and test_chat.py. All bot-specific values are
    passed as parameters.

    Sets up logging, lock file, signal handlers, and enters the long-polling
    loop. Runs indefinitely until SIGTERM/SIGINT.

    Args:
        branch_name: Branch identifier (e.g., "assistant", "test").
            Used in logger name, pending file name, and pending file metadata.
        session_name: tmux session name (e.g., "telegram-assistant").
            The tmux session that runs Claude.
        config_path: Path to bot config JSON file.
            Must contain at minimum "telegram_bot_token".
        work_dir: Working directory for the tmux session.
            Claude will start with this as CWD.
        log_dir: Directory to write log files into.
            Creates {branch_name}_chat.log inside this directory.
        data_dir: Directory for offset file and lock file.
            Creates telegram_offset.json and chat.lock inside this directory.
        bot_name: Display name for the bot (shown in /start, /status responses).
        custom_commands: Optional dict of bot-specific commands in the same
            format as STANDARD_COMMANDS for inclusion in /help and /start.

    Returns:
        0 on clean exit, 1 on error
    """
    # Derived paths
    offset_file = data_dir / "telegram_offset.json"
    lock_file = data_dir / "chat.lock"
    pending_file = PENDING_DIR / f"telegram-{branch_name}.json"

    # Setup logging
    logger = _setup_logger(branch_name, log_dir)

    # Mutable state (dict to avoid global keyword)
    state = {
        "last_message_time": 0.0,
        "running": True,
        "message_count": 0,
        "start_time": time.time(),
        "uptime": None,
    }

    # ---- Signal handling ----

    def shutdown_handler(signum, frame):
        """Handle SIGTERM/SIGINT for clean shutdown."""
        sig_name = signal.Signals(signum).name if hasattr(signal, "Signals") else str(signum)
        logger.info("Received %s, shutting down...", sig_name)
        state["running"] = False

    def cleanup():
        """Clean up resources on exit."""
        remove_lock(lock_file, logger)
        logger.info("Chat listener stopped")

    # ---- Startup ----

    logger.info("=" * 60)
    logger.info("%s Telegram chat listener starting", branch_name.capitalize())

    # Load config
    try:
        config = load_config(config_path, logger)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error("Failed to load config from %s: %s", config_path, e)
        return 1

    bot_token = config.get("telegram_bot_token")
    if not bot_token:
        logger.error("No telegram_bot_token in config")
        return 1

    logger.info("Bot: @%s", config.get("telegram_bot_username", "unknown"))
    logger.info("Authorized chat_id: %s", PATRICK_CHAT_ID)

    # Setup lock file
    create_lock(lock_file, session_name, logger)
    atexit.register(cleanup)

    # Setup signal handlers
    signal.signal(signal.SIGTERM, shutdown_handler)
    signal.signal(signal.SIGINT, shutdown_handler)

    # Ensure pending directory exists
    ensure_pending_dir()

    # Clean stale pending file from previous runs
    clean_stale_pending(pending_file, logger)

    # Load offset
    offset = load_offset(offset_file, logger)
    logger.info("Starting poll loop (offset=%d)", offset)

    # ---- Main polling loop ----

    while state["running"]:
        try:
            # Update uptime for /status command
            elapsed = time.time() - state["start_time"]
            hours, remainder = divmod(int(elapsed), 3600)
            minutes, seconds = divmod(remainder, 60)
            state["uptime"] = f"{hours}h {minutes}m {seconds}s"

            updates = poll_updates(bot_token, offset, logger)

            for update in updates:
                if not state["running"]:
                    break

                process_update(
                    update=update,
                    bot_token=bot_token,
                    branch_name=branch_name,
                    session_name=session_name,
                    work_dir=work_dir,
                    pending_file=pending_file,
                    bot_name=bot_name,
                    custom_commands=custom_commands,
                    state=state,
                    logger=logger,
                )

                # Advance offset past this update
                new_offset = update.get("update_id", 0) + 1
                if new_offset > offset:
                    offset = new_offset
                    save_offset(offset, offset_file, logger)

        except KeyboardInterrupt:
            logger.info("KeyboardInterrupt received")
            break
        except Exception as e:
            logger.error("Error in poll loop: %s: %s", type(e).__name__, e)
            time.sleep(5)  # Back off on error

    logger.info("Poll loop exited")
    return 0
