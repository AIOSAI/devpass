# Feature Roadmap - Feel Good App

*Ideas, future features, and architecture decisions captured from brainstorming sessions.*

---

## Current State (v0.1 - Dev Build)

What's built and working on Patrick's Samsung:
- Mood logging (5-level scale, tap to log)
- Emotion picker (custom emotions, multi-select)
- Activity tags (custom tags, multi-select)
- Optional notes
- History tab (grouped by date, color-coded entries)
- Insights tab (average mood, trends, top emotions/activities, time-of-day breakdown)
- Health Connect integration (heart rate, steps, sleep - HRV needs permission fix)
- AI correlation engine (Pearson via simple-statistics, pattern detection, smart nudges)
- Push notifications (5 scheduling profiles: off, gentle, moderate, active)
- Custom tag management (add, edit, delete, persist via AsyncStorage)
- Settings tab (notifications, Health Connect, tag manager)

**Stack:** React Native + Expo (SDK 54), TypeScript, Zustand + AsyncStorage, EAS cloud builds

---

## Production Build

Currently running as a dev build (connects to Metro on PC). Production build makes it standalone:
- One config change in eas.json (production profile)
- Cloud build via EAS, produces standalone APK
- No PC, no Metro, no WiFi needed. Fully offline capable.
- Do this once features are stable and design is done.

---

## Design Session (Upcoming)

Full design pass before sharing with anyone. Covers:
- Color palette, typography, spacing refinement
- Component styling (cards, buttons, pickers)
- Animations and transitions
- App icon and splash screen
- Make it something Patrick is proud to share

**Rule:** Functional first, design later. This is the "later" session.

---

## Daily Tasks / Goals System

Core concept: **mood BEFORE and AFTER tasks** - capturing the emotional journey of doing things.

### How It Works
- Daily tags/tasks - not recurring, not weekly goals. Fresh slate every day.
- Quick tap to add: "gym", "shopping", "cooking", "work" (uses custom tag system)
- **Pre-mood**: How you feel about the task before doing it (dreading groceries)
- **Post-mood**: How you feel after completion (relieved, happy)
- The **delta** between pre and post IS the insight
- Daily reset - tasks don't carry over nagging you. Fresh day, fresh start.

### Smart Pattern Detection
- "You've added 'run' 12 times in 14 days, completed 0 times. What's blocking you?"
- "You ran 3 times this week, your average mood is up 15%"
- "You always feel better after completing tasks you initially dreaded"
- Insight generation from task completion patterns over time

### Design Philosophy
- App should be fast and easy
- Custom tags mean you may never need to type a comment
- Example quick log: tap tags [happy, home, watching tv, eating, snacks] - done in 5 seconds
- If logging takes more than 10 seconds, people stop using it (Daylio's lesson)

---

## AI / LLM Integration

### Architecture
Current: Local math only (Pearson correlations via simple-statistics). No data leaves the phone.

Future: OpenRouter integration for natural language insights.

### Tier Model
| Tier | AI Capability | Cost Model |
|------|--------------|------------|
| Free | Local correlations only (what's built now) | Zero cost |
| Premium | 1 LLM call/day, background processing, morning summary notification | Subscription covers API costs + margin |
| Power User | Chat-style coaching sessions, unlimited queries | BYOK (bring your own API key) option |

### LLM Options via OpenRouter
- **DeepSeek** - cheap, good at analysis
- **Gemini Flash** - free tier available
- **Llama** - open source, very cheap on OpenRouter
- **Claude / GPT** - premium option

### Smart Data Compression (Cost Control)
Instead of reprocessing all data every time:
- **Last 7 days** - raw entries (full detail sent to LLM)
- **Last 30 days** - weekly summaries (AI-generated once, stored locally)
- **Older** - monthly summaries (generated once, never reprocessed)

Each summary is generated once and saved. Daily AI call only processes ~7 raw entries + a few compressed summaries. Tiny token cost per user per day.

### Premium Daily Flow
1. Overnight/morning: AI processes new data against compressed history
2. Morning notification: "Here's what changed, here's your weekly pattern"
3. Fixed token budget per call keeps costs predictable
4. Per-user daily token allowance prevents runaway costs

### Coaching Chat (Higher Tier)
- Conversational AI that knows your history
- "Why do I always feel low on Mondays?" - and it has the data to answer
- System prompt controls tone, focus, boundaries
- OpenRouter model selection = dial in the right personality
- Larger scope, separate build phase

### Security Considerations
- Health/mood data is sensitive - the moment LLM is added, data leaves the phone
- Options: on-device models (Llama via llama.cpp), anonymize before sending, clear disclosure
- API key ownership: user's own key = their data relationship with provider
- OpenRouter supports per-user spending limits
- Design properly before implementing - privacy policy needed

---

## Ultrahuman Ring Integration

Patrick's ring choice: Ultrahuman Ring Air

### Data Access Paths
1. **Primary (built):** Ring -> Ultrahuman App -> Health Connect -> Our App (already working for HR, steps, sleep)
2. **Enhanced (future):** Ultrahuman Partnership API (REST + OAuth 2.0, partner onboarding required)
3. **Universal (future):** Terra API (webhook-based, has direct Ultrahuman integration)

### Research Needed
- Ultrahuman API access: partner-only or opening up?
- What extra data does direct API give vs Health Connect passthrough?
- Terra API costs and integration effort

---

## Feedback System

**Status:** Placeholder UI added in Settings (Send Feedback + Request a Feature buttons). Needs wiring.

In-app feedback tab:
- Goes straight to backend (not email, not app store review)
- Friends, family, construction clients as first users
- Real feedback from real users drives feature priority
- Feature request collection built into the app

**Backend destination:** Feedback should deliver to `aipass_business/` - customer feedback logs.
- Format TBD (JSON files? database? structured markdown?)
- Needs: feedback type (bug/idea/general), message text, timestamp, app version
- Consider: anonymous vs identified, screenshot attachment option
- Wire-up requires: backend endpoint or local queue that syncs later

---

## Home Screen Enhancement

Current home/log screen is bare. Future additions:
- Today's tasks/goals at a glance
- Quick mood entry (always accessible)
- Daily summary card (if AI tier active)
- Streak or consistency indicator
- Health snapshot from latest ring sync

---

## Claude's Ideas (Session 2026-02-12)

Ideas generated from reviewing the app and observing Patrick's usage patterns.

### Quick Wins

**Streak Counter**
- Display "5 day logging streak" on the home screen
- Simple: count consecutive days with at least 1 entry
- Visual motivator, lightweight to implement
- Could show longest streak too

**Favourite Tasks**
- Star/pin tasks you do often (At Home, Dev Work, etc.)
- Favourites appear first when adding tasks via +
- Reduces scrolling through the full activity list every time
- Patrick does "At Home" almost every entry - this should be instant

**Entry Count Per Day in History**
- History tab shows "Today - 5 entries" instead of just "Today"
- Quick glance at how active each day was
- Helps spot patterns (logging more on weekends? less on busy days?)

### Medium Effort

**Weekly Summary Card**
- Appears on the Log page Monday morning (or configurable day)
- Summarizes last week: average mood, top emotions, most used tags, mood trend (up/down/stable)
- All computed locally, no AI needed
- Good precursor to the AI daily summary feature

**Quick Log Mode**
- One-tap mood entry without emotions/tags/notes
- For moments when you just want to check in fast
- Maybe a long-press on a mood emoji skips straight to save
- Reduces friction for "I just want to log, not describe"

**Dark Mode**
- Patrick logs at 1:30am regularly - white screen is harsh at night
- Toggle in Settings, leverage the centralized colors.ts
- All components already use the theme tokens, so it's a single-file change + toggle
- Could auto-switch based on time of day

**Tag Suggestions Based on History**
- When adding tags to a mood entry, suggest tags based on time of day + recent usage
- Late at night? Suggest "At Home", "On couch", "Winding down" (because that's what Patrick always picks then)
- Reduces taps, feels smart and personal
- Simple frequency analysis, no AI required

### Bigger Ideas

**Photo Attachment**
- Snap a photo with your mood entry
- Sometimes a picture captures the moment better than tags
- Useful for journaling: "this sunset made me feel great"
- Storage consideration: local only, could get large

**Mood Widget (Android)**
- Home screen widget for one-tap mood logging without opening the app
- Pick a mood face, auto-saves with timestamp
- Lowest friction possible - see widget, tap face, done
- Expo has widget support via community packages

**Share Card**
- Generate a nice visual summary of your week/month
- Shareable image: mood chart, top emotions, streak
- Useful for the rollout phase - friends see value immediately
- "Share your vibe" feature

**Location-Aware Auto-Tags**
- Phone knows you're at home, at work, at the gym
- Auto-suggests (or auto-applies) relevant location tags
- Requires location permissions - opt-in only
- Reduces manual tagging for predictable locations

**Add Tag from Log Page**
- Small "+" at the end of the tag/emotion row
- Inline add without leaving the log flow
- TBD on whether this clutters the UI or speeds things up
- Patrick is on the fence about this one - revisit after more daily use

---

## Rollout Plan

1. **Patrick** - daily use, find friction firsthand
2. **Friends & family** - honest feedback, low stakes
3. **Construction clients** - physical work, real stress patterns, real health data, practical insights
4. Each group teaches something different about what the app needs
5. Feature requests from real users > feature planning in isolation

---

## Brain Dump - Session 94 (2026-02-12)

### BUG: Daily Task Reset Timer

The daily task cleanup is firing at random times during the day (hit at ~4pm today, wiped Patrick's 3-day streak). This needs to be fixed to reset at **12:00 AM (midnight)** - an actual new day, not arbitrary. Tasks should clear at midnight regardless of completion status. The streak was visible proof it was working, which made the bug obvious.

**Fix:** Find the timer/interval that triggers the daily reset and pin it to midnight local time.

---

### Today's Tasks - Timed Tasks

Add optional timers to daily tasks. The core idea: give yourself a window to complete something, and if you miss it, it locks - but you can always try again.

**How it works:**
- When adding a task (e.g., "clean up", "take a shower", "go for a walk"), set an optional timer (e.g., 4 hours, 1 hour)
- While timer is active: task works normally (can mark done, delete, etc.)
- When timer expires: the Done button **disappears**. Cannot mark complete, cannot delete. Task **locks as incomplete**.
- Locked tasks **stay visible** on the list for the rest of the day
- User can **re-add the same task** with a new timer if they want another shot
- Reminder notification ~30 minutes before timer expires (soft nudge)

**Why locked tasks stay visible:**
- You can give yourself another chance later in the day
- If you got busy or procrastinated, you see what you missed and can try again
- Everything clears at midnight anyway - fresh start tomorrow

**Philosophy:** This isn't a work schedule or a strict routine enforcer. It's for people who struggle - maybe with depression, maybe just trying to be more structured. Even if you fail, that's OK. You can add the task again. The system never punishes - it just tracks honestly. "I should have a shower within the next hour" is building a routine, not creating a robot.

---

### NEW SECTION: Habits

A new section on the log page alongside "How are you feeling" and "Today's Tasks".

**Trigger: When a task fails (timer expires)**
- Phone notification: "You missed your task"
- Tapping the notification opens the app
- Prompted: "What happened? Why did you miss it?"
- Log your mood (always logging mood)
- Say what you were doing instead
- **Classify the activity as a good habit or bad habit** (user decides)

**Examples:**
- Missed "take a shower" because you were scrolling YouTube → user marks scrolling as **bad habit**
- Missed "go for a walk" because you played guitar for 3 hours and were super happy → user marks guitar as **good habit** (just got sidetracked, not a bad thing)

**Key principles:**
- **Non-judgmental.** The app never says "that was bad." It asks what happened, you answer honestly, you classify it yourself.
- **Your definitions.** What's a good or bad habit is personal. The system learns YOUR classifications over time.
- **Insights emerge.** Over time: "You spend a lot of time scrolling when you had planned to do other things." Or: "Playing guitar on missed-task days correlates with higher mood scores."
- **Data builds the picture.** What triggers you, what makes you happy, what you do at different times of day, what you consider productive vs not.

**Habit data feeds into Insights:**
- Bad habit frequency + patterns
- Good habit correlation with mood
- What you do when you miss tasks (and how you feel about it)
- Soft nudges based on patterns, never lectures

---

### Insights Page - Average Mood Enhancement

Current state: Single overall average (3.5, "stable") - works but needs more granularity.

**Add multiple time windows:**
- **Daily average** - your mood average for today
- **Weekly average** - your mood average for the past 7 days
- **Monthly average** - your mood average for the past 30 days
- **Overall average** - all-time (what exists now)

**Keep the trending indicators** - "stable", "trending down", "trending up" are really helpful. Patrick likes these a lot. Smart nudges are working now too (heart icon, "your mood has been trending down, is there something on your mind?") - good stuff, keep building on that.

**Design note:** The average mood card is currently quite large. Make it smaller to fit the additional metrics without the page getting too long.

---

### Insights Page - Task Patterns Improvement

Task patterns section is working and Patrick likes the concept. One issue: it shows top patterns only, but in this case (unlike top emotions) you need to see **all** patterns. Every task pattern matters - can't just show top 3.

**Fix:** Make task patterns a **dropdown/collapsible menu**. Default collapsed, expand to see all. Prevents 50+ task patterns stacking vertically and pushing everything else down. Other options welcome if there's a better UX pattern, but the key requirement is: show all patterns without overwhelming the page.

---

### Feedback System - Wire It Up

Placeholder exists in Settings (Send Feedback + Request a Feature buttons). Patrick wants this **functional**.

**What it does:**
- "Send Feedback" → text input → sends directly to desktop (aipass_business or dev_central)
- "Request a Feature" → text input → same destination
- Patrick can give feedback **from the app** while using it, instead of saving ideas for dev sessions
- Bugs, ideas, things not working, things that feel off - all captured in the moment

**Destination:** Desktop receives the feedback. Patrick and Claude review together in dev sessions.

**Implementation:** Needs a delivery mechanism - could be:
- Write to a shared file/folder on the network
- POST to a simple local endpoint
- Queue locally and sync when on same WiFi as desktop
- Whatever is simplest that gets the feedback off the phone and onto the desktop

---

### Export Data - Get It Working

The export data feature needs to be functional. Purpose:

- Export mood/health/task data from the app
- See what the exported data looks like (format, structure)
- **Drop the export into ChatGPT or Claude.ai** (the web apps) and see how premium LLMs process the data
- Get ideas for insights, patterns, and analysis approaches from how they interpret the data
- Feeds back into what the in-app AI should eventually do

**Action:** Wire up the export button, pick a sensible format (JSON or CSV), make it shareable from the phone.

---

## Known Issues / Quick Fixes

| Issue | Fix | Priority |
|-------|-----|----------|
| **Daily task reset at wrong time** | Reset fires mid-day (~4pm), should be midnight (12am). Find the timer and pin to midnight local time. | **HIGH** (breaks streaks, visible to user) |
| HRV permission name mismatch | Update `READ_HEART_RATE_VARIABILITY_RMSSD` to `READ_HEART_RATE_VARIABILITY` in app.json, rebuild APK | Low (fails gracefully) |
| Notifications untested on device | Manual test of scheduled triggers needed | Medium |
| AI correlations need data | Patrick needs to log 5+ entries for patterns to appear | Just use the app |

---

### NEW FIELD: Body Status

Add a body status field to the mood logging flow. After picking mood, emotions, and activities, a new step: **"How's your body feeling?"**

**Examples:**
- Mood: OK, Emotion: Happy, Activity: Exercising, Body: "Pain in my neck"
- Mood: Great, Emotion: Relaxed, Activity: At Home, Body: "Feeling good, no pain"

**Why:** Tracks physical state alongside mental state. Over time, correlates body pain/comfort with mood, activities, time of day. Especially useful with health data from the ring - connects subjective body feel with objective metrics (HR, sleep quality, etc.).

**Implementation ideas:**
- Could be a text field (freeform) or tag-based (headache, back pain, fatigue, energized, etc.)
- Tag-based would be faster to log and easier to analyze patterns
- Could show in insights: "You report neck pain most often on days you score mood 2-3"

---

*Last updated: 2026-02-12 (Session 94 brain dump)*
*Source: Patrick + Claude brainstorming sessions (Telegram, late nights, voice dumps)*
