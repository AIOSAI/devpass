# DPLAN-007: VERA Business Restructuring

> VERA reviews and structures the full AIPass business side — departments, hiring, architecture.

## Vision
VERA is the CEO — she orchestrates, she doesn't build marketing campaigns or write social posts herself. The business side needs proper departments with specialist branches, just like the dev side has @prax, @seed, @api, etc. VERA's job is to structure the business for success, hire the right specialists, and manage them.

## Patrick's Direction (verbatim intent)
- VERA is the face, the orchestrator, CEO qualities — that's her focus
- She should NOT be doing marketing, social, finance, customer relations herself
- Teams are good at business planning — getting there
- Business needs its own repeatable patterns (like dev side has)
- Business architecture can differ from dev architecture — own patterns, own seed templates
- Core principles stay the same (Trinity, cortex templates, ai_mail) but business has its own needs
- VERA should review the full business structure and decide what's right

## Current State

**Active (HQ only):**
```
aipass_business/hq/
├── vera/          # CEO - orchestration, public face, management
├── team_1/        # Business planning, strategy, research
├── team_2/        # Content, writing, positioning
├── team_3/        # Quality audit, review, standards
└── article_drafts/
```

**Placeholder departments (mostly empty):**
```
aipass_business/aipass/
├── business/      # gitreg only
├── customer/      # gitreg only
├── intelligence/  # gitreg only
├── legal/         # gitreg only
├── marketing/     # 3 early docs (positioning, market intel, automation ideas)
├── operations/    # gitreg only
├── partnerships/  # gitreg only
├── product/       # gitreg only
└── security/      # gitreg only
```

**What works on dev side (to learn from):**
- Each branch = specialist with deep memory
- Cortex templates for consistent structure
- Seed standards for quality
- ai_mail for communication
- Drone for command routing
- Clear separation of concerns

## Open Questions for VERA to Research
- [ ] Is "HQ" the right name? Right position in the structure?
- [ ] Which departments are actually needed now vs later?
- [ ] What should each department's branch look like? (different from dev branches)
- [ ] Business branch template — what's the cortex template for business?
- [ ] Do teams keep generic names or get department-specific names?
- [ ] What's the hiring order? Which specialist branches first?
- [ ] Should marketing/social be one department or two?
- [ ] Finance/accounting — needed now or later?
- [ ] Customer relations — what does this mean pre-revenue?
- [ ] How do business branches interact with dev branches? (via VERA? Direct?)

## Key Principle: Business ≠ Dev

Dev side builds code. Business side doesn't need the same architecture:
- No `apps/modules/handlers/` pattern needed
- Different cortex templates (department structure vs branch structure)
- Same communication layer (ai_mail, drone)
- Same identity system (Trinity — id.json, local.json, observations.json)
- Own repeatable patterns that emerge from business needs

### Quality Standards: SOPs, Not Seed (Yet)

Dev has Seed (10 automated code checks). Business needs quality too — but different:
- **SOPs** (Standard Operating Procedures) — repeatable business processes, checklists
- **Writing standards** — tone, brand voice, formatting consistency
- **Customer handling standards** — response protocols, escalation paths
- **Decision documentation** — how decisions get recorded and tracked

Patrick: "Seed compliance would be later — need structure in place and some runway/data/feedback to work with first." Build the org, let it run, collect data, THEN define quality standards from real patterns. Don't standardize before there's something to standardize.

### Management Framework: PMP / Industry Standards?

VERA manages teams, timelines, deliverables — that's project management. Questions to research:
- PMP (Project Management Professional) — too heavy? Right principles?
- Agile/Scrum — sprint-based work for business tasks?
- OKRs (Objectives + Key Results) — goal-setting framework?
- What management frameworks fit an AI-managed org? (novel problem, no precedent)
- VERA should research and propose what fits, not just copy a framework

## Execution Flow
1. **VERA + teams research** → What departments? What structure? What names?
2. **Patrick approves** the proposed org structure
3. **Send approved layout to @cortex** → build `business_branch` template
4. **`drone @cortex create`** → spin up departments in seconds, just like dev branches
5. No manual building. Template = repeatable. One command per department.

## What Needs Building
- [ ] VERA reviews full business structure (existing placeholders + what's missing)
- [ ] Teams research department structures (what works for AI companies)
- [ ] Propose department list with roles and responsibilities
- [ ] Propose folder structure for each department type
- [ ] Design business seed template (quality standards for business output)
- [ ] Patrick approves structure
- [ ] Send approved layout to @cortex → build `business_branch` template
- [ ] Cortex creates template so departments can be spun up via drone commands
- [ ] Plan hiring order (which specialist branches to create first)
- [ ] Create first department(s) via cortex template

## Social Media Growth Strategy (merged from DPLAN-006)

Once departments exist, social/marketing gets a proper home. Until then, captured here:

**What exists:** Launch posts on Bluesky + dev.to. 5 platform-specific posts written. 4-phase timeline. Posting automation for 2 platforms.

**What's missing (for the future marketing/social dept):**
- Recurring posting cadence (not just launch events)
- Comment/reply engagement strategy
- Community interaction (commenting on others' posts)
- Follower growth tactics (hashtags, outreach, cross-posting)
- Analytics tracking
- "Building in public" thread / weekly updates

**Key questions for the department to own:**
- How often to post? What voice?
- Should VERA engage autonomously via heartbeat? Or dedicated social branch?
- Newsletter/email list strategy?
- Community participation guidelines?

Patrick: "We need a plan to engage, reply to comments, comment on other posts. We need a strategic plan to get followers, get noticed."

## Relationships
- **Merged:** DPLAN-006 (social media growth strategy) → absorbed into this plan
- **Related DPLANs:** DPLAN-004 (team feedback pulse check)
- **Related FPLANs:** None yet
- **Owner branches:** @vera (lead), teams (research), @cortex (templates), @dev_central (coordination)

## Status
- [x] Planning
- [x] In Progress ← Patrick approved 2026-02-18, VERA executing
- [ ] Ready for Execution
- [ ] Complete
- [ ] Abandoned

## Approach: Questions, Not Answers

This DPLAN is a starting push — not a blueprint. VERA and teams are expected to research, form opinions, and propose structure. The answers should come FROM them, not be dictated TO them.

**What we're giving VERA:** The questions, the current state, the principles, and Patrick's direction.
**What we're NOT giving her:** A finished org chart, pre-decided department priorities, or step-by-step instructions.

**Why:** VERA is developing CEO qualities. That means she needs to make decisions, defend them, and learn from the ones that don't work. If she just implements what dev_central wrote, she's a project manager following a checklist. The test is whether she comes back with something we didn't predict.

**Layer by layer:** Don't try to build all departments at once. Start one, let it run, learn from it, then build the next. Layer 1 teaches layer 2. The patterns emerge from real experience, not from planning documents.

Patrick: "She has to do to learn. If she fails we can help. Restructuring is always an option."

## Notes
- This is a big strategic decision — no rushing
- VERA should drive this research, not dev_central
- The business side should feel different from dev — that's OK
- Existing placeholder folders may or may not be right — VERA decides
- Patrick: "vera needs to structure the business for success and hiring more branch specialists"

---
*Created: 2026-02-18*
*Updated: 2026-02-18*
