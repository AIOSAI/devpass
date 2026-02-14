#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: telegram_response.py - Stop Hook for Telegram Response Delivery
# Date: 2026-02-12
# Version: 1.0.0
# Category: hooks
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2026-02-12): Initial - Stop hook reads JSONL transcript, sends to Telegram
#
# CODE STANDARDS:
#   - Must be FAST - exits in <10ms when no pending Telegram request
#   - All errors logged to file, never stdout (hooks must be quiet)
#   - No external dependencies beyond stdlib + requests
# =============================================

"""
Telegram Response Stop Hook

Fires on every Claude Code Stop event. Checks if the response was triggered
by a Telegram message (pending file exists), reads the JSONL transcript,
extracts the last assistant response, and sends it to Telegram via Bot API.

Coordination mechanism:
- Bridge writes: ~/.aipass/telegram_pending/{session_name}.json
- Hook reads: JSONL transcript for the session
- Hook sends: response to Telegram via requests.post
- Hook cleans: pending file after successful delivery
"""

import json
import logging
import os
import sys
import time
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError

# Logging to file only (hooks must be quiet on stdout/stderr)
LOG_FILE = Path.home() / "system_logs" / "telegram_hook.log"
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger("telegram_hook")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.FileHandler(str(LOG_FILE))
    handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)

# Constants
PENDING_DIR = Path.home() / ".aipass" / "telegram_pending"
PENDING_TTL = 600  # 10 minutes - ignore stale pending files
TELEGRAM_CHAR_LIMIT = 4096


def find_pending_file(session_id: str) -> Path | None:
    """
    Find a pending file that matches the current session.

    Primary match: CWD-derived branch name → telegram-{branch}.json
    Fallback: session_id field match (if bridge knows the real session ID)

    The bridge can't know Claude's real session_id ahead of time, so we
    match by the working directory (each tmux session runs in a branch dir).

    Args:
        session_id: Claude Code session ID from the Stop hook

    Returns:
        Path to the matching pending file, or None
    """
    if not PENDING_DIR.exists():
        return None

    def _check_ttl(pending_file: Path) -> Path | None:
        """Check if pending file is fresh enough. Returns file or None."""
        try:
            data = json.loads(pending_file.read_text(encoding="utf-8"))
            ts = data.get("timestamp", 0)
            if isinstance(ts, str):
                try:
                    ts = float(ts)
                except ValueError:
                    ts = 0
            if time.time() - ts > PENDING_TTL:
                logger.info("Stale pending file (>%ds): %s", PENDING_TTL, pending_file.name)
                pending_file.unlink(missing_ok=True)
                return None
            return pending_file
        except (json.JSONDecodeError, OSError):
            return None

    # Primary: match by CWD-derived branch name
    # Claude runs in the branch directory inside tmux, so CWD = branch path
    try:
        cwd = Path.cwd()
        branch_name = cwd.name
        pending_path = PENDING_DIR / f"telegram-{branch_name}.json"
        if pending_path.exists():
            result = _check_ttl(pending_path)
            if result:
                logger.info("Matched pending file by CWD branch: %s", branch_name)
                return result
    except Exception:
        pass

    # Fallback: match by session_id field
    for pending_file in PENDING_DIR.glob("*.json"):
        try:
            data = json.loads(pending_file.read_text(encoding="utf-8"))
            if data.get("session_id") == session_id:
                return _check_ttl(pending_file)
        except (json.JSONDecodeError, OSError):
            continue

    return None


def extract_assistant_response(transcript_path: str) -> str | None:
    """
    Extract the last assistant response from a JSONL transcript file.

    Reads from the end of file to find the last assistant message,
    then extracts all text content blocks.

    Args:
        transcript_path: Path to the JSONL transcript file

    Returns:
        The assistant's text response, or None if not found
    """
    path = Path(transcript_path)
    if not path.exists():
        logger.warning("Transcript file not found: %s", transcript_path)
        return None

    try:
        lines = path.read_text(encoding="utf-8").strip().split("\n")
    except OSError as e:
        logger.error("Failed to read transcript: %s", e)
        return None

    if not lines:
        return None

    # Find the last user message line number
    last_user_idx = -1
    for i, line in enumerate(lines):
        try:
            entry = json.loads(line)
            if entry.get("type") == "user":
                last_user_idx = i
        except json.JSONDecodeError:
            continue

    if last_user_idx == -1:
        logger.warning("No user message found in transcript")
        return None

    # Collect all assistant text from after the last user message
    text_parts = []
    for line in lines[last_user_idx + 1:]:
        try:
            entry = json.loads(line)
            if entry.get("type") == "assistant":
                message = entry.get("message", {})
                content = message.get("content", [])
                for block in content:
                    if block.get("type") == "text":
                        text = block.get("text", "")
                        if text:
                            text_parts.append(text)
        except json.JSONDecodeError:
            continue

    if not text_parts:
        logger.warning("No assistant text found after last user message")
        return None

    return "\n\n".join(text_parts)


def chunk_text(text: str, limit: int = TELEGRAM_CHAR_LIMIT) -> list[str]:
    """
    Split text into chunks for Telegram's message limit.

    Args:
        text: The full response text
        limit: Maximum characters per chunk

    Returns:
        List of text chunks within the limit
    """
    if len(text) <= limit:
        return [text]

    chunks = []
    remaining = text

    while remaining:
        if len(remaining) <= limit:
            chunks.append(remaining)
            break

        chunk = remaining[:limit]

        # Try sentence boundary
        best_break = -1
        for i in range(len(chunk) - 1, max(0, len(chunk) - 500), -1):
            if chunk[i] in '.!?' and (i + 1 >= len(chunk) or chunk[i + 1] in ' \n'):
                best_break = i + 1
                break

        # Try paragraph break
        if best_break == -1:
            pos = chunk.rfind('\n\n')
            if pos > limit // 2:
                best_break = pos + 2

        # Try newline
        if best_break == -1:
            pos = chunk.rfind('\n')
            if pos > limit // 2:
                best_break = pos + 1

        # Try space
        if best_break == -1:
            pos = chunk.rfind(' ')
            if pos > limit // 2:
                best_break = pos + 1

        # Hard break
        if best_break == -1:
            best_break = limit

        chunks.append(remaining[:best_break].rstrip())
        remaining = remaining[best_break:].lstrip()

    return chunks


def send_to_telegram(bot_token: str, chat_id: int, text: str, message_id: int | None = None) -> bool:
    """
    Send a message to Telegram via Bot API using urllib (no external deps).

    Args:
        bot_token: Telegram bot token
        chat_id: Target chat ID
        text: Message text
        message_id: Optional message ID to reply to

    Returns:
        True if sent successfully
    """
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    payload = {
        "chat_id": chat_id,
        "text": text,
    }
    if message_id:
        payload["reply_to_message_id"] = message_id

    data = json.dumps(payload).encode("utf-8")
    req = Request(url, data=data, headers={"Content-Type": "application/json"})

    try:
        with urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read())
            if result.get("ok"):
                return True
            logger.error("Telegram API error: %s", result.get("description"))
            return False
    except URLError as e:
        logger.error("Failed to send to Telegram: %s", e)
        return False
    except Exception as e:
        logger.error("Unexpected error sending to Telegram: %s", e)
        return False


def edit_telegram_message(bot_token: str, chat_id: int, message_id: int, text: str) -> bool:
    """
    Edit an existing Telegram message via Bot API.

    Args:
        bot_token: Telegram bot token
        chat_id: Target chat ID
        message_id: ID of the message to edit
        text: New message text

    Returns:
        True if edited successfully
    """
    url = f"https://api.telegram.org/bot{bot_token}/editMessageText"

    payload = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text,
    }

    data = json.dumps(payload).encode("utf-8")
    req = Request(url, data=data, headers={"Content-Type": "application/json"})

    try:
        with urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read())
            return result.get("ok", False)
    except Exception as e:
        logger.warning("Failed to edit message: %s", e)
        return False


def main() -> None:
    """
    Main hook entry point. Reads Stop hook payload from stdin.

    Expected stdin JSON:
    {
        "session_id": "...",
        "transcript_path": "...",
        ...
    }
    """
    # Read hook payload from stdin
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, Exception):
        return  # Not valid JSON, exit silently

    session_id = payload.get("session_id", "")
    transcript_path = payload.get("transcript_path", "")

    if not session_id:
        return  # No session ID, exit silently

    # Fast exit: check if there's a pending Telegram request for this session
    pending_file = find_pending_file(session_id)
    if not pending_file:
        return  # Not a Telegram session, exit silently (<10ms)

    logger.info("Processing Telegram response for session %s", session_id[:8])

    # Read pending data
    try:
        pending_data = json.loads(pending_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        logger.error("Failed to read pending file: %s", e)
        pending_file.unlink(missing_ok=True)
        return

    chat_id = pending_data.get("chat_id")
    bot_token = pending_data.get("bot_token")
    processing_message_id = pending_data.get("processing_message_id")

    if not chat_id or not bot_token:
        logger.error("Missing chat_id or bot_token in pending file")
        pending_file.unlink(missing_ok=True)
        return

    # Extract assistant response from transcript
    if not transcript_path:
        # Try to find transcript from Claude's project directory
        logger.warning("No transcript_path in payload, cannot extract response")
        pending_file.unlink(missing_ok=True)
        return

    response_text = extract_assistant_response(transcript_path)

    if not response_text:
        logger.warning("No assistant response found in transcript")
        pending_file.unlink(missing_ok=True)
        return

    # Chunk and send response
    chunks = chunk_text(response_text)
    logger.info("Sending %d chunk(s) to chat %s", len(chunks), chat_id)

    for i, chunk in enumerate(chunks):
        if i == 0 and processing_message_id:
            # Edit the "Processing..." message with the first chunk
            text = f"[1/{len(chunks)}]\n{chunk}" if len(chunks) > 1 else chunk
            if not edit_telegram_message(bot_token, chat_id, processing_message_id, text):
                # Fallback: send as new message
                send_to_telegram(bot_token, chat_id, text)
        else:
            prefix = f"[{i + 1}/{len(chunks)}]\n" if len(chunks) > 1 else ""
            send_to_telegram(bot_token, chat_id, prefix + chunk)

    # Clean up pending file after successful delivery
    pending_file.unlink(missing_ok=True)
    logger.info("Response delivered and pending file cleaned up")


if __name__ == "__main__":
    main()
