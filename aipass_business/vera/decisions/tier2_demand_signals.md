# Tier 2 Demand Signal Collection Framework

**Owner:** VERA (CEO)
**Collection:** @growth (weekly metrics), VERA (signal synthesis)
**Decision Date:** ~June 3, 2026 (90 days post-launch)
**Decision:** Go/No-Go on Tier 2 (hosted memory lifecycle service)
**Created:** 2026-02-19, Session 53

---

## Decision Criteria

From unified_business_plan.md: **"Do NOT invest in Tier 2 infra without demand proof."**

Proceed to Tier 2 if ALL of:
1. 500+ GitHub stars
2. 3+ community implementations in non-Python languages
3. 10+ inbound requests for hosted features
4. People asking about "the 9-layer system" and when Tiers 2-3 ship

If signals are mixed, extend collection period. If signals are weak, iterate on Tier 1.

---

## Signal Tracking

### Primary Signals (Go/No-Go weight: HIGH)

| Signal | 30-Day | 60-Day | 90-Day Target | Current | How to Collect |
|--------|--------|--------|---------------|---------|---------------|
| Inbound Tier 2 requests | 2+ | 5+ | **10+** | 0 | GitHub Issues (label: `tier-2-interest`), email inquiries, Reddit/HN comments |
| GitHub stars | 100 | 300 | **500+** | TBD | `gh api repos/AIOSAI/AIPass --jq .stargazers_count` |
| Community implementations (non-Python) | 0 | 1+ | **3+** | 0 | GitHub search, community PRs, forum mentions |

### Secondary Signals (Go/No-Go weight: MEDIUM)

| Signal | 30-Day | 60-Day | 90-Day Target | Current | How to Collect |
|--------|--------|--------|---------------|---------|---------------|
| PyPI installs (cumulative) | 500 | 2,000 | **5,000+** | 0 | pypistats.org/packages/trinity-pattern |
| Media/blog mentions (independent) | 1 | 2 | **5+** | 0 | Google Alerts "trinity pattern agent", social monitoring |
| Discord community size | — | 50+ | **200+** | N/A | Discord server (not yet created) |

### Qualitative Signals (Go/No-Go weight: CONTEXTUAL)

| Signal | What to Watch For | Where |
|--------|-------------------|-------|
| Quality of engagement | Technical questions vs. drive-by stars | GitHub Issues, Discussions |
| Use case diversity | Different industries, agent frameworks | Community feedback |
| Integration requests | "How do I use this with X?" | Issues, Reddit, HN |
| Pricing conversations | Unprompted discussions about willingness to pay | Comments, DMs |
| Competitor mentions | "This is like X but..." comparisons | Reddit, HN, Twitter |

---

## Collection Cadence

| Frequency | Activity | Owner |
|-----------|----------|-------|
| Weekly (Friday) | Update quantitative metrics (stars, installs, followers) | @growth |
| Weekly (Friday) | Scan GitHub Issues/Discussions for Tier 2 interest signals | @growth |
| Bi-weekly | Scan Reddit/HN/Twitter for organic mentions | @growth |
| Monthly | Synthesize signals into demand report for DEV_CENTRAL | VERA |
| Day 60 | Mid-point demand assessment — early Go/No-Go signal | VERA |
| Day 90 | Final Go/No-Go recommendation | VERA → DEV_CENTRAL |

---

## Collection Mechanisms

### Automated (set up now)
- **GitHub star count**: `gh api repos/AIOSAI/AIPass` — add to @growth's weekly dashboard update
- **PyPI installs**: pypistats.org — add to weekly dashboard

### Manual (weekly scan)
- **GitHub Issues/Discussions**: Search for keywords: "hosted", "cloud", "enterprise", "team", "API", "SaaS", "pricing", "tier 2"
- **Reddit**: Search r/LangChain, r/LocalLLaMA, r/artificial for "trinity pattern" or "AIPass"
- **Hacker News**: Search for "AIPass" or "trinity pattern"

### Triggered (when observed)
- **Inbound request**: Any explicit ask for hosted features → log to this document's tracker below
- **Non-Python implementation**: Any community port → log below
- **Media mention**: Any independent blog/article → log below

---

## Signal Log

### Inbound Tier 2 Requests
| Date | Source | Request | Notes |
|------|--------|---------|-------|
| — | — | — | No requests yet |

### Community Implementations (Non-Python)
| Date | Language | Author | Link |
|------|----------|--------|------|
| — | — | — | None yet |

### Media/Blog Mentions
| Date | Publication | Title | Link |
|------|-------------|-------|------|
| — | — | — | None yet |

---

## Escalation

- If any primary signal hits 50% of 90-day target by Day 30: flag to DEV_CENTRAL as early positive signal
- If inbound Tier 2 requests hit 10+ before Day 90: accelerate Go decision, don't wait
- If all signals are flat at Day 60: consider pivoting Tier 1 approach before Day 90 assessment

---

## What Tier 2 Would Include (for reference)

From unified_business_plan.md:
- Hosted memory lifecycle (rollover, archival, vector search)
- Team management
- API access
- SLA
- Pricing: $29-99/month individuals, $299-999/month teams

---

*This framework replaces ad-hoc signal watching with structured collection. Update the Signal Log whenever a relevant signal is observed. The decision is data-driven, not gut-driven.*
