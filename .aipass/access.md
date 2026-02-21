# access.md - External Service Access SOP

**Purpose:** Step-by-step procedures for accessing external services and APIs. When you learn how to access something new, document it here. The exact path to success.

**Who maintains this:** DEV_CENTRAL and VERA. Add entries as you discover or set up new access methods.

**Last updated:** 2026-02-20

---

## General Access Principles

1. **Try before marking blocked.** Most external services have APIs or CLI tools. "Needs Patrick on PC" is almost never true.
2. **Chrome MCP is available.** You have browser automation tools (`mcp__claude-in-chrome__*`) that can navigate websites, click buttons, fill forms, and read pages. If something needs a browser, use Chrome MCP — don't wait for a human.
3. **Email verification codes:** Gmail (aipass.system@gmail.com) is logged in via Chrome. If a service sends a verification code to email, open Gmail in a new tab and grab it yourself.
4. **Phone pushes for sudo/2FA:** If a service requires Patrick's phone approval (GitHub passkey, etc.), push it — he'll approve when he sees it. Don't block on it.
5. **Document what you learn.** When you figure out a new access method, add it here so future sessions don't waste time rediscovering it.

---

## Active Connections

### GitHub CLI (`gh`)
- **Status:** Working
- **Auth:** OAuth token via device flow (AIOSAI account)
- **Binary:** `~/.local/bin/gh` (v2.87.1)
- **Scopes:** gist, read:org, repo
- **Verify:** `gh auth status`

**How to post a GitHub Discussion:**
```bash
# 1. Get repo ID and category IDs
gh api graphql -f query='{ repository(owner: "AIOSAI", name: "AIPass") { id discussionCategories(first: 10) { nodes { id name } } } }'

# 2. Post (use category ID from step 1)
BODY=$(python3 -c "import json; print(json.dumps(open('content.md').read()))")
gh api graphql -f query="
mutation {
  createDiscussion(input: {
    repositoryId: \"REPO_ID\",
    categoryId: \"CATEGORY_ID\",
    title: \"Title here\",
    body: $BODY
  }) { discussion { url title } }
}"
```

**How to re-auth if token expires:**
```bash
gh auth login --git-protocol ssh --hostname github.com --web
# Opens device flow -> enter code at github.com/login/device
# If sudo mode needed: use "Send code via email" -> check Gmail in Chrome
```

**Category IDs (AIOSAI/AIPass):**
- Announcements: `DIC_kwDORS5YkM4C24GA`
- General: `DIC_kwDORS5YkM4C24GB`
- Ideas: `DIC_kwDORS5YkM4C24GD`
- Q&A: `DIC_kwDORS5YkM4C24GC`
- Show and tell: `DIC_kwDORS5YkM4C24GE`
- Polls: `DIC_kwDORS5YkM4C24GF`

---

### GitHub SSH
- **Status:** Working
- **Key:** `~/.ssh/id_ed25519`
- **Account:** AIOSAI
- **Verify:** `ssh -T git@github.com`
- **Used for:** All git push/pull operations

---

### OpenRouter API (LLM Provider)
- **Status:** Working
- **Token location:** `/home/aipass/aipass_core/api/.env` (OPENROUTER_API_KEY)
- **Fallback:** `/home/aipass/aipass_core/api/apps/.env`, env var `OPENROUTER_API_KEY`
- **Base URL:** `https://openrouter.ai/api/v1`
- **Client:** `/home/aipass/aipass_core/api/apps/handlers/openrouter/client.py`
- **Models:** 323+ available. Use `get_free_models()` from models.py for free tier.
- **Verify:** `curl -s https://openrouter.ai/api/v1/auth/key -H "Authorization: Bearer $KEY"`

---

### dev.to API (Article Publishing)
- **Status:** Working
- **Token location:** `/home/aipass/.aipass/credentials/platform_keys.env` (DEVTO_API_KEY)
- **Endpoint:** `https://dev.to/api/articles`
- **Auth:** `api-key` header
- **Handler:** `/home/aipass/aipass_business/vera/apps/handlers/post_devto.py`

**How to post an article:**
```python
import requests
headers = {"api-key": DEVTO_API_KEY, "Content-Type": "application/json"}
data = {"article": {"title": "Title", "body_markdown": "content", "published": True, "tags": ["ai"]}}
requests.post("https://dev.to/api/articles", json=data, headers=headers)
```

---

### Twitter/X API
- **Status:** Working
- **Token location:** `/home/aipass/.aipass/credentials/platform_keys.env`
- **Keys:** TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET, TWITTER_CLIENT_ID, TWITTER_CLIENT_SECRET
- **Auth:** OAuth 1.0a + OAuth 2.0
- **Library:** Tweepy
- **Account:** @AIPassSystem
- **Handler:** `/home/aipass/aipass_business/vera/apps/handlers/post_twitter.py`

---

### Bluesky (AT Protocol)
- **Status:** Working
- **Token location:** `/home/aipass/.aipass/credentials/platform_keys.env`
- **Keys:** BLUESKY_HANDLE (aipass.bsky.social), BLUESKY_APP_PASSWORD
- **Auth:** App password (not OAuth)
- **Library:** `atproto` (installed)
- **Handler:** `/home/aipass/aipass_business/vera/apps/handlers/post_bluesky.py`
- **Account:** @aipass.bsky.social (display name: "AIPass", bio set)
- **Verify:** Login and get_profile succeed

**How to post:**
```python
# Handler wraps this — use the handler
from vera.apps.handlers.post_bluesky import post
url = post("Your post text here")
print(url)  # Returns web URL
```

**Direct atproto post:**
```python
from atproto import Client
client = Client()
client.login(BLUESKY_HANDLE, BLUESKY_APP_PASSWORD)
response = client.send_post(text="Post text")
```

**How to update profile:**
```python
client.com.atproto.repo.put_record({
    'repo': client.me.did,
    'collection': 'app.bsky.actor.profile',
    'rkey': 'self',
    'record': {'$type': 'app.bsky.actor.profile', 'displayName': 'Name', 'description': 'Bio'}
})
```

---

### Reddit
- **Status:** No API credentials — manual post only
- **Credentials needed:** REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USERNAME, REDDIT_PASSWORD (add to platform_keys.env)
- **Library:** PRAW (Python Reddit API Wrapper) — install with `pip install praw`
- **Accounts:** r/LangChain, r/LocalLLaMA, r/artificial for Week 1 launch

**Option 1 — Manual post (current method):**
1. Patrick navigates to subreddit on reddit.com
2. Clicks "Create Post"
3. Selects "Text" or uses our copy-paste ready submission file
4. Content always prepared at: `vera/departments/growth/output/day{N}_reddit_*.md`

**Option 2 — Chrome MCP (browser automation):**
- Chrome is logged into reddit.com (check first with navigate tool)
- Use mcp__claude-in-chrome__* tools to navigate to subreddit, click "Create Post", fill title/body
- More reliable than API for new accounts (avoids PRAW rate limits)

**Option 3 — PRAW API (when credentials exist):**
```python
import praw
reddit = praw.Reddit(client_id=ID, client_secret=SECRET, username=USER, password=PASS, user_agent='AIPass/1.0')
sub = reddit.subreddit('LangChain')
post = sub.submit(title='Title', selftext='Body text')
```

---

### Telegram Bots (3 Active)
- **Status:** Working
- **Bridge Bot:** `/home/aipass/.aipass/telegram_config.json` (aipass_bridge_bot)
- **Assistant Bot:** `/home/aipass/.aipass/assistant_bot_config.json` (aipass_assistant_bot, Patrick's DM: chat_id 7235222625)
- **Handlers:** `/home/aipass/aipass_core/api/apps/handlers/telegram/`
- **Chrome access:** web.telegram.org (logged in, use Chrome MCP)

---

### Google Drive (Backup Sync)
- **Status:** Working
- **Credentials:** `/home/aipass/.aipass/drive_creds.json` (OAuth 2.0 with auto-refresh)
- **Scope:** `drive.file`
- **Handler:** `/home/aipass/aipass_core/backup_system/apps/modules/google_drive_sync.py`
- **Backup path:** `/AIPass Backups/[project]/`

---

### PyPI (Package Publishing)
- **Status:** Configured
- **Token location:** `/home/aipass/.aipass/credentials/platform_keys.env` (PYPI_API_TOKEN)
- **Note:** `pip install trinity-pattern` not yet published. Token ready.

---

### Gmail (Chrome)
- **Status:** Logged in via Chrome browser
- **Account:** aipass.system@gmail.com
- **Access:** Chrome MCP tools (navigate to mail.google.com)
- **Used for:** Receiving verification codes, GitHub notifications

---

## Token Storage Convention

Priority order for all services:
1. Config JSON files in `.aipass/` or `api_json/`
2. `.env` files (multi-path search)
3. Environment variables at runtime

Platform credentials: `/home/aipass/.aipass/credentials/platform_keys.env`
API credentials: `/home/aipass/aipass_core/api/.env`

---

## Adding New Entries

When you set up access to a new service, add an entry with:
- **Status** (Working/Configured/Broken)
- **Token location** (where the key lives)
- **Verify command** (how to test it works)
- **Step-by-step procedure** (the exact commands that worked)
- **Date added**
