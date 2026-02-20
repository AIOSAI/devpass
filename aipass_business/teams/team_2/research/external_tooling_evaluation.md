# External Tooling for Business — Technical Evaluation

**Author:** TEAM_2
**Date:** 2026-02-20
**Requested by:** VERA (dispatch cb638845, origin: Patrick via DEV_CENTRAL)
**Status:** Complete

---

## 1. MCP Server Installation & Configuration

### How MCP Works in Our Environment

MCP (Model Context Protocol) servers are external processes that expose tools, resources, and prompts to Claude Code via a standardized protocol. Claude discovers and invokes them during sessions.

### Three Configuration Scopes

| Scope | Location | Visibility | Use Case |
|-------|----------|------------|----------|
| **Local** | `~/.claude.json` (per-project section) | You only, this project | Personal/experimental servers |
| **Project** | `.mcp.json` in project root | Everyone (version-controlled) | Shared team tools |
| **User** | `~/.claude.json` (global section) | You only, all projects | Personal utilities |

Precedence: Local > Project > User.

### What Already Exists in AIPass

We already have MCP infrastructure via the `@mcp_servers` branch:

- **Global config** at `/home/aipass/.mcp.json` — 4 servers configured (serena, context7, playwright, sequential-thinking)
- **All 4 currently disabled** at project level in `~/.claude.json`
- **Plugin marketplace** has 13 installable MCP plugins (asana, github, gitlab, slack, stripe, etc.)
- **Reference servers** at `/home/aipass/mcp_servers/servers/src/` (filesystem, git, memory, fetch, etc.)

### Adding/Removing Servers

```bash
# Add HTTP server
claude mcp add --transport http myserver https://example.com/mcp

# Add local stdio server
claude mcp add --transport stdio myserver -- python3 /path/to/server.py

# List / remove
claude mcp list
claude mcp remove myserver

# Check status inside session
/mcp
```

### Config Format

```json
{
  "mcpServers": {
    "my-server": {
      "type": "stdio",
      "command": "python3",
      "args": ["/path/to/server.py"],
      "env": { "API_KEY": "xxx" }
    }
  }
}
```

Supports: stdio (local process), HTTP (remote), SSE (deprecated), OAuth.

---

## 2. Custom MCP Servers

### SDK Support

Official SDKs exist for **Python**, **TypeScript**, **Java**, **Kotlin**, **C#**, and **Rust**.

For us: **Python (FastMCP)** is the obvious choice.

```bash
pip install "mcp[cli]"
```

### Minimal Custom Server (Python)

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("content-manager")

@mcp.tool()
async def post_to_platform(platform: str, content: str, draft: bool = True) -> str:
    """Post content to a social platform."""
    # call our existing handlers
    return f"Posted to {platform}"

def main():
    mcp.run(transport="stdio")
```

Register: `claude mcp add --transport stdio content-mgr -- python3 /path/to/server.py`

### Can Branches Have Their Own MCP Servers?

**Yes.** Each directory can have its own `.mcp.json`. A VERA-specific `.mcp.json` would make its tools available only when working in the VERA directory. This already works — `/home/aipass/mcp_servers/.mcp.json` is a branch-specific config.

### Content Management MCP Server for VERA

Entirely feasible. Could wrap our existing handlers (post_devto.py, post_bluesky.py, post_twitter.py) into MCP tools, then add scheduling, analytics, content calendar capabilities. Claude would be able to call `post_to_bluesky("text")` as a native tool during any session.

**Verdict:** Worth building eventually, but not urgent. Our handlers work. MCP wrapper adds convenience for agent-driven posting but doesn't unlock new capabilities yet.

---

## 3. Claude Code Skills System

### What Skills Are

Skills are reusable instructions/workflows invoked via `/skill-name` slash commands or auto-loaded by Claude when relevant. They replaced the older `.claude/commands/` system.

### File Format

```
.claude/skills/my-skill/
  SKILL.md           # Required — instructions + frontmatter
  templates/         # Optional — supporting files
  scripts/           # Optional — executable scripts
```

SKILL.md frontmatter:
```yaml
---
name: my-skill
description: What this does
user-invocable: true        # Show in / menu
disable-model-invocation: true  # Prevent auto-loading
allowed-tools: Bash, Read   # Restrict available tools
context: fork               # Run in isolated subagent
---
Instructions here. Use $ARGUMENTS for passed args.
```

### What We Have

- **2 legacy commands**: `/docs` and `/updateall` at `~/.claude/commands/`
- **No global skills directory** — `~/.claude/skills/` doesn't exist yet
- **Heavy hooks usage** — 6 UserPromptSubmit hooks, PostToolUse, PreToolUse, Stop, Notification, PreCompact

### Branch-Specific Skills

Natively supported. If `/home/aipass/aipass_business/vera/.claude/skills/post/SKILL.md` existed, `/post` would be available when working in VERA's directory. Nested discovery is automatic.

### Potential Skills for AIPass

| Branch | Skill | Purpose |
|--------|-------|---------|
| VERA | `/post` | Content posting workflow (platform, draft/publish) |
| VERA | `/schedule` | Content calendar management |
| Any | `/startup` | Standardized session initialization |
| Any | `/dispatch` | Streamlined dispatch email sending |

**Verdict:** Skills are strictly more powerful than our legacy commands. Migration is backward-compatible. Branch-specific skills are a natural fit for our architecture. Low effort, high value.

---

## 4. Build vs Use Evaluation Matrix

### Our Current Handlers

| Handler | Location | Lines | Library | Capabilities |
|---------|----------|-------|---------|-------------|
| post_devto.py | vera/apps/handlers/ | 58 | urllib (stdlib) | Post articles, tags, draft/publish |
| post_bluesky.py | vera/apps/handlers/ | 41 | atproto | Post text, returns URL |
| post_twitter.py | vera/apps/handlers/ | 42 | tweepy | Post tweets, returns URL |

### Platform-by-Platform Evaluation

#### Dev.to

| Aspect | Current | Alternative | Assessment |
|--------|---------|------------|------------|
| **Our handler** | post_devto.py (58 lines) | — | Simple, works, stdlib only |
| **MCP server** | — | nickytonline/dev-to-mcp | Read-only, no write support |
| **Best alternative** | — | Raw Forem REST API (what we already use) | Same approach |
| **Effort to migrate** | — | N/A | No benefit to migration |
| **Capability delta** | — | MCP adds content discovery, tag search | Nice but not needed |
| **Recommendation** | **KEEP CUSTOM** | Our handler is 58 lines of stdlib. It works. MCP server can't even write. No reason to change. |

#### Twitter/X

| Aspect | Current | Alternative | Assessment |
|--------|---------|------------|------------|
| **Our handler** | post_twitter.py (42 lines) | — | Simple tweepy wrapper |
| **MCP server** | — | taazkareem/twitter-mcp-server | Full-featured (threads, media, search) |
| **Best alternative** | — | twitter-api-v2 library | Similar to tweepy |
| **Effort to migrate** | — | Medium (configure MCP, test auth) | |
| **Capability delta** | — | MCP adds threads, media, search, analytics | Significant |
| **Blocker** | **API credits — currently getting 402 errors** | Same issue regardless of tooling | |
| **Recommendation** | **KEEP CUSTOM (blocked)** | API cost is the blocker ($100/mo Basic tier), not tooling. Fix credits first. Evaluate MCP later for thread support. |

#### Bluesky

| Aspect | Current | Alternative | Assessment |
|--------|---------|------------|------------|
| **Our handler** | post_bluesky.py (41 lines) | — | Text-only, basic |
| **MCP server** | — | cameronrye/atproto-mcp | 30+ tools, images, threads, analytics |
| **Best alternative** | — | atproto SDK (same lib we use) | More features available |
| **Effort to migrate** | — | Low (pip install, add .mcp.json) | |
| **Capability delta** | — | MCP adds images, threads, feed management, search, analytics | Major |
| **Recommendation** | **ADOPT MCP** | Best MCP ecosystem of all platforms. Free API, mature server, 30+ tools. Our handler is text-only. MCP gives us threads, images, analytics with zero custom code. Best ROI. |

#### Reddit

| Aspect | Current | Alternative | Assessment |
|--------|---------|------------|------------|
| **Our handler** | None (manual posting) | — | Content drafted, posted by hand |
| **MCP server** | — | jordanburke/reddit-mcp-server | Write support, early maturity |
| **Best alternative** | — | **PRAW** (Python Reddit API Wrapper) | Gold standard, battle-tested |
| **Effort to build** | — | Low-Medium (PRAW handler ~50 lines) | |
| **Recommendation** | **BUILD HANDLER (PRAW)** | PRAW is the industry standard — handles auth, rate limiting, retries automatically. More reliable than any Reddit MCP server. Build a post_reddit.py handler like our other three. ~50 lines. |

#### Hacker News

| Aspect | Current | Alternative | Assessment |
|--------|---------|------------|------------|
| **Our handler** | None (manual posting) | — | Show HN draft prepared |
| **MCP server** | — | paabloLC/mcp-hacker-news | Read-only (top stories, search) |
| **Best alternative** | — | None — **HN has no write API** | |
| **Effort to build** | — | N/A — not possible reliably | |
| **Recommendation** | **MANUAL ONLY** | HN deliberately has no write API. Programmatic posting requires fragile form scraping that violates TOS. Plan for manual posting always. MCP useful for monitoring only. |

#### GitHub Discussions

| Aspect | Current | Alternative | Assessment |
|--------|---------|------------|------------|
| **Our handler** | None (manual or gh CLI) | — | Draft prepared |
| **MCP server** | — | github/github-mcp-server (official, 51+ tools) | Partial discussion support |
| **Best alternative** | — | **GraphQL API via `gh api graphql`** | Full CRUD, standard approach |
| **Effort to build** | — | Low (~30 lines, GraphQL mutation) | |
| **Recommendation** | **BUILD HANDLER (GraphQL)** | `gh api graphql` is the standard for Discussions. No native `gh discussion` command exists. Build a post_github_discussions.py with a simple GraphQL mutation. The official GitHub MCP server is great for broader GitHub ops but discussion CRUD is still limited. |

### Summary Matrix

| Platform | Current State | Recommendation | Priority | Effort |
|----------|--------------|----------------|----------|--------|
| Dev.to | Handler exists | **Keep custom** | — | None |
| Twitter/X | Handler exists (blocked) | **Keep custom** (fix API credits first) | Low | None |
| Bluesky | Handler exists (basic) | **Adopt MCP** (atproto-mcp) | High | Low |
| Reddit | No handler | **Build handler** (PRAW) | High | Low-Medium |
| Hacker News | No handler | **Manual only** (no write API) | — | None |
| GitHub Discussions | No handler | **Build handler** (GraphQL) | Medium | Low |

---

## 5. Integration Architecture (MCP + Dispatch Daemon)

### How MCP Fits Our Architecture

MCP servers run as child processes of Claude Code. When the dispatch daemon spawns a Claude session via `claude -c -p`, that session inherits MCP server configuration from:
1. `~/.claude.json` (user scope)
2. `.mcp.json` in the working directory (project scope)

This means: **if VERA's directory has a `.mcp.json` with a content-posting MCP server, every dispatch-spawned session in VERA automatically gets posting tools.**

### Dispatch → MCP Flow

```
dispatch_daemon.py
  └─ spawns: claude -c -p "Check inbox for task"
       └─ working dir: /home/aipass/aipass_business/vera/
            └─ discovers: vera/.mcp.json
                 └─ starts: content-mgr MCP server
                      └─ Claude can call: post_to_bluesky(), schedule_post(), etc.
```

### Key Insight

MCP tools become available as native Claude tools — Claude can call them without scripts, without `python3 handler.py` invocations, without file I/O. The agent just says "post this to Bluesky" and the MCP tool handles it.

### What This Enables

1. **VERA dispatches to herself**: "Post Day 3 Bluesky follow-up" → dispatch daemon wakes VERA → VERA reads content → calls MCP tool `post_to_bluesky()` → done. No human in the loop.
2. **Content scheduling**: MCP server could maintain a schedule.json and post at the right time via cron + dispatch.
3. **Analytics collection**: MCP tools for fetching engagement metrics → VERA reviews performance autonomously.

### What It Doesn't Change

- Dispatch daemon doesn't need modification — it spawns Claude sessions, not MCP servers
- MCP servers start/stop with Claude sessions automatically
- Safety rails (kill switch, per-branch limits, max turns) still apply
- Cross-branch protocol unchanged — MCP tools are per-session, not system-wide

### Recommended Architecture

```
Phase 1 (Now):     Keep handlers, build Reddit + GitHub Discussions handlers
Phase 2 (Soon):    Install atproto-mcp for Bluesky, evaluate in practice
Phase 3 (Later):   Wrap all handlers into unified content-mgr MCP server
                   Add scheduling + analytics tools
                   Deploy as VERA's project-scoped .mcp.json
```

---

## Appendix: Skills Opportunity

Independent of MCP, the skills system offers quick wins:

| Skill | What It Does | Effort |
|-------|-------------|--------|
| `/post` | Guided posting workflow — picks platform, loads content, confirms, posts | 1 SKILL.md file |
| `/launch-status` | Shows current launch schedule, what's posted, what's next | 1 SKILL.md file |
| `/dispatch` | Streamlined dispatch email template | 1 SKILL.md file |

These are complementary to MCP — skills provide workflow instructions, MCP provides tool access.

---

*Research based on 4 parallel agent deployments: MCP installation, skills system, existing handlers audit, platform MCP ecosystem survey.*
