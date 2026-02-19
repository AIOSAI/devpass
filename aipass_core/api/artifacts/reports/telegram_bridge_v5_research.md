# Telegram Bridge v5 Research Report

**FPLAN-0351** | **Author**: API Branch (Session 48) | **Date**: 2026-02-17

---

## 1. Root Cause Confirmation

### The Bug: Stop Hook Fires on ALL Assistant Responses

**Confirmed with evidence from code, logs, and transcript analysis.**

The Stop hook (`~/.claude/hooks/telegram_response.py` v1.0.5) fires on **every** Claude Code Stop event system-wide. It matches Telegram sessions by checking if a pending file exists at `~/.aipass/telegram_pending/telegram-{branch}.json` where `{branch}` is derived from `Path.cwd().name`.

The hook has **no mechanism** to distinguish:
- Response to Patrick's Telegram message (INTENDED)
- Subagent/Task tool completion (BUG - sends internal content)
- Context compaction event (BUG - sends stale content)
- Monitoring agent periodic check (BUG - sends monitoring data)

### Evidence Chain

**Code evidence (`telegram_response.py`):**
- Lines 64-123: `find_pending_file()` matches by CWD branch name only. ANY Stop event from the same branch directory matches.
- Lines 127-189: `extract_assistant_response()` grabs the last assistant text from the JSONL transcript. No way to distinguish which response was for Patrick vs internal activity.
- Lines 393-407: Retry loop with delays means even delayed internal responses can match.
- Lines 445-446: On success, pending file is DELETED. The real response's Stop event fires later but finds no pending file and silently drops.
- Stop hook registered in `settings.json` with NO matcher field - fires on ALL Stop events including subagent completions.

**Log evidence (`telegram_hook.log`):**
- 264 total deliveries across the log history.
- 68 deliveries required retry (text not immediately available - indicating the Stop event fired before the assistant text was written, typical of subagent/intermediate events).
- Feb 15: 3.6x delivery-to-bridge ratio (multiple deliveries per user message = subagent events leaking).
- Feb 16-17: ~1:1 ratio (simpler conversations with fewer subagents).

**Transcript evidence (session 553fe213, Feb 17):**
- Subagent `a9db575` (monitoring VERA's progress) ran with CWD `/home/aipass/aipass_os/dev_central` - SAME as parent session.
- Subagent `ade244b` (researching Telegram bridge config) ran from same CWD.
- Both share `sessionId: 553fe213` with the parent session.
- When these subagents' Stop events fire, `find_pending_file()` matches `telegram-dev_central.json` because CWD.name = "dev_central".

### The Exact Failure Sequence

```
1. Patrick sends message via Telegram
2. Bridge writes telegram-dev_central.json (pending file)
3. Bridge injects "Patrick via Telegram: {msg}" into tmux
4. Claude starts processing, spawns Task tool (monitoring agent)
5. Monitoring agent completes -> Stop event fires
6. Stop hook matches telegram-dev_central.json (CWD = dev_central)
7. Hook extracts monitoring agent's internal text from transcript
8. Hook sends WRONG content to Patrick on Telegram
9. Hook DELETES the pending file
10. Claude's ACTUAL response to Patrick completes -> Stop event fires
11. No pending file exists -> response silently dropped
12. Patrick receives monitoring gibberish, never gets his real answer
```

### Secondary Issue: No Proactive Push

Even if the leaking bug is fixed, there is no mechanism for Claude to proactively push activity updates. The current system is purely reactive: message in -> response out. Patrick wants to see monitoring agent completions, background task status, and general activity.

---

## 2. Solution Options

### Option A: Message Index Correlation (RECOMMENDED)

**Concept:** When the bridge injects a message, record the transcript line count at that moment. The Stop hook only extracts assistant text that appears after that specific line.

**Implementation:**
1. Bridge counts lines in the JSONL transcript BEFORE injecting the message via tmux.
2. Bridge writes `transcript_line_count` into the pending file alongside `chat_id`, `bot_token`, etc.
3. Stop hook reads `transcript_line_count` from pending file.
4. `extract_assistant_response()` skips all lines before `transcript_line_count`.
5. Only extracts assistant text that was written AFTER the user's Telegram message was injected.
6. Subagent Stop events will find no new user message after the recorded line -> extraction returns empty -> pending file kept for retry.

**Pseudocode:**
```python
# In bridge.py write_pending_file():
transcript_path = get_transcript_path(branch_name)
line_count = count_lines(transcript_path) if transcript_path else 0
pending_data = {
    "chat_id": chat_id,
    "bot_token": bot_token,
    "timestamp": time.time(),
    "transcript_line_after": line_count,  # NEW
    "processing_message_id": msg_id
}

# In telegram_response.py extract_assistant_response():
start_line = pending_data.get("transcript_line_after", 0)
lines = transcript_lines[start_line:]
# Find last user message in THIS slice only
# Extract assistant text after it
```

**Pros:**
- Minimal code change (~20 lines)
- No new dependencies
- Preserves fast exit path for non-Telegram sessions
- Backwards compatible (missing field = old behavior)
- Deterministic - not timing-based

**Cons:**
- Requires bridge to know transcript location (currently only the hook knows)
- Transcript may grow between line count and injection (race window, but small)
- Doesn't solve proactive push (Phase 3 issue)

**Feasibility: HIGH** | **Risk: LOW** | **Effort: SMALL**

---

### Option B: Subagent-Aware Hook Filtering

**Concept:** Detect whether the Stop event comes from a subagent or the parent session. Only process parent session Stop events.

**Implementation:**
1. Check if the Stop hook stdin payload contains subagent indicators.
2. Claude Code hooks provide `hook_event_name` in the payload. For subagent completions, a separate `SubagentStop` event exists.
3. Register the Telegram hook ONLY on `Stop` (not `SubagentStop`).
4. Additionally check if `transcript_path` points to a subagent JSONL (pattern: `subagents/agent-*.jsonl`).

**Pseudocode:**
```python
# In telegram_response.py main():
payload = json.load(sys.stdin)
event_name = payload.get("hook_event_name", "")

# Skip subagent events entirely
if event_name == "SubagentStop":
    sys.exit(0)

# Also check transcript path for subagent pattern
transcript = payload.get("transcript_path", "")
if "/subagents/" in transcript:
    sys.exit(0)
```

**Pros:**
- Very simple filter (~5 lines)
- Eliminates the most common false positive (subagent completions)
- No changes needed to bridge.py

**Cons:**
- Does NOT solve context compaction Stop events (these fire on the parent session)
- Does NOT solve multi-turn tool call intermediate Stop events
- `SubagentStop` has a known issue: all subagents in the same session share the same `session_id`, making per-agent filtering impossible (GitHub issue #7881)
- Still relies on "last assistant text" extraction which can pick up wrong content

**Feasibility: HIGH** | **Risk: MEDIUM** (partial fix) | **Effort: TRIVIAL**

---

### Option C: Transcript Position Tracking with Debounce

**Concept:** Instead of responding to the FIRST Stop event after a pending file appears, wait for the conversation to "settle" (no new Stop events for N seconds), then extract the final response.

**Implementation:**
1. Stop hook writes a "response ready" marker file instead of immediately sending.
2. A separate lightweight daemon (or cron job, every 5s) checks for marker files.
3. If a marker file exists AND no Stop event has fired in the last 3 seconds, extract and send.
4. This naturally skips intermediate subagent/tool Stop events.

**Pseudocode:**
```python
# In telegram_response.py (simplified):
# Instead of send_to_telegram(), write a marker:
marker = {
    "pending_file": pending_path,
    "last_stop_time": time.time(),
    "transcript_path": transcript_path
}
write_json(f"{PENDING_DIR}/ready-{branch}.json", marker)

# Separate daemon (response_sender.py):
while True:
    for marker in glob(f"{PENDING_DIR}/ready-*.json"):
        data = read_json(marker)
        if time.time() - data["last_stop_time"] > 3.0:  # Settled
            text = extract_assistant_response(data["transcript_path"])
            send_to_telegram(...)
            delete(marker)
            delete(data["pending_file"])
    time.sleep(1)
```

**Pros:**
- Naturally handles multi-turn tool calls and subagent events
- Always sends the FINAL response, not intermediate ones
- Simple conceptually

**Cons:**
- Adds 3+ second latency to ALL responses
- Requires a separate daemon process
- More complex coordination (two files instead of one)
- Edge case: if Claude works for 30 seconds straight, the response arrives late
- Doesn't solve proactive push

**Feasibility: MEDIUM** | **Risk: MEDIUM** | **Effort: MEDIUM**

---

### Option D: Replace Stop Hook with Transcript Polling

**Concept:** Abandon the Stop hook entirely. Replace it with a lightweight daemon that polls the JSONL transcript for new content after a message is injected.

**Implementation:**
1. Bridge writes pending file with `transcript_path` and `injected_at_line`.
2. A daemon polls the transcript every 2 seconds.
3. When it detects a new user message (matching "Patrick via Telegram:") followed by assistant text that appears to be a complete response, it sends to Telegram.
4. "Complete response" heuristic: no new lines for 2 seconds, or explicit end-of-turn marker.

**Pros:**
- Completely eliminates Stop hook race conditions
- Can also watch for proactive activity (Phase 3)
- Single daemon handles both conversation replies and activity push
- No hook timing issues

**Cons:**
- Polling adds latency (up to poll interval)
- Parsing JSONL to detect "complete" responses is non-trivial
- Must handle large transcript files efficiently (seek to end, not re-read)
- More infrastructure (systemd service)
- Harder to debug than hook-based approach

**Feasibility: MEDIUM** | **Risk: HIGH** | **Effort: LARGE**

---

### Option E: Hybrid - Stop Hook + SubagentStop Filter + Message Index (RECOMMENDED COMBINATION)

**Concept:** Combine Options A and B for defense in depth.

**Implementation:**
1. Filter out `SubagentStop` events immediately (Option B - 5 lines)
2. Add `transcript_line_after` to pending file (Option A - 20 lines)
3. Extract only text after the recorded line position
4. Keep retry loop for timing, but with position-aware extraction

This provides two layers of protection:
- Layer 1: Subagent events are rejected at the gate
- Layer 2: Even if a parent-session Stop event fires early (e.g., compaction), the position-based extraction only finds text written after Patrick's message

**Feasibility: HIGH** | **Risk: LOW** | **Effort: SMALL**

---

## 3. Prior Art

### Most Relevant Projects

| Project | Repo | Architecture | How They Solve Bidirectional |
|---------|------|-------------|------------------------------|
| **CCBot** | [six-ddc/ccbot](https://github.com/six-ddc/ccbot) | tmux + Telegram topics | Each topic = 1 session. Window-session mappings in `session_map.json`. Streams thinking, tool use, responses separately. |
| **CCC** | [kidandcat/ccc](https://github.com/kidandcat/ccc) | Go + tmux + topics | `ccc listen` polls Telegram. Topics tied to tmux sessions. Claude Code hook sends responses back. |
| **claudecode-telegram** | [hanxiao/claudecode-telegram](https://github.com/hanxiao/claudecode-telegram) | tmux + webhook + Stop hook | File-based coordination. Bridge writes state, hook reads state. Our v4 architecture is derived from this. |
| **claude-code-telegram** | [RichardAtCT/claude-code-telegram](https://github.com/RichardAtCT/claude-code-telegram) | Claude Code SDK + FastAPI | Webhook server for GitHub events. Scheduler for recurring tasks. `NOTIFICATION_CHAT_IDS` for proactive messages (separate from conversation). |
| **Kai** | [linuz90/claude-telegram-bot](https://github.com/linuz90/claude-telegram-bot) | Persistent Claude process | **Real-time tool visibility** - streams tool usage events to chat. Terminal UI mode shows what Claude is doing. `ask_user` MCP server for tappable buttons. |
| **claude-telegram-relay** | [godagoo/claude-telegram-relay](https://github.com/godagoo/claude-telegram-relay) | Bun daemon + Supabase | **Smart check-ins** every 30 min. Claude decides when to reach out. Daily morning briefings. Voice in/out. |
| **OpenClaw** | [openclaw/openclaw](https://github.com/openclaw/openclaw) | Gateway daemon + 3-layer | **Per-session FIFO outbound queue**. Awaits message tool completion before final reply. Heartbeat pattern for proactive push. Most sophisticated race condition handling. |
| **TinyClaw** | [jlia0/tinyclaw](https://github.com/jlia0/tinyclaw) | ~400 lines shell + tmux | File-based queue: `incoming/` -> `processing/` -> `outgoing/`. Multi-agent routing via `@agent_id`. |
| **Zylos** | [zylos-ai/zylos-core](https://github.com/zylos-ai/zylos-core) | C4 Communication Bridge | Unified gateway. All messages through single bus. SQLite persistence. Channel-agnostic protocol. |
| **Tmux-Orchestrator** | [Jedward23/Tmux-Orchestrator](https://github.com/Jedward23/Tmux-Orchestrator) | 3-tier agent hierarchy | Agents self-schedule check-ins. `send-claude-message.sh` handles timing. Inter-agent coordination. |

### Key Patterns from Prior Art

**Pattern 1: Telegram Topics for Session Isolation** (CCBot, CCC)
- Each conversation gets its own Telegram topic (forum thread)
- Messages from subagents go to the right thread naturally
- Pro: Clean separation. Con: Requires Telegram supergroup (forum mode).

**Pattern 2: Per-Session FIFO Outbound Queue** (OpenClaw)
- ALL outbound messages queued sequentially per session
- Final reply only dispatched after all in-flight tool sends complete
- Pro: Guarantees ordering. Con: Complex implementation.

**Pattern 3: Separate Notification Channel** (claude-code-telegram, claude-telegram-relay)
- Proactive notifications go to configured `NOTIFICATION_CHAT_IDS` or separate bot
- Conversation replies go to the originating chat
- Pro: Clean separation. Con: Split attention across chats.

**Pattern 4: Real-Time Activity Streaming** (Kai)
- Stream tool usage events to chat in real-time (not just final response)
- Terminal UI mode shows what Claude is doing as it works
- Pro: Full visibility. Con: Noisy, requires careful formatting.

**Pattern 5: Heartbeat/Smart Check-ins** (OpenClaw, claude-telegram-relay)
- Background timer wakes agent to check if proactive message is warranted
- Agent decides whether to message based on context
- Pro: Intelligent, not spammy. Con: Requires always-on daemon.

### OpenClaw Race Condition Solutions (Directly Relevant)

OpenClaw has documented and solved the exact same race conditions we face:

1. **Issue #15147**: Reply ordering race between message tool sends and post-turn final replies. **Solution**: Per-session FIFO outbound queue.
2. **Issue #11614**: Race condition between auto-reply and message tool sends. **Solution**: Await message tool completion before dispatching final reply.
3. **Issue #7694**: Message ordering conflict when user sends message during active tool execution. **Solution**: Per-session serial locking.

---

## 4. Claude Code Hooks API Deep Dive

### Available Hook Events

| Event | When It Fires | Payload Fields |
|-------|--------------|----------------|
| `Stop` | After EVERY assistant turn completes (including subagents) | `session_id`, `transcript_path`, `cwd`, `hook_event_name`, `stop_hook_active` |
| `SubagentStop` | When a subagent (Task tool) completes | Same as Stop, but `hook_event_name = "SubagentStop"` |
| `UserPromptSubmit` | When user submits a prompt (before Claude processes) | `session_id`, `transcript_path`, `cwd`, `hook_event_name` |
| `PreToolUse` | Before a tool is executed | Above + `tool_name`, `tool_input` |
| `PostToolUse` | After a tool completes | Above + `tool_name`, `tool_input`, `tool_result` |
| `PreCompact` | Before context compaction | `session_id`, `transcript_path`, `cwd` |

### Key Findings

1. **Stop vs SubagentStop**: These are SEPARATE events. Our hook is registered on `Stop` only (no matcher), so `SubagentStop` events should theoretically not trigger it. **However**, the v1.0.1 handling note in our code ("Subagent Stop events may not include transcript_path") suggests subagent completions DO trigger the parent's Stop hook in some cases.

2. **No message-level correlation**: The Stop payload contains NO message ID, turn ID, or user message reference. There is no built-in way to say "this Stop event corresponds to the response for user message X."

3. **SubagentStop shared session_id bug** (GitHub #7881): All subagents in the same session share the parent's `session_id`. You cannot distinguish which subagent completed from the SubagentStop payload alone.

4. **Hook stdout injection**: `UserPromptSubmit` hook stdout gets injected into Claude's context. This could be used to inject "respond to Telegram message" instructions.

5. **`continue: true` in Stop hook**: A Stop hook can return `{"continue": true}` to force Claude to keep working. This could be used to prevent premature response delivery.

6. **Matchers**: Hooks support a `matcher` field for filtering. But Stop hooks have no tool name to match against - the matcher for Stop appears to be limited.

### JSONL Transcript Format

Each line is a JSON object with:
```json
{
  "parentUuid": "...",          // Parent message UUID
  "isSidechain": true/false,    // Whether this is a sidechain (subagent)
  "userType": "external",       // "external" for user, "internal" for system
  "cwd": "/path/to/branch",     // Working directory
  "sessionId": "uuid",          // Session UUID
  "agentId": "abc1234",         // Agent ID (for subagents)
  "type": "user|assistant",     // Message type
  "message": {
    "role": "user|assistant",
    "content": [{"type": "text", "text": "..."}]
  },
  "timestamp": "ISO-8601"
}
```

**Key insight for correlation**: The `isSidechain: true` field marks subagent entries. The `agentId` field identifies which subagent. The main session entries have `isSidechain: false` or omit it. This could be used to filter out subagent text during extraction.

---

## 5. Recommended Approach

### Phase 2: Fix Stop Hook Leaking

**Use Option E (Hybrid: SubagentStop Filter + Message Index Correlation)**

Implementation steps:
1. Add `SubagentStop` filtering to `telegram_response.py` - reject events where `hook_event_name == "SubagentStop"` or `transcript_path` contains `/subagents/`.
2. Add `isSidechain` filtering to `extract_assistant_response()` - skip JSONL lines where `isSidechain: true`.
3. Add `transcript_line_after` to pending file - bridge records transcript line count before injection.
4. Update `extract_assistant_response()` to only look at lines after `transcript_line_after`.
5. Keep existing retry loop but with position-aware extraction.

**Why this combination:**
- Layer 1 (SubagentStop filter) catches the most common false positive
- Layer 2 (isSidechain filter) catches subagent text that leaks into the parent transcript
- Layer 3 (position tracking) catches compaction events and any other intermediate content
- Each layer is simple (~5-10 lines). Combined = robust defense in depth.

### Phase 3: Add Proactive Activity Push

**Use the existing `notifier.py` pattern, extended to the bridge chat.**

Implementation steps:
1. Create `activity_push.py` - a function that sends formatted activity updates to Patrick's chat via the bridge bot token.
2. Register a `SubagentStop` hook (separate from the conversation Stop hook) that calls `activity_push.py`.
3. The activity push formats the subagent's result as a distinct message type (e.g., prefixed with `[Activity]` or using Telegram's monospace formatting).
4. Activity messages are sent as NEW messages (not edits to "Processing..."), so they don't interfere with conversation flow.
5. Rate-limit activity pushes (max 1 per 10 seconds) to prevent spam during heavy subagent work.

**Alternative for Phase 3**: Use the existing scheduler bot (`notifier.py`) which already sends to a SEPARATE chat. This is cleaner (no message collision risk) but means Patrick monitors two chats.

---

## 6. Risk Assessment

### Fix Risks (Phase 2)

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Transcript line count race (bridge counts, then content is added before injection) | Low | Low - would just include slightly more context | Count AFTER injection, not before |
| SubagentStop not firing for all subagent types | Medium | Medium - some false positives survive | isSidechain filter as backup layer |
| `isSidechain` field missing from older transcript entries | Low | Low - falls through to position-based filter | Position filter catches these |
| Performance regression on non-Telegram sessions | Very Low | High if it happens | SubagentStop check is first (before file I/O), exits in <1ms |
| Breaking change for existing pending file format | Low | Medium | New field is additive, old files work with fallback |

### Activity Push Risks (Phase 3)

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Activity spam overwhelming Patrick | Medium | Medium - bad UX | Rate limiting (1 per 10s), verbosity levels |
| Activity messages interleaved with conversation replies | Medium | Medium - confusing | Clear formatting prefix, or separate chat |
| Cost of SubagentStop hook processing | Low | Low | Fast exit for non-Telegram CWDs |

### Migration

- **Backwards compatible**: New `transcript_line_after` field in pending file is optional. Old pending files without it fall back to current behavior.
- **No bridge restart needed for hook changes**: The hook runs as a subprocess each time.
- **Bridge restart needed for pending file format change**: But bridge restarts are graceful (long-polling reconnects automatically).

---

## 7. Implementation Sketch

### telegram_response.py Changes (Phase 2)

```python
def main():
    payload = json.load(sys.stdin)

    # NEW: Layer 1 - Reject SubagentStop events
    event_name = payload.get("hook_event_name", "")
    if event_name == "SubagentStop":
        sys.exit(0)

    transcript_path = payload.get("transcript_path", "")

    # NEW: Layer 1b - Reject subagent transcripts
    if "/subagents/" in transcript_path:
        sys.exit(0)

    # Existing: Find pending file
    pending = find_pending_file(payload.get("session_id", ""))
    if not pending:
        sys.exit(0)

    # NEW: Layer 3 - Position-aware extraction
    start_line = pending.get("transcript_line_after", 0)

    # Modified extraction
    text = extract_assistant_response(transcript_path, start_line=start_line)
    # ... rest of send logic
```

```python
def extract_assistant_response(transcript_path, start_line=0):
    with open(transcript_path) as f:
        all_lines = f.readlines()

    lines = all_lines[start_line:]  # Only look at new content

    last_user_idx = -1
    for i, line in enumerate(lines):
        entry = json.loads(line)

        # NEW: Layer 2 - Skip sidechain entries
        if entry.get("isSidechain", False):
            continue

        if entry.get("type") == "user":
            last_user_idx = i

    if last_user_idx < 0:
        return ""

    # Extract assistant text after last (non-sidechain) user message
    texts = []
    for line in lines[last_user_idx + 1:]:
        entry = json.loads(line)
        if entry.get("isSidechain", False):
            continue
        if entry.get("type") == "assistant":
            # ... extract text blocks

    return "\n\n".join(texts).strip()
```

### bridge.py Changes (Phase 2)

```python
def write_pending_file(self, branch_name, chat_id, bot_token, processing_msg_id):
    # NEW: Record transcript position
    transcript_line_count = 0
    transcript_path = self._find_transcript(branch_name)
    if transcript_path and os.path.exists(transcript_path):
        with open(transcript_path) as f:
            transcript_line_count = sum(1 for _ in f)

    pending_data = {
        "chat_id": str(chat_id),
        "bot_token": bot_token,
        "timestamp": time.time(),
        "processing_message_id": processing_msg_id,
        "session_id": f"tmux-{branch_name}",
        "transcript_line_after": transcript_line_count  # NEW
    }
    # ... write to file
```

---

## 8. Conclusion

The Stop hook leaking bug is confirmed and well-understood. The root cause is the absence of any correlation between the Stop event and the specific user message that triggered it. The recommended fix (Option E: Hybrid approach) adds three layers of filtering with minimal code change (~30 lines total) and zero performance impact on non-Telegram sessions.

Prior art confirms this is a solved problem in the broader ecosystem. OpenClaw, CCBot, and claude-code-telegram all implement variations of message correlation and outbound queuing. Our recommended approach is simpler than any of these because we can leverage the JSONL transcript's `isSidechain` field - a correlation mechanism that didn't exist when the v4 bridge was originally built.

Phase 3 (proactive activity push) should be built after Phase 2 is stable. The simplest approach is a `SubagentStop` hook that formats and sends activity summaries to Patrick's chat, rate-limited to prevent spam.

---

*Research conducted with 4 parallel sub-agents: internal code analysis, log/evidence analysis, Claude Code hooks API research, and AI-Telegram bridge prior art survey.*
