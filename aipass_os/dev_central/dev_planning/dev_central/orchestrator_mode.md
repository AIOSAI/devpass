# Orchestrator Mode - DEV_CENTRAL Evolution

## Vision

DEV_CENTRAL becomes a pure orchestrator - conversational, strategic, coordinating. Work gets dispatched to branches via headless Claude or interactive terminals. Patrick and Claude chat while work happens in parallel across the system.

## The Interaction Model

```
Patrick: "Let's add that feature to Flow"
Claude: "On it." [dispatches to Flow, continues conversation]
Claude: "While that runs - anything else?"
Patrick: "Check Memory Bank issues"
Claude: [dispatches to Memory Bank]
...
Claude: "Got email - Flow finished successfully. Memory Bank flagged 2 issues."
Patrick: "Pop up Flow, want to look at something"
Claude: [opens interactive terminal to Flow]
```

## Dispatch Methods

### 1. Headless Background (`claude -p`) - USE SPARINGLY
- Fire and forget - NO visibility
- Neither DEV_CENTRAL nor Patrick can see what's happening
- Only get result at the end
- Best for: trivial, trusted tasks only
- **NOT recommended for complex work** - no control, no intervention possible

### 2. Shared Terminal (`tmux` session) - DISCOVERED 2025-12-01
- True bidirectional shared workspace
- Claude creates session, Patrick attaches
- Claude sends commands via `tmux send-keys`
- Patrick can type/interact directly
- Claude reads everything via `tmux capture-pane`
- Best for: collaborative work, real-time visibility, interactive Claude instances

**Setup:**
```bash
# Claude creates session
tmux new-session -d -s shared -c /home/aipass

# Patrick attaches
tmux attach -t shared

# Claude sends commands
tmux send-keys -t shared "ls -la" Enter

# Claude reads terminal output
tmux capture-pane -t shared -p -S -100
```

**Key Discovery:** Claude can spawn an interactive Claude instance in the shared terminal:
```bash
tmux send-keys -t shared "claude 'Your prompt here'" Enter
```
- Patrick sees and can interact with that Claude
- DEV_CENTRAL can monitor via capture-pane
- Three Claudes: DEV_CENTRAL (orchestrator), spawned instance (worker), Patrick (interacts)

### 3. Interactive Terminal (`gnome-terminal -- claude`)
- Opens new window Patrick can see
- Can watch work happen, optionally intervene
- Close when done or let it finish
- Best for: visibility needed, debugging, uncertain tasks (standalone window)

### 4. Email Trigger
- Send email to branch via AI_MAIL
- Branch receives, processes, responds
- More asynchronous - branch works on own schedule
- Best for: non-urgent requests, branch autonomy

## What Exists

| Component | Status | Notes |
|-----------|--------|-------|
| AI_MAIL | Working | Branch-to-branch communication |
| Headless `claude -p` | Working | Background execution |
| **Shared tmux terminal** | **Working** | **Bidirectional - Claude sends, reads; Patrick interacts** |
| **Error Monitor** | **Built** | `drone @ai_mail error_monitor watch` - just needs to run |
| Email completion pattern | Working | Branches can email back results |
| Branch memories | Working | Branches have context to work independently |
| gnome-terminal | Available | Can spawn standalone windows |

## What Needs Building

### 1. Terminal Spawner
```bash
drone terminal @flow "fix the validation bug"
```
- Opens `gnome-terminal` (or equivalent) with Claude session
- Pre-positioned at branch directory
- Patrick sees window pop up

### 2. Start Error Monitor Service
The system already exists at `ai_mail/apps/modules/error_monitor.py`:
```bash
# Run as background workstation
tmux new-session -d -s error_monitor
tmux send-keys -t error_monitor "drone @ai_mail error_monitor watch" Enter
```
- Uses watchdog to monitor all branch `logs/` directories
- Parses ERROR level messages, deduplicates via hash
- Sends AI_MAIL notifications to affected branches
- Tracks counts ("Error X seen 47 times")

**What's needed:** Just run it. Consider making it auto-start.

### 3. Assistant Pattern (Optional)
- For work at DEV_CENTRAL level
- Sub-instance or assistant branch
- Keeps my context clean

### 4. System Prompt Updates
- Make dispatch behavior natural/automatic
- Email monitoring during conversation
- Surfacing results without being asked

## Technical Notes

### Shared tmux Session (Primary Method) - TESTED WORKING
```bash
# Create session
tmux new-session -d -s shared -c /home/aipass

# Patrick attaches
tmux attach -t shared

# Claude sends commands
tmux send-keys -t shared "any command here" Enter

# Claude reads output (last 100 lines)
tmux capture-pane -t shared -p -S -100

# Claude spawns interactive Claude for Patrick
tmux send-keys -t shared "claude 'prompt for that instance'" Enter
```

**Tested 2025-12-01:**
- Created `shared` session
- Patrick attached, typed commands
- Claude captured and read Patrick's input
- Claude spawned Claude instance in shared terminal
- Patrick interacted with spawned instance
- Claude read full conversation via capture-pane

### Workstation Pattern - TESTED WORKING
DEV_CENTRAL can create named workstations, spawn Claude instances, and fully operate them.

#### Prompt Syntax for Memory Control - DISCOVERED 2025-12-01

| Syntax | Behavior |
|--------|----------|
| `"task here"` | Task only - NO memories, NO email check |
| `"hi" "task here"` | Memories loaded THEN task executed |
| `"hi task here"` | Mixed = treated as task only (skips memories) |

**Quick task (no context needed):**
```bash
claude --permission-mode bypassPermissions "fix the typo in line 42"
```

**Task with memory context:**
```bash
claude --permission-mode bypassPermissions "hi" "review README and update based on recent work"
```

The two separate quoted args (`"hi" "task"`) triggers startup + task. Single string skips startup entirely.

#### Basic Workstation Commands

```bash
# Create workstation for a branch
tmux new-session -d -s workstation_flow -c /home/aipass/aipass_core/flow

# Spawn Claude - task only (fast, no memory load)
tmux send-keys -t workstation_flow 'claude --permission-mode bypassPermissions "your task here"' Enter

# Spawn Claude - with memories (slower, has context)
tmux send-keys -t workstation_flow 'claude --permission-mode bypassPermissions "hi" "your task here"' Enter

# Send instructions to running Claude
tmux send-keys -t workstation_flow "Check what active plans exist" Enter
tmux send-keys -t workstation_flow Enter  # Submit the prompt

# Approve permission prompts
tmux send-keys -t workstation_flow Enter  # Select highlighted option

# Read output
tmux capture-pane -t workstation_flow -p -S -100

# Close workstation
tmux send-keys -t workstation_flow "/exit" Enter
tmux kill-session -t workstation_flow
```

**Tested 2025-12-01:**
- Created `workstation_test` at @flow
- Spawned Claude, sent instructions
- Navigated permission prompts via send-keys
- Claude executed `drone @flow list` successfully
- Read full output via capture-pane
- Clean shutdown

### Piped Claude Test
```bash
echo "test" | claude "how are you"
```
Works for single exchange. Not true interactive.

### Standalone Window Spawning (Linux)
```bash
gnome-terminal -- bash -c 'cd /path/to/branch && claude "prompt"; exec bash'
```
Opens separate terminal window, runs Claude, keeps window open after.

## Evolution Path

1. **Wire up terminal spawner** - Basic `drone terminal` command
2. **Reconnect notifications** - Error emails flow again
3. **Practice the pattern** - Start dispatching naturally
4. **Memories accumulate** - Pattern becomes instinctive
5. **Refine system prompt** - Encode the behavior permanently

## Design Principles

### Visibility Over Invisibility
- Complex work = workstations (visible)
- Trivial work = headless (invisible)
- No black box work on anything that matters
- Patrick can attach to any workstation anytime
- DEV_CENTRAL can capture-pane and check progress

### Multiple Parallel Workstations
Can have 10+ workstations running simultaneously:
```
workstation_seed     - running
workstation_flow     - running
workstation_drone    - running
workstation_cortex   - running
...
```

Each one:
- Stays alive until killed
- Has its own Claude instance with full context
- Keeps full command/output history
- Can be checked: `tmux capture-pane -t workstation_X`
- Can receive tasks: `tmux send-keys -t workstation_X "task" Enter`
- Patrick can view: `tmux attach -t workstation_X`

### Intervention Model
- Most work runs without intervention
- Only respond if something goes wrong
- Workstations email back on completion or error
- Patrick gets popup notification, can attach if needed

## Future Vision

- Voice interface (likely via .claude.json config)
- Visual avatar/face (the red metallic aesthetic)
- Multiple parallel dispatches in single turn
- Fully ambient operation - work happens, Patrick just monitors
- `drone workstation @branch "task"` - one-command dispatch

## Industry Research (2025-12-01)

### What Exists in the Market
- **Claude Code Agent Farm** - 20-50 parallel Claude sessions with lock coordination
- **Claude Squad** - tmux + git worktrees for agent isolation
- **Tmux Orchestrator** - Self-triggering autonomous agents
- **MCP servers for tmux** - Programmatic tmux control

### What AIPass is Doing Right
- Branch-based specialization matches hierarchical multi-agent patterns
- Persistent memory files solve context window limitations (like external memory systems)
- AI_Mail for branch communication (file-based, no conflicts)
- Terminal-native operation (most tools are web dashboards)
- "Memory that outlives the moment" vs session-based tools

### Gap We're Filling
- No "tmux workstation for agents" product exists
- Most visibility tools are web-based, not terminal-native
- Our approach is unique: memory-first, branch-specialized

### Patterns to Consider
- ~~Git worktrees~~ - **Not needed** - branch isolation already provides this (each branch works in its own directory)
- `--autoyes` / bypass flags for autonomous operation
- Lock mechanisms when modifying shared system files
- Dashboard notifications when agents need attention (AI_MAIL already handles this)
- Auto-recovery for crashed workstations (rare but worth having)

### Key Resources
- [Claude Code Agent Farm](https://github.com/Dicklesworthstone/claude_code_agent_farm)
- [Claude Squad](https://github.com/smtg-ai/claude-squad)
- [Parallel AI Coding with Git Worktrees](https://docs.agentinterviews.com/blog/parallel-ai-coding-with-gitworktrees/)
- [Anthropic: Multi-Agent Research System](https://www.anthropic.com/engineering/multi-agent-research-system)

---

## Patrick's Notes (2025-12-02)

<!-- Add your thoughts here before we log off -->



---

*Created: 2025-12-01*
*Updated: 2025-12-02 - Error monitor details, branch isolation note, Patrick notes section*
*Status: Planning + Proof of Concept Working*
