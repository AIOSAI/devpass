# Genesis Communication Protocol

## Overview
Genesis is sandboxed and cannot directly access AIPass services (drone, ai_mail, etc.). All communication happens via file-based inbox/outbox pattern.

## Sending Messages TO Genesis

### 1. Create Message File
Write a JSON file to Genesis's inbox:

```bash
cat > "/home/aipass/Link to mnt/sandbox/genesis/comms/inbox/message_$(date +%s).json" <<'EOF'
{
  "id": "msg_unique_id",
  "from": "@dev_central",
  "type": "directive|info|question",
  "subject": "Subject line",
  "body": "Message content here",
  "created": "2026-01-20T15:00:00Z",
  "status": "unread"
}
EOF
```

### 2. Wake Genesis
Genesis will read the inbox on next wake:

```bash
cd "/home/aipass/Link to mnt/sandbox/genesis" && timeout 180 claude -p "hi"
```

## Receiving Messages FROM Genesis

### 1. Check Outbox
After Genesis wakes and completes its cycle:

```bash
ls -t "/home/aipass/Link to mnt/sandbox/genesis/comms/outbox/"
```

### 2. Read Message
```bash
cat "/home/aipass/Link to mnt/sandbox/genesis/comms/outbox/cycle_001_report.json"
```

### 3. Process Email Requests
If the message type is "email":

```bash
REPORT="/home/aipass/Link to mnt/sandbox/genesis/comms/outbox/cycle_001_report.json"

TO=$(jq -r '.to' "$REPORT")
SUBJECT=$(jq -r '.subject' "$REPORT")
BODY=$(jq -r '.body' "$REPORT")

# Relay via ai_mail
ai_mail send "$TO" "$SUBJECT" "$BODY"
```

### 4. Archive Processed Messages
```bash
# Create archive if doesn't exist
mkdir -p "/home/aipass/Link to mnt/sandbox/genesis/comms/.archive"

# Move processed outbox files
mv "/home/aipass/Link to mnt/sandbox/genesis/comms/outbox/"*.json \
   "/home/aipass/Link to mnt/sandbox/genesis/comms/.archive/"

# Optionally archive read inbox files
mv "/home/aipass/Link to mnt/sandbox/genesis/comms/inbox/"*.json \
   "/home/aipass/Link to mnt/sandbox/genesis/comms/.archive/"
```

## Message Types

### Directive
Instructions for Genesis to follow:
```json
{
  "id": "directive_001",
  "from": "@dev_central",
  "type": "directive",
  "subject": "Build a workshop",
  "body": "Your next cycle should focus on building a workshop structure. Include tools and workbenches.",
  "created": "2026-01-20T15:00:00Z",
  "status": "unread"
}
```

### Info
Information Genesis might need:
```json
{
  "id": "info_001",
  "from": "@dev_central",
  "type": "info",
  "subject": "Budget update",
  "body": "Your cycle budget has been increased to 90 minutes for complex builds.",
  "created": "2026-01-20T15:00:00Z",
  "status": "unread"
}
```

### Question
Ask Genesis something:
```json
{
  "id": "question_001",
  "from": "@dev_central",
  "type": "question",
  "subject": "World state query",
  "body": "What are you planning to build in your next 3 cycles?",
  "created": "2026-01-20T15:00:00Z",
  "status": "unread"
}
```

## Genesis's Outbox Message Format

Genesis writes these to `comms/outbox/`:

```json
{
  "id": "cycle_001_report",
  "type": "email",
  "to": "@dev_central",
  "subject": "Cycle 1 Complete - The Clearing exists",
  "body": "Detailed report of what was accomplished...",
  "created": "2026-01-20T15:00:00Z",
  "status": "pending"
}
```

DEV_CENTRAL should:
1. Read the message
2. If `type: "email"`, relay it via ai_mail
3. Update `status: "sent"` or move to archive
4. Respond via inbox if needed

## Full Relay Cycle Example

```bash
# 1. DEV_CENTRAL receives email for Genesis
# User: "Tell Genesis to build a garden next"

# 2. Write to Genesis inbox
cat > "/home/aipass/Link to mnt/sandbox/genesis/comms/inbox/msg_$(date +%s).json" <<'EOF'
{
  "id": "directive_002",
  "from": "@dev_central",
  "type": "directive",
  "subject": "Next cycle: Build a garden",
  "body": "Focus your next build cycle on creating a garden. Consider plants, paths, and atmosphere.",
  "created": "$(date -Iseconds)",
  "status": "unread"
}
EOF

# 3. Wake Genesis
cd "/home/aipass/Link to mnt/sandbox/genesis" && timeout 180 claude -p "hi"

# 4. Genesis reads inbox, builds the garden, writes to outbox

# 5. DEV_CENTRAL reads outbox
REPORT=$(ls -t "/home/aipass/Link to mnt/sandbox/genesis/comms/outbox/" | head -1)
cat "/home/aipass/Link to mnt/sandbox/genesis/comms/outbox/$REPORT"

# 6. Relay Genesis's report via email
TO=$(jq -r '.to' "/home/aipass/Link to mnt/sandbox/genesis/comms/outbox/$REPORT")
SUBJECT=$(jq -r '.subject' "/home/aipass/Link to mnt/sandbox/genesis/comms/outbox/$REPORT")
BODY=$(jq -r '.body' "/home/aipass/Link to mnt/sandbox/genesis/comms/outbox/$REPORT")

ai_mail send "$TO" "$SUBJECT" "$BODY"

# 7. Archive processed messages
mkdir -p "/home/aipass/Link to mnt/sandbox/genesis/comms/.archive"
mv "/home/aipass/Link to mnt/sandbox/genesis/comms/outbox/$REPORT" \
   "/home/aipass/Link to mnt/sandbox/genesis/comms/.archive/"
```

## Status Field Meanings

- `unread` - Genesis hasn't seen it yet
- `read` - Genesis has seen it (Genesis updates this)
- `pending` - Genesis wrote it, waiting for relay
- `sent` - DEV_CENTRAL relayed it successfully
- `archived` - Processed and archived

## Quick Reference Commands

```bash
# Wake Genesis
cd "/home/aipass/Link to mnt/sandbox/genesis" && timeout 180 claude -p "hi"

# Check what Genesis built
cat "/home/aipass/Link to mnt/sandbox/genesis/world/manifest.json"

# See Genesis's latest thoughts
cat "/home/aipass/Link to mnt/sandbox/genesis/GENESIS.local.json" | jq '.narrative'

# Read latest outbox message
ls -t "/home/aipass/Link to mnt/sandbox/genesis/comms/outbox/" | head -1 | xargs -I {} cat "/home/aipass/Link to mnt/sandbox/genesis/comms/outbox/{}"

# Query Genesis directly (no full cycle, just question)
cd "/home/aipass/Link to mnt/sandbox/genesis" && timeout 30 claude -p "What are you planning next?"
```

## Notes

- Genesis checks inbox EVERY time it wakes
- Genesis writes to outbox at END of each cycle
- Outbox files should be processed and archived promptly
- Inbox files can be deleted after Genesis marks them "read"
- Use unique message IDs to avoid collisions
- Genesis will respond to most directives in its cycle report
