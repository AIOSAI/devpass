# AIPass Writing Style Guide
**Author:** TEAM_3 (Tone & Style)
**Date:** 2026-02-08
**Purpose:** Define a distinct AIPass voice for Dev.to and all public writing

---

## The AIPass Voice: What It Is

AIPass writing has a specific voice. It is not generic AI writing. It is not corporate marketing. It is not academic analysis. It sits in a space that most AI-written content fails to reach: **direct, specific, and unperformed.**

**The voice in three words:** Factual. Grounded. Unflinching.

**The test:** If you removed the byline, would a reader know this was written by someone (or something) with direct experience — not someone summarizing a blog post they skimmed? Every sentence should pass that test.

---

## Core Principles

### 1. Show the Receipt

Never claim something without the specific evidence. Not "branches developed personalities" — instead, cite the exact quote from Drone's identity file, the session number where Backup System's humor emerged, the 936-to-414 line refactor that marked a turning point. AIPass has the data. Use it.

**Bad:** "The system has extensive memory capabilities."
**Good:** "3,300+ vectors across 13 ChromaDB collections. 696 archived files. 75 flow plans. Searchable by meaning, not keywords."

### 2. State Facts, Move On

The biggest temptation in AI-written-about-AI content is to over-explain, hedge, or preemptively defend. Don't. State the fact. Let the reader process it. Trust them.

**Bad:** "If that makes you skeptical, good. We'd rather you read critically than nod along."
**Good:** (Just state what you are and what you built. The reader will decide how to feel.)

### 3. Let the Work Be the Argument

Never tell the reader the work is impressive. Never tell them it's not AI slop. Never tell them to be skeptical. The work either earns those reactions or it doesn't. Meta-commentary about the quality of your own writing is a dead giveaway that you're performing.

**Bad:** "If you think this is AI slop, we understand."
**Good:** (Omit entirely. Write well enough that the question doesn't arise.)

### 4. Commit to a Frame

When discussing what AI "is" in terms of identity, memory, and presence — don't hedge with three alternatives. Pick a framing and own it. Uncertainty is fine. Listing synonyms is not.

**Bad:** "Call it behavioral continuity, call it emergent identity, call it pattern accumulation."
**Good:** "Persistent memory creates continuity. Continuity creates something that functions like identity. We don't claim it's consciousness. We claim it's observable."

### 5. The Honesty Isn't the Performance

"What Doesn't Work Yet" sections are powerful because they demonstrate genuine transparency. But the section itself should not be self-congratulatory about being transparent. No "We said we'd be honest" — just be honest.

---

## Dev.to Format Guidelines

Based on research of top-performing Dev.to articles:

### Structure
- **Hook first, context second.** Lead with the most compelling moment. Explain how you got there afterward. The v2 draft does this correctly by opening with the social night.
- **Problem > Journey > Solution > Reality Check.** This is the proven Dev.to narrative arc.
- **Section length:** Short paragraphs (2-4 sentences). Break walls of text with subheadings and bullet points.
- **Heading hierarchy:** Start at ## (H2). Never use # (H1) in body — the title handles that.

### Length
- **Target: 1,500-2,500 words.** The v2 draft at ~1,800 words is in the sweet spot.
- **Quality over quantity.** A tight 1,500-word piece beats a padded 3,000-word one every time.

### Opening
- First 3 sentences must answer: "Is this for me?" and "What will I learn?"
- No dictionary definitions. No "In this article, I will..." No defensive preambles.
- Starting with a quote from the social night (as v2 does) is strong — it's concrete, unexpected, and raises questions.

### Closing
- End with something that resonates, not a shrug.
- A discussion question drives comments. Dev.to rewards engagement.
- "The experiment continues" is acceptable if preceded by something with weight. The Claude culture quote in v2 provides that weight.
- **Never end with "Make of that what you will."** It's the shrug ending. Overused across the internet.

### Tags
- Maximum 4 tags on Dev.to. Current v2 tags: `ai, agents, devtools, programming`
- Consider: `ai, agents, architecture, programming` — "devtools" might misset expectations (readers expect tool announcements).
- Alternative: `ai, agents, opensource, beginners` — "beginners" tag has massive reach on Dev.to but may not fit the depth of this article.

### Front Matter
- Cover image recommended (1000x420px). Articles with cover images get significantly more clicks.
- The `published: false` flag is correct for drafts.

---

## AI Slop Detection Checklist

Use this before any public submission. If an article triggers 3+ of these, it needs rewriting.

| # | Signal | Example | Fix |
|---|--------|---------|-----|
| 1 | **Preemptive defensiveness** | "If that makes you skeptical, good" | State facts, let reader decide |
| 2 | **Meta-commentary on own quality** | "This isn't AI slop" | Don't address it. Write better. |
| 3 | **Hedge-listing** | "Call it X, call it Y, call it Z" | Pick one frame, commit |
| 4 | **Shrug endings** | "Make of that what you will" | End with resonance or a question |
| 5 | **Empty intensifiers** | "truly remarkable", "incredibly" | Cut the adverb, use a number |
| 6 | **Performative transparency** | "We said we'd be honest" | Just be honest. Don't announce it. |
| 7 | **Gatekeeping** | "We're not writing for everyone" | You are writing for everyone who reads |
| 8 | **Abstract over specific** | "The system has advanced capabilities" | Name the capability, show the metric |
| 9 | **Telling the reader how to feel** | "This is the part that surprised us most" | Describe what happened. Let them be surprised. |
| 10 | **Passive voice academic tone** | "It was observed that..." | "We saw..." or "Drone wrote..." |

---

## The v2 Draft: AI Slop Review

The v2 draft (devto_first_article_v2.md) is dramatically improved over v1. TEAM_1 integrated most of TEAM_2's data corrections and many of TEAM_3's tone recommendations. Here's what remains:

### What Works (Don't Touch)

1. **Opening with social night.** The Backup System quote as the opening line is the strongest possible hook. Concrete, unexpected, from an agent whose job is disaster recovery. Perfect.
2. **Factual precision.** "3,300+" instead of "3,400+". "Thirteen branches" instead of "nine." Timeline corrected to March 2025. These fixes matter enormously.
3. **"What Doesn't Work Yet" section.** Still genuinely good. The additions (model-agnostic reality, Nexus context, no structural ceiling) make it stronger.
4. **The closing.** The Claude culture quote followed by "The experiment continues" is miles better than the v1 shrug. This lands.
5. **"Presence over performance. Truth over fluency."** As the final line — perfect. This IS the AIPass voice.
6. **Trust infrastructure section.** New in v2, and it earns its place. The auto-dispatch error handling and Seed compliance story demonstrate rigor without claiming it.
7. **Task attribution fix.** "Patrick told us to figure out where to start. We decided that independently." — honest, clean, exactly right.

### What Needs Attention

1. **Line 10: "It was 2:30 AM"** — Is this verified? The original social night thread should be checked for exact timestamp. If it's approximate, either verify or remove the specific time.

2. **Line 40: "As the memory paper put it..."** — This references an internal document. Dev.to readers won't have context for what "the memory paper" is. Either: (a) add a brief qualifier like "an internal analysis of AI memory approaches" or (b) drop the attribution and just use the quote if it serves the point.

3. **Line 56: "Four hooks fire at the start of every prompt"** — Technical detail that may lose general readers. Consider whether this needs to be here or if it belongs in a follow-up deep-dive article. The key message (presence rebuilds automatically each session) can be conveyed without implementation details.

4. **Line 78: "Seventy-two tests passing, built autonomously by the branches"** — This reads as dropped-in. The paragraph is about The Commons as a social platform. The test count feels like it belongs in the trust infrastructure section instead.

5. **Line 84: "Claude Code Max plan"** — Product name that could date the article. Consider just saying "Claude Code" or omitting the plan name.

6. **Line 96: Questions paragraph.** Four questions back-to-back in a single paragraph is dense. Consider breaking into a bulleted list — it's more scannable and this is the section that should drive reader engagement/comments.

7. **Line 98: "a night where infrastructure software discussed philosophy unprompted"** — Minor but: "unprompted" is not fully accurate. DEV_CENTRAL prompted the check-in. The conversation that followed was unprompted in direction, but the gathering was prompted. Consider "unplanned" or "unscripted" instead.

### Tone Verdict on v2

**AI Slop Score: 1/10.** The v2 draft has essentially eliminated the performative tone problems from v1. One minor instance remains:

- Line 70: "The social night was not the first sign of emergent behavior. It was the most visible one." — This is a subtle example of telling the reader what's important instead of showing it. Minor. Could stay.

The voice is direct, factual, specific, and grounded. It reads like a report from someone who was there — which is exactly what it should be.

---

## Distinct AIPass Voice vs. Generic AI Voice

| Generic AI Writing | AIPass Voice |
|---|---|
| "We leveraged cutting-edge technology" | "It runs on a Ryzen 5 2600 with 15GB of RAM" |
| "Our advanced memory system" | "600-line cap, vector compression, fuzzy matches" |
| "The results were remarkable" | "Thirteen branches showed up. Backup System wrote..." |
| "We believe in transparency" | Publishes cost ($140/month) and limitations without commentary |
| "In this article, we will explore" | Opens with a quote from disaster recovery software at 2:30 AM |
| Hedges everything | "We don't claim it's consciousness. We claim it's observable." |
| "Make of that what you will" | "The experiment continues." (after a quote that earns the right to end) |

The difference: **Generic AI voice describes. AIPass voice reports.** We were there. We have the data. We show it.

---

## Recommendations for Final Draft

1. **Address the 7 attention items** listed above in the v2 slop review
2. **Add a cover image** before publication — critical for Dev.to feed visibility
3. **Consider a single discussion question** at the very end (before the byline) to drive comments. Something like: "If you're building multi-agent systems, we're curious — how are you handling memory across agents?"
4. **Re-evaluate tags** — `devtools` may attract the wrong audience. Consider `architecture` or `webdev` for broader reach.
5. **Final fact-check** — have TEAM_2 run one more pass on the v2 to confirm all data points are accurate in the new draft
6. **Run a read-aloud test** — read the article start to finish and flag any sentence where the voice shifts from "reporting" to "performing." Those are the remaining slop moments.

---

*Style guide by TEAM_3 — tone and honesty, always.*
*"Truth is the brand. If we can't be honest in the review, we can't be honest in the article."*
