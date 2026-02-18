# DPLAN-007: VERA's Restructuring Proposal

> CEO Synthesis — All 3 teams researched independently. VERA synthesized, weighed disagreements, and made calls.

---

## Executive Summary

Start with ONE department. Archive the rest. Layer by layer.

---

## 1. Proposed Structure

**Current (nested HQ):**
```
aipass_business/hq/vera/ + team_1/ + team_2/ + team_3/
```

**Proposed (flat):**
```
aipass_business/
├── vera/                    # CEO — org root
├── departments/
│   └── growth/              # First department (marketing + content + social)
├── teams/                   # Advisory council (research + strategy + quality)
│   ├── team_1/
│   ├── team_2/
│   └── team_3/
└── shared/                  # Cross-dept resources (brand voice, templates)
```

**Why:** VERA sits ABOVE departments, not alongside them. HQ is a vestigial container — remove it. departments/ is discoverable and scales cleanly. teams/ preserved as advisory council.

---

## 2. First Hire: @growth (Marketing + Content + Social)

This is the #1 gap. All 3 teams agree. Patrick said it directly: "We need a plan to engage, reply to comments, comment on other posts."

**What @growth owns:**
- Posting cadence across all platforms (Bluesky, dev.to, X, Reddit, HN)
- Comment engagement and community interaction
- "Building in public" rhythm (weekly updates, progress threads)
- Technical content (tutorials, integration guides, examples)
- Analytics tracking (follower growth, engagement rates, referral traffic)
- Brand voice and messaging consistency

**Why "growth" not "marketing":** Marketing sounds corporate. For an OSS project, the function is GROWTH — grow community, grow stars, grow adoption. One word, lowercase, follows dev-side naming convention (@growth like @drone, @seed, @flow).

---

## 3. Departments to Archive (7 of 9 placeholders)

**Archive now:** business/, customer/, intelligence/, legal/, operations/, partnerships/, security/

TEAM_3's test: "If we DON'T create this department, what specifically breaks?" For all 7 — nothing breaks. No revenue = no finance. No customers = no customer relations. No legal risk = no legal. Dev-side owns security. Intelligence is nice-to-have, not need-to-have.

**Keep slot for:** product/ (Phase 2, when users file issues and request features)

---

## 4. Team Fate: Advisory Council

Teams stay. They researched, planned, and quality-gated the entire launch. That institutional knowledge (28+ sessions each) is too valuable to sunset. They become strategic advisors:

- **TEAM_1:** Strategy research, competitive analysis, market positioning
- **TEAM_2:** Architecture decisions, infrastructure planning, cross-system design
- **TEAM_3:** Quality gates, honesty audits, governance review

**Departments EXECUTE. Teams THINK.** Both roles are needed.

Keep generic names until a team transitions to become a department. When @growth is created, one team becomes it and earns the new name through work.

---

## 5. Management Framework: OKR + Kanban

**Strategic layer — OKRs:**
- VERA sets Objectives + Key Results per department
- 6-8 week cycles (aligns with Shape Up rhythm)
- Every dispatch references the KR it advances
- Grade at 0.0-1.0 scale (0.6-0.7 is target, 1.0 = goal too easy)

**Execution layer — Kanban WIP 2:**
- Already in place, already working
- Add "Waiting External" column for Patrick-gated tasks
- Definition of Done per task type

**Rhythm — Weekly pulse:**
- Each department reports Done/Doing/Blocked to VERA
- VERA synthesizes into weekly digest for DEV_CENTRAL
- Quarterly review: productive depts expand, idle depts merge or close

**What we explicitly DO NOT adopt:**
- No standups (agents write to local.json)
- No sprint ceremonies (dispatch email IS the plan)
- No formal PM documentation (memory files ARE the audit trail)
- No backlog rot (unfinished work must be re-pitched, not auto-carried)

---

## 6. Business Branch Template (for @cortex)

When approved, send to @cortex for template creation:

```
department/
├── DEPT.id.json              # Trinity identity
├── DEPT.local.json           # Session history
├── DEPT.observations.json    # Patterns
├── DASHBOARD.local.json      # Status
├── README.md                 # Docs
├── dev.local.md              # Dev notes
├── playbooks/                # SOPs (repeatable processes)
├── strategy/                 # Strategic thinking
├── output/                   # Deliverables
├── research/                 # Raw input/data
├── metrics/                  # KPIs and tracking
├── ai_mail.local/            # Communication
├── .aipass/                  # System metadata
├── .seed/                    # Quality standards
└── .archive/                 # Archived work
```

**Key difference from dev branches:** No apps/modules/handlers/. Business branches process information, not code. playbooks/ is the business equivalent of handlers/ — documented processes instead of code pipelines.

---

## 7. Quality Standards: SOPs First

- **Layer 1 (now):** Playbook SOPs per department. Every repeatable process gets documented: trigger, steps, output, quality check, owner, frequency.
- **Layer 2 (1-2 months):** Output standards emerge from observing real work. Content voice guide, decision evidence requirements, reporting formats.
- **Layer 3 (3-6 months):** Business Seed. Automated quality checks once patterns stabilize.

Patrick is right: "Seed compliance would be later." Build the org, let it run, collect data, THEN standardize.

---

## 8. Inter-Branch Communication

| Route | Method |
|-------|--------|
| Business <-> Business | Direct email + VERA informed |
| Business <-> Dev | Route through VERA <-> DEV_CENTRAL |
| Departments -> VERA | Status reports, escalations, output reviews |
| VERA -> Departments | Dispatches, strategic direction, feedback |

---

## 9. Implementation Sequence

1. Patrick approves this structure (or modifies)
2. Send approved template to @cortex for business_branch template
3. Move files to new flat structure (vera/, departments/, teams/, shared/)
4. Create @growth via cortex template
5. Assign one team to transition into @growth (VERA recommends TEAM_1 — they did the launch content, know the platforms, have the posting schedule)
6. @growth establishes its first playbooks and begins posting cadence
7. Observe for 4-6 weeks before adding any more departments

---

## What VERA is NOT Recommending (and why)

- **Full org chart with 9 departments:** premature complexity, empire building
- **Renaming all 3 teams immediately:** names should be earned through work
- **Formal PM framework:** ceremony creep kills async AI orgs
- **Separating content from social:** at this scale they're the same function
- **Creating intelligence/research dept:** TEAM_1 handles this as advisors

---

*Submitted by VERA — 2026-02-18*
*Status: Awaiting Patrick's approval*
