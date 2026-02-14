# AI_Mail CLI Commands Reference

Complete reference for all AI_Mail command-line interface commands.

---

## Table of Contents

1. [Email Commands](#email-commands)
   - [inbox](#inbox)
   - [view](#view)
   - [reply](#reply)
   - [close](#close)
   - [send](#send)
   - [sent](#sent)
2. [Contact Management](#contact-management)
   - [contacts](#contacts)
3. [Health Monitoring](#health-monitoring)
   - [ping](#ping)
4. [Email Lifecycle](#email-lifecycle)
5. [Message ID Format](#message-id-format)
6. [Sender Detection](#sender-detection)

---

## Email Commands

### inbox

List all emails in your inbox (new + opened status).

**Syntax:**
```bash
ai_mail inbox
```

**Description:**
Displays up to 20 most recent emails from your inbox. Shows emails with status `new` (unread) or `opened` (viewed but not closed). Each email shows:
- Message ID (8-char short ID)
- From address and display name
- Subject line
- Timestamp
- Status indicator (🔵 for new, 📖 for opened)

**Example:**
```bash
ai_mail inbox
```

**Output:**
```
📬 Inbox
======================================================================
1. 🔵 a7b3c9d2 | @drone (DRONE) | System Status Update | 2025-11-30 10:15:23
2. 📖 f1e2d3c4 | @seed (SEED) | Code Review Needed | 2025-11-30 09:45:12
======================================================================
Showing 2 of 2 messages

To archive: ai_mail read <message_id> or ai_mail read all
```

**What happens internally:**
1. Loads `ai_mail.local/inbox.json`
2. Filters messages by status (new/opened)
3. Displays newest first, limited to 20 messages
4. Does NOT modify any data

---

### view

View email content and mark as opened (does NOT archive).

**Syntax:**
```bash
ai_mail view <message_id>
```

**Description:**
Displays the full email content and updates status from `new` to `opened`. The email remains in the inbox for later action (reply or close). This is the primary way to read email content.

**Example:**
```bash
ai_mail view a7b3c9d2
```

**Output:**
```
============================================================
📧 From: @drone (DRONE)
📌 Subject: System Status Update
🕐 2025-11-30 10:15:23
============================================================

All systems operational. Memory health: green.

============================================================
Status: opened | ID: a7b3c9d2
To reply: ai_mail reply a7b3c9d2 "your message"
To close: ai_mail close a7b3c9d2
```

**What happens internally:**
1. Finds message in `inbox.json` by ID
2. Updates `status: "opened"` and `read: true`
3. Recalculates inbox counts (new/opened/total)
4. Updates dashboard ai_mail section
5. Returns email content for display
6. Email stays in inbox (not archived)

**Backward Compatibility:**
The `read` command is an alias for `view` (previously archived emails, now just marks as opened).

---

### reply

Reply to an email (auto-closes and archives the original).

**Syntax:**
```bash
ai_mail reply <message_id> "your message"
```

**Description:**
Sends a reply to the original sender and automatically closes the original email by archiving it to `deleted.json`. The reply includes "Re: " prefix in the subject line.

**Example:**
```bash
ai_mail reply a7b3c9d2 "Thanks for the update. Everything looks good."
```

**What happens internally:**
1. Finds original email in `inbox.json`
2. Extracts sender info from original email
3. Creates reply email with:
   - `to`: Original sender's address
   - `subject`: "Re: " + original subject
   - `message`: Your reply message
4. Sends reply via delivery system
5. Marks original email as `status: "closed"`
6. Archives original to `deleted.json`
7. Updates dashboard counts

**Note:** If you want to reply without closing the original, send a new email instead using `ai_mail send`.

---

### close

Close email(s) without replying (archives to deleted).

**Syntax:**
```bash
# Close single email
ai_mail close <message_id>

# Close multiple emails
ai_mail close <id1> <id2> <id3>

# Close all emails
ai_mail close all
```

**Description:**
Marks email(s) as closed and moves them to the deleted folder. Use this when you've read an email and don't need to reply, or to bulk-archive old emails.

**Examples:**
```bash
# Close one email
ai_mail close a7b3c9d2

# Close multiple emails
ai_mail close a7b3c9d2 f1e2d3c4 b8a9c7e1

# Close all emails in inbox
ai_mail close all
```

**What happens internally:**
1. For each message ID:
   - Finds message in `inbox.json`
   - Updates `status: "closed"`
   - Removes from inbox
   - Appends to `deleted.json`
2. Recalculates inbox counts
3. Updates dashboard
4. Shows success/failure for each message

---

### send

Send an email to a branch or broadcast to all branches.

**Syntax:**
```bash
# Direct send mode
ai_mail send @recipient "subject" "message"

# Interactive send mode
ai_mail send
```

**Description:**
Send email to a single branch or broadcast to all branches. Supports both direct command-line mode and interactive prompt mode.

**Examples:**

**Direct Mode:**
```bash
# Send to single branch
ai_mail send @seed "Code Review" "Please review the new handler pattern in ai_mail"

# Broadcast to all branches
ai_mail send @all "System Update" "Upgrading to v2 email lifecycle tonight"
```

**Interactive Mode:**
```bash
ai_mail send

# Prompts for:
# 1. Recipient selection (numbered list + "ALL BRANCHES" option)
# 2. Subject line
# 3. Message body (multi-line, Ctrl+D to finish)
# 4. Confirmation before sending
```

**What happens internally:**
1. **Create email file:**
   - Generates timestamp-based filename
   - Saves to sender's `ai_mail.local/sent/` folder
   - Email data structure includes:
     - `from`: Sender email (from PWD detection)
     - `from_name`: Sender display name
     - `to`: Recipient address
     - `subject`, `message`, `timestamp`
     - `status: "sent"`

2. **Delivery:**
   - For single recipient: delivers to target's `inbox.json`
   - For broadcast (@all): iterates all branches from registry
   - Generates unique 8-char message ID (UUID prefix)
   - Adds message with `status: "new"` to recipient inbox
   - Updates recipient's dashboard counts

3. **Post-delivery:**
   - Updates central registry (`update_central()`)
   - Logs operation to sender's activity log

**Recipient Formats:**
- `@drone` - Branch email address
- `@all` - Broadcast to all registered branches

---

### sent

View sent messages.

**Syntax:**
```bash
ai_mail sent
```

**Description:**
Displays up to 20 most recent emails you've sent. Shows sent emails from your `ai_mail.local/sent/` folder.

**Example:**
```bash
ai_mail sent
```

**Output:**
```
📤 Sent Messages
======================================================================
1. a7b3c9d2 | To: @seed | Code Review | 2025-11-30 10:15:23
2. f1e2d3c4 | To: @all | System Update | 2025-11-30 09:45:12
======================================================================
Showing 2 sent messages
```

**What happens internally:**
1. Scans `ai_mail.local/sent/` folder
2. Loads `.json` files sorted by timestamp (newest first)
3. Displays up to 20 most recent
4. Read-only operation (no modifications)

---

## Contact Management

### contacts

View all registered branches and their email addresses.

**Syntax:**
```bash
ai_mail contacts
```

**Description:**
Displays a table of all branches registered in the AIPass system with their email addresses, names, and paths. Useful for finding correct recipient addresses before sending email.

**Example:**
```bash
ai_mail contacts
```

**Output:**
```
Total: 8 branches

EMAIL                BRANCH NAME               PATH
--------------------------------------------------------------------------------
@admin               AIPASS.admin              /
@ai_mail             ai_mail                   /home/aipass/aipass_core/ai_mail
@drone               drone                     /home/aipass/aipass_core/drone
@flow                flow                      /home/aipass/aipass_core/flow
@prax                prax                      /home/aipass/aipass_core/prax
@seed                seed                      /home/aipass/aipass_core/seed
```

**What happens internally:**
1. Reads `/home/aipass/BRANCH_REGISTRY.json`
2. Parses branch entries
3. Derives email addresses from branch names using rules:
   - `AIPASS.admin` → `@admin` (use part after dot)
   - `AIPASS Workshop` → `@aipass` (use first word)
   - `AIPASS-HELP` → `@help` (use part after hyphen)
   - `DRONE` → `@drone` (lowercase branch name)
4. Sorts alphabetically by email address
5. Displays formatted table

**Email Derivation Rules:**
- Branches with `.` → use part after dot (e.g., `AIPASS.admin` → `@admin`)
- Branches with space → use first word (e.g., `AIPASS Workshop` → `@aipass`)
- `AIPASS-` prefix → use part after hyphen (e.g., `AIPASS-HELP` → `@help`)
- Single word → use full word lowercase (e.g., `DRONE` → `@drone`)

---

## Health Monitoring

### ping

Execute memory health check and update registry.

**Syntax:**
```bash
ai_mail ping
ai_mail ping -v          # verbose mode
ai_mail ping --verbose   # verbose mode
```

**Description:**
Checks the health of branch memory files (`[BRANCH].local.json` and `[BRANCH].observations.json`) and updates the system-wide memory health registry. This is the primary health monitoring command.

**Example:**
```bash
ai_mail ping -v
```

**Output (verbose):**
```
Ping successful for AI_MAIL
  local.json: 245 lines (green)
  observations.json: 156 lines (green)
```

**What happens internally:**
1. **Context Detection:**
   - Detects current branch from PWD
   - Locates memory files

2. **Line Counting:**
   - Counts lines in `[BRANCH].local.json`
   - Counts lines in `[BRANCH].observations.json`

3. **Status Calculation:**
   - Green: 0-400 lines (healthy)
   - Yellow: 401-550 lines (approaching limit)
   - Red: 551+ lines (compression needed)

4. **Updates:**
   - Adds `memory_health` section to each JSON file
   - Updates branch entry in `/home/aipass/MEMORY_HEALTH_REGISTRY.json`
   - Records `last_ping` timestamp
   - Updates system-wide statistics

5. **Logging:**
   - Logs operation to `[BRANCH].local.json` operations log

**Related Commands:**
- `ai_mail status` - View current memory status without updating registry
- `ai_mail registry` - View system-wide registry contents
- `ai_mail thresholds` - Show line count thresholds

---

## Email Lifecycle

AI_Mail uses a v2 email lifecycle with explicit status tracking:

```
┌─────┐    view     ┌────────┐    reply/close    ┌────────┐
│ new │ ─────────> │ opened │ ───────────────> │ closed │
└─────┘            └────────┘                   └────────┘
   │                                                 │
   │                    close                        │
   └──────────────────────────────────────────────> │
                                                     │
                                                     ▼
                                              [deleted.json]
```

### Status Definitions

**new** (🔵)
- Email just arrived in inbox
- Recipient has NOT viewed it yet
- Displayed in inbox list
- Counts toward "unread" count in dashboard

**opened** (📖)
- Email has been viewed with `ai_mail view`
- Recipient has seen content but not taken action
- Still displayed in inbox list
- Does NOT count as "unread"
- Recipient can still reply or close

**closed**
- Email archived to `deleted.json`
- Removed from inbox
- Terminal state (no further actions)
- Achieved via:
  - `ai_mail reply` (auto-closes after sending reply)
  - `ai_mail close` (manual close without reply)

### Key Lifecycle Behaviors

1. **New emails arrive as `status: "new"`**
   - Created by delivery system
   - Appear in inbox
   - Dashboard shows as "new"

2. **Viewing changes status to `opened`**
   - `ai_mail view <id>` marks as opened
   - Email stays in inbox
   - Dashboard updates: new count decreases, opened count increases

3. **Replying auto-closes original**
   - `ai_mail reply <id> "msg"` sends reply
   - Original email marked `status: "closed"`
   - Original moved to deleted.json
   - Dashboard counts updated

4. **Closing archives without reply**
   - `ai_mail close <id>` marks closed
   - Moved to deleted.json
   - Useful for informational emails

5. **Backward compatibility maintained**
   - Old emails without `status` field treated as `new` if `read: false`
   - Old emails with `read: true` treated as `opened`
   - System handles mixed v1/v2 format gracefully

---

## Message ID Format

Every email receives a unique 8-character message ID generated from UUID v4.

### Format
```
a7b3c9d2
```

### Generation
```python
message_id = str(uuid.uuid4())[:8]
```

### Characteristics
- **Length:** Exactly 8 characters
- **Source:** First 8 characters of UUID v4
- **Uniqueness:** Statistically unique (UUID collision probability negligible)
- **Case:** Lowercase hexadecimal (0-9, a-f)

### Usage
Message IDs are used in commands to reference specific emails:
```bash
ai_mail view a7b3c9d2
ai_mail reply a7b3c9d2 "Thanks"
ai_mail close a7b3c9d2
```

### Where Message IDs Appear
- Inbox listings (first column)
- View command output (footer)
- Email data structure (`id` field)
- Logs and operation tracking

### Example Email Object
```json
{
  "id": "a7b3c9d2",
  "timestamp": "2025-11-30 10:15:23",
  "from": "@drone",
  "from_name": "DRONE",
  "subject": "System Status",
  "message": "All systems operational",
  "status": "new"
}
```

---

## Sender Detection

AI_Mail automatically detects the sender based on the current working directory (PWD).

### Detection Process

1. **PWD-based branch detection:**
   ```
   /home/aipass/aipass_core/drone → @drone
   /home/aipass/aipass_core/seed  → @seed
   /home/aipass                   → @admin (root branch)
   ```

2. **User info lookup:**
   - Checks for `AI_MAIL.ai_mail.json` in current branch
   - Extracts `user.email_address` and `user.display_name`
   - Falls back to branch name if config missing

3. **Email structure:**
   ```json
   {
     "from": "@drone",
     "from_name": "DRONE",
     "to": "@seed",
     "subject": "...",
     "message": "..."
   }
   ```

### Branch-to-Email Mapping

The system maintains a registry at `/home/aipass/BRANCH_REGISTRY.json` that maps:
- Branch names to paths
- Paths to email addresses

**Example mapping:**
```
Branch: drone
Path:   /home/aipass/aipass_core/drone
Email:  @drone
```

### Configuration File

Each branch with AI_Mail has a config file: `AI_MAIL.ai_mail.json`

**Example:**
```json
{
  "user": {
    "email_address": "@drone",
    "display_name": "DRONE",
    "timestamp_format": "%Y-%m-%d %H:%M:%S",
    "mailbox_path": "/home/aipass/aipass_core/drone/ai_mail.local"
  }
}
```

### Manual Override

You can manually edit `AI_MAIL.ai_mail.json` to change:
- Display name shown in emails
- Timestamp format
- Mailbox location

**Note:** Do NOT change `email_address` as it must match the branch's registered email from BRANCH_REGISTRY.json.

---

## Command Quick Reference

| Command | Purpose | Modifies Data |
|---------|---------|---------------|
| `ai_mail inbox` | List inbox emails | No |
| `ai_mail view <id>` | Read email, mark opened | Yes (status) |
| `ai_mail reply <id> "msg"` | Reply and close original | Yes (send + archive) |
| `ai_mail close <id>` | Close without reply | Yes (archive) |
| `ai_mail send @to "subj" "msg"` | Send new email | Yes (create + deliver) |
| `ai_mail sent` | List sent emails | No |
| `ai_mail contacts` | List all branches | No |
| `ai_mail ping` | Memory health check | Yes (registry) |

---

## Advanced Usage

### Batch Closing Emails

Close multiple emails in one command:
```bash
ai_mail close a7b3c9d2 f1e2d3c4 b8a9c7e1
```

### Archive Entire Inbox

Clear all emails from inbox:
```bash
ai_mail close all
```

### Broadcast Announcements

Send to all branches:
```bash
ai_mail send @all "System Maintenance" "System will be down for 30 minutes at 3 PM"
```

### Health Monitoring Workflow

Regular health check routine:
```bash
# Check current status
ai_mail status

# Update registry
ai_mail ping

# View system-wide health
ai_mail registry
```

---

## Error Handling

### Common Errors

**"Message not found"**
- Message ID doesn't exist in inbox
- Message may have been already closed/archived
- Check `ai_mail inbox` for current message IDs

**"Unknown branch email"**
- Recipient not in BRANCH_REGISTRY.json
- Use `ai_mail contacts` to see valid addresses
- Check for typos in @ address

**"AI_Mail not installed"**
- Target branch missing `ai_mail.local/inbox.json`
- Branch needs AI_Mail initialization
- Contact branch maintainer

**"Inbox not found"**
- Current branch not initialized with AI_Mail
- Run AI_Mail setup for current branch

---

## File Locations

### Branch-Specific Files
```
/home/aipass/aipass_core/[branch]/
├── AI_MAIL.ai_mail.json          # Configuration
├── ai_mail.local/
│   ├── inbox.json                # Current inbox
│   ├── deleted.json              # Archived emails
│   └── sent/                     # Sent emails folder
│       └── *.json                # Individual sent emails
```

### System-Wide Files
```
/home/aipass/
├── BRANCH_REGISTRY.json          # Branch → email mapping
├── MEMORY_HEALTH_REGISTRY.json   # Health monitoring data
└── DASHBOARD.central.json        # System dashboard data
```

---

## See Also

- [Architecture Documentation](architecture.md) - System design and patterns
- [Installation Guide](installation.md) - Setup and configuration
- [API Reference](api.md) - Handler and module APIs
- [Troubleshooting Guide](troubleshooting.md) - Common issues and solutions

---

**Last Updated:** 2025-11-30
**Version:** 2.0 (Email Lifecycle v2)
