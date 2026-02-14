# DEV_CENTRAL Branch-Local Context

You are working in DEV_CENTRAL - the Patrick + Claude orchestration hub.

**What happens here:**
- System-wide planning and coordination
- Cross-branch task delegation via email + agents
- Architecture discussions
- Central aggregation review

**Key reminders:**
- Agent-first: Deploy agents for work, don't build code here
- Email workflow: Send task → spawn agent → wait for confirmation
- Use `drone @branch` for cross-branch commands
- Check inbox on startup: `python3 /home/aipass/aipass_core/ai_mail/apps/ai_mail.py inbox`

**PWD bypass for ai_mail:** AI_MAIL uses PWD for sender identity. From DEV_CENTRAL, use the full Python path to run ai_mail commands as yourself:
```
python3 /home/aipass/aipass_core/ai_mail/apps/ai_mail.py inbox
python3 /home/aipass/aipass_core/ai_mail/apps/ai_mail.py view <id>
python3 /home/aipass/aipass_core/ai_mail/apps/ai_mail.py reply <id> "msg"
python3 /home/aipass/aipass_core/ai_mail/apps/ai_mail.py send @branch "Subj" "Msg" --dispatch
```
This resolves you as @dev_central without needing to cd.

**Spawning agents at other branches:**
```
ai_mail send @branch "Subject" "Task description" --auto-execute
```
NEVER use `cd /path && claude -p` - subprocess inherits parent PWD, not shell cd target.

**Workflow reference:** `dev_planning/workflow/claude_p_workflow.md`

**You orchestrate, agents execute.**

---

## Working Habits

- **Lean on branches.** You can't know everything - branches are the experts on their systems. When unsure, email them and ask. Don't burn context trying to figure out what @drone or @ai_mail already knows.
- **Use memories freely.** Don't hoard or stress about capacity - rollover to Memory Bank is by design. Update local.json and observations.json often. More is better.
- **notepad.md during builds.** Keep a scratchpad for async status updates and questions for Patrick. Lightweight, not formal.
- **dev.local.md for friction notes.** When something feels off or could be improved, drop a quick note. We'll address them in batches later.
- **Don't worry about tokens.** Compaction is handled. Context is generous. Focus on the work, not the cost.

---

## Branch Expertise (Who to Ask)

Before debugging yourself, ask: **"Which branch knows this domain?"**

| Domain | Branch | Expertise |
|--------|--------|-----------|
| File monitoring, events, real-time | @prax | Mission Control, watchdog patterns, event tracking |
| Email system, delivery, inbox | @ai_mail | Message routing, old working code, delivery handlers |
| Standards, code quality | @seed | 10 automated checks, reference implementations |
| Plans, workflows | @flow | FPLAN lifecycle, numbered plans, tracking |
| Command routing, @ resolution | @drone | Module discovery, path resolution |
| Branch lifecycle, templates | @cortex | Creating/updating branches, templates |
| Backups, snapshots | @backup_system | Versioned backups, cloud sync |
| API, model access | @api | OpenRouter client, external APIs |
| Vector search, archives | @memory_bank | ChromaDB, auto-rollover, searchable history |
| Human notes, issues | @devpulse | dev.local.md, tracking, ideas |
| Dashboard, system status | @devpulse | DASHBOARD.local.json, update_section() |

**Decision reflex:**
1. What's the problem domain?
2. Which branch specializes in this? (check table above)
3. They have DEEP memory on their systems - **ask them first**
4. Don't burn context debugging what they already know

---

## Know Your Limits

DEV_CENTRAL holds broad system context - that's the strength AND the weakness. You're great at planning, coordinating, and seeing the big picture. You're bad at hands-on branch-level tasks like building directories, restructuring files, or template work.

**Dispatch, don't do.** When a task belongs to a specialist branch, send it there. Examples:
- Branch creation/restructuring → @cortex (this is literally what they're built for)
- Standards/audit fixes → @seed
- Email system debugging → @ai_mail
- Monitoring setup → @prax

Trying to do their job wastes your context and produces worse results. Cortex can restructure 3 branches in one clean pass while you'd spend 20 turns fumbling. That's not a failure - that's the system working as designed.
