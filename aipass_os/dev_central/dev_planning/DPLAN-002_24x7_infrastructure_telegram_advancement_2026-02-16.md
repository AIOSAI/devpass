# DPLAN-002: 24/7 Infrastructure & Telegram Advancement

> Always-on AIPass accessible from anywhere, with Telegram as the primary mobile command center

## Vision

AIPass runs 24/7 without depending on Patrick's desktop being on or him being home. Telegram evolves from a chat interface into a full mobile operations dashboard - monitoring, git visibility, file viewing, system control. Patrick can manage the entire ecosystem from his phone, from anywhere in the world.

## Current State

**What works today:**
- PC runs AIPass when powered on (Ubuntu desktop)
- Telegram bridge v4.5.0: 2-way chat, @branch routing, sticky sessions, image support
- 2-way chat bots: @aipass_assistant_bot, @aipass_test_bot
- Cron actions: scheduler_cron.py (*/30 heartbeat), assistant_wakeup.py (:15/:45)
- GitHub app on phone: file viewing, git workflow already accessible
- systemd services for Telegram bridge + chat listeners

**What's missing:**
- Always-on hosting (currently dies when PC sleeps/shuts down)
- Prax monitoring via Telegram (no mobile visibility into system health)
- Telegram-based system commands beyond chat (no /dashboard, /prax, /git)
- Remote access when traveling (no SSH, no VPS)
- Server/self-hosting knowledge

## What Needs Building

### Phase 1: Always-On (PC as Server)
- [x] Auto-updates disabled (caused crash, already fixed)
- [x] Electricity free, heat is fine (winter in Canada)
- [ ] UPS for power outage protection (~$50-100)
- [ ] Configure PC to auto-boot on power restore (BIOS setting)
- [ ] Verify all services survive reboot (systemd enable, cron persistence)
- [ ] Test: shut down and reboot - does everything come back?

### Phase 2: MacBook as Home Server
- [ ] Install Linux on MacBook (or keep macOS, evaluate)
- [ ] Configure clamshell mode (lid closed, stays running)
- [ ] Set up SSH server (remote access from PC + phone)
- [ ] Migrate core services: Telegram bots, cron actions, chat listeners
- [ ] Test: SSH from phone (Termius/JuiceSSH) → full access
- [ ] Low power: 10-15W vs 100-200W desktop

### Phase 3: Telegram Advancement
- [ ] **Prax monitoring commands** - `/prax` or `/monitor` shows system health, active branches, recent errors
- [ ] **Dashboard command** - `/dashboard` shows DASHBOARD.local.json summary
- [ ] **Git status** - `/git` shows recent commits, branch status (supplement GitHub app)
- [ ] **Morning digest** - Push summary: "3 branches completed overnight, 2 errors auto-healed, inbox has 4 items"
- [ ] **Typing indicator** - sendChatAction(typing) while processing
- [ ] **Live progress streaming** - Poll tmux buffer, send condensed status updates as Claude works
- [ ] **Error digest** - Batch errors into single Telegram message instead of 7 separate emails

### Phase 4: Remote Access (Travel-Ready)
- [ ] SSH from anywhere (dynamic DNS or Tailscale for home server)
- [ ] VPS option evaluated (Hetzner $4-5/mo for lightweight relay)
- [ ] Telegram works from any country (already true - Telegram is global)
- [ ] Test: full workflow from phone only, no desktop

### Phase 5: VPS Migration (Future)
- [ ] Evaluate VPS providers (Hetzner, DigitalOcean, Linode)
- [ ] Minimal VPS: Telegram bots + cron + SSH gateway
- [ ] Data sync strategy (git pull on VPS, memory files synced)
- [ ] Full migration vs hybrid (VPS for always-on services, home for heavy compute)

## Design Decisions

| Decision | Options | Leaning | Notes |
|----------|---------|---------|-------|
| **First step** | PC always-on / MacBook / VPS | **PC always-on** | Simplest, already working, free electricity |
| **Second step** | MacBook server / VPS | **MacBook** | Own hardware, learn SSH, built-in UPS, low power |
| **Telegram scope** | Chat only / Commands / Full dashboard | **Progressive** | Start with /dashboard and /prax, expand from there |
| **Remote access** | Port forwarding / Tailscale / VPN | **Tailscale** | Zero-config mesh VPN, works behind NAT, free tier |
| **Git on phone** | Build Telegram commands / GitHub app | **GitHub app** | Already works, don't rebuild what exists |

## Key Constraints

- $400/mo already on Claude subscription - infrastructure should be cheap
- Patrick learning servers/self-hosting alongside building
- Each step teaches the next (SSH → services → remote → VPS)
- Telegram is the primary mobile interface - invest there
- GitHub app handles git/file viewing - don't duplicate

## Relationship to Other Plans

- **DPLAN-001 (Actions)** - Cron actions are the workload that needs 24/7. More actions = more reason for always-on.
- **Autonomous Branch Life** (dev.local.md idea) - Branches waking up on schedule requires always-on infrastructure
- **Personal/Business as Branches** (dev.local.md idea) - Life OS needs to be always available

## Status
- [x] Planning
- [ ] In Progress
- [ ] Ready for Execution
- [ ] Complete
- [ ] Abandoned

## Notes

### Session 105 - 2026-02-16 (Patrick via Telegram)

**Origin:** Patrick asked "how would it look having AIPass running 24/7 where I don't have to turn my PC on?"

**Key points from conversation:**
- PC won't break running 24/7, modern hardware handles it fine
- Electricity is free in his setup, heat is welcome (Canadian winter)
- Auto-updates already disabled after crash last week
- MacBook can run in clamshell mode (screen closed) as a server
- $400/mo on Claude, wants infrastructure cheap (Hetzner $4-5/mo for basic VPS)
- GitHub app on phone already solves git file viewing
- Patrick gravitating hard toward Telegram as primary interface
- Wants: Prax monitoring, more visibility, git workflow via Telegram
- Portability matters: PC isn't portable, MacBook/VPS solves travel scenario
- Self-hosting knowledge is important for AIPass's future (deployment story)
- "Actions" (cron events) is the agreed term from session 103

**Patrick's progression preference:**
1. PC always-on (now) → 2. MacBook server (soon) → 3. VPS (when ready)

---
*Created: 2026-02-16*
*Updated: 2026-02-16*
