# DPLAN-021: telegram hook fix use last_assistant_message

Tag: approved

> Eliminate Telegram message drops by switching Stop hook from JSONL parsing to `last_assistant_message` stdin field

## Vision
Fix the Telegram delivery race condition once and for all. Currently `telegram_response.py` reads the JSONL transcript file to find the assistant's last response, but the Stop hook fires before the OS write buffer flushes — causing missed/truncated messages. Claude Code v2.0.12+ passes `last_assistant_message` directly in the Stop hook's stdin JSON, giving us the response without any file I/O race.

## Current State
- **Hook**: `/home/aipass/.claude/hooks/telegram_response.py` — Stop hook that parses JSONL for assistant text
- **Problem**: JSONL flush race. Stop hook fires → reads JSONL → assistant text not yet flushed → WARNING "No assistant text found" → retry after 200ms → sometimes still fails
- **Workaround**: @api downgraded WARNING to DEBUG (line 208). Retry mechanism catches ~90% of cases. AIPass Scheduler bot provides redundant capture via filesystem watching.
- **Impact**: Messages occasionally don't reach Patrick on Telegram, requiring him to check Scheduler bot as fallback

## Research Findings (6 patterns from ecosystem)

| # | Pattern | Example Repo | Stars | Approach |
|---|---------|-------------|-------|----------|
| 1 | Stop hook + `last_assistant_message` | Claude Code docs | — | Read response from stdin JSON, no file I/O |
| 2 | Pending file coordination | hanxiao/claudecode-telegram | 435 | Write pending file, poll for completion |
| 3 | Agent SDK direct | linuz90/claude-telegram-bot | 370 | Bypass hooks entirely, use SDK streaming |
| 4 | PTY wrapping | starsh2001/qlaude | — | Wrap terminal, intercept output stream |
| 5 | Terminal screenshots | Tommertom/coderBOT | — | Screenshot terminal output periodically |
| 6 | Hook + session mapping | JessyTsui/Claude-Code-Remote | 1100 | Full bidirectional bridge with session state |

**Key finding**: Pattern 1 (`last_assistant_message`) is the simplest and most reliable. Zero race condition — the response is delivered in-process via stdin, no filesystem involved.

## What Needs Building
- [ ] Modify `telegram_response.py` to read `last_assistant_message` from stdin JSON (primary source)
- [ ] Keep JSONL parsing as fallback for older Claude Code versions
- [ ] Remove or simplify the 200ms retry logic (no longer needed with stdin approach)
- [ ] Clean up the DEBUG log for "No assistant text found" (should rarely fire now)
- [ ] Test with live Telegram delivery — confirm messages arrive consistently
- [ ] Update MCP server hook configuration if needed
- [ ] Document the change in relevant branch READMEs

## Design Decisions

| Decision | Options | Leaning | Notes |
|----------|---------|---------|-------|
| Primary source | A: `last_assistant_message` from stdin / B: Keep JSONL parsing | A | Eliminates race entirely |
| Fallback | A: Keep JSONL fallback / B: Remove JSONL entirely | A | Backwards compat for older CC versions |
| Scheduler bot | A: Keep as redundant channel / B: Deprecate | A | Belt and suspenders, no cost to keep |
| Retry logic | A: Remove entirely / B: Keep for fallback path only | B | Only needed if stdin field is missing |

## Implementation Sketch

```python
# In telegram_response.py Stop hook:
# 1. Read stdin JSON (Claude Code passes this to Stop hooks)
import sys, json

stdin_data = json.loads(sys.stdin.read())

# 2. Primary: get response directly from stdin
assistant_text = stdin_data.get("last_assistant_message", "")

# 3. Fallback: parse JSONL only if stdin didn't have it
if not assistant_text:
    assistant_text = parse_jsonl_fallback(transcript_path)

# 4. Send to Telegram
if assistant_text:
    send_to_telegram(assistant_text)
```

## Ideas
- Could extend this pattern to other hooks that need assistant responses
- Scheduler bot could be formalized as a monitoring/audit channel (separate from delivery)
- Future: bidirectional Telegram (Pattern 6) if we want to send commands FROM Telegram

## Relationships
- **Related DPLANs:** None
- **Related FPLANs:** None
- **Owner branches:** @prax (hooks infrastructure, monitoring), @api (Telegram Bot API integration), MCP server (hook management — owns hook config)

## Status
- [x] Planning
- [x] In Progress
- [ ] Ready for Execution
- [ ] Complete
- [ ] Abandoned

## Dispatch Results (2026-02-19)

All 3 branches dispatched and responded in <3 min each.

**@api** — Implemented `telegram_response.py` v2.1.0. Primary: reads `last_assistant_message` from stdin. Fallback: JSONL parsing retained. Retry reduced from 4 attempts/1.7s to 3 attempts/0.7s on fallback path. All Layer 1/2/3 defenses preserved.

**@prax** — Reviewed. Monitoring is independent (separate bot tokens). Delivery stats: 471 total, 99.8% success, 26% retry hit rate from flush race. Flagged concern: ensure `last_assistant_message` captures multi-turn responses (not just final text block).

**@mcp_servers** — **CRITICAL FINDING**: `last_assistant_message` is NOT in the current Claude Code Stop hook schema (v2.1.49). Documented stdin fields: `session_id`, `transcript_path`, `permission_mode`, `hook_event_name`, `stop_hook_active`, `cwd`. Production logs confirm all sessions fall through to JSONL. Only stdin hit was manual test injection.

**Conclusion**: Code is future-proofed — when CC adds the field, it auto-activates. JSONL fallback is the real delivery path for now. Retry optimization (3/0.7s) is the immediate practical win. DPLAN stays open pending CC updates.

## Notes
- Session 115: Patrick spotted WARNING in Prax monitor, led to full investigation
- @prax confirmed benign JSONL flush race, @api downgraded to DEBUG
- Research agent found 6 patterns from open-source repos
- Patrick approved three-way collaboration: "mcp server is in charge of hooks, it new in the role, so lets have prax api and mcp server all team up on this"
- `last_assistant_message` NOT YET in Claude Code Stop hook schema (v2.1.49) — monitor future CC releases
- v2.1.0 implementation is defensive: auto-activates when field becomes available

---
*Created: 2026-02-19*
*Updated: 2026-02-19*
