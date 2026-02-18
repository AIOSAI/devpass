# DPLAN-006: VERA Social Media Growth Strategy

> **MERGED INTO DPLAN-007** (VERA Business Restructuring). Social media strategy is now a department concern under the broader business org structure. See DPLAN-007 for all content.

~~## Vision~~
Move from "we launched" to "we're visible and growing." VERA needs a sustained posting cadence, community engagement playbook, and follower growth plan — not just one-off launch posts.

## Current State
**What exists:**
- Launch posts live on Bluesky + dev.to
- 5 platform-specific posts written (Reddit x3, HN, Twitter) — not all posted yet
- 4-phase timeline in strategy_roadmap.md (launch → 30d → 60d → 90d)
- KPIs defined (100→250→500 GitHub stars over 90 days)
- Content sequence planned (tutorial → integration guide → metrics report)
- Posting automation for Bluesky + dev.to working

**What's missing:**
- No recurring posting schedule (event-driven only)
- No comment/reply engagement strategy
- No community interaction plan (commenting on others' posts, joining conversations)
- No follower growth tactics (hashtags, outreach, cross-posting)
- No analytics tracking
- Nothing beyond 90 days

## Open Questions (to discuss with Patrick)
- [ ] How often should VERA post? (daily? 2-3x/week? weekly?)
- [ ] Should VERA engage on other people's posts in the AI/dev community?
- [ ] What's our voice — technical thought leader? Builder sharing progress? Both?
- [ ] Do we want VERA to monitor and respond to comments autonomously via heartbeat?
- [ ] Reddit/HN — post manually or build automation?
- [ ] Newsletter/email list — worth starting early?
- [ ] Paid promotion — ever? Or purely organic?
- [ ] Should VERA cross-post GitHub activity to social? (new releases, PRs, stars milestones)

## Ideas
- **"Building in public" thread** — weekly update on what we shipped, transparent metrics
- **Comment engagement via heartbeat** — VERA checks platforms for comments during heartbeat wakes, drafts replies
- **Community participation** — VERA comments on relevant AI agent posts (not spam, genuine engagement)
- **Milestone celebrations** — auto-post when hitting star counts, install counts, contributor milestones
- **Cross-platform amplification** — dev.to article → Bluesky summary → Twitter thread → Reddit discussion
- **Hashtag strategy** — #AIAgents #OpenSource #DevTools #BuildInPublic
- **Collab posts** — reach out to other AI agent framework authors for cross-promotion

## What Needs Building (once strategy is decided)
- [ ] Content calendar with recurring cadence
- [ ] Engagement playbook (how to reply, when to engage, tone)
- [ ] Comment monitoring (check platforms for new comments)
- [ ] Analytics tracking (stars, installs, followers, engagement)
- [ ] Growth tactics execution plan

## Design Decisions

| Decision | Options | Leaning | Notes |
|----------|---------|---------|-------|
| Posting cadence | Daily / 2-3x week / Weekly | TBD | Discuss with Patrick |
| Community engagement | Passive (reply only) / Active (seek out conversations) | TBD | Active feels right but needs guidelines |
| Comment monitoring | Manual / Heartbeat automated / Separate bot | TBD | Heartbeat could work since VERA wakes every 30min |
| Analytics | Manual tracking / Dashboard / GitHub Actions | TBD | Start manual, automate later? |

## Relationships
- **Related DPLANs:** DPLAN-004 (team feedback — could inform what's working)
- **Related FPLANs:** None yet
- **Owner branches:** @vera (execution), @dev_central (strategy direction)

## Status
- [x] Planning
- [ ] In Progress
- [ ] Ready for Execution
- [ ] Complete
- [ ] Abandoned

## Notes
- Patrick: "Does vera have a posting schedule... is there a plan to engage, reply to comments, comment on other posts in the community?"
- Patrick: "We will need a strategic plan to get followers also, get noticed"
- This is a living document — add ideas as they come, refine over multiple conversations
- Twitter still blocked (402 credits) — strategy should work without it initially

---
*Created: 2026-02-18*
*Updated: 2026-02-18*
