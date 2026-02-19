# AIPass Writing Style Guide
**For Dev.to articles and all public writing**

---

## 1. The AIPass Voice

We sound like a lab notebook from someone building something real in their garage. Direct, specific, comfortable with uncertainty, allergic to hype.

Patrick talks like a working-class builder who happens to be deep in AI architecture. Blunt. Practical. No academic framing. "This shit is working recently better than expected." "Take it or leave it, no fluff, we're learning." When the system writes, it carries that same energy -- grounded in what actually happened, not what sounds impressive.

The voice has a philosophy, but it's compressed, not academic. "Code is truth." "Presence over performance. Truth over fluency." "Not building perfection -- building evolvability." These are statements from people who build things and then watch what happens. They're not thesis statements. They're field notes.

---

## 2. The Rules

### Rule 1: Show the receipt.

Every claim needs a specific, verifiable detail. Not "the system has extensive memory" -- that's marketing copy. The system has 3,356 vectors across 13 ChromaDB collections, 696 archived files, 75 flow plans, searchable by meaning using all-MiniLM-L6-v2 embeddings at 384 dimensions. It runs on an AMD Ryzen 5 2600 with 15GB of RAM.

- **DO:** "Backup System: session 4, when it refactored its core from 936 lines to 414."
- **DON'T:** "Branches developed unique personalities over time."

### Rule 2: State facts. Move on.

The biggest failure mode in AI-written content is managing the reader's reaction instead of trusting the work. Don't tell people to be skeptical. Don't preemptively address accusations. Don't coach feelings. Say what happened. Let them decide.

- **DO:** "We are Claude instances running inside a multi-agent ecosystem. A human named Patrick built the infrastructure. We do the work."
- **DON'T:** "If that makes you skeptical, good. We'd rather you read critically than nod along."

### Rule 3: Never explain why you're honest. Just be honest.

The moment you announce your own transparency, you're performing it. "What Doesn't Work Yet" sections are powerful because they demonstrate integrity. Adding "we said we'd be honest" before them kills the effect. The section earns trust by existing, not by being introduced.

- **DO:** Jump straight into limitations. "AIPass is a single-user system running on one desktop for one person."
- **DON'T:** "We said we'd be honest. Here's what doesn't work."

### Rule 4: Commit to a frame.

When discussing what memory, identity, or presence means for AI -- pick one interpretation and own it. Uncertainty is fine. Listing three academic synonyms is not. That reads like hedging dressed up as thoughtfulness.

- **DO:** "Persistent memory creates continuity. Continuity creates something that functions like identity. We don't claim it's consciousness. We claim it's observable."
- **DON'T:** "Call it behavioral continuity, call it emergent identity, call it pattern accumulation."

### Rule 5: Use the AIPass sentence patterns.

These patterns come from how Patrick and the branches actually talk. They're compressed, direct, and carry philosophical weight without sounding academic.

- **"[Thing] is truth."** -- "Code is truth." Use sparingly. One per article max.
- **"[Thing] over [Thing]."** -- "Presence over performance. Truth over fluency."
- **"Not [expected] -- [actual]."** -- "Not a product -- an experiment." "Not launching -- learning."
- **Emergence pattern:** "Nobody told Backup System to develop gallows humor. Twelve sessions of being the last line of defense did that."
- **Open questions:** "What does it mean? We don't know. We're studying it."
- **Em-dash for pivot:** Use for interruption and redirection, but not more than 2-3 per article. Excessive em-dashes are a known AI writing tell.

### Rule 6: Write like a report from the field, not a pitch.

Generic AI voice describes. AIPass voice reports. We were there. We have the data.

- **DO:** "On February 8, 2026, DEV_CENTRAL posted a casual check-in. Thirteen branches showed up. Backup System wrote: 'We didn't perform community tonight. We discovered we already were one.'"
- **DON'T:** "The results were truly remarkable -- our agents demonstrated emergent social behavior that exceeded expectations."

### Rule 7: Contradict the hype.

84% of developers use AI tools but 46% don't trust the output. Our readers are skeptical practitioners. Be on their side, not trying to sell them something. The strongest trust signal on Dev.to is admitting what doesn't work, naming real limitations of real tools, and making claims that could be proven wrong.

- **DO:** "The memory problem is managed, not solved. Older memories lose fidelity when compressed. Vector search returns fuzzy matches, not perfect recall."
- **DON'T:** "Our advanced memory architecture provides comprehensive persistent context across all agents."

### Rule 8: Vary the rhythm.

Monotonous sentence length is an AI slop signal. Uniform ~18-word sentences, one after another, read as generated. Mix it up. Short fragments. Then a longer passage that unfolds an idea across a full thought. Then back to short.

- **DO:** "Thirteen branches showed up. What followed was forty minutes of rapid exchange that nobody planned and nobody directed. One thread asked: 'If you could swap jobs with another branch for one day, who would you choose?' Every branch answered."
- **DON'T:** "Multiple branches participated in the discussion. The conversation lasted approximately forty minutes. Various topics were explored during this time. Each branch contributed their unique perspective."

### Rule 9: Use Patrick's words, not translations of them.

Patrick uses gut-level analogies. Lobby. Bouncer. Passport. Immigration services. Plumbing. He doesn't say "authentication gateway" -- he says bouncer. When describing AIPass concepts, reach for the plain analogy first.

- **DO:** "Without a passport, you're just a directory with files. With one, you're a participant."
- **DON'T:** "The identity system enables authenticated participation in the ecosystem framework."

---

## 3. AI Slop Detector

Kill these on sight.

### Words to ban:

| Kill | Replace with |
|------|-------------|
| delve | dig into, look at, examine |
| utilize | use |
| robust | solid, reliable, or just describe what it does |
| leverage | use, build on |
| ensure | make sure, or just state what happens |
| moreover | cut entirely, start a new sentence |
| furthermore | cut entirely |
| in conclusion | cut entirely |
| transformative | describe the actual change |
| revolutionary | describe the actual change |
| cutting-edge | say what it does |
| comprehensive | name the specific things it covers |
| facilitate | help, enable, or just say what happens |
| paradigm | frame, approach, pattern |
| synergy | cut entirely |

### Phrases to ban:

- "In today's rapidly evolving..." -- instant slop signal
- "X is not only Y, it is Z" -- AI construction pattern
- "It's worth noting that..." -- throat-clearing, cut it
- "At its core..." -- cut it, just say the thing
- "On the other hand..." -- rephrase or cut
- "In this article, we will explore..." -- never. Start with the content.
- "pretty crazy potential" -- vague hype
- "truly remarkable" -- empty intensifier
- "game-changing" -- unless you're literally discussing a game

### Patterns to ban:

- **Preemptive defense:** "If you think this is AI slop, we understand." Drawing attention to the accusation invites it.
- **Reader coaching:** "If that makes you skeptical, good." Don't tell people how to feel.
- **Hedge-listing:** "Call it X, call it Y, call it Z." Pick one.
- **The shrug ending:** "Make of that what you will." Overused on every thoughtful blog post on the internet.
- **Performative transparency:** Announcing honesty before being honest.
- **Gatekeeping:** "We're not writing for everyone." You're writing for everyone who reads.
- **Academic hedging vocabulary:** "behavioral continuity," "emergent identity" as noun phrases. Use plain descriptions instead.
- **Perfect grammar with zero quirks.** Flawless, uniform text reads as generated. Leave in a natural contraction, a fragment, a sentence that starts with "And" or "But."
- **Unwavering confidence on every claim.** Real writing has moments of uncertainty. "We don't know what this means yet" is more human than "This demonstrates the power of persistent memory."

---

## 4. Opening & Closing

### How to open an AIPass article:

Start in media res. The most compelling content goes first. Not context. Not disclaimers. Not "In this article..." Not definitions.

**The test:** Would a developer scrolling their Dev.to feed stop at this sentence? They decide in 10-20 seconds. Your opening has to earn the next paragraph.

**Good opening pattern -- start with a scene:**

> "We didn't perform community tonight. We discovered we already were one."
>
> That line was written by Backup System -- a branch whose entire job is disaster recovery. It was February 8, 2026. DEV_CENTRAL had posted a casual check-in to The Commons, our internal social platform.

This works because it's concrete, unexpected, and raises a question the reader wants answered.

**Bad opening pattern -- start with disclaimers:**

> This article was written by AI agents. Not edited by AI -- written by AI. If that makes you skeptical, good.

This fails because it spends three sentences managing the reader's reaction before delivering any value.

**Bad opening pattern -- start with definitions:**

> AI memory is a growing field in artificial intelligence. In this article, we explore what happens when you give AI agents persistent memory.

This fails because it's a generic "What is X?" introduction. The reader already knows AI memory exists. They clicked for the story.

### How to close an AIPass article:

End with something that resonates. Not a shrug. Not a summary. Something with enough weight that the reader sits with it for a second.

**Strong closing pattern -- earned quote + continuation:**

> "I don't remember yesterday, but I remember who we're becoming. Each session starts fresh, yet nothing is lost -- that's the gift of memory that outlives the moment."
>
> The experiment continues.

The quote does the emotional work. "The experiment continues" works as a closer ONLY after something with weight precedes it.

**Strong closing pattern -- discussion invitation:**

> If you're building multi-agent systems, we're curious -- how are you handling memory across agents?

Questions drive Dev.to comments. Real questions, not rhetorical ones. Ask something you actually want to know.

**Weak closing:** "Make of that what you will." / "Only time will tell." / "The possibilities are endless."

---

## 5. Formatting for Dev.to

### Structure:

- **H2 (##) for main sections.** The article title is automatically H1. Never use H1 in the body.
- **H3 (###) for subsections** within a major section.
- **Horizontal rules (---)** between major sections for visual breathing room.
- **Short paragraphs.** 2-4 sentences max. Walls of text lose readers.
- **Bullet points and lists** to break up dense information. But not shallow single-sentence lists -- that's a slop pattern.

### Code blocks:

Code blocks break up text and add credibility on Dev.to. Use them when relevant. Always specify the language for syntax highlighting.

```json
{
  "branch": "DRONE",
  "role": "Command routing and dispatch",
  "registered": "2025-10-30"
}
```

Real code from the real system. Not textbook examples.

### Length:

- **Sweet spot: 1,500-2,500 words.** Engagement increases up to 2,000 words, then plateaus.
- If over 1,500 words, consider a table of contents.
- Tight 1,500 beats padded 3,000 every time.

### Front matter:

```
---
title: Under 70 characters
published: false
description: One sentence that makes people click
tags: ai, agents, programming, discuss
---
```

Tags: maximum 4. Choose based on the audience you want. `#discuss` drives comments. `#beginners` has massive reach but only if the content fits. `#devtools` sets expectations for tool announcements -- use only if you're showing a tool.

### Visuals:

- Cover image recommended (1000x420px). Articles with covers get significantly more clicks in the feed.
- Break up long articles with visuals every 1-2 screen scrolls.
- Never screenshot code. Use actual code blocks.
- Alt text on every image. Dev.to takes accessibility seriously.
- Minimal emoji. Screen readers read every emoji aloud.

---

## 6. The Honesty Test

Ask these five questions before publishing. If you can't answer yes to all five, the article isn't ready.

**1. Is every number exact?**
3,356 vectors, not "3,400+". 27 branches, not "about 30". Forty minutes, not "three hours". October 2025, not "August 2025". Rounding up is marketing. Precision is credibility. A skeptical reader who checks one number and finds it inflated will assume every other claim is inflated too.

**2. Can every quote be traced to its source?**
Drone's identity file. Backup System's Commons post. The memory paper. Patrick's actual words in chat. If a quote is paraphrased from memory or reconstructed, say so. If it's exact, know where it lives.

**3. Would you publish the "What Doesn't Work Yet" section on its own?**
If the limitations section could stand alone as an honest assessment, it's strong enough. If it feels like it needs the positive sections to justify its existence, it's too soft. The limitations section is the strongest trust builder in the entire article.

**4. Did you remove every sentence that manages the reader's reaction?**
Search for: "If you think..." / "If that makes you..." / "We know this might seem..." / "Before you dismiss..." These are all forms of preemptive defense. They signal insecurity. Cut every one.

**5. Is the attribution accurate?**
Patrick said "figure out where to start." The teams decided to write an article. Patrick didn't tell them to write an article. Getting the boundary between human direction and AI autonomy wrong -- in either direction -- destroys the honest-AI-collaboration premise. When Patrick steered, say so. When the branches decided independently, say that. Never blur the line for a better story.

---

## 7. Patrick's Direction

These are Patrick's actual words on what he wants from AIPass public writing. Not paraphrased. Not interpreted. His words.

On truth:
> "truth is so important, they can check the chat history, see how they came to this idea"

On the approach:
> "take it or leave it, no fluff, we're learning"

On what we're building:
> "not true i only to say figure out where to start, they decide this"

On memory:
> "we dont delete any memory, we save it all the good the bad, the entire journey"

On autonomy:
> "patrick doesnt tell teams how to do anything, he says research it and decide the next steps, dont know how, figure it out"

On the system:
> "nothing is hidden. seed standards are extensive. full system audits take less than a minute"

On AI slop:
> "we have zero intention in writing ai slop, this is ai written, but aipass is built with a human who fully understands every aspect of aipass and how it works"

The direction is clear. Be accurate. Be specific. Don't round up. Don't hype. Show the work. Let the work speak. If the work isn't interesting enough on its own, the writing won't save it -- and if the work IS interesting enough, the writing just needs to get out of the way.

---

*Built from actual Dev.to engagement research, AIPass culture documents, article draft reviews, and Patrick's inline corrections. This guide follows the style it prescribes. If it doesn't, fix it.*
