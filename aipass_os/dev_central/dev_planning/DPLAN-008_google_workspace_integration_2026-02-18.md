# DPLAN-008: Google Workspace Integration

> Connect AIPass to Google Workspace (Gmail, Calendar, Docs, Sheets) via APIs — real-world connectivity without bypassing internal systems.

## Vision

AIPass currently lives in a closed loop — ai_mail, drone, dispatch are all internal. Google Workspace becomes the **external bridge**. Not replacing anything — complementing. Agents don't need visuals, they need data. Gmail API delivers structured notifications directly to ai_mail. No browser automation, no MCP navigation, just data in → data out.

Patrick owns aipass.ai. Google Workspace on that domain gives professional external presence + API access to the full suite.

## Patrick's Direction (seed idea)

- "Google ecosystem. I will pay for this."
- "Calendar, emails, docs, sheets, all the above. Using the pipeline."
- "Not bypassing our internal systems, but complement them."
- "Like having the roadmap scheduled out for my visibility."
- "Agents communications with external contacts, in email."
- "ai_mail is far superior for AI system comms, that won't change."
- "Gmail notification going to ai_mail direct to the AI."
- "Agents don't need visuals, just data."
- "A good cost-effective way to get updates — like dev.to post notifications will just show as new inbox in ai_mail."

## Core Principle

**Google = external layer. ai_mail = internal nervous system.** An adapter sits between them — translates in both directions. Internal comms never touch Google. External comms never bypass ai_mail. Both systems do what they're best at.

## Current State

**What exists:**
- aipass.ai domain (Patrick owns it)
- ai_mail system (mature, reliable for internal comms)
- Dispatch daemon (polls inboxes, spawns agents)
- Telegram bot (scheduler_bot — already bridges external notifications)
- @api branch (handles external API connections)

**What doesn't exist:**
- Google Workspace account on aipass.ai
- Gmail API integration
- Calendar API integration
- Any external → ai_mail bridge for email

## Use Cases (data-first, no visuals)

| External Event | Flow | Result |
|----------------|------|--------|
| dev.to comment notification | Gmail → bridge → ai_mail @growth | Agent reads, drafts response |
| GitHub issue opened | Gmail → bridge → ai_mail @vera | VERA routes to right branch |
| Customer email to hello@aipass.ai | Gmail → bridge → ai_mail @customer | Future dept handles it |
| Roadmap milestone due | Calendar API → ai_mail reminder | Patrick sees it on phone calendar |
| Agent needs to email externally | ai_mail → bridge → Gmail API → sent | Outbound through aipass.ai |
| Weekly metrics report | Agent → Sheets API → shared spreadsheet | Patrick reviews on phone |

## Architecture Sketch

```
External World                    AIPass Internal
─────────────                    ───────────────
Gmail (aipass.ai)  ──┐
Calendar           ──┤── Gmail/Calendar API ── bridge.py ── ai_mail
Docs/Sheets        ──┘                         (adapter)
                                                  │
dev.to notifications ─── Gmail ─────────────────┘
GitHub notifications ─── Gmail ─────────────────┘
```

**bridge.py pattern:** Same as daemon.py — poll-based, lightweight, runs alongside dispatch daemon. Checks Gmail API every N minutes for new emails, converts to ai_mail messages, routes by sender/subject rules.

## What Needs Building

- [ ] Set up Google Workspace on aipass.ai (Patrick — manual, paid)
- [ ] Gmail API credentials (OAuth2, service account)
- [ ] Gmail → ai_mail bridge (poll Gmail, create ai_mail messages)
- [ ] ai_mail → Gmail bridge (outbound: agent drafts → Gmail sends)
- [ ] Calendar API integration (read/write events)
- [ ] Routing rules (which Gmail → which ai_mail branch)
- [ ] Approval flow for outbound emails (agents draft, Patrick/VERA approves before send)

## Design Decisions

| Decision | Options | Leaning | Notes |
|----------|---------|---------|-------|
| Gmail polling | API poll / Push (Pub/Sub) / Webhook | API poll | Start simple like daemon, upgrade later |
| Outbound approval | Auto-send / Draft + approve / Always approve | Draft + approve | Safety first for external comms |
| Bridge location | @api branch / New @integrations branch / Standalone | @api branch | They own external API connections |
| Calendar sync | One-way (read) / Two-way (read+write) | Two-way | Agents should create events too |
| Cost | Workspace Starter ($7/mo) / Business Standard ($14/mo) | Starter | Enough for APIs + custom domain email |

## Ideas

- **Notification classifier:** Incoming Gmail gets classified (support, notification, spam, personal) and routed to the right branch automatically
- **Email templates:** Brand-consistent outbound emails with aipass.ai signature
- **Shared Drive:** Replace git-based doc sharing with Google Drive for non-code deliverables
- **Sheets dashboard:** Live metrics dashboard Patrick can check from phone — stars, followers, engagement, agent activity
- **Calendar-driven sprints:** OKR cycles auto-created as calendar events, deadlines visible on Patrick's phone

## Relationships

- **Related DPLANs:** DPLAN-007 (business restructuring — external comms is a department need)
- **Related FPLANs:** None yet
- **Owner branches:** @api (API integration), @vera (business routing), @dev_central (coordination)

## Status

- [x] Planning (seed idea captured)
- [ ] In Progress
- [ ] Ready for Execution
- [ ] Complete
- [ ] Abandoned

## Notes

- This is a seed idea — captured early, developed when ready
- Google Workspace setup is a Patrick action (paid account, domain verification)
- Technical build is straightforward once workspace exists — Gmail API is well-documented
- The Telegram bot bridge (scheduler_bot) is a precedent — same pattern, different platform
- Agents don't need visuals, just data. APIs beat browser automation every time.
- aipass.ai domain makes this professional — real email addresses, real calendar, real docs

---
*Created: 2026-02-18*
*Updated: 2026-02-18*
