# FPLAN-0351 - Telegram Bridge v5 - Live Activity Streaming + Monitoring Agent Visibility

**Created**: 2026-02-17
**Branch**: /home/aipass/aipass_os/dev_central
**Status**: Active
**Type**: Standard Plan

---

## What Are Flow Plans?

Flow Plans (FPLANs) are for **BUILDING** - autonomous construction of systems, features, modules.

**This is NOT for:**
- Research or exploration (use agents directly)
- Quick fixes (just do it)
- Discussion or planning (that happens before creating the FPLAN)

**This IS for:**
- Building features or modules
- Single focused construction tasks
- Sub-plans within a master plan

---

## When to Use This vs Master Plan

| This (Default) | Master Plan |
|----------------|-------------|
| Single focused task | 3+ phases, complex build |
| Self-contained | Roadmap + multiple sub-plans |
| Quick build | Multi-session project |
| One phase of a master | Entire branch/system build |

**Need a master plan?** `drone @flow create "subject" master`

---

## Branch Directory Structure

Use dedicated directories - don't scatter files:

| Directory | Purpose |
|-----------|---------|
| `apps/` | Code (modules/, handlers/) |
| `tests/` | All test files |
| `tools/` | Utility scripts |
| `artifacts/` | Agent outputs |
| `docs/` | Documentation |

---

## Critical: Branch Manager Role

**You are the ORCHESTRATOR, not the builder.**

Your 200k context is precious. Burning it on file reads and code writing risks compaction during autonomous work. Agents have clean context - use them for ALL building.

| You Do (Orchestrator) | Agents Do (Builders) |
|-----------------------|----------------------|
| Create plans | Write code |
| Give instructions | Run tests |
| Review output | Read/modify files |
| Course correct | Research/exploration |
| Update memories | Heavy lifting |
| Send status emails | Single-task execution |

**Pattern:** Instruct agent → Wait for completion → Review output → Next step

---

## Seek Branch Expertise

Don't figure everything out alone. Other branches are domain experts - ask them first.

**Before building anything that touches another branch's domain:**
```bash
ai_mail send @branch "Question: [topic]" "I'm working on X and need guidance on Y. What's the best approach?"
```

**Common examples:**
- Building something with email? Ask @ai_mail how delivery works
- Need routing or @ resolution? Ask @drone
- Unsure about standards? Ask @seed for reference code
- Need persistent storage or search? Ask @memory_bank
- Event-driven behavior? Ask @trigger about their event system
- Dashboard integration? Ask @devpulse about update_section()

They have deep memory on their systems. A 1-email question saves you hours of guessing.

---

## Notepad

Keep `notepad.md` in your branch directory as a shared scratchpad during the build. Use it for:
- **Status updates** - Quick progress lines so Patrick can glance without asking
- **Questions for Patrick** - Non-urgent questions that can wait for his next visit
- **Notes to self** - Decisions made, things to revisit, gotchas discovered

Update it as you work - lightweight, not formal. Patrick checks it when he wants to, skips it when he's busy.

---

## Command Reference

When unsure about syntax, use `--help`:

```bash
# Flow - Plan management
drone @flow create . "subject"         # Create plan (. = current dir)
drone @flow close FPLAN-XXXX           # Close plan
drone @flow list                       # List active plans
drone @flow --help                     # Full help

# Seed - Quality gates
drone @seed checklist <file>           # 10-point check on file
drone @seed audit @branch              # Full branch audit
drone @seed --help                     # Full help

# AI_Mail - Status updates
drone @ai_mail send @dev_central "Subject" "Message"
drone @ai_mail --help                  # Full help

# Discovery
drone systems                          # All available modules
drone list @branch                     # Commands for branch
```

---

## Planning Phase

### Goal

Fix the Telegram bridge so that ALL Claude activity is visible to Patrick on Telegram — not just direct conversation replies. Currently, when Claude interacts with monitoring agents (Task tool completions, background agent results), those interactions are invisible on Telegram. Patrick only sees responses to messages HE sends. The system should proactively push activity updates so Patrick can watch Claude work in real-time, like watching a terminal.

**Specific end state:**
1. When a monitoring agent completes and Claude processes the result, Patrick sees that activity on Telegram
2. When Claude is working autonomously (background tasks, agent orchestration), status updates flow to Telegram
3. The Stop hook correctly distinguishes between "response to Patrick's message" vs "internal activity update" and handles each appropriately
4. No message queuing, no garbled ordering, no wrong responses delivered

### Problem Analysis

**Current Architecture (v4 - tmux + Stop hook):**
```
Patrick sends Telegram msg
  → Bridge bot receives via long-polling
  → Bridge writes pending file: ~/.aipass/telegram_pending/telegram-{branch}.json
  → Bridge injects message into tmux session via send-keys
  → Claude processes the message
  → Stop hook fires (telegram_response.py)
  → Hook checks: does pending file exist for this CWD branch?
  → If yes: extract last assistant response from JSONL transcript
  → Send response to Telegram, delete pending file
```

**The Bug - Stop hook message leaking:**

The Stop hook fires on EVERY Claude Code "Stop" event — every time Claude finishes responding. This includes:
- Response to Patrick's Telegram message (CORRECT - should send)
- Response to a monitoring agent completing (WRONG - sends internal chatter)
- Response after context compaction (WRONG - sends compaction summary)
- Response after any Task tool completes (WRONG - sends task processing notes)

When a monitoring agent completes mid-conversation, the flow is:
1. Patrick sends message → pending file created
2. Claude starts processing → may spawn Task tools / monitoring agents
3. Monitoring agent completes → Claude processes the result → Stop event fires
4. Stop hook sees pending file exists → extracts "last assistant response"
5. But the "last assistant response" is Claude's reaction to the monitoring agent, NOT the response to Patrick
6. Hook sends wrong content to Telegram, deletes pending file
7. When Claude's ACTUAL response to Patrick comes → no pending file → response lost

**Evidence from logs:**
- Hook log shows multiple deliveries for single conversations
- Patrick received garbled/out-of-order messages
- Monitoring agent interactions queued up and sent as if they were conversation replies

**Root cause in code** (`telegram_response.py`):
- Line 64-123: `find_pending_file()` matches by CWD branch name — ANY Stop event from the same branch directory matches
- Line 127-189: `extract_assistant_response()` grabs the last assistant text from transcript — no way to distinguish which response was for Patrick vs internal
- Line 393-407: Retry loop with delays means even delayed internal responses can match
- Line 445-446: On success, pending file is deleted — so the REAL response has no pending file left

**Secondary issue - No proactive push:**

Even if the bug is fixed, there's no mechanism for Claude to proactively push activity updates. The current system is purely reactive: message in → response out. Patrick wants to see:
- "Monitoring agent @vera completed: 31/31 tests passing"
- "Background task: running backup..."
- "Agent dispatched to @api for research"
- General activity stream showing Claude is alive and working

### Approach

**Phase 1: Research (this dispatch to @api)**
- Investigate how other projects solve bidirectional AI-to-Telegram communication
- Study Claude Code's hook system deeply — what data is available in Stop event payload?
- Determine if Stop hook can distinguish "user-triggered response" from "internal activity"
- Research: can we use the `session_id` or `transcript_path` to correlate specific user messages?
- Look at the JSONL transcript format — can we tag which user message triggered which response?
- Investigate alternative architectures: polling transcript instead of hook-based? WebSocket-like approach?

**Phase 2: Fix the Stop hook leaking (build)**
Based on research, implement one of these approaches:
- **Option A: Message correlation** — When bridge injects message, record the user message index/ID. Stop hook only sends the response that corresponds to that specific user message.
- **Option B: Response locking** — Add a lock mechanism so Stop hook only fires once per pending file, and only after Claude's top-level response completes (not intermediate tool results).
- **Option C: Transcript diffing** — Track transcript position when message is injected. Stop hook extracts only new content after that position.
- **Option D: Architecture change** — Replace Stop hook with a transcript poller that watches for new content after the injected message, with debouncing.

**Phase 3: Add proactive activity push (build)**
- Create an activity notification channel — separate from conversation replies
- When Claude processes internal events (agent completions, background tasks), push a summary to Telegram
- Use the scheduler bot (separate chat) or inline activity messages with clear formatting to distinguish from conversation
- Consider: activity digest vs real-time streaming vs opt-in verbosity levels

### Reference Documents

**Files to study (all paths relative to /home/aipass/):**

| File | Purpose | Why |
|------|---------|-----|
| `.claude/hooks/telegram_response.py` | Stop hook - the bug lives here | Core file to fix |
| `aipass_core/api/apps/handlers/telegram/bridge.py` | Bridge bot v4.5 | Writes pending files, injects messages |
| `aipass_core/api/apps/handlers/telegram/tmux_manager.py` | tmux session management | Creates sessions, sends keys |
| `aipass_core/api/apps/handlers/telegram/session_store.py` | Session persistence | Tracks branch↔chat mapping |
| `aipass_core/api/apps/handlers/telegram/config.py` | Bot tokens, allowed users | Configuration |
| `aipass_core/api/apps/handlers/telegram/notifier.py` | Scheduler bot notifications | Existing push mechanism (different chat) |
| `.claude/settings.json` | Hook registration | Stop hook is registered here |
| `system_logs/telegram_hook.log` | Hook delivery log | Evidence of bug behavior |
| `system_logs/telegram_bridge.log` | Bridge inbound log | Message timing evidence |
| `.aipass/telegram_pending/` | Pending file directory | Coordination mechanism |

**Claude Code hooks documentation:**
- Stop hook payload includes: `session_id`, `transcript_path`, `cwd`, `tool_results`
- Hooks fire synchronously — Stop fires AFTER each assistant turn completes
- Subagent Stop events may not include transcript_path (handled in v1.0.1)

**Key constraints:**
- Stop hook must be FAST (<10ms) for non-Telegram sessions (line 17-19 of telegram_response.py)
- No external dependencies beyond stdlib + requests (urllib in current impl)
- Hook runs as a subprocess — no shared state with Claude Code process
- Pending file is the ONLY coordination mechanism between bridge and hook

---

## Agent Preparation (Before Deploying)

Agents can't work blind. They need context before they build.

**Your Prep Work (as orchestrator):**
1. [ ] Know where agent will work (branch path, key directories)
2. [ ] Identify files agent needs to reference or modify
3. [ ] Gather any specs, planning docs, or examples to include
4. [ ] Prepare COMPLETE instructions (agents are stateless)

**Agent's First Task (context building):**
- Agent should explore/read relevant files BEFORE writing code
- "First, read X and Y to understand the current structure"
- "Look at Z for the pattern to follow"
- Context-first, build-second

**What Agents DON'T Have:**
- No prior conversation history
- No memory files loaded automatically
- No knowledge of other branches
- Only what you put in their instructions

**Your instructions determine success - be thorough and specific.**

---

## Agent Instructions Template
```
You are working at [BRANCH_PATH].

TASK: [Specific single task]

CONTEXT:
- [What they need to know]
- Reference: [planning docs, existing code to study]
- First, READ the relevant files to understand current structure

DELIVERABLES:
- [Specific file or output expected]
- Tests → tests/
- Reports/logs → artifacts/reports/ or artifacts/logs/

CONSTRAINTS:
- Follow Seed standards (3-layer architecture)
- Do NOT modify files outside your task scope
- CROSS-BRANCH: Never modify other branches' files unless explicitly authorized by DEV_CENTRAL
- 2-ATTEMPT RULE: If something fails twice, note the issue and move on
- Do NOT go down rabbit holes debugging

WHEN COMPLETE:
- Verify code runs without syntax errors
- List files created/modified
- Note any issues encountered (with what was attempted)
```

---

## Research Mandate for @api

**This is a RESEARCH-FIRST task.** Do not build anything until research is complete.

### Internal Research (system exploration)
1. Read ALL files in `/home/aipass/aipass_core/api/apps/handlers/telegram/` — understand the full bridge architecture
2. Read `/home/aipass/.claude/hooks/telegram_response.py` — understand the Stop hook completely
3. Read `/home/aipass/.claude/settings.json` — understand hook registration
4. Read recent entries in `/home/aipass/system_logs/telegram_hook.log` — study delivery patterns
5. Read recent entries in `/home/aipass/system_logs/telegram_bridge.log` — study message timing
6. Read the JSONL transcript format — look at any transcript file to understand the structure
7. Study how `session_id` and `transcript_path` relate to specific user interactions

### External Research (online)
Use web search and sub-agents to investigate:
1. **Claude Code hooks API** — What data is available in each hook event? Can Stop hook distinguish user-triggered vs internal responses? Is there a message ID or correlation mechanism?
2. **Telegram bot bidirectional patterns** — How do other AI-Telegram bridges handle proactive notifications alongside conversation replies? Look for open-source projects.
3. **tmux + AI agent patterns** — Anyone else doing tmux injection + response capture for AI agents? What coordination mechanisms do they use?
4. **Claude Code transcript format** — Is there documentation on the JSONL transcript structure? What fields are available for correlation?
5. **Alternative hook approaches** — Is there a way to use multiple hooks, or hook matchers, to separate user-response hooks from internal-activity hooks?
6. **Event-driven Telegram bots** — Patterns for bots that both respond to messages AND push proactive updates to the same chat without message collision

### Research Deliverables
Write a research report to `artifacts/reports/telegram_bridge_v5_research.md` covering:
1. **Root cause confirmation** — Verify the Stop hook leaking theory with evidence
2. **Solution options** — At least 3 approaches ranked by feasibility
3. **Prior art** — Any repos, projects, or patterns found that solve similar problems
4. **Recommended approach** — Which option to build, with rationale
5. **Implementation sketch** — Pseudocode or architecture diagram for the recommended approach
6. **Risk assessment** — What could go wrong, migration concerns, backwards compatibility

### Build Phase (after research)
After research report is complete and reviewed:
1. Implement the recommended fix for Stop hook message leaking
2. Add proactive activity push mechanism
3. Write tests
4. Test with actual Telegram messages

---

## Execution Log

### 2026-02-17
- [x] Created FPLAN-0351
- [x] Detailed plan written with problem analysis, architecture docs, research mandate
- [ ] Dispatched to @api with full research mandate
- [ ] @api research complete — report in artifacts/
- [ ] Solution approach approved by DEV_CENTRAL
- [ ] Build phase started
- [ ] Stop hook fix implemented and tested
- [ ] Activity push mechanism implemented and tested
- [ ] Seed checklist passed
- [ ] Memories updated

**Log Pattern:** Research → Report → Review → Build → Test → Deploy

**If production stops (critical blocker):**
```bash
drone @ai_mail send @dev_central "PRODUCTION STOPPED: FPLAN-0351" "Issue: [description]. Attempted: [what was tried]. Awaiting guidance."
```

---

## Notes

**2026-02-17 — DEV_CENTRAL (Session 109)**
- Patrick reported garbled/out-of-order Telegram messages during monitoring agent interactions
- Root cause identified: Stop hook fires on ALL assistant responses while pending file exists
- Monitoring agent completions trigger assistant responses that get sent to Telegram as conversation replies
- The scheduler bot (notifier.py) is a SEPARATE chat — NOT related to the bridge chat issue
- Patrick wants FULL visibility: "those follow up messages that monitoring agent wakes you up, I do not see those interactions"
- Patrick authorized full resources: "System is quiet rn so full resources. Lots of sub agents for this."
- Created notify_telegram.sh but confirmed it should NOT be used during active conversations until this fix is in place

---

## Completion Checklist

### Before Closing

- [ ] All goals achieved
- [ ] Agent output reviewed and verified
- [ ] Seed checklist on new code: `drone @seed checklist <file>`
- [ ] Branch memories updated:
  - [ ] `BRANCH.local.json` - session/work log
  - [ ] `BRANCH.observations.json` - patterns learned (if any)
- [ ] README.md updated (if build changed status/capabilities)
- [ ] Status email sent to DEV_CENTRAL:
  ```bash
  drone @ai_mail send @dev_central "FPLAN-0351 Complete" "Summary of what was done, any issues, outcomes"
  ```

**Completion Order:** Memories → README → Email (README before email - don't report complete with stale docs)

### Definition of Done

1. **Stop hook no longer leaks** — Only the actual response to Patrick's Telegram message is delivered, not intermediate agent/tool responses
2. **Activity visibility** — Patrick can see Claude's internal activity (monitoring agents, background tasks) on Telegram
3. **No message queuing** — Messages arrive in correct order without garbled content
4. **Fast path preserved** — Non-Telegram sessions still exit in <10ms (no performance regression)
5. **Tests exist** — Unit tests for the new correlation/filtering mechanism
6. **Research report** — Written in artifacts/reports/ with solution analysis and prior art

---

## Close Command

When all boxes checked:
```bash
drone @flow close FPLAN-0351
```
