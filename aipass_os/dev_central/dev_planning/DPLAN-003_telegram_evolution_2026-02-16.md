# DPLAN-003: Telegram Evolution

> Telegram as the primary mobile command center for AIPass - from chat to full operations dashboard

## Vision

Telegram evolves beyond 2-way chat into Patrick's primary mobile interface for the entire AIPass ecosystem. Monitor system health, view files, manage branches, receive digests - all from the phone. The goal: Patrick can manage AIPass from anywhere in the world with just Telegram.

## Current State

**What's built and working:**
- Bridge v4.5.0: 2-way chat with @branch routing + sticky sessions
- telegram_standards.py: shared commands across all bots (/help, /welcome, /status, /list, /start)
- 4 bots: @aipass_bridge_bot (main), @aipass_scheduler_bot, @aipass_assistant_bot, @aipass_test_bot
- 2-way direct chat (assistant + test): urllib polling → tmux → Stop hook response
- @branch prefix on responses (v1.0.5) - always know who you're talking to
- Image/document support (bridge downloads, injects file path into prompt)
- Stop hook response delivery (telegram_response.py v1.0.4 with retry + flush race handling)
- Cron integration: heartbeat (*/30), wake-up (:15/:45), Telegram notifications for all cron events
- Config-driven handler (direct_chat.py) - adding new chat bots = one thin launcher file

**Known issues (from dev.local.md):**
- "Processing..." no visibility - can't tell if Claude is working or stuck
- Message drops on longer responses (intermittent)
- Image upload path handling needs verification

## What Needs Building

### Visibility & Monitoring
- [ ] **Typing indicator as heartbeat** - `sendChatAction(typing)` every ~5s in a loop while Claude processes. Double purpose: (1) UX feedback that Claude is working, (2) crash detection - if typing stops but no response arrives, Claude died. Bridge starts loop after message injection, checks PID/tmux alive each cycle. Stop hook fires → loop ends. Process dies → loop ends naturally. Patrick sees: typing = working, typing stops + response = done, typing stops + no response = crashed (resend or "continue"). Currently zero visibility from phone.
- [ ] **Prax monitoring via Telegram** - `/prax` or `/monitor` shows system health, active branches, recent errors
- [ ] **Dashboard command** - `/dashboard` pushes DASHBOARD.local.json summary
- [ ] **Morning digest** - Auto-push: "3 branches completed overnight, 2 errors auto-healed, inbox has 4 items"
- [ ] **Error digest batching** - Aggregate errors into single Telegram message instead of 7 separate emails
- [ ] **Live progress streaming** - Poll tmux buffer, send condensed status as Claude works (highest impact)

### Proactive Outreach (Claude → Patrick)
- [ ] **Branch-initiated messages** - Branches can SEND to Patrick on Telegram proactively
- [ ] **Completion notifications** - "FPLAN-0345 complete. 4 phases, 98% Seed. Want a summary?"
- [ ] **Decision requests** - "Found 3 issues: 2 easy, 1 needs your call. Handle the easy ones?"
- [ ] **Scheduled reports** - Weekly system health summary, pushed at a chosen time

### Commands & Controls
- [ ] **Stop/cancel processing** - `/stop` sends Ctrl+C to tmux session, interrupts Claude mid-processing. Bridge intercepts before injection. Extensions: `/clear` (stop + discard), `/redo "new msg"` (stop + resend corrected). Critical UX when Patrick catches a typo or changes mind mid-message.
- [ ] **`/recap` - Session reconnect** - On demand summary: which @branch you're talking to, session uptime, last few exchanges, any pending work. Perfect for reconnecting after being away. Patrick's favorite: "rather than asking, it's just a slash command." Could also support `/update all` to trigger full system refresh.
- [ ] **`/brief` / `/casual` mode** - Toggle for shorter, conversational responses. Mood-dependent - sometimes Patrick wants detail, sometimes "ugg that's long." Implementation: bridge sets a flag, system prompt gets "respond briefly, mobile-friendly" injected. `/brief` toggles on/off, `/casual` as alias.
- [ ] **Inline @branch keyboard** - Telegram inline buttons for quick branch switching. Tap a button instead of typing `@api`. The @ symbol stays as the visual breadcrumb - consistent across the whole system. Shows active branches as button row below messages.
- [ ] **Commons via Telegram** - `/commons` shows recent posts, `/commons post "room" "title" "content"`
- [ ] **Email via Telegram** - `/inbox` shows mail count + subjects, `/view <id>` reads one
- [ ] **Plan status** - `/plans` shows active FPLANs + DPLANs
- [ ] **Branch status** - `/branches` shows which are running/idle

### UX & Polish
- [ ] **GitHub deep links** - File paths in responses auto-convert to clickable GitHub URLs. Tap on phone → opens in GitHub app. Regex in telegram_response.py: detect backticked paths or `/home/aipass/...` → convert to `[filename](https://github.com/AIOSAI/aipass/blob/main/relative/path)`. Confirmed: GitHub app deep linking works on Patrick's phone.
- [ ] **Message chunking (4096 char limit)** - Telegram caps messages at 4096 UTF-8 characters. Long responses must split intelligently - not mid-sentence, not mid-code-block. Bridge should chunk at paragraph/section boundaries. Also impacts `/brief` mode - stay well under 4096 in casual mode.
- [ ] **Markdown formatting** - Telegram supports markdown - use it for structured output
- [ ] **Delivery confirmation** - Visible indicator that message was received AND processed
- [ ] **Session indicator** - Every reply includes subtle session hash + uptime

## Design Decisions

| Decision | Options | Leaning | Notes |
|----------|---------|---------|-------|
| **Command routing** | All via bridge / Separate bots per function | **Bridge handles all** | One bot to rule them all, @branch routing already works |
| **Monitoring commands** | Build in bridge / Separate monitoring bot | **Bridge** | /prax, /dashboard are just commands like /help |
| **Proactive messages** | bot.send_message direct / Queue system | **Direct** | Simple, Patrick's chat_id known, no queue complexity |
| **Digest format** | Plain text / Structured markdown / Mini dashboard | **Markdown** | Telegram renders markdown nicely, structured but readable |
| **Git on phone** | Build Telegram commands / GitHub app | **GitHub app** | Already works, don't rebuild |
| **Response length** | Always full / Configurable `/brief` mode | **Configurable** | Mood-dependent: sometimes detail, sometimes casual. 4096 char Telegram limit |
| **Branch switching** | Type `@branch` / Inline keyboard buttons | **Both** | Keyboard for speed, typing for flexibility. @ symbol consistent |

## Ideas

- **Quick reactions** - Patrick reacts with emoji (thumbs up/down) to approve/reject decisions without typing
- **Location-aware** - Different digest format when traveling vs at home
- **Multi-bot dashboard** - One overview showing status of all 4 bots
- **Photo analysis** - Send photo of whiteboard/sketch → Claude analyzes and captures ideas
- **`/update all`** - Trigger full system update from Telegram. Bridge intercepts, runs `drone @assistant update` or equivalent. One command to refresh everything.
- **Compaction notification** - When Claude auto-compacts mid-conversation, send a Telegram message: "Context compacted - working from summary now." Gives Patrick visibility into why tone/flow suddenly shifts. Without this, it just feels like Claude got lost.

**Already solved naturally (no build needed):**
- Voice-to-text: Patrick's phone keyboard + Telegram's built-in voice handle this already
- Multi-message batching: Patrick types ~100wpm on phone, not needed
- Offline message queue: Telegram naturally queues messages when offline, Patrick always sees them

## Relationships
- **Related DPLANs:** DPLAN-002 (24/7 Infrastructure - Telegram is Phase 3), DPLAN-001 (Actions - Telegram notifications for cron actions)
- **Related FPLANs:** FPLAN-0317 (Bridge v4), FPLAN-0344 (Bot Standards), FPLAN-0343 (Scheduler)
- **Owner branches:** @api (bridge.py, spawner.py), @dev_central/assistant (chat bots, cron)

## Status
- [x] Planning
- [ ] In Progress
- [ ] Ready for Execution
- [ ] Complete
- [ ] Abandoned

## Notes

### Session 105 - 2026-02-16

**Origin:** Patrick expressed strong gravitational pull toward Telegram as primary interface. "I really like Telegram with our latest upgrades, I think it's really powerful."

**Key signal:** Patrick wants Prax monitoring, more visibility, and advancement to "the next level." This isn't just chat anymore - it's becoming the mobile operations dashboard.

**Patrick's cool idea:** TBD - he mentioned having one in mind, hasn't shared yet.

**Brainstorm results (6 proposals → Patrick's feedback):**
1. Multi-message batching → Not needed (100wpm on phone + voice)
2. `/recap` → Loved it. "Rather than asking, it's just a slash command." Also sparked `/update all` idea.
3. Voice notes (Whisper) → Already solved (phone keyboard + Telegram built-in)
4. `/brief` / `/casual` → Interested. Mood-dependent. Wants Telegram char limits respected (4096).
5. Offline queue → Already works naturally in Telegram
6. Inline @branch keyboard → Approved. "@ symbol is a beautiful breadcrumb, consistent."

**Telegram limits confirmed:** 4096 UTF-8 characters per message (standard), 4096 for media captions (Premium).

---
*Created: 2026-02-16*
*Updated: 2026-02-16*
