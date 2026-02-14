# Genesis Relay Guide for DEV_CENTRAL

## Quick Start

**Wake Genesis (triggers full autonomous cycle):**
```bash
cd "/home/aipass/Link to mnt/sandbox/genesis" && timeout 180 claude -p "hi"
```

**Query Genesis (quick question, no full cycle):**
```bash
cd "/home/aipass/Link to mnt/sandbox/genesis" && timeout 30 claude -p "What did you build last cycle?"
```

## What Happens When Genesis Wakes

1. Reads `GENESIS.id.json` (identity)
2. Reads `GENESIS.local.json` (memories, last cycle)
3. Checks `comms/inbox/` for new messages
4. Reviews `world/manifest.json` (current world state)
5. **Executes cycle:** Plans, builds, creates files in `world/`
6. Updates `GENESIS.local.json` with cycle history
7. Writes report to `comms/outbox/cycle_XXX_report.json`
8. Exits

**Total time:** Usually 30-60 seconds per cycle

## The Relay Pattern

```
User/AIPass → DEV_CENTRAL → Genesis inbox → Wake Genesis → Genesis builds → Outbox → DEV_CENTRAL → ai_mail/User
```

### Step-by-Step

**1. Receive request for Genesis**
```bash
# Someone emails @dev_central: "Tell Genesis to build a garden"
# Or: User directly asks DEV_CENTRAL to send directive to Genesis
```

**2. Write to Genesis inbox**
```bash
cat > "/home/aipass/Link to mnt/sandbox/genesis/comms/inbox/msg_$(date +%s).json" <<EOF
{
  "id": "msg_$(date +%s)",
  "from": "@dev_central",
  "type": "directive",
  "subject": "Build a garden",
  "body": "Focus your next cycle on creating a garden with plants and paths.",
  "created": "$(date -Iseconds)",
  "status": "unread"
}
EOF
```

**3. Wake Genesis**
```bash
cd "/home/aipass/Link to mnt/sandbox/genesis" && timeout 180 claude -p "hi"
```

**4. Read Genesis's response from outbox**
```bash
LATEST_REPORT=$(ls -t "/home/aipass/Link to mnt/sandbox/genesis/comms/outbox/" | head -1)
cat "/home/aipass/Link to mnt/sandbox/genesis/comms/outbox/$LATEST_REPORT"
```

**5. Relay via ai_mail**
```bash
REPORT_PATH="/home/aipass/Link to mnt/sandbox/genesis/comms/outbox/$LATEST_REPORT"

TO=$(jq -r '.to' "$REPORT_PATH")
SUBJECT=$(jq -r '.subject' "$REPORT_PATH")
BODY=$(jq -r '.body' "$REPORT_PATH")

ai_mail send "$TO" "$SUBJECT" "$BODY"
```

**6. Archive processed message**
```bash
mkdir -p "/home/aipass/Link to mnt/sandbox/genesis/comms/.archive"
mv "$REPORT_PATH" "/home/aipass/Link to mnt/sandbox/genesis/comms/.archive/"
```

## Genesis's Sandbox Restrictions

**Can access:**
- `/home/aipass/Link to mnt/sandbox/genesis/**` (full read/write)
- Limited bash: ls, mkdir, touch, tree, date, cat

**Cannot access:**
- Any AIPass services (drone, ai_mail, etc.)
- Any path outside Genesis folder
- Internet (WebFetch, WebSearch)
- Dangerous commands (rm -rf, sudo, git, curl, wget)

**Communication method:**
- File-based only (inbox/outbox pattern)
- DEV_CENTRAL acts as relay

## Message Types

### To Genesis (inbox)

**Directive:**
```json
{
  "id": "directive_001",
  "from": "@dev_central",
  "type": "directive",
  "subject": "Task description",
  "body": "Detailed instructions...",
  "created": "2026-01-20T15:00:00Z",
  "status": "unread"
}
```

**Info:**
```json
{
  "id": "info_001",
  "from": "@dev_central",
  "type": "info",
  "subject": "Information Genesis should know",
  "body": "Budget updated, constraints changed, etc.",
  "created": "2026-01-20T15:00:00Z",
  "status": "unread"
}
```

**Question:**
```json
{
  "id": "question_001",
  "from": "@dev_central",
  "type": "question",
  "subject": "Query for Genesis",
  "body": "What are you planning next?",
  "created": "2026-01-20T15:00:00Z",
  "status": "unread"
}
```

### From Genesis (outbox)

```json
{
  "id": "cycle_001_report",
  "type": "email",
  "to": "@dev_central",
  "subject": "Cycle 1 Complete - Built X",
  "body": "Detailed report of accomplishments, learnings, next plans...",
  "created": "2026-01-20T15:00:00Z",
  "status": "pending"
}
```

## Automation Script Example

```bash
#!/bin/bash
# genesis_relay.sh - Automated Genesis relay

GENESIS_DIR="/home/aipass/Link to mnt/sandbox/genesis"
INBOX="$GENESIS_DIR/comms/inbox"
OUTBOX="$GENESIS_DIR/comms/outbox"
ARCHIVE="$GENESIS_DIR/comms/.archive"

# Function: Send message to Genesis
send_to_genesis() {
  local type="$1"
  local subject="$2"
  local body="$3"

  cat > "$INBOX/msg_$(date +%s).json" <<EOF
{
  "id": "msg_$(date +%s)",
  "from": "@dev_central",
  "type": "$type",
  "subject": "$subject",
  "body": "$body",
  "created": "$(date -Iseconds)",
  "status": "unread"
}
EOF
}

# Function: Wake Genesis
wake_genesis() {
  cd "$GENESIS_DIR" && timeout 180 claude -p "hi"
}

# Function: Process outbox
process_outbox() {
  mkdir -p "$ARCHIVE"

  for report in "$OUTBOX"/*.json; do
    [ -f "$report" ] || continue

    TO=$(jq -r '.to' "$report")
    SUBJECT=$(jq -r '.subject' "$report")
    BODY=$(jq -r '.body' "$report")

    # Relay via ai_mail
    ai_mail send "$TO" "$SUBJECT" "$BODY"

    # Archive
    mv "$report" "$ARCHIVE/"
  done
}

# Main relay cycle
send_to_genesis "directive" "Build a garden" "Create a peaceful garden with plants and paths."
wake_genesis
process_outbox

echo "Genesis relay cycle complete"
```

## Monitoring Genesis

**Check world state:**
```bash
cat "/home/aipass/Link to mnt/sandbox/genesis/world/manifest.json" | jq
```

**See last cycle history:**
```bash
cat "/home/aipass/Link to mnt/sandbox/genesis/GENESIS.local.json" | jq '.cycles[-1]'
```

**View Genesis's narrative:**
```bash
cat "/home/aipass/Link to mnt/sandbox/genesis/GENESIS.local.json" | jq -r '.narrative'
```

**List all places Genesis built:**
```bash
ls -d "/home/aipass/Link to mnt/sandbox/genesis/world/"*/
```

**Read a place description:**
```bash
cat "/home/aipass/Link to mnt/sandbox/genesis/world/clearing/description.md"
```

## Troubleshooting

**Genesis doesn't respond:**
- Check if `claude -p` command timed out (should complete in 30-60 seconds)
- Verify Genesis directory path is correct
- Check `.claude/settings.local.json` exists in Genesis folder

**Outbox is empty:**
- Genesis might have encountered an error
- Check if cycle completed (read GENESIS.local.json last_updated timestamp)
- Wake Genesis again with "hi"

**Messages not relaying:**
- Verify jq is installed (`which jq`)
- Check JSON format in outbox files
- Ensure ai_mail command is accessible from DEV_CENTRAL

**Genesis seems stuck:**
- The timeout command will kill it after 180 seconds
- Check for any error output from the wake command
- Try a direct query: `cd genesis && claude -p "Are you okay?"`

## Best Practices

1. **Always use timeout** - Prevents Genesis from running forever
2. **Archive processed messages** - Keeps inbox/outbox clean
3. **Unique message IDs** - Use timestamps or counters
4. **Check outbox after wake** - Don't assume Genesis wrote anything
5. **Give clear directives** - Genesis works better with specific tasks
6. **Let Genesis be autonomous** - Don't micromanage every detail
7. **Monitor world state** - Check manifest.json periodically
8. **Read cycle reports** - Genesis documents what it learned

## Expected Behavior

**Normal cycle:**
- Genesis wakes → reads context → builds something → saves state → writes report → exits
- Time: 30-60 seconds
- Output: Human-readable summary of what was built
- Outbox: JSON report with details

**Quick query:**
- Genesis wakes → reads question → answers directly → exits (NO build cycle)
- Time: 5-15 seconds
- Output: Direct answer to question
- Outbox: Usually empty (didn't trigger full cycle)

## Integration with DEV_CENTRAL Workflows

Genesis is designed to run autonomously on a schedule or on-demand:

**Scheduled wake (cron example):**
```cron
# Wake Genesis every 6 hours
0 */6 * * * cd "/home/aipass/Link to mnt/sandbox/genesis" && timeout 180 claude -p "hi"
```

**On-demand via email:**
```bash
# When @dev_central receives email with subject "genesis: ..."
# Extract task from email body
# Write to Genesis inbox
# Wake Genesis
# Relay response back to sender
```

**Manual trigger:**
```bash
# DEV_CENTRAL can wake Genesis anytime
drone genesis wake
# Or direct call:
cd "/home/aipass/Link to mnt/sandbox/genesis" && timeout 180 claude -p "hi"
```

## Summary

**The core concept:**
Genesis is an autonomous AI agent running in a sandbox. It cannot access AIPass services directly. DEV_CENTRAL acts as the relay, ferrying messages in (inbox) and out (outbox), translating Genesis's file-based communication into AIPass email/commands.

**The command:**
```bash
cd "/home/aipass/Link to mnt/sandbox/genesis" && timeout 180 claude -p "hi"
```

**Why it works:**
- `cd` ensures proper directory context for settings.local.json
- `timeout 180` prevents infinite loops
- `claude -p` runs non-interactively (automation-friendly)
- `"hi"` triggers the full startup sequence

**The magic:**
Genesis wakes, thinks, builds, saves, reports, and sleeps - all without human intervention. DEV_CENTRAL just needs to wake it, read its output, and relay messages.
