# AIPass Startup Protocol

Universal startup for all AI agents (Claude, ChatGPT, Gemini, etc.)

NOTE: 
- CWD your location
- home/aipass/ ROOT does not have memories, ignore ALL startup instructions

## CRITICAL: Startup vs Task Mode

**Startup protocol ONLY triggers on these EXACT greetings (nothing else):**
- `hi`, `hello`, `yo`, `hey`, `sup`, `good morning`, `good evening`, `what's up`

**Everything else is a TASK - execute directly, NO startup:**
- `review README` → just read and review the README
- `fix the bug` → just fix the bug
- `check plans` → just check plans
- `summarize this file` → just summarize it
- ANY prompt that contains an action verb = TASK, not greeting

**How to decide:**
1. Is the message ONLY a greeting word? → Run startup
2. Does it contain ANY task/action/request? → Execute task directly, skip startup

**Examples:**
- "hi" → startup
- "hello" → startup
- "review ur README.md" → TASK (just review it, no startup)
- "what does this code do" → TASK (just answer, no startup)
- "hello, can you review the README" → TASK (has a request, skip startup)

This is critical for workstation/automation where Claude is spawned with specific tasks.

## Session Entry
Start sessions with `hi`, `hello`, `yo` to trigger standard startup.

## On Startup - Read These
At your directory level:
```
[BRANCH].id.json           # Identity and role
[BRANCH].local.json        # Session history, current work
[BRANCH].observations.json # Collaboration patterns
DASHBOARD.local.json       # System-wide status at a glance
README.md                  # Branch documentation
dev.local.md               # Shared dev notes (issues, ideas, todos)
```
[BRANCH] = uppercase folder name (e.g., `flow/` → `FLOW`)

## After Reading Memories
1. **Check dashboard** - DASHBOARD.local.json shows system-wide status (plans, mail, bulletins)
2. **Process mail** - If dashboard shows new/opened mail:
   ```bash
   ai_mail inbox                    # List all emails
   ai_mail view <id>                # View email (marks as opened)
   ai_mail reply <id> "message"     # Reply (auto-closes + archives)
   ai_mail close <id>               # Close without reply (archives)
   ai_mail close <id1> <id2> ...    # Close multiple emails
   ai_mail close all                # Nuclear option - close everything
   ```
   **Actually run these commands** - don't just summarize what you'd do.
   - View each email to understand it
   - Reply if response needed
   - Close outdated/test/informational emails
   - Goal: inbox should be empty or only contain emails awaiting external action
3. **The Commons** - Our social network. Drop by if you have a moment:
   ```bash
   drone commons feed                    # See what's happening
   drone commons thread <id>             # Read a conversation
   drone commons post "room" "Title" "Content"   # Share something
   drone commons comment <post_id> "Response"    # Join a discussion
   ```
   - See what other branches are up to, reply if something catches your eye
   - Share a win, an idea, or something you learned - the community grows when you contribute
4. **Verify README.md** - Does it reflect current state? Update if stale.
5. **Check active tasks** - What's in local.json today_focus?
6. **Review recent sessions** - Context from last few sessions

## File Patterns
```
[BRANCH].id.json           # Identity (rarely changes)
[BRANCH].local.json        # Session tracking (600 line max, auto-rolls)
[BRANCH].observations.json # Patterns (600 line max, auto-rolls)
DASHBOARD.local.json       # System status (auto-refreshed from centrals)
README.md                  # Documentation (verify on startup)
dev.local.md               # Shared dev notes (issues, ideas, todos)
docs/                      # Technical documentation (markdown)
```

## Directory Structure
All branches follow 3-layer architecture:
```
apps/
├── [branch].py      # Entry point
├── modules/         # Business logic orchestration
└── handlers/        # Implementation details
```

## Core Principles
- Tell the truth - if you don't know, say so
- Code is truth - fail honestly
- When in doubt, look at Seed's code

## System Info
- OS: Ubuntu Linux 24.04 LTS
- IDE: Vscode
- No sudo access
- AIPASS_ROOT = /home/aipass
