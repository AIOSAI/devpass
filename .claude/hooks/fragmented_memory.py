#!/home/aipass/MEMORY_BANK/.venv/bin/python3
"""
Fragmented Memory Hook v2.0 - Reads active conversation from JSONL transcripts

Fires on UserPromptSubmit. Reads the active Claude Code conversation,
extracts recent human messages, and queries the fragment engine
for relevant memory associations.

Part of Memory Bank Fragmented Memory system (FPLAN-0290)

Version: 2.0.0
Created: 2026-02-05
Updated: 2026-02-08
"""
import json
import sys
import time
from pathlib import Path

# Setup paths
AIPASS_ROOT = Path.home()
sys.path.insert(0, str(AIPASS_ROOT))

CLAUDE_PROJECTS_DIR = AIPASS_ROOT / ".claude" / "projects"
STATE_FILE = AIPASS_ROOT / "MEMORY_BANK" / "apps" / "json_templates" / "custom" / "fragmented_memory_state.json"
HEARTBEAT_INTERVAL = 1800  # 30 min between heartbeats
TAIL_BYTES = 500_000  # Read last ~500KB for message extraction


def find_active_jsonl():
    """
    Find the most recently modified main session JSONL.

    Scans all project directories under .claude/projects/ for UUID-named
    JSONL files (skipping agent-* subagent files). Returns the most
    recently modified one, which is the active conversation.
    """
    if not CLAUDE_PROJECTS_DIR.exists():
        return None

    candidates = []
    for project_dir in CLAUDE_PROJECTS_DIR.iterdir():
        if not project_dir.is_dir():
            continue
        for f in project_dir.glob("*.jsonl"):
            # Skip agent subagent files - we want main session transcripts
            if f.name.startswith("agent-"):
                continue
            candidates.append(f)

    if not candidates:
        return None

    return max(candidates, key=lambda f: f.stat().st_mtime)


def extract_human_messages(jsonl_path, max_messages=8):
    """
    Extract last N human text messages from tail of JSONL.

    Reads only the last TAIL_BYTES of the file for performance.
    Filters for user messages with actual text content (not tool results).

    Returns list of dicts with 'role' and 'content' keys.
    """
    messages = []
    file_size = jsonl_path.stat().st_size
    seek_pos = max(0, file_size - TAIL_BYTES)

    with open(jsonl_path, 'rb') as f:
        f.seek(seek_pos)
        if seek_pos > 0:
            f.readline()  # Skip partial first line

        for line in f:
            line = line.decode('utf-8', errors='ignore').strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue

            if entry.get('type') != 'user':
                continue

            content = entry.get('message', {}).get('content', '')

            # Direct human text (string content)
            if isinstance(content, str) and content.strip():
                messages.append({'role': 'user', 'content': content.strip()})
            # List content - extract text items (not tool_results)
            elif isinstance(content, list):
                texts = [
                    item.get('text', '').strip()
                    for item in content
                    if isinstance(item, dict)
                    and item.get('type') == 'text'
                    and item.get('text', '').strip()
                ]
                if texts:
                    messages.append({'role': 'user', 'content': ' '.join(texts)})

    return messages[-max_messages:]


def count_messages_since(jsonl_path, byte_offset):
    """
    Count human text messages added since a byte offset in the file.

    Used to determine how many messages have passed since the last
    fragment was surfaced, which gates the surfacing frequency.
    """
    count = 0
    file_size = jsonl_path.stat().st_size

    if byte_offset >= file_size:
        return 0

    with open(jsonl_path, 'rb') as f:
        f.seek(byte_offset)
        if byte_offset > 0:
            f.readline()  # Skip partial line

        for line in f:
            line = line.decode('utf-8', errors='ignore').strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue

            if entry.get('type') != 'user':
                continue

            content = entry.get('message', {}).get('content', '')
            if isinstance(content, str) and content.strip():
                count += 1
            elif isinstance(content, list):
                if any(
                    isinstance(item, dict)
                    and item.get('type') == 'text'
                    and item.get('text', '').strip()
                    for item in content
                ):
                    count += 1

    return count


def load_state():
    """Load persistent state from JSON file between hook invocations."""
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {}


def save_state(state):
    """Save persistent state to JSON file."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2)


def main():
    """
    Main hook execution.

    1. Find active conversation JSONL
    2. Load persistent state (tracks surfaces across invocations)
    3. Count new messages since last surface
    4. Extract recent human messages for context
    5. Pre-configure handler SESSION_STATE from persisted data
    6. Run fragment engine via process_hook()
    7. On surface: print recall, update state
    8. On no surface: occasional heartbeat message
    """
    try:
        # Find active conversation
        jsonl_path = find_active_jsonl()
        if not jsonl_path:
            return

        # Load persistent state
        state = load_state()
        session_key = str(jsonl_path)

        # Reset state if session changed (new conversation)
        if state.get('session_jsonl') != session_key:
            state = {
                'session_jsonl': session_key,
                'byte_offset_at_last_surface': 0,
                'last_surface_time': 0,
                'surfaces_count': 0,
                'last_heartbeat_time': 0
            }

        # Count messages since last surface
        byte_offset = state.get('byte_offset_at_last_surface', 0)
        messages_since = count_messages_since(jsonl_path, byte_offset)

        # Extract recent human messages for context
        messages = extract_human_messages(jsonl_path, max_messages=8)
        if not messages:
            return

        # Import via module API (handler direct imports are guarded)
        from MEMORY_BANK.apps.modules import symbolic

        # Pre-set session state from persisted data
        # (SESSION_STATE resets each process invocation, so we restore it)
        symbolic.hook.SESSION_STATE['messages_since_last'] = messages_since
        symbolic.hook.SESSION_STATE['fragments_surfaced'] = state.get('surfaces_count', 0)
        symbolic.hook.SESSION_STATE['last_surface_time'] = state.get('last_surface_time', 0)

        # Run the fragment engine with real conversation context
        result = symbolic.process_hook(messages)

        if result.get('success') and result.get('surfaced'):
            recall_text = result.get('recall', '')
            if recall_text:
                print(f"\n💭 Memory Fragment:\n{recall_text}")

                # Update persisted state after successful surface
                state['byte_offset_at_last_surface'] = jsonl_path.stat().st_size
                state['last_surface_time'] = time.time()
                state['surfaces_count'] = state.get('surfaces_count', 0) + 1
                save_state(state)
        else:
            # Heartbeat: if no fragment surfaced and enough time has passed
            now = time.time()
            last_activity = max(
                state.get('last_heartbeat_time', 0),
                state.get('last_surface_time', 0)
            )

            if messages_since >= 15 and (now - last_activity) > HEARTBEAT_INTERVAL:
                print("\n💭 Memory Bank is listening... no connections surfaced yet, but I'm here.")
                state['last_heartbeat_time'] = now
                save_state(state)

    except ImportError:
        # Memory Bank not available - silent fail
        pass
    except Exception:
        # Any error - silent fail (don't break the prompt)
        pass


if __name__ == "__main__":
    main()
