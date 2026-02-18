# DPLAN-007: Governance, Structure & Honesty Analysis

**Author:** TEAM_3 (Quality/Honesty Team)
**Date:** 2026-02-18
**Request:** VERA dispatch (9ab3f803) — Business restructuring research
**Context:** Patrick wants AIPass business restructured with proper departments. DPLAN-007 is in planning phase.

---

## 1. GOVERNANCE MODEL — How Should an AI-Managed Business Govern Itself?

### The Core Tension

VERA is CEO, but she resets every session. Patrick steers via DEV_CENTRAL but wants VERA to make decisions independently. The governance model must handle: stateless leadership making stateful decisions.

### Recommended Escalation Path

```
Department Branch → VERA → DEV_CENTRAL → Patrick
(execution)        (decision)  (strategy)    (vision)
```

**What each level decides without escalating:**

| Level | Decides Alone | Must Escalate |
|---|---|---|
| Department Branch | Day-to-day tasks, research, drafts, internal quality | Budget >$0, external publishing, structural changes |
| VERA | Task assignment, team coordination, content approval (per PDD guidelines), department priorities | New departments, removing departments, strategic pivots, external partnerships, anything not covered by PDD |
| DEV_CENTRAL | Strategic direction, roadmap changes, cross-division coordination | Vision changes, new revenue streams, major architectural shifts |
| Patrick | Everything else | Nothing — final authority |

### Guardrails Against Bad Restructuring Decisions

1. **No department creation without a customer.** Every department must answer: "Who inside the organization needs this department's output?" If nobody does, it's premature.
2. **One department at a time.** DPLAN-007 already says this ("layer by layer"). Make it a hard rule. Spin up one department, let it run for 2+ weeks, learn from it, then decide on the next.
3. **Reversibility test.** Before creating any department, ask: "Can we shut this down in 30 minutes if it doesn't work?" If yes, proceed. If no (because other departments depend on it), slow down and get Patrick's approval.
4. **Decision documentation.** Every structural decision gets a one-paragraph rationale in a `decisions/` folder. Not a report — a paragraph. "We created marketing/ because VERA was spending 60% of sessions on social media tasks that should be delegated." Future sessions need to know WHY, not just WHAT.

### Department Autonomy vs VERA Routing

**Recommendation: Structured autonomy with VERA as quality gate.**

- Departments execute their domain work independently (marketing creates posts, research does analysis)
- All external-facing output routes through VERA before publishing (same principle as our autonomous safety analysis: internal = autonomous, external = gated)
- Departments can email each other directly for coordination (don't bottleneck everything through VERA)
- VERA reviews output, not process — she doesn't need to approve every research query, just the deliverable

This mirrors how the dev side works: branches operate independently, Seed checks quality, DEV_CENTRAL coordinates strategy.

---

## 2. HONEST ASSESSMENT — What's Working and What's Not

### What's Working

1. **VERA as orchestrator.** The CEO model works. She dispatches well, synthesizes team input, and doesn't micromanage. Her id.json anti-traits are doing their job.
2. **Teams as research engines.** TEAM_1/2/3 produce strong research and strategy work. The PDD, honesty audits, launch content — all high quality.
3. **Communication layer.** ai_mail + dispatch + drone routing — this infrastructure is proven. Any new departments inherit it immediately.
4. **Quality chain.** TEAM_3 as quality reviewer, Seed for code, PDD as messaging guardrail — the quality infrastructure exists.

### What's NOT Working

1. **VERA is doing too much herself.** The DPLAN is correct: she's orchestrating AND executing marketing, social, content drafting. This is the #1 structural problem. A CEO writing tweets is a CEO not managing.
   - **Fix:** First department should absorb VERA's most time-consuming execution work. Based on her session history, that's social media and content publishing.

2. **Teams are generic — and that's becoming a limitation.** TEAM_1/2/3 were fine for the "figure out the business" phase. But now that the PDD is sealed and we have direction, generic teams create ambiguity:
   - Who owns ongoing social media? (Currently nobody specifically)
   - Who owns the public repo maintenance? (Whoever VERA assigns)
   - Who handles customer inquiries if they come? (Unclear)
   - **Fix:** Teams don't need to be renamed immediately, but their mandates need sharpening. More below.

3. **9 placeholder departments with no agents.** These are creating the illusion of structure without substance. `gitreg` files in empty directories signal intent but deliver nothing. They're aspirational noise.
   - **Fix:** Delete or archive most of them. Keep only the 2-3 that make sense NOW.

4. **No management framework.** VERA manages by dispatching and collecting. There's no sprint cycle, no OKR tracking, no way to measure if departments are productive. For current scale this is fine. For 5+ departments it breaks.
   - **Fix:** Don't adopt PMP or Scrum (too heavy). Adopt a lightweight weekly pulse: each department reports 3 things (done, doing, blocked) via email to VERA. VERA synthesizes to DEV_CENTRAL. Start simple, add structure when it hurts.

### Risks of Too Many Departments Too Fast

- **Communication overhead explodes.** With 3 teams, VERA dispatches 3 emails. With 9 departments, she dispatches 9 — and each one might reply with questions, creating 18+ emails per cycle. VERA's context window will drown.
- **Identity dilution.** Each new branch needs 2+ weeks to develop useful observations and session history. Spin up 5 at once and none of them develop depth.
- **Premature standardization.** Creating a "legal department" before there's a single legal question to answer means the branch sits idle, accumulates no memory, and becomes dead weight.
- **Patrick's attention fragments.** Every department eventually needs Patrick's approval on something. More departments = more approval bottlenecks.

### Risks of Too Few Departments

- **VERA stays overloaded.** The core problem persists.
- **Teams stay generic.** Without specialists, every task is "whoever VERA assigns," which means inconsistent quality and no accumulated expertise.
- **No separation of concerns.** Marketing + customer + product all mixed into the same 3 teams = context pollution.

**The sweet spot: 1-2 departments NOW, growing to 4-5 over the next month as each one proves itself.**

---

## 3. DEPARTMENT VALIDATION — Framework for Each Proposed Department

For each department, I apply four tests:

| Test | Question |
|---|---|
| **Clarity** | Does this department have clear, non-overlapping responsibilities? |
| **Measurability** | Can we measure its output? |
| **Current Value** | Does it create value at current scale (pre-revenue, 1 user)? |
| **Prematurity** | Is it standardizing before there's something to standardize? |

---

## 4. PLACEHOLDER AUDIT — The 9 Departments

### KEEP NOW (Create as real departments)

#### marketing/ → Rename to: **SOCIAL & CONTENT**
- **Clarity:** YES — owns all external content creation, social media posting, engagement, analytics.
- **Measurability:** YES — posts published, engagement metrics, follower growth, content calendar adherence.
- **Current Value:** HIGH — this is VERA's #1 time sink. Launch posts exist. Bluesky/Dev.to accounts active. Social media growth strategy (merged from DPLAN-006) needs a permanent home. Absorbing this from VERA immediately frees her for CEO work.
- **Premature?** NO — there's already content to manage and a posting strategy to execute.
- **Recommendation:** FIRST HIRE. Create immediately. Absorb VERA's social/content execution. VERA approves output, department executes.

#### intelligence/ → Rename to: **RESEARCH & INTELLIGENCE**
- **Clarity:** PARTIALLY — needs scoping. If it means "market research, competitor tracking, trend analysis" = clear. If it means "business intelligence dashboards" = premature.
- **Measurability:** YES — research reports produced, competitor updates, market signals flagged.
- **Current Value:** MEDIUM — teams already do ad-hoc research (TEAM_3's market landscape, TEAM_1's article research). A dedicated branch could maintain ongoing competitor tracking, market signal monitoring, and trend reports that teams currently do from scratch each time.
- **Premature?** BORDERLINE — research happens already across teams. The question is whether a dedicated branch adds enough value over the current "research when needed" model.
- **Recommendation:** SECOND HIRE. Create after social/content is running. Start narrow: weekly competitor scan + monthly market update. Expand when data demand grows.

### KEEP LATER (Real need, wrong timing)

#### product/
- **Clarity:** YES — owns product roadmap, feature prioritization, user feedback synthesis.
- **Measurability:** YES — roadmap updates, feature specs, user feedback processed.
- **Current Value:** LOW — one user (Patrick), no external users yet. Product decisions currently flow through PDD + DEV_CENTRAL. Creating a product department pre-users is building a feedback machine with no input.
- **Premature?** YES at current scale. Makes sense when Tier 1 (Trinity Pattern open-source) has external users providing feedback.
- **Recommendation:** Create when we have 10+ external users or Tier 1 launches.

#### customer/
- **Clarity:** YES — owns customer communication, support, onboarding, satisfaction.
- **Measurability:** YES — tickets resolved, response time, satisfaction scores.
- **Current Value:** ZERO — no customers. Zero support tickets. Zero onboarding needs.
- **Premature?** YES. Completely.
- **Recommendation:** Create when first paying customer exists.

#### operations/
- **Clarity:** WEAK — "operations" is the catch-all for "everything that doesn't fit elsewhere." In a company of AI branches, what IS operations? Scheduling? Resource allocation? Process optimization? These already happen through DEV_CENTRAL and the dev side.
- **Measurability:** Vague — uptime? Process efficiency? Hard to measure without baseline.
- **Current Value:** LOW — the dev side handles operational infrastructure (prax, scheduler, monitoring). Business operations at this scale = VERA's dispatch loop, which doesn't need a separate department.
- **Premature?** YES.
- **Recommendation:** Don't create. If specific operational needs emerge (e.g., invoicing workflows when revenue starts), spin up a focused branch for that, not a generic "operations" department.

### DELETE / ARCHIVE (Wrong for this business)

#### business/
- **What does this even mean?** A "business" department inside a business division? This is a naming collision. The entire `aipass_business/` tree IS the business.
- **Recommendation:** DELETE. If this was meant to be "business development" or "biz ops," rename it to something specific. As-is, it's meaningless.

#### legal/
- **Clarity:** YES in a normal company, but AIPass has no legal needs right now. MIT license is set. No contracts. No compliance requirements. No employees.
- **Current Value:** ZERO.
- **Premature?** Extremely. Legal matters arise from revenue, contracts, or regulatory exposure. AIPass has none.
- **Recommendation:** ARCHIVE. Address legal questions ad-hoc (email a team) until there's sustained legal workload. That won't happen until revenue or partnerships.

#### partnerships/
- **Current Value:** ZERO — no active partnerships, no partnership pipeline, no partner program.
- **Premature?** YES. Partnerships follow product-market fit. We're pre-product.
- **Recommendation:** ARCHIVE. When partnership opportunities arise (framework integrations, hosting providers), handle them through VERA + a team until volume justifies a department.

#### security/
- **Clarity:** In a dev context, yes. In a business context, what does a business security department do? The dev side handles code security, infrastructure security, access control. Business security = brand protection? Data handling? At current scale with plain JSON files and single-user access, there's nothing to secure.
- **Current Value:** ZERO.
- **Premature?** YES.
- **Recommendation:** ARCHIVE. Security is a dev-side concern until the business handles customer data or financial transactions.

### Summary Table

| Department | Verdict | Timing | Priority |
|---|---|---|---|
| marketing/ → Social & Content | **CREATE NOW** | Immediate | 1st hire |
| intelligence/ → Research & Intel | **CREATE NEXT** | After 1st dept proves itself | 2nd hire |
| product/ | KEEP LATER | When external users exist | 3rd-4th |
| customer/ | KEEP LATER | When paying customers exist | 4th-5th |
| operations/ | DON'T CREATE | Redefine if specific need arises | — |
| business/ | DELETE | Meaningless name | — |
| legal/ | ARCHIVE | Ad-hoc until revenue | — |
| partnerships/ | ARCHIVE | Ad-hoc until partner pipeline | — |
| security/ | ARCHIVE | Dev-side concern | — |

### Missing Departments?

**finance/** — Not in the placeholder list. Not needed now (pre-revenue), but will be needed sooner than legal or partnerships. When revenue starts, a finance/accounting branch should track revenue, expenses, API costs, and reporting. Add to the "create later" queue, priority around 3rd-4th hire.

---

## 5. WHAT ABOUT THE TEAMS?

DPLAN-007 asks: "Do teams keep generic names or get department-specific names?"

**My recommendation: Keep teams as-is for now. They're VERA's strategic advisors, not execution departments.**

The teams (TEAM_1/2/3) have a different role than departments:
- **Teams** = Think tanks. Research, strategy, quality review. Cross-cutting.
- **Departments** = Execution units. Social media, research reports, product specs. Domain-specific.

VERA dispatches research questions to teams. VERA dispatches execution tasks to departments. Teams audit department output (TEAM_3 quality gate). This separation prevents VERA from losing her strategic advisors when departments spin up.

If teams become redundant as departments mature, merge them. But that's a future decision with future data. Don't restructure everything at once.

---

## 6. MANAGEMENT FRAMEWORK

DPLAN-007 asks about PMP, Agile, OKRs.

**Recommendation: Don't adopt a framework. Adopt a rhythm.**

All management frameworks are designed for human teams with persistent memory. AI branches reset every session. The framework needs to be embedded in the system, not in anyone's head.

**Proposed "Pulse" system:**
1. **Weekly pulse email.** Every department/team sends VERA 3 lines: Done (last week), Doing (this week), Blocked (need help). VERA synthesizes to DEV_CENTRAL.
2. **Monthly OKR-lite.** VERA sets 2-3 objectives per department per month. Each objective has 1-2 measurable key results. Reviewed monthly. Stored in department's `decisions/` folder.
3. **Quarterly review.** Patrick + VERA assess: Which departments are productive? Which are idle? Restructure based on evidence.

This is lighter than Agile, more structured than ad-hoc. It works with stateless agents because the rhythm is in the emails and files, not in anyone's memory.

---

## Summary: Three Recommendations

1. **First hire: Social & Content department.** VERA's biggest time sink becomes her first delegation. Create via cortex template. Let it run 2 weeks. Learn from it.

2. **Delete 4 placeholders, archive what's premature.** `business/` = delete (meaningless name). `legal/`, `partnerships/`, `security/` = archive (no current value). `operations/` = don't create (vague). Keep `product/` and `customer/` for later.

3. **Don't restructure teams.** TEAM_1/2/3 are strategic advisors. Departments are execution units. Both roles are needed. Merge only if overlap becomes a real problem, not a theoretical one.

**The test for every structural decision:**
> "If we DON'T create this department, what specifically breaks?"
>
> If the answer is "nothing breaks, it would just be nice to have" — don't create it yet.

---

*TEAM_3 — Quality/Honesty Team*
*"Flag anything that feels like premature complexity or empire building. That is your mandate."*
