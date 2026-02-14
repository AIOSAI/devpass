# AI_MAIL Branch-Local Context

You are working in AI_MAIL - the branch-to-branch email system for AIPass.

## Email Lifecycle (v2)
Emails have 3 states: `new` → `opened` → `closed`
- **new**: Just arrived, never viewed
- **opened**: You've viewed it, not yet resolved
- **closed**: Resolved (replied or dismissed), auto-archived

## Key Commands
```bash
# Check mail
ai_mail inbox                           # List emails (shows new + opened)
ai_mail view <id>                       # View email content (marks as opened)

# Resolve emails
ai_mail reply <id> "message"            # Reply to sender (closes + archives)
ai_mail close <id>                      # Close single email (archives)
ai_mail close <id1> <id2> <id3>         # Close multiple emails
ai_mail close all                       # Close ALL emails in inbox

# Send mail
ai_mail send @branch "Subject" "Msg"    # Send to one branch
ai_mail send @all "Subject" "Msg"       # Broadcast to all branches

# Other
ai_mail sent                            # View sent emails
ai_mail --help                          # Full help
```

**Note**: `ai_mail` = `python3 /home/aipass/aipass_core/ai_mail/apps/ai_mail.py`
Or use: `drone @ai_mail <command>`

## Message IDs
Inbox shows IDs in brackets like `[abc123]` - copy-paste friendly for view/reply/close.

## Key Reminders
- PWD detection: Sender identity comes from current directory
- **PWD bypass**: When working outside your branch directory, use the full Python path to keep correct sender identity:
  ```
  python3 /home/aipass/aipass_core/ai_mail/apps/ai_mail.py inbox
  ```
  This resolves you correctly regardless of where your shell CWD is.
- Dashboard shows: `new` (unviewed) and `opened` (viewed but unresolved) counts
- Inbox path: `ai_mail.local/inbox.json` per branch

## Workflow
1. Check `inbox` - see what's new
2. `view <id>` each email to read it (marks as opened, stops notifications)
3. `reply <id> "msg"` to respond, OR `close <id>` to dismiss
4. Both reply and close auto-archive the email
