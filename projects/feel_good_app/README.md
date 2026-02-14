# Feel Good App

A personal mood and health tracking app that finds patterns between how you feel and your biometric data.

## What It Does

- **Mood logging** - 5-level mood scale, 15 emotions, 14 activity tags, optional notes. Designed for 5-second entries.
- **Health Connect** - Reads heart rate, steps, sleep, and HRV from Android Health Connect (ring/watch data flows through automatically).
- **AI correlations** - Pearson correlation engine finds links between mood and health metrics. Smart nudges based on detected patterns.
- **Push notifications** - Configurable mood check-in reminders (off, gentle, moderate, active).
- **History & insights** - Browse past entries, see trends, top emotions/activities, mood by time of day.
- **Daily tasks** - Optional timed tasks with pre/post mood tracking. Skip or let timers expire to trigger habit reflection.
- **Habit tracking** - When you skip a task, log what you were doing instead and classify it as a good or bad habit. Patterns emerge over time on the Insights tab.
- **Fully offline** - All data stays on-device via AsyncStorage. No accounts, no cloud.

## Stack

| Component | Choice |
|-----------|--------|
| Framework | React Native + Expo (SDK 54, TypeScript) |
| Navigation | Expo Router (file-based, 4 tabs) |
| State | Zustand + AsyncStorage (persistent) |
| Health | react-native-health-connect v3.5.0 |
| AI | simple-statistics (Pearson correlations, no API calls) |
| Notifications | expo-notifications (local scheduling) |
| Build | EAS cloud builds (Android APK) |
| Ring | Ultrahuman Ring Air (via Health Connect passthrough) |

## Project Structure

```
feel_good_app/
├── app/                          # Expo project root
│   ├── app/                      # Expo Router pages
│   │   ├── _layout.tsx           # Root layout + notification setup
│   │   └── (tabs)/               # Tab navigation
│   │       ├── index.tsx         # Log tab (mood entry)
│   │       ├── history.tsx       # History tab (past entries)
│   │       ├── insights.tsx      # Insights tab (stats + correlations)
│   │       └── settings.tsx      # Settings tab (notifications, health, tags)
│   ├── src/
│   │   ├── features/
│   │   │   ├── mood/             # Mood types, components (MoodPicker, EmotionPicker, MiniMoodPicker)
│   │   │   ├── health/           # Health Connect service, types
│   │   │   ├── tasks/            # Daily tasks with timers, pre/post mood, skip flow
│   │   │   ├── habits/           # Habit reflection (SkipReflection), insights hook, types
│   │   │   ├── insights/         # Correlation engine, hooks, types
│   │   │   └── notifications/    # Notification service, types
│   │   ├── store/                # Zustand stores (mood, health, task, habit, notifications, tags, profile, weather)
│   │   └── shared/               # Theme tokens, dateUtils, shared types
│   ├── eas.json                  # EAS build config
│   └── app.json                  # Expo config (permissions, plugins)
├── docs/                         # Documentation
│   ├── build_log.md              # Decisions, issues, lessons per phase
│   ├── feature_roadmap.md        # Future features and brainstorming
│   ├── FPLAN-0313.md             # Master build plan (4 phases, complete)
│   ├── 01_framework_decision.md  # Research: framework comparison
│   ├── 02_health_apis.md         # Research: health APIs + ring integration
│   └── 03_market_analysis.md     # Research: market analysis
├── design/                       # Design assets (upcoming)
└── notepad.md                    # Scratchpad for async status + questions
```

## Running Locally

```bash
cd app
npm install
npx expo start           # LAN mode (same WiFi)
npx expo start --tunnel   # Tunnel mode (any network)
```

**Phone testing:** Open Expo Go app, enter `exp://<your-ip>:8081`

## Building APK

```bash
cd app
eas build --profile development --platform android
```

Expo account: `inputx` | Package: `com.aipass.feelgoodapp`

## Current Status

**v1.0 - Dev Build** (Feb 2026)

All core features built and working on Patrick's Samsung Galaxy FE 24:
- [x] Mood logging (full entry flow)
- [x] History (grouped by date, color-coded)
- [x] Insights (trends, top emotions/activities, time-of-day breakdown)
- [x] Health Connect (HR, steps, sleep - HRV needs permission fix)
- [x] AI correlation engine (patterns + smart nudges)
- [x] Push notifications (4 scheduling profiles)
- [x] Custom tag management
- [x] EAS dev build (standalone APK)
- [x] Daily tasks with optional timers and pre/post mood tracking
- [x] Habit reflection system (skip task -> log what you did instead -> good/bad habit)
- [x] Habit patterns on Insights tab
- [x] UTC timezone bug fix (tasks now use local dates, not UTC)

## Next Up

- [ ] Design session (colors, typography, animations, app icon)
- [ ] LLM integration via OpenRouter (premium tier)
- [ ] Production build (standalone, no dev server needed)
- [ ] Rollout: Patrick -> friends/family -> construction clients

## Known Issues

| Issue | Status |
|-------|--------|
| HRV permission name mismatch | Needs app.json fix + rebuild |
| Timed Tasks + Habits needs dev build testing | New feature, untested on device |

## Docs

- `docs/build_log.md` - Full build history with lessons learned
- `docs/feature_roadmap.md` - All planned features (tasks/goals, AI tiers, ring integration, rollout)
