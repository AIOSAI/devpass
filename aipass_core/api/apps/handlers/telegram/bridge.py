#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: bridge.py - Telegram Bridge Service
# Date: 2026-02-04
# Version: 4.1.0
# Category: api/handlers/telegram
#
# CHANGELOG (Max 5 entries):
#   - v4.1.0 (2026-02-13): Add /help command + show chat_id in /status
#   - v4.0.0 (2026-02-12): tmux persistent sessions - replace spawn-and-capture with tmux injection + Stop hook
#   - v3.0.0 (2026-02-10): Photo/document/file upload handling (Phase 5 FPLAN-0312)
#   - v2.9.0 (2026-02-10): Edit-in-place progress messages (Phase 4 FPLAN-0312)
#   - v2.8.0 (2026-02-10): Session persistence + /new, /status commands (Phase 3)
#
# CODE STANDARDS:
#   - Pure functions with proper error raising
#   - No Prax imports (handler tier 3)
# =============================================

"""
Telegram Bridge Service v4 - tmux Persistent Sessions

Core bot service for AIPass Telegram bridge:
- Long-polling mode (no webhooks needed)
- Persistent tmux sessions per branch (Claude Code runs continuously)
- Messages injected via tmux send-keys, responses via Stop hook
- Branch targeting (@branch prefix routes to different directories)
- File upload support (photos, documents)
- User allowlist and rate limiting

Architecture:
1. Message arrives from Telegram
2. Bridge resolves @branch target
3. Bridge creates/finds tmux session for that branch
4. Bridge writes pending file (coordination with Stop hook)
5. Bridge injects message via tmux send-keys
6. Stop hook fires when Claude responds, sends to Telegram
"""

# Infrastructure
import sys
from pathlib import Path
AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))

# Standard library
import asyncio
import json
import logging
import re
import time
from datetime import datetime
from typing import Any, Optional, Dict

# Telegram imports
from telegram import Update, Message
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes
from telegram.request import HTTPXRequest

# Internal imports
from api.apps.handlers.telegram.config import (
    get_bot_token, get_bot_username, get_allowed_user_ids
)
from api.apps.handlers.telegram.tmux_manager import (
    create_session, session_exists, send_message as tmux_send_message,
    kill_session, list_sessions,
)
from api.apps.handlers.telegram.session_store import (
    save_session, clear_session, get_session_info, get_session,
    get_session_by_branch
)
from api.apps.handlers.telegram.file_handler import (
    download_telegram_file, detect_file_type, build_file_prompt,
    cleanup_file, MAX_FILE_SIZE
)

# Response timeout (how long to wait before giving up on Stop hook)
RESPONSE_TIMEOUT = 120  # seconds

# Rate limiting configuration
RATE_LIMIT_MESSAGES = 5  # Max messages per window
RATE_LIMIT_WINDOW = 60  # Window in seconds

# In-memory rate limit tracking: {user_id: [timestamp1, timestamp2, ...]}
_rate_limit_tracker: Dict[int, list] = {}

# Branch targeting
DEFAULT_BRANCH = "dev_central"
DEFAULT_SESSION_PATH = Path.home() / "aipass_os" / "dev_central"
BRANCH_REGISTRY_PATH = Path.home() / "BRANCH_REGISTRY.json"

# Pending file coordination
PENDING_DIR = Path.home() / ".aipass" / "telegram_pending"

# Telegram char limit for chunking
TELEGRAM_CHAR_LIMIT = 4096

# =============================================
# LOGGING SETUP
# =============================================

LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_LEVEL = logging.INFO
logging.basicConfig(format=LOG_FORMAT, level=LOG_LEVEL)
logger = logging.getLogger("telegram_bridge")

# Reduce httpx noise
logging.getLogger("httpx").setLevel(logging.WARNING)

# =============================================
# LOCAL CHAT LOGGING
# =============================================

CHAT_LOG_FILE = Path.home() / "system_logs" / "telegram_chats.log"


def _ensure_chat_log_dir() -> None:
    """Ensure the chat log directory exists."""
    CHAT_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)


def log_chat(sender: str, message: str, response: Optional[str] = None) -> None:
    """
    Log chat interaction to local file.

    Args:
        sender: Who sent the message (username or name)
        message: Full incoming message text
        response: Claude's response (if any)
    """
    _ensure_chat_log_dir()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        with open(CHAT_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"\n{'='*60}\n")
            f.write(f"TIMESTAMP: {timestamp}\n")
            f.write(f"SENDER: {sender}\n")
            f.write(f"MESSAGE:\n{message}\n")
            if response:
                f.write(f"\nRESPONSE:\n{response}\n")
            f.write(f"{'='*60}\n")
    except OSError as e:
        logger.error("Failed to write chat log: %s", e)

# =============================================
# HEALTH TRACKING
# =============================================

_health: Dict[str, Any] = {
    "started_at": None,
    "last_message_at": None,
    "messages_received": 0,
    "messages_failed": 0,
    "errors": 0,
}


def get_health() -> Dict[str, object]:
    """Return current health metrics."""
    return dict(_health)


# =============================================
# TELEGRAM REPLY HELPER
# =============================================

REPLY_MAX_RETRIES = 3
REPLY_BASE_DELAY = 1.0  # seconds

async def safe_reply(message: Any, text: str, retries: int = REPLY_MAX_RETRIES) -> Optional[Message]:
    """
    Send reply_text with retry and exponential backoff.

    Args:
        message: Telegram Message object
        text: Text to send
        retries: Max retry attempts

    Returns:
        The sent Message object if successful, None if all retries failed.
    """
    for attempt in range(retries):
        try:
            sent = await message.reply_text(text, read_timeout=20, write_timeout=20)
            return sent
        except Exception as e:
            delay = REPLY_BASE_DELAY * (2 ** attempt)
            logger.warning(
                "[REPLY] Attempt %d/%d failed (%s: %s). Retrying in %.1fs...",
                attempt + 1, retries, type(e).__name__, e, delay
            )
            if attempt < retries - 1:
                await asyncio.sleep(delay)

    logger.error("[REPLY] All %d attempts failed for message: %s...", retries, text[:80])
    _health["messages_failed"] = int(_health.get("messages_failed", 0)) + 1
    return None


# =============================================
# SECURITY HELPERS
# =============================================

def is_user_allowed(user_id: int) -> bool:
    """
    Check if user ID is in the allowlist.

    Args:
        user_id: Telegram user ID to check

    Returns:
        True if allowed (or allowlist empty), False if blocked
    """
    allowed_ids = get_allowed_user_ids()
    if not allowed_ids:
        return True  # Empty list = allow all (for testing)
    return user_id in allowed_ids


def check_rate_limit(user_id: int) -> bool:
    """
    Check if user is within rate limits.

    Uses sliding window: tracks timestamps of recent messages.

    Args:
        user_id: Telegram user ID to check

    Returns:
        True if within limits, False if rate limited
    """
    current_time = time.time()

    if user_id not in _rate_limit_tracker:
        _rate_limit_tracker[user_id] = []

    timestamps = _rate_limit_tracker[user_id]
    _rate_limit_tracker[user_id] = [
        ts for ts in timestamps if current_time - ts < RATE_LIMIT_WINDOW
    ]

    if len(_rate_limit_tracker[user_id]) >= RATE_LIMIT_MESSAGES:
        return False

    _rate_limit_tracker[user_id].append(current_time)
    return True


# =============================================
# BRANCH TARGETING
# =============================================

def resolve_branch_target(message: str) -> tuple[str, str, Path]:
    """
    Extract @branch target from message and resolve to a directory path.

    If message starts with @branch_name, look up the branch in BRANCH_REGISTRY.json
    and return the cleaned message, branch name, and the branch path.

    Args:
        message: The raw Telegram message text

    Returns:
        Tuple of (cleaned_message, branch_name, target_path)
    """
    match = re.match(r'^@(\w+)\s*(.*)', message, re.DOTALL)
    if not match:
        return message, DEFAULT_BRANCH, DEFAULT_SESSION_PATH

    branch_name = match.group(1).lower()
    rest_of_message = match.group(2).strip()

    try:
        with open(BRANCH_REGISTRY_PATH, 'r', encoding='utf-8') as f:
            registry = json.load(f)

        branches = registry.get("branches", [])
        for branch_entry in branches:
            clean_email = branch_entry.get("email", "").replace("@", "").lower()
            if clean_email == branch_name:
                branch_path = Path(branch_entry.get("path", ""))
                if branch_path.is_dir():
                    logger.info("Branch target resolved: @%s -> %s", branch_name, branch_path)
                    return rest_of_message or "hi", branch_name, branch_path
                else:
                    logger.warning("Branch path not found on disk: %s", branch_path)
                    return message, DEFAULT_BRANCH, DEFAULT_SESSION_PATH

    except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
        logger.warning("Failed to resolve branch @%s: %s", branch_name, e)

    return message, DEFAULT_BRANCH, DEFAULT_SESSION_PATH


# =============================================
# PENDING FILE COORDINATION
# =============================================

def write_pending_file(
    branch_name: str,
    chat_id: int,
    message_id: int,
    bot_token: str,
    session_id: str,
    processing_message_id: Optional[int] = None,
) -> bool:
    """
    Write a pending file for Stop hook coordination.

    The Stop hook checks this file to know if a response should be
    sent to Telegram.

    Args:
        branch_name: Branch name for the session
        chat_id: Telegram chat ID
        message_id: Original message ID
        bot_token: Bot token for API calls
        session_id: Claude Code session ID
        processing_message_id: ID of the "Processing..." message to edit

    Returns:
        True if written successfully
    """
    PENDING_DIR.mkdir(parents=True, exist_ok=True)

    pending_data = {
        "chat_id": chat_id,
        "message_id": message_id,
        "bot_token": bot_token,
        "session_id": session_id,
        "processing_message_id": processing_message_id,
        "timestamp": time.time(),
        "branch_name": branch_name,
    }

    pending_path = PENDING_DIR / f"telegram-{branch_name}.json"

    try:
        pending_path.write_text(
            json.dumps(pending_data, indent=2),
            encoding="utf-8",
        )
        logger.info("Wrote pending file for session %s", session_id[:8] if session_id else "unknown")
        return True
    except OSError as e:
        logger.error("Failed to write pending file: %s", e)
        return False


def get_session_id_from_store(branch_name: str) -> Optional[str]:
    """
    Get the Claude session ID for a branch from the session store.

    Args:
        branch_name: Branch name

    Returns:
        Claude session ID or None
    """
    data = get_session_by_branch(branch_name)
    if data:
        return data.get("session_id")
    return None


# =============================================
# RESPONSE CHUNKING (kept for edge cases)
# =============================================

def chunk_response(text: str, limit: int = TELEGRAM_CHAR_LIMIT) -> list[str]:
    """
    Split text into chunks for Telegram's message limit.

    Args:
        text: The full response text
        limit: Maximum characters per chunk (default 4096)

    Returns:
        List of text chunks, each within the limit
    """
    if len(text) <= limit:
        return [text]

    chunks: list[str] = []
    remaining = text

    while remaining:
        if len(remaining) <= limit:
            chunks.append(remaining)
            break

        chunk = remaining[:limit]

        best_break = -1
        for i in range(len(chunk) - 1, max(0, len(chunk) - 500), -1):
            if chunk[i] in '.!?' and (i + 1 >= len(chunk) or chunk[i + 1] in ' \n'):
                best_break = i + 1
                break

        if best_break == -1:
            newline_pos = chunk.rfind('\n\n')
            if newline_pos > limit // 2:
                best_break = newline_pos + 2

        if best_break == -1:
            newline_pos = chunk.rfind('\n')
            if newline_pos > limit // 2:
                best_break = newline_pos + 1

        if best_break == -1:
            space_pos = chunk.rfind(' ')
            if space_pos > limit // 2:
                best_break = space_pos + 1

        if best_break == -1:
            best_break = limit

        chunks.append(remaining[:best_break].rstrip())
        remaining = remaining[best_break:].lstrip()

    return chunks


# =============================================
# MESSAGE HANDLERS
# =============================================

async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command."""
    _ = context
    if not update.message:
        return

    user = update.effective_user
    username = user.username if user else "Unknown"
    user_id = user.id if user else 0

    logger.info("[START] User: @%s (ID: %s)", username, user_id)

    await safe_reply(
        update.message,
        "Hello! I'm the AIPass Bridge Bot.\n"
        "Send me a message and I'll relay it to Claude.\n\n"
        "Commands:\n"
        "/new - Start fresh session\n"
        "/status - Show session info\n"
        "/switch @branch - Switch target branch\n"
        "/list - List active sessions\n"
        "/end - End current session\n"
        "/branch - Show current branch\n"
        "/help - Show this message"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle incoming text messages.

    Flow:
    1. Security checks (allowlist, rate limit)
    2. Resolve @branch target
    3. Ensure tmux session exists for target branch
    4. Write pending file for Stop hook coordination
    5. Inject message via tmux send-keys
    6. Response delivery handled by Stop hook asynchronously
    """
    _ = context
    if not update.message or not update.message.text:
        return

    message_text = update.message.text
    user = update.effective_user
    chat = update.effective_chat

    username = user.username if user and user.username else None
    user_id = user.id if user else 0
    first_name = user.first_name if user else "Unknown"
    chat_id = chat.id if chat else 0
    display_name = f"@{username}" if username else first_name

    logger.info(
        "[MESSAGE] From: %s (ID: %s) | Chat: %s | Text: %s...",
        display_name, user_id, chat_id, message_text[:100]
    )

    # Security checks
    if not is_user_allowed(user_id):
        logger.warning("[BLOCKED] User ID %s not in allowlist", user_id)
        return

    if not check_rate_limit(user_id):
        logger.warning("[RATE_LIMITED] User ID %s exceeded rate limit", user_id)
        await safe_reply(update.message, "Rate limit exceeded. Please wait before sending more messages.")
        return

    # Health tracking
    _health["last_message_at"] = datetime.now().isoformat()
    _health["messages_received"] = int(_health.get("messages_received", 0)) + 1

    # Resolve branch target
    resolved_message, branch_name, target_cwd = resolve_branch_target(message_text)

    # Update session store with current branch for this chat
    save_session(chat_id, branch_name)

    # Ensure tmux session exists
    if not session_exists(branch_name):
        logger.info("Creating tmux session for branch %s at %s", branch_name, target_cwd)
        if not create_session(branch_name, target_cwd):
            await safe_reply(update.message, "Failed to create Claude session. Please try again.")
            _health["errors"] = int(_health.get("errors", 0)) + 1
            return
        # Give Claude a moment to start up
        await asyncio.sleep(3)

    # Send processing indicator
    processing_msg = await safe_reply(update.message, "Processing...")
    processing_msg_id = processing_msg.message_id if processing_msg else None

    # Get bot token for the Stop hook
    bot_token = get_bot_token()
    if not bot_token:
        await safe_reply(update.message, "Bot configuration error.")
        return

    # Get Claude session ID from session store
    session_id = get_session_id_from_store(branch_name) or f"tmux-{branch_name}"

    # Write pending file for Stop hook
    write_pending_file(
        branch_name=branch_name,
        chat_id=chat_id,
        message_id=update.message.message_id,
        bot_token=bot_token,
        session_id=session_id,
        processing_message_id=processing_msg_id,
    )

    # Format and inject message via tmux
    prompt = f"Patrick via Telegram: {resolved_message}"
    success = await tmux_send_message(branch_name, prompt)

    if not success:
        await safe_reply(update.message, "Failed to send message to Claude. Session may have died.")
        _health["errors"] = int(_health.get("errors", 0)) + 1
        # Clean up pending file
        pending_path = PENDING_DIR / f"telegram-{branch_name}.json"
        pending_path.unlink(missing_ok=True)
        return

    # Log the interaction (response will be logged by Stop hook)
    log_chat(display_name, message_text, "[TMUX_INJECT] Message sent to tmux session")

    logger.info("[TMUX] Message injected into telegram-%s", branch_name)


async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle incoming photo and document messages.

    Downloads the file, builds a prompt, and injects via tmux.
    """
    _ = context
    if not update.message:
        return

    user = update.effective_user
    chat = update.effective_chat

    username = user.username if user and user.username else None
    user_id = user.id if user else 0
    first_name = user.first_name if user else "Unknown"
    chat_id = chat.id if chat else 0
    display_name = f"@{username}" if username else first_name

    # Security checks
    if not is_user_allowed(user_id):
        logger.warning("[BLOCKED] User ID %s not in allowlist (file)", user_id)
        return

    if not check_rate_limit(user_id):
        logger.warning("[RATE_LIMITED] User ID %s exceeded rate limit (file)", user_id)
        await safe_reply(update.message, "Rate limit exceeded. Please wait before sending more messages.")
        return

    # Health tracking
    _health["last_message_at"] = datetime.now().isoformat()
    _health["messages_received"] = int(_health.get("messages_received", 0)) + 1

    caption = update.message.caption
    file_path = None

    try:
        # Determine file source
        if update.message.photo:
            photo = update.message.photo[-1]
            if photo.file_size and photo.file_size > MAX_FILE_SIZE:
                await safe_reply(update.message, f"Photo too large (max {MAX_FILE_SIZE // (1024 * 1024)}MB).")
                return
            file_obj = await photo.get_file()
            file_path = await download_telegram_file(file_obj)
            logger.info("[FILE] Photo from %s (%s bytes)", display_name, photo.file_size)

        elif update.message.document:
            doc = update.message.document
            if doc.file_size and doc.file_size > MAX_FILE_SIZE:
                await safe_reply(update.message, f"File too large (max {MAX_FILE_SIZE // (1024 * 1024)}MB).")
                return
            file_obj = await doc.get_file()
            file_path = await download_telegram_file(file_obj, filename=doc.file_name)
            logger.info("[FILE] Document from %s: %s (%s bytes)", display_name, doc.file_name, doc.file_size)

        else:
            return

        # Detect type and build prompt
        file_type = detect_file_type(file_path)
        prompt = build_file_prompt(file_path, file_type, caption=caption, sender_name=display_name)

        # Get current branch for this chat
        session_data = get_session(chat_id)
        branch_name = session_data.get("branch_name", DEFAULT_BRANCH) if session_data else DEFAULT_BRANCH
        target_cwd = _resolve_branch_path(branch_name)

        # Ensure tmux session exists
        if not session_exists(branch_name):
            if not create_session(branch_name, target_cwd):
                await safe_reply(update.message, "Failed to create Claude session.")
                return
            await asyncio.sleep(3)

        # Send processing indicator
        processing_msg = await safe_reply(update.message, f"Processing {file_type} file...")
        processing_msg_id = processing_msg.message_id if processing_msg else None

        # Get bot token
        bot_token = get_bot_token()
        if not bot_token:
            await safe_reply(update.message, "Bot configuration error.")
            return

        session_id = get_session_id_from_store(branch_name) or f"tmux-{branch_name}"

        # Write pending file
        write_pending_file(
            branch_name=branch_name,
            chat_id=chat_id,
            message_id=update.message.message_id,
            bot_token=bot_token,
            session_id=session_id,
            processing_message_id=processing_msg_id,
        )

        # For text files, content is inline in the prompt
        # For image/pdf, Claude needs the file on disk
        if file_type == 'text':
            cleanup_file(file_path)
            file_path = None

        # Inject via tmux
        success = await tmux_send_message(branch_name, prompt)

        if not success:
            await safe_reply(update.message, "Failed to send file to Claude.")
            pending_path = PENDING_DIR / f"telegram-{branch_name}.json"
            pending_path.unlink(missing_ok=True)
            return

        log_chat(display_name, f"[FILE:{file_type}] {caption or 'no caption'}", "[TMUX_INJECT] File sent to tmux session")

    except ValueError as e:
        await safe_reply(update.message, str(e))
    except Exception as e:
        logger.error("[FILE] Unexpected error: %s: %s", type(e).__name__, e)
        _health["errors"] = int(_health.get("errors", 0)) + 1
        await safe_reply(update.message, "Failed to process file. Please try again.")
    finally:
        if file_path:
            cleanup_file(file_path)


def _resolve_branch_path(branch_name: str) -> Path:
    """
    Resolve a branch name to its directory path.

    Args:
        branch_name: Branch name to resolve

    Returns:
        Path to the branch directory
    """
    try:
        with open(BRANCH_REGISTRY_PATH, 'r', encoding='utf-8') as f:
            registry = json.load(f)

        for branch_entry in registry.get("branches", []):
            clean_email = branch_entry.get("email", "").replace("@", "").lower()
            if clean_email == branch_name:
                path = Path(branch_entry.get("path", ""))
                if path.is_dir():
                    return path
    except (FileNotFoundError, json.JSONDecodeError):
        pass

    return DEFAULT_SESSION_PATH


async def handle_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors in the bot."""
    _health["errors"] = int(_health.get("errors", 0)) + 1

    error_name = type(context.error).__name__ if context.error else "Unknown"
    error_msg = str(context.error) if context.error else "No details"

    user_info = "N/A"
    if isinstance(update, Update) and update.effective_user:
        user = update.effective_user
        user_info = f"{user.first_name} (ID: {user.id})"

    logger.error(
        "[ERROR] %s: %s | User: %s",
        error_name, error_msg, user_info
    )


# =============================================
# APPLICATION SETUP
# =============================================

def create_application() -> Optional[Application]:  # type: ignore[type-arg]
    """
    Create and configure the Telegram Application.

    Returns:
        Configured Application instance or None if setup fails
    """
    token = get_bot_token()
    if not token:
        logger.error("No bot token found. Check ~/.aipass/telegram_config.json")
        return None

    bot_username = get_bot_username()
    logger.info("Creating application for bot: @%s", bot_username)

    request = HTTPXRequest(
        read_timeout=20.0,
        write_timeout=20.0,
        connect_timeout=10.0,
        pool_timeout=5.0,
    )
    application = Application.builder().token(token).request(request).build()

    # Command handlers
    application.add_handler(CommandHandler("start", handle_start))
    application.add_handler(CommandHandler("help", handle_start))
    application.add_handler(CommandHandler("new", handle_new))
    application.add_handler(CommandHandler("status", handle_status))
    application.add_handler(CommandHandler("switch", handle_switch))
    application.add_handler(CommandHandler("list", handle_list))
    application.add_handler(CommandHandler("end", handle_end))
    application.add_handler(CommandHandler("branch", handle_branch))
    application.add_handler(CommandHandler("url", handle_url))

    # File handlers (before text to catch photos/docs)
    application.add_handler(MessageHandler(filters.PHOTO, handle_file))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_file))

    # Text handler
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Error handler
    application.add_error_handler(handle_error)

    logger.info("Application configured with v4 tmux handlers")
    _health["started_at"] = datetime.now().isoformat()
    return application


# =============================================
# SESSION COMMANDS (Phase 4)
# =============================================

async def handle_new(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /new command - kill tmux session and start fresh.
    """
    _ = context
    if not update.message:
        return

    chat = update.effective_chat
    chat_id = chat.id if chat else 0

    session_data = get_session(chat_id)
    branch_name = session_data.get("branch_name", DEFAULT_BRANCH) if session_data else DEFAULT_BRANCH

    # Kill the tmux session
    kill_session(branch_name)

    # Clear session store
    if chat_id:
        clear_session(chat_id)

    logger.info("[NEW] Session killed and cleared for branch %s", branch_name)
    await safe_reply(update.message, f"Session cleared for @{branch_name}. Next message starts fresh.")


async def handle_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /status command - show tmux session info.
    """
    _ = context
    if not update.message:
        return

    chat = update.effective_chat
    chat_id = chat.id if chat else 0

    session_data = get_session(chat_id)
    branch_name = session_data.get("branch_name", DEFAULT_BRANCH) if session_data else DEFAULT_BRANCH

    active = session_exists(branch_name)
    all_sessions = list_sessions()

    info = get_session_info(chat_id)
    status_text = (
        f"Chat ID: {chat_id}\n"
        f"Branch: @{branch_name}\n"
        f"tmux session: {'Active' if active else 'Inactive'}\n"
        f"Active sessions: {len(all_sessions)}\n"
        f"\n{info}"
    )

    await safe_reply(update.message, status_text)


async def handle_switch(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /switch @branch - switch target branch.
    """
    _ = context
    if not update.message or not update.message.text:
        return

    chat = update.effective_chat
    chat_id = chat.id if chat else 0

    # Parse branch name from command args
    parts = update.message.text.split()
    if len(parts) < 2:
        await safe_reply(update.message, "Usage: /switch @branch_name")
        return

    target = parts[1].lstrip("@").lower()

    # Verify branch exists
    target_path = _resolve_branch_path(target)
    if target_path == DEFAULT_SESSION_PATH and target != DEFAULT_BRANCH:
        await safe_reply(update.message, f"Branch @{target} not found in registry.")
        return

    # Update session store
    save_session(chat_id, target)

    logger.info("[SWITCH] Chat %s switched to branch @%s", chat_id, target)
    await safe_reply(
        update.message,
        f"Switched to @{target}.\n"
        f"Session: {'Active' if session_exists(target) else 'Will create on next message'}"
    )


async def handle_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /list command - list all active tmux sessions.
    """
    _ = context
    if not update.message:
        return

    sessions = list_sessions()

    if not sessions:
        await safe_reply(update.message, "No active tmux sessions.")
        return

    lines = ["Active sessions:"]
    for branch in sessions:
        lines.append(f"  - telegram-{branch}")
    lines.append(f"\nTotal: {len(sessions)}")

    await safe_reply(update.message, "\n".join(lines))


async def handle_end(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /end command - kill tmux session for current branch.
    """
    _ = context
    if not update.message:
        return

    chat = update.effective_chat
    chat_id = chat.id if chat else 0

    session_data = get_session(chat_id)
    branch_name = session_data.get("branch_name", DEFAULT_BRANCH) if session_data else DEFAULT_BRANCH

    if session_exists(branch_name):
        kill_session(branch_name)
        await safe_reply(update.message, f"Session for @{branch_name} ended. Next message will create a new one.")
    else:
        await safe_reply(update.message, f"No active session for @{branch_name}.")


async def handle_branch(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /branch command - show which branch this chat targets.
    """
    _ = context
    if not update.message:
        return

    chat = update.effective_chat
    chat_id = chat.id if chat else 0

    session_data = get_session(chat_id)
    branch_name = session_data.get("branch_name", DEFAULT_BRANCH) if session_data else DEFAULT_BRANCH

    await safe_reply(
        update.message,
        f"Current branch: @{branch_name}\n"
        f"Use /switch @branch_name to change."
    )


async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /url command - return current Feel Good App tunnel URL."""
    _ = context
    if not update.message:
        return

    import httpx

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get("http://localhost:4040/api/tunnels")
            data = resp.json()

        tunnels = data.get("tunnels", [])
        https_urls = [t["public_url"] for t in tunnels if t.get("proto") == "https"]

        if https_urls:
            url = https_urls[0]
            await safe_reply(update.message, f"Feel Good App URL:\n{url}")
        else:
            await safe_reply(update.message, "No active tunnel found.")

    except Exception as e:
        logger.warning("[URL] Failed to query ngrok: %s", e)
        await safe_reply(update.message, "Could not reach Expo dev server.")


# =============================================
# MAIN ENTRY POINT
# =============================================

def run_polling() -> None:
    """
    Run the bot in long-polling mode with automatic reconnection.

    Main entry point for the bridge service.
    """
    bot_username = get_bot_username()
    retry_delay = 5
    max_retry_delay = 60

    while True:
        application = create_application()
        if not application:
            logger.error("Failed to create application. Retrying in %ds...", retry_delay)
            time.sleep(retry_delay)
            retry_delay = min(retry_delay * 2, max_retry_delay)
            continue

        logger.info("Starting @%s in long-polling mode (v4 tmux)...", bot_username)
        retry_delay = 5

        try:
            application.run_polling(
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=True
            )
            logger.info("Polling stopped cleanly. Exiting.")
            break
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received. Exiting.")
            break
        except Exception as e:
            error_name = type(e).__name__
            logger.warning(
                "Polling disconnected (%s: %s). Reconnecting in %ds...",
                error_name, e, retry_delay
            )
            time.sleep(retry_delay)
            retry_delay = min(retry_delay * 2, max_retry_delay)


if __name__ == "__main__":
    run_polling()
