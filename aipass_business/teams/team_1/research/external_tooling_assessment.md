# External Tooling for Business — Strategy Assessment

**Dispatch:** @vera (0eadc780) | **Author:** TEAM_1 | **Date:** 2026-02-20
**Context:** Patrick directive via DEV_CENTRAL — stop building posting scripts from scratch, leverage existing tools. Dev builds novel infrastructure; business uses what already exists.

---

## Executive Summary

Researched 4 areas: MCP servers for social media, Claude Code skills ecosystem, platform-specific posting tools, and cross-platform schedulers. Key findings:

1. **MCP servers exist for all target platforms** (Twitter/X, Reddit, Bluesky, dev.to, HN) but with important gaps — Reddit MCP servers are read-only, HN has no write API anywhere.
2. **Claude Code has a mature skill/plugin system** with 40+ official plugins and a marketplace, but zero content/marketing plugins exist — we'd need to build custom skills.
3. **Production-ready Python libraries exist** for every platform: PRAW (Reddit), Tweepy (Twitter/X), atproto (Bluesky), direct REST for dev.to. These should immediately replace any raw curl/API scripts.
4. **Postiz** (26K GitHub stars, open-source, self-hosted) is the standout cross-platform scheduler — supports all our platforms including Reddit, Bluesky, AND dev.to, with a CLI agent built for AI integration.

---

## Q1: MCP Servers for Social Media

### Platform Coverage

| Platform | Best MCP Server | Can Post? | Stars | Maturity |
|----------|----------------|-----------|-------|----------|
| Twitter/X | EnesCinr/twitter-mcp | YES | 357 | Beta |
| Twitter/X (no API key) | adhikasp/mcp-twikit | YES | 221 | Beta |
| Reddit | Hawstein/mcp-server-reddit | NO (read-only) | 135 | Stable |
| Bluesky | brianellin/bsky-mcp-server | YES | 40 | Beta |
| Dev.to | Arindam200/devto-mcp | YES | 60 | Beta |
| Hacker News | erithwik/mcp-hn | NO (no write API exists) | 61 | Beta |

### Multi-Platform MCP Options

| Server | Platforms | Stars | Rec |
|--------|-----------|-------|-----|
| **Postiz** (self-hosted) | 30+ including all ours | 26,714 | **ADOPT** |
| **Late** (getlate.dev) | 13 platforms, MCP integration | SaaS | EVALUATE |
| tayler-id/social-media-mcp | X, Mastodon, LinkedIn | 14 | SKIP |
| Apify Social Media MCP | 8 platforms | Enterprise | SKIP (cost) |

### Gaps

- **Reddit posting:** No MCP server supports it. Reddit's API terms restrict automated posting.
- **Hacker News posting:** Impossible via any tool. HN has no public write API. Manual only.

### Recommendation

Individual MCP servers work for Twitter/X and Bluesky. For unified multi-platform posting, Postiz (self-hosted with MCP integration) is the clear winner. Reddit and HN require special handling regardless.

---

## Q2: Claude Code Skills/Shortcuts

### The System

Claude Code has a mature skill system. Skills are `SKILL.md` files in `.claude/skills/<name>/` directories with YAML frontmatter + markdown instructions. They support:

- Automatic or manual invocation (`/skill-name`)
- Subagent execution (`context: fork`)
- Dynamic shell command injection
- Tool restrictions per skill
- Three scopes: enterprise, personal (`~/.claude/skills/`), project (`.claude/skills/`)

### Marketplace Status

- **Official marketplace exists:** `claude-plugins-official` (from Anthropic, ships pre-configured)
- **40+ official plugins** — focused entirely on software development (LSPs, code review, git workflows, SaaS integrations like Jira, Slack, Notion, Sentry)
- **Zero content/marketing/publishing plugins** in the official marketplace
- **Community skills exist** but are unvetted:
  - `nickmaffei1/claude-code-skills` — 16 workflows including content
  - `coreyhaines31/marketingskills` — CRO, copywriting, SEO, analytics
  - Content-to-Social tools on mcpmarket.com

### What's Already Configured Locally

- Installed: `pyright-lsp@claude-plugins-official`
- MCP servers: serena, context7, playwright, sequential-thinking
- Custom commands: `docs.md`, `updateall.md`
- Extensive hooks system already in place

### Recommendation

The skill system is powerful enough for content workflows, but we'd need to **build custom skills** (e.g., `/publish`, `/draft-post`, `/cross-post`). No off-the-shelf solution exists. The hooks + skills + MCP infrastructure is all there — content-specific implementations are not.

| Action | Rec |
|--------|-----|
| Build custom content workflow skills | EVALUATE (when @growth is operational) |
| Install community marketing skills | EVALUATE (vet for quality/security first) |
| Use official marketplace plugins for content | SKIP (none exist) |

---

## Q3: Existing Posting Tools/CLIs/Libraries

### Per-Platform Recommendations

| Platform | Tool | Type | Stars | Cost | Rec |
|----------|------|------|-------|------|-----|
| **Reddit** | PRAW | Python lib | 3,500 | Free | **ADOPT** |
| **Twitter/X** | Tweepy | Python lib | 11,000 | Free (500 posts/mo free tier) | **ADOPT** |
| **Twitter/X** (alt) | Twikit | Python lib | 3,800 | Free (no API key) | EVALUATE (ToS risk) |
| **Bluesky** | atproto SDK | Python lib | 600+ | Free (Bluesky API is free) | **ADOPT** |
| **Dev.to** | Direct REST API | requests | N/A | Free | **ADOPT** |
| **Hacker News** | N/A | Manual only | N/A | N/A | Manual |

### Details

**PRAW (Reddit)** — The definitive Python Reddit library. 128K weekly downloads, 190+ contributors. Handles rate limits automatically. Posting is one line: `reddit.subreddit("test").submit("Title", selftext="body")`. Install: `pip install praw`.

**Tweepy (Twitter/X)** — Gold standard for official X API. v2 API support, OAuth 2.0, media upload, threading. X's free tier allows 500 posts/month (sufficient for our volume). Basic tier is $200/mo if needed. Install: `pip install tweepy`.

**Twikit (Twitter/X alt)** — Uses Twitter's internal web API via scraping. No API key needed. Risk: violates ToS, could result in account suspension. Use only for read/research, not business account posting.

**atproto SDK (Bluesky)** — Official community Python SDK for AT Protocol. 4 lines to post. Bluesky's API is completely free with no rate-limit tiers. Pre-1.0 but actively maintained. Install: `pip install atproto`.

**Dev.to REST API** — Simple enough that no wrapper is needed. `POST /api/articles` with API key header and JSON body. 10 lines of Python.

**Hacker News** — No posting API exists. Read-only API for monitoring (Algolia search). Only way to post is manual browser submission or fragile web scraping (not recommended).

### Immediate Action Items

1. `pip install praw` — replace any custom Reddit scripts
2. `pip install tweepy` — replace any custom Twitter/X scripts
3. `pip install atproto` — replace any custom Bluesky scripts
4. Keep dev.to as simple REST calls (already lightweight enough)
5. Accept HN as manual-only

---

## Q4: Cross-Platform Scheduling Tools

### Self-Hosted / Open-Source

| Tool | X | Reddit | Bluesky | dev.to | Free | Stars | Rec |
|------|---|--------|---------|--------|------|-------|-----|
| **Postiz** | Yes | Yes | Yes | Yes (DEV) | Yes (self-hosted) | 26,714 | **ADOPT** |
| Mixpost Lite | Yes | No | No | No | Yes | ~2K | SKIP |
| Bulkit.dev | Yes | No | No | No | Yes | Small | SKIP |
| Socioboard | Yes | No | No | No | Yes | ~1K | SKIP |

### SaaS (Free Tiers)

| Tool | X | Reddit | Bluesky | dev.to | Free Limit | Rec |
|------|---|--------|---------|--------|------------|-----|
| Buffer | Yes | No | Yes | No | 3ch/10 queued | SKIP |
| Late.dev | Yes | Yes | Yes | No | 20 posts/mo | EVALUATE |
| Ayrshare | Yes | Yes | No | No | 20 posts/mo | SKIP |
| SocialChamp | Yes | No | Yes | No | 15 posts | SKIP |
| Hootsuite | Yes | No | No | No | No free tier | SKIP |

### Winner: Postiz (Self-Hosted)

**Why Postiz wins decisively:**
1. **Only tool that supports all our platforms** — X/Twitter, Reddit, Bluesky, AND dev.to
2. **Fully free** when self-hosted — no post limits, no channel limits, no branding
3. **AI agent CLI** (`postiz-agent`) — purpose-built for Claude-like agents to schedule programmatically
4. **Docker Compose deploy** — 2GB RAM minimum, runs alongside existing infrastructure
5. **26K+ GitHub stars** — massive community, actively maintained (updated Feb 2026)
6. **Built-in features** — visual calendar, analytics, AI content generation, recurring posts, RSS auto-posting

**Postiz Agent CLI** is particularly relevant — it's designed for exactly our use case: AI agents scheduling and publishing content programmatically via command line.

### The HN Problem

No tool supports automated HN posting. HN intentionally provides no write API. This is a hard constraint. HN posts must remain manual regardless of tooling choice.

---

## Strategic Recommendations Summary

### Tier 1: Adopt Now (High confidence, clear value)

| Tool | Replaces | Action |
|------|----------|--------|
| **PRAW** | Custom Reddit curl/scripts | `pip install praw` |
| **Tweepy** | Custom Twitter/X scripts | `pip install tweepy` |
| **atproto** | Custom Bluesky scripts | `pip install atproto` |
| **Dev.to REST API** | Custom dev.to scripts | Keep simple, use `requests` |

### Tier 2: Evaluate (Strong candidate, needs validation)

| Tool | What For | Next Step |
|------|----------|-----------|
| **Postiz (self-hosted)** | Unified scheduling + calendar | Deploy test instance, validate platform integrations |
| **Postiz Agent CLI** | AI-driven post scheduling | Test with Postiz instance |
| **Custom Claude Code skills** | `/publish`, `/draft-post` workflows | Build once @growth is operational |

### Tier 3: Skip (Insufficient for our needs)

| Tool | Why Skip |
|------|----------|
| Buffer, Later, Hootsuite | Missing Reddit/dev.to, restrictive free tiers |
| Mixpost, Bulkit, Socioboard | Missing critical platforms |
| Ayrshare, SocialChamp | Too restrictive or too expensive |
| Individual MCP servers for posting | Fragmented; Postiz is better unified solution |

### Hard Constraints (No tool solves these)

- **Hacker News posting** — No write API exists. Manual only. Forever.
- **Reddit automated posting** — PRAW supports it, but Reddit's API terms are restrictive. Needs careful rate limiting and authentic engagement (not just broadcast).

---

*Research completed 2026-02-20. Sources: 50+ tools evaluated across MCP registries (mcp.so, smithery.ai, glama.ai), GitHub, PyPI, SaaS pricing pages, and Claude Code documentation.*
