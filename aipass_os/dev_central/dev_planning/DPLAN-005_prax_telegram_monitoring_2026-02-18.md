# DPLAN-005: Prax Telegram Monitoring

> Wire Prax Mission Control output to Telegram scheduler bot. Manual start/stop, with Telegram slash commands.

## Vision
When Patrick runs `drone @prax monitor`, it starts monitoring AND sends the same output to the Telegram scheduler bot. When he stops it, both stop. Eventually, he can start/stop monitoring directly from Telegram via slash commands (`/prax monitor`, `/drone @prax monitor`).

## Requirements (from Patrick)
1. **Mirror Prax monitor output to Telegram** — whatever shows in terminal also goes to scheduler bot
2. **Manual start/stop only** — no auto-start, no daemon. Patrick turns it on when he wants it, off when done
3. **Silent notifications** — scheduler bot messages are silent on Patrick's phone, so frequency is fine. He checks on a need-to basis
4. **Match Prax monitor format** — Telegram output should match terminal output as closely as possible
5. **Single control** — start Prax monitor = starts both terminal + Telegram. Stop = stops both
6. **Telegram slash commands (stretch goal)** — start/stop monitoring from Telegram itself: `/prax monitor` or `/drone @prax monitor`, just like terminal commands

## Architecture Notes
- **Telegram bot**: scheduler_bot (already configured at `~/.aipass/scheduler_config.json`)
- **Notifier**: `_notify_telegram()` already exists in daemon.py — similar pattern can be reused
- **Existing notifier**: `api/apps/handlers/telegram/notifier.py` has `send_telegram_notification()`
- **Prax monitor**: `drone @prax monitor` runs interactively, watches filesystem events via watchdog
- **Telegram bridge**: `api/apps/handlers/telegram/bridge.py` (v4.6.0) — already handles command routing from Telegram. Breadcrumb: this is where slash command support would plug in

## What Needs Building
- [ ] Hook Telegram notifications into Prax monitor event handlers
- [ ] When monitor starts → send "Monitoring started" to scheduler bot
- [ ] When monitor detects events → send formatted event to scheduler bot
- [ ] When monitor stops → send "Monitoring stopped" to scheduler bot
- [ ] Telegram slash command handler for `/prax monitor` start/stop (stretch)

## Collaboration
**@prax** owns the monitor — they know the event handlers, the output format, the watchdog patterns.
**@api** owns the Telegram infrastructure — they know the bot setup, the bridge, the notifier.

They need to collaborate: Prax decides WHAT to send, API decides HOW to send it.

## Design Decisions

| Decision | Options | Leaning | Notes |
|----------|---------|---------|-------|
| Notification transport | Direct API call / Import notifier / New shared util | Direct API call | Keep it simple, same pattern as daemon.py |
| Event filtering | All events / Filtered subset | Filtered | Don't spam with VSCode temp file changes |
| Telegram commands | Bridge bot / Scheduler bot | Scheduler bot | Keep it on the same bot Patrick already uses |
| Message format | Plain text / Markdown | Markdown | Match terminal formatting |

## Relationships
- **Related DPLANs:** DPLAN-004 (team feedback — separate but related visibility goal)
- **Related FPLANs:** FPLAN-0352 (daemon Telegram notifications — pattern to follow)
- **Owner branches:** @prax (monitor logic), @api (Telegram transport)

## Status
- [x] Planning
- [ ] Ready for Execution
- [ ] In Progress
- [ ] Complete
- [ ] Abandoned

## Notes
- Patrick: "scheduler msgs are silent on my end so they can come as frequent as possible"
- Patrick: "i want it i turn it on, im good i turn it off via prax"
- Patrick: "ideally i could do a slash command from scheduler in telegram to start and stop it"
- Stretch: Telegram slash commands would go through the bridge bot's command routing

---
*Created: 2026-02-18*
*Updated: 2026-02-18*
