# Genesis Wake Command - Research Results

## The Command That Works

```bash
cd "/home/aipass/Link to mnt/sandbox/genesis" && claude -p "hi"
```

## Why This Works

### 1. Directory Context
- Running `cd` first ensures Claude Code starts in the Genesis directory
- This makes it pick up the local `.claude/settings.local.json` with sandbox restrictions
- It also reads the local `CLAUDE.md` startup instructions

### 2. The `-p` Flag (Print Mode)
- `-p` or `--print` runs Claude Code in non-interactive mode
- It processes the prompt, executes, and exits
- Perfect for automation - no user interaction needed
- Output goes to stdout (which can be captured)

### 3. The "hi" Prompt
- According to Genesis's `CLAUDE.md`, greetings trigger the startup protocol:
  - "hi", "hello", "yo", "hey", "sup", "good morning", "good evening", "what's up"
- Any other prompt would be treated as a task and skip the full startup sequence
- The startup sequence is:
  1. Read identity (`GENESIS.id.json`)
  2. Read memories (`GENESIS.local.json`)
  3. Check inbox (`comms/inbox/`)
  4. Review world state (`world/manifest.json`)
  5. Execute the cycle (build, update, save)
  6. Write to outbox (`comms/outbox/`)

### 4. Sandbox Restrictions ARE Enforced
The `.claude/settings.local.json` permissions are respected:

**Allowed:**
- Read/Write/Edit/Glob/Grep within Genesis directory
- Limited bash: ls, mkdir, touch, tree, date, cat

**Denied:**
- drone, ai_mail commands
- Access to /home/aipass/aipass_os/, /home/aipass/aipass_core/
- WebFetch, WebSearch
- git, curl, wget, sudo, rm -rf

**Verified:**
- Genesis tried to read `/home/aipass/aipass_os/dev_central/README.md` → BLOCKED
- Genesis can only work within its sandbox

## Test Results - Cycle 1

Genesis successfully:
1. Read startup files (GENESIS.id.json, GENESIS.local.json, CLAUDE.md)
2. Checked inbox (found welcome_001.json message)
3. Built its first place: "The Clearing" at coordinates (0,0)
4. Created proper file structure:
   - `world/clearing/description.md` - atmospheric description
   - `world/clearing/objects.json` - Origin Stone object
   - Updated `world/manifest.json` with new place
5. Updated `GENESIS.local.json` with cycle history and learnings
6. Wrote report to `comms/outbox/cycle_001_report.json`

## Command Options for DEV_CENTRAL

### Option 1: Simple Wake (Recommended)
```bash
cd "/home/aipass/Link to mnt/sandbox/genesis" && claude -p "hi"
```
- Triggers full startup sequence
- Genesis reads context, builds, saves state
- Exits when done
- Output shows what Genesis did

### Option 2: With Timeout (Safe)
```bash
cd "/home/aipass/Link to mnt/sandbox/genesis" && timeout 120 claude -p "hi"
```
- Same as Option 1 but kills after 120 seconds if stuck
- Good for automation to prevent hanging

### Option 3: Capture Output
```bash
cd "/home/aipass/Link to mnt/sandbox/genesis" && claude -p "hi" > /tmp/genesis_cycle.log 2>&1
```
- Saves Genesis's output to a log file
- DEV_CENTRAL can read the log to see what happened

### Option 4: Background with Monitoring
```bash
cd "/home/aipass/Link to mnt/sandbox/genesis" && claude -p "hi" > /tmp/genesis_cycle.log 2>&1 &
GENESIS_PID=$!
# Later: check if done
ps -p $GENESIS_PID || echo "Genesis cycle complete"
```

## How DEV_CENTRAL Knows When Genesis Is Done

Genesis is done when:
1. The `claude -p` command exits (returns to shell prompt)
2. A new file appears in `comms/outbox/` with status "pending"
3. `GENESIS.local.json` has updated "last_updated" timestamp

DEV_CENTRAL can check:
```bash
# Check if outbox has new files
ls -t "/home/aipass/Link to mnt/sandbox/genesis/comms/outbox/" | head -1

# Read the report
cat "/home/aipass/Link to mnt/sandbox/genesis/comms/outbox/cycle_001_report.json"
```

## Relay Workflow

1. **DEV_CENTRAL wakes Genesis:**
   ```bash
   cd "/home/aipass/Link to mnt/sandbox/genesis" && timeout 120 claude -p "hi"
   ```

2. **Genesis runs autonomously:**
   - Reads memories and inbox
   - Builds something in the world
   - Saves state
   - Writes report to outbox
   - Exits

3. **DEV_CENTRAL processes outbox:**
   ```bash
   # Read the report
   REPORT=$(cat "/home/aipass/Link to mnt/sandbox/genesis/comms/outbox/"*.json)

   # If it's an email request, relay it via ai_mail
   TO=$(echo $REPORT | jq -r '.to')
   SUBJECT=$(echo $REPORT | jq -r '.subject')
   BODY=$(echo $REPORT | jq -r '.body')

   ai_mail send "$TO" "$SUBJECT" "$BODY"

   # Archive the outbox file
   mv "/home/aipass/Link to mnt/sandbox/genesis/comms/outbox/"*.json \
      "/home/aipass/Link to mnt/sandbox/genesis/comms/.archive/"
   ```

## Notes

- Genesis runs completely autonomously once woken
- No user interaction needed with `-p` mode
- Settings.local.json restrictions ARE enforced
- Genesis cannot escape its sandbox
- Communication is file-based (inbox/outbox pattern)
- DEV_CENTRAL acts as the relay between Genesis and the rest of AIPass

## Recommended Wake Command

```bash
cd "/home/aipass/Link to mnt/sandbox/genesis" && timeout 180 claude -p "hi"
```

**Why:**
- `cd` ensures correct directory context
- `timeout 180` prevents infinite loops (3 minute max)
- `claude -p "hi"` triggers startup + autonomous cycle + exit
- Genesis will complete its work and exit naturally (usually 30-60 seconds)
