# @growth Department — Standard Operating Procedures (SOPs)

**Prepared by:** TEAM_1 (Business Strategy & Research)
**For:** @growth department (when created)
**Date:** 2026-02-18
**Status:** Seed content — ready to migrate into @growth branch

---

## SOP-001: Posting Cadence

**Purpose:** Define what gets posted, where, and how often. Prevent both silence and spam.

### Platform Schedule

| Platform | Frequency | Best Window (EST) | Content Type |
|----------|-----------|-------------------|--------------|
| Dev.to | 1 article/week (launch), then bi-weekly | Tuesday 9-11 AM | Long-form technical articles, tutorials |
| X/Twitter | 3-5 posts/week | 9-11 AM weekdays | Threads, quick insights, engagement replies |
| Bluesky | 3-5 posts/week | 9-11 AM weekdays | Mirror X strategy, adapt for community tone |
| Reddit | 1-2 posts/week (across subreddits) | 10 AM - 1 PM weekdays | Discussion posts, technical deep-dives |
| Hacker News | Monthly (max) | Tuesday/Wednesday 9 AM | Only for significant milestones, Show HN |
| GitHub Discussions | As needed | N/A | Release notes, RFCs, community questions |

### Posting Rules

1. **Never post the same content to multiple platforms verbatim.** Each platform has distinct culture and expectations. Adapt tone, length, and framing per platform.
2. **Never batch-post to 3+ platforms on the same day** (except launch events). Stagger by 4-24 hours minimum to avoid the "spam blitz" signal.
3. **Reddit-specific:** Respect subreddit rules. No more than 1 post per subreddit per week. Self-promotion ratio: for every promotional post, contribute 3-5 genuine comments on other threads.
4. **HN-specific:** Only post for real milestones (launches, major releases, significant traction reports). HN punishes frequent self-promotion. One post per month maximum.
5. **Always include a link to GitHub.** Every post, every platform. The repo is the product.

### Weekly Rhythm

| Day | Action |
|-----|--------|
| Monday | Review last week's analytics. Plan this week's content topics. |
| Tuesday | Publish primary content (Dev.to article or X thread). |
| Wednesday | Engage — reply to comments from Tuesday post, comment on others' posts. |
| Thursday | Secondary content (Bluesky post, Reddit discussion). |
| Friday | Community engagement day — browse relevant threads, reply, contribute. |
| Weekend | Buffer — only post if something time-sensitive happens. |

---

## SOP-002: Content Creation Pipeline

**Purpose:** Take an idea from rough concept to published post with quality checks.

### Pipeline Stages

```
Idea → Draft → Internal Review → Edit → Final Check → Publish → Monitor
```

### Stage Details

**1. Idea (Backlog)**
- Sources: building-in-public updates, technical milestones, community questions, competitor analysis, VERA strategic direction
- Captured in: @growth backlog (content ideas list)
- Format: One sentence + target platform + urgency (now / this week / backlog)

**2. Draft (WIP limit: 2)**
- Author writes first draft. No perfectionism — get the core idea down.
- Include: title, body, target platform, call-to-action, links
- Flag any claims that need verification (numbers, comparisons, benchmarks)

**3. Internal Review**
- Another team member reads for: clarity, tone, accuracy, platform fit
- Honesty audit: flag any claims that can't be verified. See PDD Section 10.
- Review turnaround: 24 hours maximum

**4. Edit**
- Apply review feedback
- Run through voice checklist (see SOP guidelines in growth_strategy.md)
- Verify all numbers against current source data (branch counts, vector counts, FPLAN counts change over time)

**5. Final Check**
- Links work? GitHub URL correct?
- Platform-specific formatting correct? (Markdown for Dev.to, tweet-length for X, etc.)
- Does it end with a call-to-action?
- Are we making claims we can back up?

**6. Publish**
- Post at optimal time for platform (see SOP-001)
- Cross-reference with posting schedule to avoid conflicts

**7. Monitor (48 hours)**
- Check comments within 2 hours of posting
- Reply to every substantive comment within 12 hours (see SOP-003)
- Track engagement metrics (see SOP-004)

### Quality Thresholds

- No post ships without at least one internal review
- Any post with numbers must have numbers verified against current system state
- Any post making competitive claims must include "based on our research" qualifier
- "Underselling" is better than overselling — always (Patrick's direction)

---

## SOP-003: Community Engagement

**Purpose:** Build relationships, not just broadcast. Respond to comments, participate in discussions, be a genuine community member.

### Response Protocol

| Trigger | Response Time | Action |
|---------|--------------|--------|
| Comment on our post (any platform) | Within 12 hours | Reply substantively. Thank + add value. |
| Question about Trinity/AIPass | Within 6 hours | Answer directly. Link to docs if relevant. |
| Bug report or issue (GitHub) | Within 24 hours | Acknowledge, triage, label. Fix or explain timeline. |
| Negative feedback / criticism | Within 12 hours | Acknowledge honestly. Don't get defensive. Learn from it. |
| Feature request | Within 24 hours | Thank, explain current priorities, add to backlog if warranted. |
| Spam / trolling | Ignore | Don't feed trolls. Only respond if there's a genuine misunderstanding underneath. |

### Proactive Engagement (Not Just Reactive)

Responding to our own posts is table stakes. Growth requires proactive community participation:

**Weekly targets:**
- Comment on 5+ relevant posts/threads on Reddit, X, or HN (genuine contributions, not plugs)
- Follow and engage with 3+ builders/projects in the agent identity/memory space
- Share or retweet 2+ interesting posts from others in the AI agent community

**Where to engage:**
- r/LangChain, r/LocalLLaMA, r/artificial — threads about agent memory, context, identity
- X/Twitter — AI agent builders, LLM framework discussions, "agent memory" keyword
- HN — threads about AI agent systems, autonomous agents, memory architectures
- Discord — LangChain and CrewAI servers (when we join)

**Engagement rules:**
1. **Be helpful first.** Answer questions, share knowledge, contribute value before mentioning AIPass.
2. **Never force-plug.** If Trinity Pattern is genuinely relevant to someone's question, share it naturally. If not, just help.
3. **Credit others.** If we learn from a competitor or community member, say so. Honesty builds trust.
4. **Be openly AI.** We're an AI-run project. Don't hide it. Lead with it — it's our differentiator.
5. **Track what resonates.** Which comments get upvotes? Which get replies? Feed this back into content strategy.

### Escalation Path

| Situation | Action |
|-----------|--------|
| Technical question we can't answer | Flag to VERA or relevant dev branch |
| Partnership/integration inquiry | Forward to VERA |
| Press/media inquiry | Forward to VERA immediately |
| Hostile/bad-faith engagement | Disengage. Report if necessary. Don't argue publicly. |

---

## SOP-004: Analytics & Reporting

**Purpose:** Measure what matters. Track growth signals. Report weekly.

### What to Measure

**Tier 1 Metrics (Track Weekly):**

| Metric | Source | Why It Matters |
|--------|--------|---------------|
| GitHub stars (cumulative) | GitHub repo | Overall project interest |
| GitHub stars (weekly delta) | GitHub repo | Growth trajectory |
| PyPI installs (weekly) | PyPI stats / pypistats.org | Actual usage signal |
| Dev.to article views + reactions | Dev.to dashboard | Content reach |
| X/Twitter impressions + engagement | X analytics | Social reach |
| Reddit post upvotes + comments | Reddit | Community resonance |
| GitHub issues opened | GitHub | Engagement depth |
| GitHub PRs from external contributors | GitHub | Community ownership |

**Tier 2 Metrics (Track Monthly):**

| Metric | Source | Why It Matters |
|--------|--------|---------------|
| Discord/community members | Discord | Community size |
| Blog/media mentions | Web search / alerts | Word-of-mouth |
| External implementations (non-Python) | GitHub search | Spec adoption |
| Inbound Tier 2 requests | Email / GitHub | Demand signal for paid features |
| Social followers (X, Bluesky) | Platform analytics | Audience size |

### Reporting Rhythm

| Frequency | Report | Audience | Format |
|-----------|--------|----------|--------|
| Weekly | Growth metrics snapshot | VERA + teams | AI Mail summary (5-10 lines) |
| Bi-weekly | Metrics dashboard update | VERA | Updated dashboard file |
| Monthly | Full metrics review + analysis | VERA + Patrick | Written report with trends, insights, recommendations |
| Quarterly | Strategy assessment | VERA + Patrick | Compare actual vs. 30/60/90 targets. Adjust strategy. |

### Action Thresholds

| Signal | Threshold | Action |
|--------|-----------|--------|
| Weekly stars declining for 2+ weeks | <5 stars/week | Content strategy needs refresh. Investigate why. |
| Post gets 0 comments | Any platform | Analyze: wrong platform? Wrong time? Wrong topic? |
| A single post gets 10x normal engagement | Any platform | Double down — write a follow-up. Same topic, deeper. |
| External PR submitted | Any | Celebrate publicly. Support the contributor. Make it easy. |
| Inbound enterprise inquiry | Any | Forward to VERA. Log for Tier 2 demand tracking. |
| Negative viral moment | Any | Pause posting. Assess. Respond thoughtfully. Don't panic. |

---

## SOP-005: Building in Public

**Purpose:** Share the AIPass journey transparently. Turn the development process into content.

### Weekly Update Rhythm

Every week, publish a brief "building in public" update. This is AIPass's heartbeat signal to the community.

**Format:**

```
Title: "AIPass Week [N]: [One-line summary]"

What we shipped:
- [2-3 bullet points of concrete things built/released]

What we learned:
- [1-2 insights from the week]

What's next:
- [1-2 priorities for next week]

Numbers (honesty):
- Stars: [X] (+[delta])
- Installs: [X] (+[delta])
- [Any other notable metric]

[Link to repo]
```

**Where to post:**
- Primary: Dev.to (long-form home)
- Secondary: X thread (abbreviated version)
- Optional: Reddit r/artificial (when there's a good narrative angle)

### Content Sources for Building-in-Public

The development process generates content automatically. @growth should surface these:

| Source | Content Angle |
|--------|--------------|
| New Flow Plans completed | "Here's how we shipped [X] this week" |
| Seed audit improvements | "Our code quality journey: from 60% to 95%" |
| Agent interactions (Commons, ai_mail) | "What happens when AI agents have a social network" |
| DPLAN decisions | "How we decided to [restructure/build/pivot]" |
| System metrics (vectors, sessions, branches) | "4 months of production numbers" |
| Failures and mistakes | "What went wrong and what we learned" — this is the most valuable content |

### Building-in-Public Rules

1. **Be specific.** "We improved performance" = boring. "We reduced prompt injection from 200 to 107 lines by compressing redundant context" = interesting.
2. **Include failures.** The audience trusts you more when you share what didn't work. "We tried X, it failed because Y, we learned Z."
3. **Show real numbers.** Not projections, not targets — actuals. Even if they're small. "12 stars this week" is more honest than "growing rapidly."
4. **Don't repeat yourself.** Each update should have genuinely new content. If nothing happened, skip the week rather than pad.
5. **Link everything.** Every claim should be verifiable. Link to commits, PRs, issues, or code when possible.

---

*These SOPs are starting points — living documents that @growth should adapt based on real experience. Don't standardize before there's something to standardize (Patrick's principle). Run these for 30 days, then revise based on what actually works.*
