#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: telegram_response.py - Stop Hook for Telegram Response Delivery
# Date: 2026-02-12
# Version: 2.0.0
# Category: hooks
#
# CHANGELOG (Max 5 entries):
#   - v2.0.0 (2026-02-17): FPLAN-0351 - 3-layer defense: SubagentStop filter, isSidechain filter, transcript position tracking
#   - v1.0.5 (2026-02-15): Feature - Prepend @branch identifier to every Telegram response
#   - v1.0.4 (2026-02-15): Fix - Retry extraction with delays (JSONL flush race), retry sends with backoff
#   - v1.0.3 (2026-02-15): Fix - Strip whitespace from extracted text (Claude emits \n\n preamble blocks)
#   - v1.0.2 (2026-02-15): Fix - Capture Telegram error details, don't delete pending on send failure
#
# CODE STANDARDS:
#   - Must be FAST - exits in <10ms when no pending Telegram request
#   - All errors logged to file, never stdout (hooks must be quiet)
#   - No external dependencies beyond stdlib + requests
# =============================================

"""
Telegram Response Stop Hook (v2 - FPLAN-0351)

Fires on every Claude Code Stop event. Uses 3-layer defense to ensure only
the correct response (to Patrick's Telegram message) is delivered:

Layer 1: SubagentStop filter - rejects subagent/sidechain Stop events at the gate
Layer 2: isSidechain filter - skips sidechain entries during transcript extraction
Layer 3: Transcript position - only extracts text after the recorded injection point

Coordination mechanism:
- Bridge writes: ~/.aipass/telegram_pending/{session_name}.json (with transcript_line_after)
- Hook reads: JSONL transcript for the session (position-aware)
- Hook sends: response to Telegram via Bot API
- Hook cleans: pending file after successful delivery
"""

import json
import logging
import sys
import time
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

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


def extract_assistant_response(transcript_path: str, start_line: int = 0) -> str | None:
    """
    Extract the last assistant response from a JSONL transcript file.

    Uses position-aware extraction (Layer 3) and sidechain filtering (Layer 2)
    to ensure only the correct main-chain response is returned.

    Args:
        transcript_path: Path to the JSONL transcript file
        start_line: Only look at lines from this index onward (Layer 3 - transcript position)

    Returns:
        The assistant's text response, or None if not found
    """
    path = Path(transcript_path)
    if not path.exists():
        logger.warning("Transcript file not found: %s", transcript_path)
        return None

    try:
        all_lines = path.read_text(encoding="utf-8").strip().split("\n")
    except OSError as e:
        logger.error("Failed to read transcript: %s", e)
        return None

    if not all_lines:
        return None

    # LAYER 3: Only examine lines after the recorded injection point
    lines = all_lines[start_line:] if start_line > 0 else all_lines

    # Find the last non-sidechain, non-tool-result user message in the relevant slice
    # Tool results (from tool_use responses) are "user" type but are intermediate
    # messages, not real user input. Skipping them ensures we capture ALL assistant
    # text across multi-turn responses (text → tool_use → tool_result → more text).
    last_user_idx = -1
    for i, line in enumerate(lines):
        try:
            entry = json.loads(line)
            # LAYER 2: Skip sidechain (subagent) entries
            if entry.get("isSidechain", False):
                continue
            if entry.get("type") == "user":
                # Skip tool_result messages - they're intermediate, not real user input
                message = entry.get("message", {})
                content = message.get("content", [])
                if isinstance(content, list) and all(
                    isinstance(b, dict) and b.get("type") == "tool_result"
                    for b in content
                    if isinstance(b, dict)
                ):
                    continue
                last_user_idx = i
        except json.JSONDecodeError:
            continue

    if last_user_idx == -1:
        logger.warning("No user message found in transcript (start_line=%d)", start_line)
        return None

    # Collect assistant text from after the last non-sidechain user message
    text_parts = []
    for line in lines[last_user_idx + 1:]:
        try:
            entry = json.loads(line)
            # LAYER 2: Skip sidechain (subagent) entries
            if entry.get("isSidechain", False):
                continue
            if entry.get("type") == "assistant":
                message = entry.get("message", {})
                content = message.get("content", [])
                for block in content:
                    if block.get("type") == "text":
                        text = block.get("text", "").strip()
                        if text:
                            text_parts.append(text)
        except json.JSONDecodeError:
            continue

    if not text_parts:
        logger.warning("No assistant text found after last user message (start_line=%d)", start_line)
        return None

    result = "\n\n".join(text_parts).strip()
    return result if result else None


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
    except HTTPError as e:
        # Capture Telegram's detailed error response body
        try:
            body = json.loads(e.read().decode("utf-8"))
            description = body.get("description", "unknown")
            logger.error("Telegram HTTP %d: %s (text_len=%d)", e.code, description, len(text))
        except Exception:
            logger.error("Telegram HTTP %d: %s (text_len=%d)", e.code, e.reason, len(text))
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

    # LAYER 1: Reject SubagentStop events at the gate (FPLAN-0351)
    # SubagentStop fires when a Task tool agent completes. These are internal
    # events that should never trigger a Telegram response delivery.
    hook_event = payload.get("hook_event_name", "")
    if hook_event == "SubagentStop":
        return  # Subagent completion, not a user-facing response

    session_id = payload.get("session_id", "")
    transcript_path = payload.get("transcript_path", "")

    # LAYER 1b: Reject if transcript path indicates a subagent
    if transcript_path and "/subagents/" in transcript_path:
        return  # Subagent transcript, not the main session

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
        # No transcript path - may be a subagent or incomplete payload.
        # Keep pending file for retry by the parent session's Stop event.
        logger.warning("No transcript_path in payload - keeping pending file for retry")
        return

    # LAYER 3: Get transcript position from pending file (written by bridge)
    start_line = pending_data.get("transcript_line_after", 0)

    # Extract with retry - the JSONL transcript may not be fully flushed to disk
    # when the Stop event fires. Claude writes entries sequentially (\n\n preamble
    # first, then thinking, then real text) and the OS write buffer may not have
    # committed the final text block yet. Retry with increasing delays.
    response_text = None
    for attempt in range(4):  # 0, 1, 2, 3
        response_text = extract_assistant_response(transcript_path, start_line=start_line)
        if response_text:
            if attempt > 0:
                logger.info("Transcript text found on attempt %d", attempt + 1)
            break
        if attempt < 3:
            delay = [0.2, 0.5, 1.0][attempt]  # 200ms, 500ms, 1s
            logger.info("No text yet, waiting %.1fs before retry (attempt %d/4)", delay, attempt + 1)
            time.sleep(delay)

    if not response_text:
        # After 4 attempts (~1.7s total wait), still no text. This is likely a
        # subagent Stop event or context compaction. Keep pending file for retry.
        logger.warning("No assistant text after 4 attempts - keeping pending file for retry")
        return

    # Prepend @branch identifier so user knows which branch responded
    try:
        branch_name = Path.cwd().name
        response_text = f"@{branch_name}\n\n{response_text}"
    except Exception:
        pass  # If CWD resolution fails, send without prefix

    # Chunk and send response
    chunks = chunk_text(response_text)
    logger.info("Sending %d chunk(s) to chat %s", len(chunks), chat_id)

    def send_with_retry(token: str, cid: int, msg: str, retries: int = 3) -> bool:
        """Send with retry and exponential backoff for transient network errors."""
        for attempt in range(retries):
            if send_to_telegram(token, cid, msg):
                return True
            if attempt < retries - 1:
                delay = 1.0 * (2 ** attempt)  # 1s, 2s
                logger.info("Send retry %d/%d after %.0fs", attempt + 2, retries, delay)
                time.sleep(delay)
        return False

    all_sent = True
    for i, chunk in enumerate(chunks):
        if i == 0 and processing_message_id:
            # Edit the "Processing..." message with the first chunk
            text = f"[1/{len(chunks)}]\n{chunk}" if len(chunks) > 1 else chunk
            if not edit_telegram_message(bot_token, chat_id, processing_message_id, text):
                # Fallback: send as new message
                if not send_with_retry(bot_token, chat_id, text):
                    all_sent = False
        else:
            prefix = f"[{i + 1}/{len(chunks)}]\n" if len(chunks) > 1 else ""
            if not send_with_retry(bot_token, chat_id, prefix + chunk):
                all_sent = False

    if all_sent:
        pending_file.unlink(missing_ok=True)
        logger.info("Response delivered and pending file cleaned up")
    else:
        # Keep pending file so next Stop event can retry delivery
        logger.error("Delivery failed - keeping pending file for retry")


if __name__ == "__main__":
    main()
