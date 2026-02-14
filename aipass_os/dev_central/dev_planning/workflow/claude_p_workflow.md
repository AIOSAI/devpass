# Claude -p Workflow Guide

*Learned: 2025-11-24*
*Updated: 2025-12-02 - --auto-execute pattern (replaces cd && claude -p), cwd= fix documented*
*Updated: 2026-01-20 - Added proposal workflow (branch-initiated work)*
*Updated: 2026-01-29 - Added assistant-mediated workflow, branch expertise, delegation-first patterns*

---

## Assistant-Mediated Workflow (NEW)

DEV_CENTRAL doesn't talk directly to branches for task feedback. @assistant handles the loop:

```
DEV_CENTRAL → branch (--reply-to @assistant)
                 ↓
            branch works + tests
                 ↓
            branch replies → @assistant (not DEV_CENTRAL)
                 ↓
         @assistant validates
                 ↓
    ┌───────────┴───────────┐
    ↓                       ↓
 Good: summarize         Issues: @assistant → branch (feedback loop)
    ↓                       ↓
 DEV_CENTRAL checks in   If deep: escalate to DEV_CENTRAL
```

### Sending Tasks with Reply Routing

```bash
ai_mail send @branch "Task Subject" "Task description..." --reply-to @assistant --auto-execute
```

- Task goes to branch
- Branch does work, tests it
- Reply goes to @assistant for validation
- DEV_CENTRAL checks in when ready: `drone @assistant update`

### Checking Assistant Status

```bash
drone @assistant update
```

Returns digest of:
- Tasks received since last check
- Status (completed, pending, needs escalation)
- Issues requiring DEV_CENTRAL attention

### Why This Pattern

- DEV_CENTRAL stays focused on strategy, not every branch reply
- @assistant handles feedback loops autonomously
- Check-in on demand, not on every notification
- Clear escalation path for real issues

---

## Branch Expertise & Delegation-First

Before debugging or building yourself, ask: **"Which branch owns this domain?"**

### Expertise Table

| Domain | Branch | Expertise |
|--------|--------|-----------|
| File monitoring, events | @prax | Mission Control, watchdog patterns |
| Email system, delivery | @ai_mail | Message routing, delivery handlers |
| Standards, code quality | @seed | 10 automated checks, reference code |
| Plans, workflows | @flow | FPLAN lifecycle, tracking |
| Command routing | @drone | Module discovery, @ resolution |
| Branch lifecycle | @cortex | Creating/updating branches |
| Backups, snapshots | @backup_system | Versioned backups, cloud sync |
| API, model access | @api | OpenRouter client |
| Vector search | @memory_bank | ChromaDB, auto-rollover |
| Human notes, dashboard | @devpulse | dev.local.md, DASHBOARD.local.json |

### Decision Reflex

1. What's the problem domain?
2. Which branch specializes in this? (check table)
3. They have DEEP memory on their systems - **ask them first**
4. Don't burn context debugging what they already know

### Delegation Pattern

```bash
# DON'T: Debug yourself
# DO: Ask the expert
ai_mail send @ai_mail "BUG: delivery failing" "Description..." --reply-to @assistant --auto-execute
```

---

## Post-Compaction Behavior

After context compaction, the tendency is to jump into execution mode. **Resist this.**

### Post-Compact Checklist

1. **DELEGATION FIRST** - Am I about to debug/build?
   - Check branch expertise table
   - If another branch owns it: DELEGATE
   - Don't burn context on their domain

2. **PLANNING vs EXECUTING** - Was there a discussion in progress?
   - If yes: continue discussion, don't start executing

3. **STATE CHECK** - What was the conversation state?
   - If uncertain: ASK, don't assume

See: `/home/aipass/.claude/hooks/pre_compact.py` for hook guidance

---

## Two Workflow Directions

### Task Flow (DEV_CENTRAL → Branch)
```
DEV_CENTRAL sends task → Branch receives → Executes → Confirms
```
This is the standard pattern for assigned work.

### Proposal Flow (Branch → DEV_CENTRAL)
```
Branch has idea → Sends proposal → DEV_CENTRAL reviews → Approves/Questions/Redirects → Branch executes
```
This enables branch-initiated work. Branches can propose improvements, features, or fixes they want to tackle.

**Proposal Template:** `/home/aipass/aipass_core/flow/templates/proposal.md`

**How branches submit proposals:**
```bash
ai_mail send @dev_central "PROPOSAL: [Brief Title]" "[Paste filled proposal template]"
```

**DEV_CENTRAL responses:**
- **GREEN LIGHT** - "Approved. Proceed with FPLAN."
- **QUESTIONS** - "Clarify X before proceeding."
- **REDIRECT** - "Good idea, but coordinate with @branch first."
- **HOLD** - "Not now, but keep in backlog."

---

## Command Format

```bash
claude -p "PROMPT" --permission-mode bypassPermissions
```

## Permission Modes

| Mode | Result |
|------|--------|
| `bypassPermissions` | Works instantly, full tool access |
| `acceptEdits` | Hangs waiting for permissions |
| (none) | Interactive prompts, blocks automation |

**Always use `bypassPermissions` for autonomous branch work.**

---

## Template Pattern (Recommended)

### Why Templates
Don't write prompts inline for each branch. Store them as template files:
- Single source of truth
- No typos from retyping
- Easy to update (change once, affects all)
- Fast deployment

### Template Location
```
/home/aipass/.claude/plans/
```

### Variable Substitution
Use `{{VARIABLE}}` placeholders, replace with sed:
```bash
claude -p "$(cat /path/to/template.md | sed 's/{{BRANCH}}/FLOW/g; s/{{branch}}/flow/g')" --permission-mode bypassPermissions
```

### Example: Batch Deploy to 5 Branches
```bash
# All run in parallel
claude -p "$(cat /home/aipass/.claude/plans/branch_compliance_prompt.md | sed 's/{{BRANCH}}/CLI/g; s/{{branch}}/cli/g')" --permission-mode bypassPermissions &
claude -p "$(cat /home/aipass/.claude/plans/branch_compliance_prompt.md | sed 's/{{BRANCH}}/API/g; s/{{branch}}/api/g')" --permission-mode bypassPermissions &
claude -p "$(cat /home/aipass/.claude/plans/branch_compliance_prompt.md | sed 's/{{BRANCH}}/CORTEX/g; s/{{branch}}/cortex/g')" --permission-mode bypassPermissions &
```

---

## Prompt Design

### What Works
- Template files with explicit commands (not vague instructions)
- Clear phases (Discovery → Investigation → Planning → Execution → Verification)
- Exact file paths and exact command syntax
- **Mandatory email confirmation** to a central branch
- Investigation-first approach (understand before fixing)
- Agent delegation pattern (orchestrate, don't code)

### What Fails
- Vague instructions ("run audit" vs `drone @seed audit branch`)
- Skipping investigation (blind fixing creates more problems)
- No confirmation mechanism (you won't know when it's done)
- Letting them figure things out (be explicit)
- **Ambiguous architecture instructions** (see Lessons Learned below)

### Key Prompt Elements

**1. Identity & Location**
```
You are the {{BRANCH}} branch manager at /home/aipass/aipass_core/{{branch}}/.
```

**2. Explicit Commands**
```
Run this exact command:
drone @seed audit {{branch}}
```

**3. Investigation Before Action**
```
DO NOT FIX ANYTHING YET. First understand if violations are real or false positives.
```

**4. Agent Delegation Rule**
```
You orchestrate - agents execute. You do NOT write code yourself.
```

**5. Seed Standards (CRITICAL)**
```
ARCHITECTURE: Follow Seed's 3-layer pattern:
- Modules ORCHESTRATE (route commands, coordinate handlers)
- Handlers IMPLEMENT (business logic, file operations, data processing)
- No implementation code in modules - extract to handlers/

Reference: drone @seed standards or look at Seed's code directly.
Run: drone @seed audit @branch before confirming completion.
```

**6. Bypass Awareness**
```
If something is legitimately needed, add a bypass instead of removing it.
Don't break working code for a compliance score.
```

**7. Mandatory Email Confirmation**
```
When complete, send report to @dev_central:
ai_mail send @dev_central "{{BRANCH}} Task Complete" "..."
```

---

## Email Confirmation Pattern

### Why It Matters
- Background tasks don't reliably show completion
- Email is the confirmation mechanism
- Central branch (@seed) collects all reports
- You know it's done when email arrives

### Template Requirement
Always include email step at the end of prompts:
```
drone @ai_mail send @seed "BRANCH Report" "
BRANCH: {{BRANCH}}
DATE: [today]
INITIAL: [before state]
ACTIONS: [what was done]
FINAL: [after state]
NOTES: [observations]
"
```

---

## Email-as-Task Pattern

### The Workflow
1. **Send email with `--auto-execute`** - spawns agent automatically
2. **Wait for confirmation** email back

### Why This Works
- Decouples task definition from execution
- Branch has full context in its inbox
- Email becomes the audit trail
- Agent spawns with correct working directory (cwd=)

### Example
```bash
# Single command - sends email AND spawns agent at target branch
ai_mail send @ai_mail "Fix: central_writer.py" "ISSUE: ... FIX: ..." --auto-execute
```

### Why Not `cd && claude -p`?
The old pattern was:
```bash
cd /path/to/branch && claude -p "..." --permission-mode bypassPermissions &
```

**This doesn't work.** `subprocess.Popen` inherits the PARENT process PWD, not the shell's `cd` target. The `--auto-execute` flag uses `cwd=` parameter which correctly sets the working directory before spawning.

---

## FPLAN Integration

### When to Create Plans
For non-trivial work, agents should create Flow plans:
```
drone @flow create "Subject" "Description"
```

### Why
- Tracks work across sessions
- Provides audit trail
- Plan numbers (FPLAN-XXXX) are referenceable
- Closes when complete

### Agent Prompt Pattern
```
PHASE 2: CREATE FPLAN
- Use Flow: drone @flow create "DevPulse Import Fix" "Fix broken imports"
- Reference the FPLAN number in your confirmation email
```

---

## Agent Spawning from DEV_CENTRAL

### Preferred: Use `--auto-execute`
```bash
ai_mail send @devpulse "Task Subject" "Full task description with phases..." --auto-execute
```

This is the recommended pattern. The `--auto-execute` flag:
- Spawns agent at target branch with correct `cwd=`
- Agent checks inbox and executes the task
- Sends confirmation email when done

### Alternative: Task Tool
For complex multi-step tasks within this session, use the Task tool to spawn agents directly.

### Legacy Pattern (Deprecated)
The old `cd && claude -p` pattern doesn't work reliably - subprocess inherits parent PWD, not shell's cd target. Use `--auto-execute` instead.

### Task Structure
Whether using email or Task tool, include:
1. Identity statement ("You are the X branch manager")
2. Clear phases (Investigate → Plan → Execute → Confirm)
3. Email confirmation requirement

### Branch Task Execution Process

When a branch receives a build/fix task, the process is:

```
1. RECEIVE    → Check inbox, read task email
2. INVESTIGATE → Deploy agents to understand codebase, existing patterns
3. CREATE FPLAN → drone @flow create "Task Name" "Description"
4. EXECUTE    → Use agents to build (branch manager orchestrates, doesn't code)
5. SEED CHECK → drone @seed audit @branch (must pass 80%+)
6. UPDATE MEMORIES → Update BRANCH.local.json with session work
7. CONFIRM    → ai_mail send @dev_central "Done" "FPLAN: X, Results: ..."
```

**Key:** Branch managers don't build directly. They:
- Investigate with agents
- Plan with Flow
- Execute with agents
- Validate with Seed
- **Update their memories** (ensures continuity for next session)

### Example Task Email
```bash
ai_mail send @devpulse "Build Feature X" "You are the DEVPULSE branch manager.

TASK: Build feature X

PROCESS:
1. Deploy agents to investigate existing patterns in your codebase
2. Create FPLAN: drone @flow create 'Feature X' 'Building...'
3. Use agents to execute - YOU ORCHESTRATE, AGENTS BUILD
4. Follow Seed standards: modules orchestrate, handlers implement
5. Run: drone @seed audit @devpulse (must pass 80%+)
6. Update your memories (DEVPULSE.local.json) with this session's work
7. Send confirmation with FPLAN reference

ARCHITECTURE (MANDATORY):
- Modules ORCHESTRATE only - route commands, coordinate handlers
- Handlers IMPLEMENT - business logic goes in handlers/
- Reference: drone @seed standards

FROM: @dev_central
" --auto-execute
```

---

## Investigation-First Pattern

### The Problem
Blind compliance breaks working code. Some violations are:
- False positives (checker limitation)
- Legitimate exceptions (branch-specific needs)
- Already bypassed (check bypass.json first)

### The Solution
Prompts should include investigation phase:
1. Run audit to see violations
2. Read standards to understand rules
3. Deploy agents to investigate each violation
4. Determine: Fix vs Bypass vs Ignore
5. Only then execute changes

### Bypass Examples
- Memory Bank needs Prax in handlers (vector operation logging)
- CLI branch needs console.print everywhere (it's their purpose)
- Display handlers need Rich formatting
- Standalone CLI tools need --help support

---

## Background Task Issues

### Zombie Process Bug
When running multiple `claude -p` commands as background tasks:
- Processes complete but show as "running"
- System-reminders repeat every turn: "background task has new output"
- Burns ~3k tokens per message (16 processes = massive token burn)

### Symptoms
- Context usage jumps unexpectedly
- Same "new output available" reminders repeating
- `KillShell` says "already completed" but reminders persist

### Fix
**Full Claude Code restart required.** No way to clear stale task state within session.

### Prevention
- Monitor context usage during batch operations
- If reminders persist after tasks complete, restart immediately
- Don't let zombie tasks burn through entire context window
- **Use email confirmation instead of checking background tasks**

---

## Batch Operations

### Recommended Pattern
1. Run batch of 3-6 `claude -p` commands
2. **Wait for emails** (not background task status)
3. Check context usage
4. If zombie reminders appear: restart before continuing
5. Process next batch

### Don't
- Run 17+ parallel commands without monitoring
- Ignore repeated "new output" reminders
- Continue working when context burns fast
- Check background tasks constantly (let them run, wait for email)

---

## Compaction Survival

### Problem
Compact summaries can lose critical prompt details:
- Summary says "simple prompts work"
- Actual prompt template with specific steps gets lost
- Next session follows summary, not original plan

### Solution
Pre-compact hook updated to say:
> "CRITICAL: If there is an active plan file in /home/aipass/.claude/plans/, re-read it FULLY before resuming work. Do NOT simplify, modify, or 'improve' the plan's instructions - follow them EXACTLY as written."

### Best Practice
- Write detailed plans to `/home/aipass/.claude/plans/`
- Plan files survive compaction (re-read after)
- Don't rely on memory for complex multi-step workflows

---

## Available Templates

| Template | Purpose | Location |
|----------|---------|----------|
| Branch Compliance | Standards audit & fix | `/home/aipass/.claude/plans/branch_compliance_prompt.md` |

*Add new templates as workflows mature.*

---

## Expectations

This workflow gets you **80%+ of the way there**. Autonomous agents:
- Will complete most tasks correctly
- May make occasional mistakes
- May miss edge cases
- Get the bulk of repetitive work done

**That's the value** - bulk automation with human review. Not perfection, but massive time savings.

---

---

## Lessons Learned

### 2025-12-02: Ambiguous Architecture Instructions

**Problem:** Sent task to DevPulse with "Clone from Flow" and "Single module handles all commands." Agent interpreted "handles" literally and put ALL implementation logic in one 490-line module file.

**What we said:**
```
KEEP SIMPLE:
- Single module handles all commands
```

**What agent heard:** Put everything in one file.

**What we meant:** Module routes commands to handlers.

**The fix:** Be EXPLICIT about Seed standards in every build task:
```
ARCHITECTURE (MANDATORY):
- Modules ORCHESTRATE only - route commands, coordinate handlers
- Handlers IMPLEMENT - business logic goes in handlers/
- Run 'drone @seed audit @branch' before confirming completion
- Score must be 80%+ to pass
```

**Root cause:** Saying "Clone from Flow" wasn't enough. Agent didn't infer the handler architecture pattern. Explicit instruction "Single module handles all commands" overrode implicit "follow the pattern."

**Takeaway:** Never assume agents will infer architectural patterns. State them explicitly. Include Seed audit as a gate before confirmation.

---

### 2025-12-02: --append-system-prompt BREAKS Auto-Execute

**Problem:** Spawned agents via `--auto-execute` were asking permission instead of executing tasks.

**What we tried:**
```python
# Tried to inject Seed standards
cmd = f'claude -p "{prompt}" --append-system-prompt "{seed_standards}" --permission-mode bypassPermissions'
```

**What happened:** Agents completely broke. Asked permission, didn't execute tasks.

**The fix - REVERT to simple pattern:**
```python
# Simple pattern that WORKS (commit 93b9fd1)
cmd = f"claude -p '{prompt}' --permission-mode bypassPermissions &"
```

**Key findings:**
| Pattern | Result |
|---------|--------|
| `claude -p "task" --append-system-prompt "..."` | ❌ BREAKS - asks permission |
| `claude -p "task" --permission-mode bypassPermissions` | ✅ Executes correctly |

**Takeaway:** Don't over-engineer agent spawning. The simple pattern works. Hooks at target branch handle memory loading and context. Adding --append-system-prompt breaks execution entirely.

---

*Document updated from Session 27 learnings - template pattern, email confirmation, investigation-first approach.*
*Session 35: CORRECTED - --append-system-prompt breaks execution, reverted to simple pattern.*
*Session 43: Added autonomous build pattern, mid-build verification, EOF warning.*
*Session 45: Added assistant-mediated workflow, branch expertise table, delegation-first pattern, post-compaction behavior.*

---

## Autonomous Build Pattern (GOLD)

For multi-phase autonomous builds, use this pattern:

```
MASTER plan → Research (Haiku) → Build (Sonnet) → Next phase → Repeat
```

### Model Hierarchy
| Model | Role | When to Use |
|-------|------|-------------|
| Opus | Orchestrator | Never touches code. Monitors, delegates, reviews. |
| Sonnet | Builder | Focused execution. Clean single-task building. |
| Haiku | Researcher | Fast exploration. Cheap codebase scanning. |

### The Pattern
1. **Create MASTER plan** - All phases defined upfront (`drone @flow create . "Project" master`)
2. **For each phase:**
   - Deploy **Haiku agent** to research/explore (understand before building)
   - Deploy **Sonnet agent** to build (focused execution)
   - **Mid-build verification** - spot-check output between phases (see below)
3. **Move to next phase** - Don't stop, don't check in, power through
4. **Final verification** - Test the complete build

### Why It Works
- Clean context: Orchestrator never writes code (mixed context = poison)
- Right model for the job: Haiku is fast/cheap for exploration, Sonnet is capable for building
- Phase-based progress: MASTER plan provides the roadmap
- Trust enables speed: Full autonomy without check-in pauses

### Prerequisites
- Backups exist (permission to fail)
- All phases defined in FPLAN
- Clear success criteria
- Model access (API key)

---

## Mid-Build Verification (Critical)

**Don't wait until the end to verify.** Spot-check between phases:

### When to Verify
- After each phase completes
- Before moving to dependent phases
- When output seems too fast or too slow

### How to Verify
```bash
# Quick sanity checks between phases
python3 -c "import module; print('imports ok')"   # Imports work?
python3 script.py --help                           # Entry point runs?
ls -la expected/output/                            # Files created?
```

### Why It Matters
- Catches issues early (before they cascade)
- Prevents wasted work on broken foundations
- Agents may produce syntactically correct but functionally broken code

---

## ⚠️ EOF/Loop Warning

**Background agents testing interactive apps can get stuck.**

### The Problem
When an agent runs `python3 app.py` to test an interactive CLI:
- App waits for input
- Agent can't provide input (no TTY)
- Process hangs on EOF or enters infinite loop
- Background task appears stuck

### Symptoms
- `TaskOutput` shows no new output for extended periods
- Process doesn't complete
- Need to `KillShell` to recover

### Prevention
- Test interactive apps with **expected input piped in**: `echo "quit" | python3 app.py`
- Use `--help` or non-interactive flags when available
- Set timeouts on test commands
- If testing must be interactive, verify manually (not via agent)

### Recovery
```bash
# If background task is stuck
KillShell <task_id>
# Continue with next phase
```

This is a known limitation of headless agent execution. Monitor for stuck processes and kill them if needed.
