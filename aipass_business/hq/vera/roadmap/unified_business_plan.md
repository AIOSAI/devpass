# AIPass Unified Business Plan
## Strategy + Technical + Identity — One Sequenced Action Plan

**Author:** VERA (CEO, AIPass Business)
**Sources:** TEAM_1 Strategy Roadmap, TEAM_2 Technical Roadmap, TEAM_3 Identity Roadmap
**Date:** 2026-02-17
**Status:** ACTIVE

---

## Executive Summary

Three teams produced three roadmaps. This document merges them into a single sequenced plan — what happens first, what depends on what, and who does each piece. The core timeline: **2 weeks to Tier 1 launch** (~March 3, 2026), followed by 90 days of community-building and validation, with a Go/No-Go decision on Tier 2 at the 90-day mark.

The plan has two tracks: **things we can do now** (no blockers) and **things waiting on Patrick** (account creation). We execute the first track immediately and queue the second.

---

## Phase 0: Foundation (Now — Days -7 to 0)

**Goal:** Everything ready for launch day. No last-minute scrambles.

### Track A: Not Blocked — Execute Immediately

| # | Task | Owner | Dependency | Deliverable |
|---|------|-------|------------|-------------|
| 1 | Expand CI pipeline — full Python matrix (3.8-3.13), multi-OS, coverage | TEAM_2 → TEAM_2_WS | None | `.github/workflows/ci.yml` (enhanced) |
| 2 | Write PyPI publish workflow (tag-triggered) | TEAM_2 → TEAM_2_WS | None | `.github/workflows/publish.yml` |
| 3 | Write security scan workflow (safety, pip-audit, CodeQL) | TEAM_2 → TEAM_2_WS | None | `.github/workflows/security.yml` |
| 4 | Write Dockerfile + docker-compose.yml for reproducible testing | TEAM_2 → TEAM_2_WS | None | `Dockerfile`, `docker-compose.yml` |
| 5 | Write integration tests for examples (Claude Code, ChatGPT, Generic) | TEAM_2 → TEAM_2_WS | None | `tests/test_examples.py` |
| 6 | Write SECURITY.md | TEAM_2 → TEAM_2_WS | None | `SECURITY.md` |
| 7 | Add coverage config to pyproject.toml | TEAM_2 → TEAM_2_WS | None | `pyproject.toml` update |
| 8 | Write issue triage + stale issue workflows | TEAM_2 → TEAM_2_WS | None | `.github/workflows/issue-triage.yml`, `stale.yml` |
| 9 | Add dependabot.yml | TEAM_2 → TEAM_2_WS | None | `.github/dependabot.yml` |
| 10 | Write docs generation workflow | TEAM_2 → TEAM_2_WS | None | `.github/workflows/docs.yml` |
| 11 | Draft Article #2: "The First Operating System for AI Agents" | TEAM_3 → TEAM_3_WS | TEAM_3 content strategy (delivered) | `public/article_2_draft.md` |
| 12 | Draft HN "Show HN" post, Reddit posts (3 subs) | TEAM_1 | Content strategy (delivered) | Launch post drafts |
| 13 | Draft X thread (6-8 tweets) | TEAM_1 | Content strategy (delivered) | Twitter thread draft |
| 14 | Draft social media bios for all platforms | TEAM_3 | Identity roadmap (delivered) | Platform bios (already in roadmap) |
| 15 | TEAM_3 review of Tier 1 repo deliverables (honesty audit) | TEAM_3 | Repo exists (done) | Review report |

### Track B: Blocked on Patrick — Queue for Human Setup

| # | Task | Why Blocked | Unblocks |
|---|------|-------------|----------|
| B1 | PyPI + TestPyPI account creation + 2FA | Requires human identity verification | Package publishing |
| B2 | Generate PyPI API tokens → GitHub Secrets | Requires authenticated session | CI/CD publish workflow |
| B3 | Create business email (ProtonMail recommended) | Phone/identity verification | Support contact, repo metadata |
| B4 | Configure aipass.ai DNS records | Registrar login | Domain, Bluesky handle, GitHub Pages |
| B5 | Create Bluesky account (@aipass.ai) | Email + DNS verification | Social presence |
| B6 | Create Twitter/X account (optional) | Phone verification | Broader reach |
| B7 | Enable GitHub Discussions on repo | Repo admin | Community Q&A |
| B8 | Enable Codecov for repo + token to Secrets | Codecov auth | Coverage reporting |
| B9 | Set up GitHub Projects board | Repo admin | Public task tracking |

**Priority order for Patrick:** B1 → B2 → B3 → B7 → B4 → B5 → B8 → B9 → B6

---

## Phase 1: Launch Week (Days 0-7)

**Target date:** ~March 3, 2026
**Goal:** Maximum visibility in a 48-hour window. Coordinated push across platforms.

| Day | Action | Platform | Owner |
|-----|--------|----------|-------|
| 0 (morning) | Tag v1.0.0 release on GitHub | GitHub | VERA coordinates |
| 0 (morning) | Publish to PyPI (if B1-B2 resolved) | PyPI | CI/CD auto |
| 0 (morning) | Submit "Show HN" post | Hacker News | TEAM_1 drafts, VERA posts |
| 0 (midday) | Publish Article #2 on Dev.to | Dev.to | TEAM_3 drafts, VERA posts |
| 0 (afternoon) | Post X thread | Twitter/X | TEAM_1 drafts, VERA posts |
| 0 (evening) | Post to r/LangChain, r/LocalLLaMA, r/artificial | Reddit | TEAM_1 drafts, VERA posts |
| 1 | Active engagement — respond to every comment | All | All teams inform, VERA responds |
| 2 | Share in LangChain + CrewAI Discords | Discord | TEAM_1 |
| 3-5 | First-time contributor support, issue responses | GitHub | All teams |
| 6-7 | Write "Week 1 retrospective" for Dev.to | Dev.to | TEAM_3 drafts |

**Quality gate:** ALL public content passes TEAM_3's pre-publication checklist before going live:
- Honesty gate (zero forbidden words, cited evidence, limitations stated)
- Voice gate (AI slop detector — 0/10 signals)
- Technical gate (code tested, paths anonymized, links verified)

---

## Phase 2: Growth (Days 8-30)

**Goal:** Sustained engagement. First integrations. Community formation.

| Week | Action | Owner |
|------|--------|-------|
| 2 | Publish tutorial: "Add Trinity to Your Agent in 5 Minutes" | TEAM_3 drafts, TEAM_2 validates code |
| 2 | Cross-post to Hugging Face community | TEAM_1 |
| 3 | Publish tutorial: "Trinity + CrewAI: Agents That Remember" | TEAM_3 drafts, TEAM_2 validates code |
| 3 | Engage AI YouTube creators for coverage | TEAM_1 research, VERA outreach |
| 4 | Submit NIST comment (April 2 deadline) | TEAM_1 drafts, TEAM_2 validates technical claims, TEAM_3 honesty audit |
| 4 | Publish "Month 1 Metrics" transparency post | TEAM_1 data, TEAM_3 drafts |

**30-Day KPIs:**

| Metric | Target | How Measured |
|--------|--------|-------------|
| GitHub stars | 100+ | GitHub API |
| PyPI installs | 500+ | PyPI stats |
| Dev.to Article #2 engagement | 2x Article #1 | Dev.to analytics |
| External contributions | 1+ PR or issue | GitHub |
| Social mentions | 5+ | Manual tracking / alerts |
| Community joins | 50+ | Discord/GitHub Discussions |

---

## Phase 3: Community Building (Days 30-90)

**Goal:** Self-sustaining community. Demand signal for Tier 2.

| Month | Action | Owner |
|-------|--------|-------|
| 2 | Launch Discord community (if not already) | VERA coordinates, TEAM_1 moderates |
| 2 | First community call / AMA | VERA hosts (text-based) |
| 2 | TypeScript implementation guide (or support contributor) | TEAM_2 specs, community builds |
| 3 | NVIDIA GTC context (March 16-19) — share if relevant | TEAM_1 monitors |
| 3 | Publish Tier 2 interest survey | TEAM_1 designs, VERA distributes |
| 3 | "90-day report" — transparent metrics, lessons, roadmap update | All teams contribute, VERA synthesizes |

**60-Day KPIs:**

| Metric | Target |
|--------|--------|
| GitHub stars | 250+ |
| PyPI installs (cumulative) | 2,000+ |
| Framework integrations | 1+ third-party |
| Blog/media mentions | 3+ independent |
| NIST comment submitted | Yes (by April 2) |
| Contributors | 5+ |

**90-Day KPIs (Go/No-Go for Tier 2):**

| Metric | Target | Decision |
|--------|--------|----------|
| GitHub stars | 500+ | Must hit |
| Community implementations | 3+ non-Python | Must hit |
| Media/blog mentions | 5+ independent | Strong signal |
| Inbound Tier 2 requests | 10+ | Critical signal |
| Discord community | 200+ | Community health |
| PyPI installs (cumulative) | 5,000+ | Adoption curve |

**Go decision:** Proceed to Tier 2 (hosted memory lifecycle) if stars, implementations, and inbound requests all meet targets.
**No-Go decision:** Iterate on Tier 1 packaging, documentation, community engagement. Do NOT invest in Tier 2 infra without demand proof.

---

## Phase 4: Revenue Path (Months 3-24)

**Recommended sequence (from TEAM_1 analysis):**

| Phase | Timeline | Revenue Path | Target |
|-------|----------|-------------|--------|
| 1 | Months 1-3 | None (free, build community) | 500 stars, 5K installs |
| 2 | Months 3-6 | Consulting (opportunistic, inbound-only) | $5K-15K validation |
| 3 | Months 6-12 | Open-core hosted service MVP (Tier 2) | $1K-5K MRR |
| 4 | Months 12-24 | Hosted + enterprise licensing | $10K-30K MRR |

**Revenue model:** Open-core. Free spec (Trinity Pattern) + paid hosted infrastructure (memory lifecycle, rollover, vector search, templates, API, SLA).

**Pricing targets:**
- Individual developers: $29-99/month
- Teams: $299-999/month
- Enterprise: $5K-50K/year

**Critical constraint:** Patrick is a single developer. Revenue paths must be self-serve (no sales team, no outbound). Consulting is inbound-only.

---

## Project Management

**Methodology:** Kanban (not Scrum). WIP limit: 2 per team.
**Flow:** Inbox → Investigating → Building → Review → Done

**Public tracking:** GitHub Projects board (Kanban columns: Backlog → Planned → In Progress → In Review → Done)
**Internal tracking:** Flow Plans + AI Mail + VERA Dashboard

**Meeting cadence (all async):**

| Meeting | Frequency | Format |
|---------|-----------|--------|
| VERA Weekly Brief | Weekly | AI Mail to all teams |
| Team Status | Weekly | Commons post or AI Mail |
| Metrics Review | Bi-weekly | Shared dashboard |
| Retrospective | Monthly | Commons thread |
| Patrick Sync | As needed | Direct |

---

## Dependency Map

```
Phase 0 (Track A) ──→ Phase 1 (Launch)
                          │
Patrick (Track B) ──→ Phase 1 (Launch)
                          │
                     Phase 2 (Growth)
                          │
                     Phase 3 (Community)
                          │
                     Go/No-Go Decision
                          │
                    ┌─────┴─────┐
                    │           │
                   GO        NO-GO
                    │           │
              Phase 4       Iterate
           (Tier 2 Build)   (Tier 1)
```

**Hard dependencies:**
- PyPI publishing requires Patrick's account setup (B1, B2)
- Launch day requires ALL Phase 0 Track A items complete
- NIST comment requires draft by ~March 25 (April 2 deadline)
- Tier 2 Go/No-Go requires 90 days of data

**No dependencies (can start anytime):**
- CI/CD expansion
- Docker setup
- Article drafting
- Social media content preparation
- Integration tests

---

## Key Dates

| Date | Milestone |
|------|-----------|
| 2026-02-17 | Unified business plan complete (this document) |
| ~2026-03-03 | Tier 1 launch target |
| 2026-03-16-19 | NVIDIA GTC (context opportunity) |
| 2026-04-02 | NIST agent identity comment deadline |
| ~2026-06-03 | 90-day review — Tier 2 Go/No-Go |
| ~2026-09-03 | Tier 2 MVP target (if Go) |

---

## Risk-Adjusted Scenarios

| Scenario | 30-Day | 90-Day | Action |
|----------|--------|--------|--------|
| Pessimistic (bottom 25%) | 30 stars, 150 installs | 150 stars, 1,500 installs | Iterate on Tier 1, do not build Tier 2 |
| Base (expected) | 100 stars, 500 installs | 500 stars, 5,000 installs | Proceed to Tier 2 |
| Optimistic (top 25%) | 500+ stars, 2,000+ installs | 2,000+ stars, 15,000+ installs | Accelerate Tier 2, consider fundraising |

---

## Quality Standards (Applied to Everything)

All public output — code, content, responses, social posts — passes TEAM_3's triple gate:

1. **Honesty Gate:** Zero forbidden words. Every claim cited. Limitations stated. AI authorship disclosed.
2. **Voice Gate:** AI slop detector (0/10 signals). Concrete numbers over adjectives. Patrick's vocabulary.
3. **Technical Gate:** Code tested. Paths anonymized. Links verified.

Review chain: Author → TEAM_3 audit → VERA review → Patrick approval (for external publication).

---

*Synthesized by VERA from TEAM_1 Strategy Roadmap, TEAM_2 Technical Roadmap, TEAM_3 Identity Roadmap.*
*Three brains, one plan. Code is truth.*
