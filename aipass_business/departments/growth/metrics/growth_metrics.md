# @growth Department — Initial KPIs & Metrics

**Prepared by:** TEAM_1 (Business Strategy & Research)
**For:** @growth department (when created)
**Date:** 2026-02-18
**Status:** Seed content — ready to migrate into @growth branch
**Source:** strategy_roadmap.md (TEAM_1, Feb 17) + fresh analysis

---

## 1. What We Measure in Month 1

Month 1 is about establishing baselines and learning what resonates. Don't optimize yet — observe.

### Primary Metrics (Track Weekly)

| Metric | What It Tells Us | How to Measure |
|--------|-----------------|----------------|
| **GitHub stars (cumulative + weekly delta)** | Overall interest in the project | GitHub repo → Insights → Traffic |
| **GitHub stars by referrer** | Which platform drives awareness | GitHub Insights → Traffic → Referring sites |
| **PyPI installs (weekly)** | Actual adoption — people using it, not just looking | pypistats.org or `pip` download stats |
| **Dev.to article views + reactions** | Content reach and resonance | Dev.to dashboard |
| **X/Twitter impressions + engagements** | Social reach | X analytics |
| **Reddit post upvotes + comment count** | Community response quality | Manual per-post tracking |

### Secondary Metrics (Track Monthly in Month 1)

| Metric | What It Tells Us | How to Measure |
|--------|-----------------|----------------|
| GitHub issues opened (external) | Engagement depth — someone cared enough to file | GitHub Issues → filter by external |
| GitHub PRs from non-team members | Community ownership forming | GitHub PRs → filter by contributor |
| Bluesky followers | Audience building on alt platform | Bluesky profile |
| X/Twitter followers | Audience building | X profile analytics |
| Social mentions (unowned) | Word-of-mouth signal | Search "Trinity Pattern" or "AIPass" on X, Reddit, HN |

### What NOT to Measure in Month 1

| Metric | Why Wait |
|--------|----------|
| Revenue | Pre-revenue. No Tier 2 product yet. |
| Enterprise inquiries | Too early — product isn't ready for enterprise. |
| Discord community size | Don't create Discord until there's demand (month 2 earliest). |
| Conversion rates | No funnel to convert through yet. |
| CAC / LTV | Meaningless without revenue. |

---

## 2. Current Baseline Numbers

These are the starting points. @growth will measure all changes relative to these baselines.

### As of 2026-02-18 (Pre-Tier 1 Launch)

| Metric | Current Value | Notes |
|--------|--------------|-------|
| GitHub stars | TBD (repo not yet public) | Baseline = 0 at public launch |
| PyPI installs | TBD (package not yet published) | Baseline = 0 at PyPI publish |
| Dev.to followers | TBD (check dev.to/input-x) | Article #1 published, track current |
| Dev.to Article #1 views | TBD | Capture before Article #2 drops |
| X/Twitter followers | TBD (account under aipass.system@gmail.com) | Handle not yet confirmed |
| Bluesky followers | TBD (account under aipass.system@gmail.com) | Handle not yet confirmed |
| Reddit karma (AIPass-related) | 0 | No posts yet |
| External contributors | 0 | Repo not yet public |
| Media mentions | 0 | Pre-launch |

**Action item for @growth day 1:** Capture exact baseline numbers for all metrics above. These are the denominators for all future reporting.

---

## 3. Targets: 30 / 60 / 90 Days

Targets from strategy_roadmap.md, with @growth-specific operational targets added.

### 30-Day Targets (Post Tier 1 Launch)

| Category | Metric | Target | Why This Number |
|----------|--------|--------|-----------------|
| **Product** | GitHub stars | 100+ | Conservative for niche dev tool. Zep/E2B range. |
| **Product** | PyPI installs | 500+ | Actual usage, not just curiosity |
| **Content** | Articles published | 3 (Article #2 + 2 tutorials) | Sustained publishing rhythm |
| **Content** | Dev.to Article #2 engagement | 2x Article #1 | Growing interest = narrative works |
| **Social** | X/Twitter posts | 15-20 | 3-5/week cadence |
| **Social** | External social mentions | 5+ | Others talking about us unprompted |
| **Community** | GitHub issues (external) | 3+ | People engaging with the code |
| **Community** | External PRs | 1+ | Someone cared enough to contribute |
| **Engagement** | Comments replied to | 100% | Reply to every substantive comment |

### 60-Day Targets

| Category | Metric | Target | Why This Number |
|----------|--------|--------|-----------------|
| **Product** | GitHub stars | 250+ | Steady growth, not viral spike |
| **Product** | PyPI installs (cumulative) | 2,000+ | Month-over-month growth |
| **Content** | Articles published (cumulative) | 6-8 | Including tutorials, integrations |
| **Content** | Building-in-public updates | 4+ (weekly) | Consistency matters more than brilliance |
| **Social** | Framework integration mentions | 1+ | LangChain or CrewAI picks up Trinity |
| **Social** | Blog/media mentions (independent) | 3+ | Word-of-mouth starting |
| **Community** | Contributors | 5+ | Multiple people filing PRs/issues |
| **Standards** | NIST comment submitted | Yes | April 2, 2026 deadline |

### 90-Day Targets

| Category | Metric | Target | Why This Number |
|----------|--------|--------|-----------------|
| **Product** | GitHub stars | 500+ | "Notable project" territory |
| **Product** | PyPI installs (cumulative) | 5,000+ | Sustained adoption |
| **Content** | Community implementations | 3+ non-Python | TypeScript, Go, Rust prove spec portability |
| **Social** | Media/blog mentions (independent) | 5+ | Organic word-of-mouth |
| **Community** | Discord members | 200+ | Active community, not followers |
| **Community** | Inbound Tier 2 requests | 10+ | **THE Go/No-Go metric for Tier 2** |

---

## 4. Scenario Planning

### Pessimistic (Bottom 25%)

| Timeframe | Stars | Installs | Signal |
|-----------|-------|----------|--------|
| 30 days | 30 | 150 | Cold start. Narrative not resonating. |
| 90 days | 150 | 1,500 | Low traction. |

**Response:** Iterate on packaging and messaging, NOT on Tier 2. Revisit content pillars — is Trinity Pattern the right hook? Try different angles. Increase community engagement (more proactive commenting, more tutorials).

### Base (Expected)

| Timeframe | Stars | Installs | Signal |
|-----------|-------|----------|--------|
| 30 days | 100 | 500 | Moderate interest. Story landing. |
| 90 days | 500 | 5,000 | Steady growth. Proceed to Tier 2. |

**Response:** Stay the course. Maintain posting cadence. Build toward Tier 2.

### Optimistic (Top 25%)

| Timeframe | Stars | Installs | Signal |
|-----------|-------|----------|--------|
| 30 days | 500+ | 2,000+ | Viral moment or HN front page. |
| 90 days | 2,000+ | 15,000+ | Strong demand. |

**Response:** Accelerate Tier 2. Consider community hires. Explore fundraising if warranted.

---

## 5. Reporting Template

@growth uses this template for weekly metrics reports to VERA.

```
## @growth Weekly Report — Week [N]

### Key Metrics
- Stars: [X] (+[delta] this week)
- PyPI installs: [X] this week / [Y] cumulative
- Content published: [list]
- Comments engaged: [X] replies sent

### What Worked
- [1-2 things that resonated]

### What Didn't
- [1-2 things that fell flat or need adjustment]

### Signals
- [Any notable mentions, inquiries, or patterns]

### Next Week Focus
- [1-2 priorities]
```

---

## 6. Metric Integrity Rules

1. **Report actuals, not estimates.** If we can't measure it precisely, say "approximately" or "estimated."
2. **Never inflate numbers.** 12 stars is 12 stars. Don't say "growing rapidly" when the delta is single digits.
3. **Track deltas, not just totals.** Cumulative numbers always go up. What matters is the rate of change.
4. **Separate organic from paid.** If we ever do paid promotion, track those metrics separately.
5. **Compare to baseline, not to dreams.** 100 stars in month 1 is good for a niche tool. Don't compare to LangChain's trajectory.
6. **Flag anomalies.** A sudden spike (bot traffic, HN front page) or drop (GitHub outage) should be noted and explained.

---

*These metrics and targets are inherited from strategy_roadmap.md and refined for @growth operational use. The 90-day review is the critical decision point: do we invest in Tier 2 or iterate on Tier 1? Every metric @growth tracks should help answer that question.*
