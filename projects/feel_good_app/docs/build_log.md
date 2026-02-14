# Build Log - Feel Good App

*Track every decision, mistake, and lesson. This becomes a reusable flow template.*

---

## Phase 1: Project Setup (Session 79)

### Decisions Made

| Decision | Choice | Why | Alternatives Considered |
|----------|--------|-----|------------------------|
| Framework | React Native + Expo (TypeScript) | AI-friendly, single codebase, Expo EAS for builds | Flutter (Dart less AI-friendly), KMP (too new) |
| Navigation | Expo Router (file-based) | Industry standard for Expo, clean routing | React Navigation (manual config) |
| State Management | Zustand + AsyncStorage | Lightweight, persistent, TypeScript-first | Redux (overkill), Context API (no persistence) |
| HealthKit Library | `@kingstinct/react-native-healthkit` v13.1.1 | Actively maintained, TypeScript-first | `react-native-health` (stale, ~1yr no updates) |
| Health Connect Library | `react-native-health-connect` v3.5.0 | Standard community library, actively maintained | - |
| Smart Ring | Ultrahuman Ring Air | No subscription, syncs to both health stores, partner API | Oura (subscription paywall), RingConn (less reliable) |
| Project Structure | Feature-based (mood/, health/, insights/) | Scales cleanly, each feature self-contained | Flat structure (messy at scale) |

### What We Built

1. **Research phase** (3 parallel agents)
   - Framework comparison → `research/01_framework_decision.md`
   - Health APIs + ring integration → `research/02_health_apis.md`
   - Market analysis → `research/03_market_analysis.md`
   - **Lesson:** Parallel agents = fast research. 3 agents, all done in ~2 min.

2. **Expo project scaffolded**
   - `npx create-expo-app@latest app --template blank-typescript`
   - 696 packages, 0 vulnerabilities
   - **Lesson:** Use `blank-typescript` template, not `tabs` - cleaner starting point.

3. **Type system first**
   - Built all domain types BEFORE any UI: mood/types.ts, health/types.ts, insights/types.ts, shared/types.ts
   - **Lesson:** Types first = fewer rewrites. The types ARE the domain model.

4. **Theme tokens**
   - colors.ts (mood colors, UI palette), typography.ts (7-level scale), spacing.ts (4px base)
   - **Lesson:** Set design tokens early. Every component references them. Change once, update everywhere.

5. **Expo Router + Tab Navigation**
   - Replaced App.tsx with file-based routing: app/_layout.tsx → app/(tabs)/
   - 4 tabs: Log, History, Insights, Settings
   - **Lesson:** `package.json` main must be `"expo-router/entry"`, not `"index.ts"`. Delete old App.tsx and index.ts.

6. **Zustand Store**
   - moodStore.ts with AsyncStorage persistence
   - **Lesson:** `zustand` had peer dep conflict with expo's react-dom. Fix: `npm install zustand --legacy-peer-deps`

7. **Mood Logging Screen (core UX)**
   - MoodPicker (5 levels), EmotionPicker (15 emotions), TagPicker (14 tags), optional note
   - Stepped reveal: mood first → emotions appear → tags appear → note appears
   - **Lesson:** Progressive disclosure keeps it simple. Don't show everything at once.

### Issues Hit

| Issue | What Happened | Fix | Time Lost |
|-------|--------------|-----|-----------|
| zustand peer dep conflict | npm ERESOLVE with react-dom version | `--legacy-peer-deps` flag | ~2 min |
| notepad.md write conflict | File modified since read | Re-read then write | ~1 min |
| Premature email archival | Closed all inbox without reading | Read from deleted/ folder to recover | ~3 min |
| Raw JSON on localhost:8081 | Dev server showed native bundle manifest, not the app | Install `react-dom` + `react-native-web` via `npx expo install`, restart with `--web` flag | ~3 min |
| White screen - import.meta | `SyntaxError: Cannot use 'import.meta' outside a module` in browser | 4-layer fix (see below) | ~8 min |
| Android java.io exception | Phone failed to download remote update on first connect | Same WiFi check, retry - resolved on second attempt | ~2 min |

#### The import.meta Bug (4 Layers Deep)

This one was a cascade - each fix revealed the next problem:

1. **Missing metro.config.js** - Web bundling needs explicit Metro config at project root. Created `metro.config.js` with `getDefaultConfig(__dirname)`.
2. **Missing babel.config.js** - Expo web needs Babel configured. Created `babel.config.js` with `babel-preset-expo`.
3. **Missing babel-preset-expo package** - Despite being an Expo project, the preset wasn't explicitly installed. Fix: `npx expo install babel-preset-expo`.
4. **import.meta still failing** - Metro web bundles load as `<script defer>` not `<script type="module">`, so `import.meta` is illegal syntax. Fix: Set `unstable_transformImportMeta: true` in babel-preset-expo options. This compiles `import.meta` to `globalThis.__ExpoImportMetaRegistry` before the bundle reaches the browser.

**Lesson:** Expo's web mode is less batteries-included than native. Metro + Babel config files aren't auto-generated. When hitting web-specific errors, check the bundling pipeline layer by layer. Agent research saved us here - deployed a research agent that found the `unstable_transformImportMeta` fix quickly.

### Version Audit (Feb 2026)

| Package | Version | Status |
|---------|---------|--------|
| Expo SDK | 54 | CURRENT (55 in beta) |
| React Native | 0.81.5 | Aligned with SDK 54 |
| React | 19.1.0 | Minor behind, bumps with SDK 55 |
| Expo Router | 6.0.23 | CURRENT |
| New Architecture | Enabled | Correct (mandatory in SDK 55) |

**Flag:** `react-native-health` is stale. Use `@kingstinct/react-native-healthkit` instead.

### Platform Targets

| Platform | Target SDK | Min Deployment | Notes |
|----------|-----------|----------------|-------|
| Android | API 35 (Android 15) | API 24 (Android 7) | Required for new Play Store apps |
| iOS | Xcode 16 / iOS 18 SDK | iOS 16 | Xcode 26 required by April 2026 |

---

## Phase 2: First Boot + Testing (Session 79 continued)

### What We Did

8. **Web testing (Chrome)**
   - Installed `react-dom` + `react-native-web` for web mode
   - Created `metro.config.js` and `babel.config.js` (not auto-generated by Expo)
   - Resolved 4-layer import.meta cascade (see Issues above)
   - Full click-through verified: mood → emotions → tags → note → save → entry count updates
   - **Lesson:** Always `--clear` the Metro cache after config changes. Stale cache = stale errors.

9. **Phone testing (Android - Expo Go)**
   - Patrick installed Expo Go on Samsung Galaxy FE 24 + iPhone 12 Mini
   - First attempt: typed `exp://` URL in phone browser → Google search (wrong place). Needs Expo Go app, not browser.
   - Second attempt in Expo Go: java.io exception → retry → loaded successfully
   - Patrick confirmed multi-tag selection working and "actually helpful"
   - **Lesson:** `exp://` is a custom protocol only Expo Go understands. QR code scan from Expo Go is the easiest path.

### Completed
- [x] Run Expo dev server - verified in Chrome + Android
- [x] Mood entry flow - working end to end
- [x] Local data persistence - Zustand + AsyncStorage confirmed (entry count persists)

### Still Planned
- [x] History screen - show past entries (Session 88)
- [x] Insights screen - computed stats from mood data (Session 88)
- [ ] Mood entry flow polish (animations, haptics)
- [ ] iPhone testing via Expo Go
- [ ] Health data integration (HealthKit + Health Connect)
- [ ] Ring data flow: Ring → Companion App → Health Store → Our App

### Open Questions
- Notification tone: gentle nudge text style?
- Data storage: local-only vs cloud backup option?
- AI model for insights: on-device vs API call?

---

## Workflow Patterns (For Future Template)

### What's Working
- **Research first, build second.** Parallel research agents before writing code.
- **Types before UI.** Domain model = source of truth.
- **Theme tokens early.** Pay upfront, save on every component.
- **Progressive disclosure.** Show what's needed, reveal as user progresses.
- **Feature-based structure.** Each feature owns its components, hooks, services, types.

### What to Watch
- **Dependency conflicts.** Expo pins React versions tightly. Don't fight it - use `--legacy-peer-deps` when needed.
- **Library freshness.** Check npm last-published dates. Stale libraries = future pain.
- **SDK alignment.** Stay on Expo's stable SDK. Don't jump ahead.
- **Web mode needs explicit config.** Unlike native, Expo web doesn't auto-generate metro.config.js or babel.config.js. You'll hit cryptic errors without them.
- **Agent-driven debugging.** When a bug is unfamiliar (like import.meta in Metro), deploying a research agent is faster than manual googling. The agent found `unstable_transformImportMeta` in one pass.

---

---

## Phase 3: History + Insights + Connectivity (Session 88)

### What We Built

10. **History tab** - Functional screen pulling from Zustand store
    - Entries grouped by date (Today, Yesterday, or formatted date)
    - Each card: mood emoji + color-coded label, time, emotions, activity tags, note (3-line truncate)
    - Empty state when no entries
    - Uses shared theme tokens

11. **Insights tab** - Computed stats from real mood data
    - Average mood score (1-5 scale, color-coded)
    - Mood trend (improving/stable/declining, needs 4+ entries)
    - Top 5 emotions with bar chart
    - Top 5 activities with bar chart
    - Mood by time of day (morning/afternoon/evening averages)
    - Placeholder cards (dashed border) for Health Correlations and Smart Nudges
    - All computed live from store data via `useMemo`

12. **Snapshot workflow established**
    - `_snapshots/v1.0_working_2026-02-10/` - first snapshot of known-working state
    - Pattern: copy working files alongside originals, swap to test/rollback
    - Used `.current` suffix to hold new versions while testing snapshot

### Issues Hit

| Issue | What Happened | Fix | Time Lost |
|-------|--------------|-----|-----------|
| Hot reload not triggering | New history.tsx didn't auto-load on phone | Shake phone → dev menu → Reload (full reload) | ~2 min |
| Expo Go LAN mode - wrong WiFi | java.io exception, phone on different WiFi network (similar names) | Switch to correct WiFi network | ~3 min |
| Expo Go LAN mode - AP isolation | Same WiFi, same subnet (192.168.1.x/24), phone still can't reach desktop | Router has AP/client isolation enabled on 5GHz band. Switched to tunnel mode | ~5 min |
| Phone browser treats IP as search | Typing `192.168.1.74:8081` in phone browser opens Google search | Must include `http://` prefix: `http://192.168.1.74:8081` | ~1 min |
| Web vs phone separate storage | Desktop web shows no entries despite phone having 4 | Expected: web uses localStorage, phone uses AsyncStorage. Separate databases | ~1 min (explanation only) |

### Workarounds

#### Expo Go Connection Priority
Try in this order when phone can't connect:
1. **Check WiFi** - Same network name doesn't mean same network. Verify phone IP is in same subnet as desktop (`192.168.1.x`)
2. **LAN mode** (default) - Works if devices can talk directly. Test: open `http://<desktop-ip>:8081` in phone browser
3. **Tunnel mode** (fallback) - If LAN fails due to AP isolation or subnet issues:
   ```bash
   # Requires @expo/ngrok (already installed)
   npx expo start --tunnel
   ```
   - Routes through ngrok, no local network needed
   - Tunnel URL: `exp://<hash>-anonymous-8081.exp.direct:443`
   - Slower than LAN but works through any network
4. **Force reload** - Shake phone → dev menu → Reload. Hot reload doesn't always pick up new files

#### File Version Swapping (Local Snapshots)
```bash
# Save current as snapshot
cp file.tsx _snapshots/v1_working/file.tsx

# Test snapshot version (swap out new code)
cp file.tsx file.tsx.current        # save new version
cp _snapshots/v1/file.tsx file.tsx  # restore snapshot

# Swap back to new version
mv file.tsx.current file.tsx
```
Pattern: `.current` suffix = new version being tested. Snapshot = known-good fallback.

---

## Phase 4: EAS Build + Notifications + Health + AI (Session 88 continued - FPLAN-0313)

### What We Built

13. **EAS Development Build Configuration**
    - eas-cli v16.32.0 installed globally
    - eas.json: development profile (APK output, no credentials, internal distribution)
    - app.json: android.package `com.aipass.feelgoodapp`, health permissions, all plugins configured
    - expo-dev-client installed for development builds
    - **Blocker:** Needs Expo account for cloud build (no local Android SDK)

14. **Push Notification System**
    - `notificationService.ts`: Android channel setup (HIGH importance), permission request, daily scheduling
    - `notificationStore.ts`: Zustand + AsyncStorage persists enabled state, frequency, scheduled IDs
    - Nudge frequencies: Off (none), Gentle (2x/day 9am+8pm), Moderate (4x/day), Active (5x/day)
    - Settings tab wired: toggles control actual scheduled notifications
    - Root layout: notification handler, channel setup on mount, tap-to-open listener

15. **Health Connect Integration (Android)**
    - `healthConnectService.ts`: Init, permission request, read HeartRate/HRV/Steps/Sleep
    - `getDailySummary()`: Aggregates all metrics for a day (avg HR, avg HRV, total steps, sleep minutes + quality)
    - Sleep quality scoring: ratio of deep+REM to total sleep + total hours → excellent/good/fair/poor
    - `healthStore.ts`: Zustand + AsyncStorage, sync last 7 days, connection state tracking
    - Settings tab: Health Connect toggle → real permission request + data sync
    - Insights tab: Health data grid (HR, steps, sleep, HRV) replaces old placeholder

16. **AI Correlation Engine**
    - `correlationEngine.ts`: Pearson correlations via `simple-statistics` library
    - Computes mood vs heartRate/steps/sleep/HRV correlations
    - Confidence levels: |r| > 0.7 = high, > 0.4 = moderate, else low
    - `detectPatterns()`: Human-readable insights from correlations + mood-only analysis
    - `generateNudges()`: Smart suggestions (health-triggered, pattern-triggered, general)
    - Works with any data volume: 0 entries → encouragement, 5+ → full analysis
    - `useCorrelations` hook: useMemo-wrapped, combines both stores
    - Insights tab: Patterns section + nudge cards + "linked to mood" badges on health metrics

### Decisions Made

| Decision | Choice | Why | Alternatives Considered |
|----------|--------|-----|--------------------------|
| Build method | EAS cloud build | No local Android SDK, cloud is zero-setup | Local build (needs Android SDK + JDK) |
| Notification library | expo-notifications | SDK 54 native, local scheduling built-in | react-native-push-notification (no Expo plugin) |
| Health library | react-native-health-connect | Standard community lib, Expo config plugin exists | Direct Android API calls (too low-level) |
| Correlation method | simple-statistics (Pearson) | Lightweight JS, no native deps, sufficient for paired data | TensorFlow Lite (overkill), mathjs (too heavy) |
| AI approach | Statistical correlation | Works immediately with small data, no training needed | On-device ML (needs training data), API calls (needs network) |
| Android only | Skip iOS for now | Patrick tests on Samsung, HealthKit needs separate work | Both platforms (doubles scope) |

### New Packages Added

| Package | Version | Purpose |
|---------|---------|---------|
| eas-cli | 16.32.0 (global) | Build management |
| expo-dev-client | ~6.0.20 | Development build UI |
| expo-notifications | ~0.32.16 | Scheduled notifications |
| react-native-health-connect | ^3.5.0 | Health Connect SDK |
| expo-health-connect | ^0.1.1 | Expo config plugin for Health Connect |
| expo-build-properties | ^1.0.10 | Android SDK version config |
| simple-statistics | ^7.8.8 | Pearson correlation, mean, stddev |

### Issues Hit

| Issue | What Happened | Fix | Time Lost |
|-------|--------------|-----|-----------|
| expo-notifications deprecated API | shouldShowBanner/shouldShowList now required (v0.32.16) | Added all 3 properties to notification handler | ~1 min |
| removeNotificationSubscription gone | Function removed in this version | Use subscription.remove() directly | ~1 min |
| TimeRangeFilter type not exported | react-native-health-connect doesn't re-export base.types | Derived type from ReadRecordsOptions['timeRangeFilter'] | ~1 min |

### Files Created This Phase

```
src/features/notifications/types.ts          - NudgeFrequency type
src/features/notifications/services/notificationService.ts - Notification scheduling
src/store/notificationStore.ts               - Notification state (Zustand)
src/features/health/services/healthConnectService.ts - Health Connect API
src/store/healthStore.ts                     - Health data state (Zustand)
src/features/insights/services/correlationEngine.ts - AI correlation engine
src/features/insights/hooks/useCorrelations.ts - Hook combining stores + engine
eas.json                                     - EAS build configuration
```

### Files Modified This Phase

```
app.json                    - android.package, permissions, plugins
package.json                - 7 new dependencies
app/app/_layout.tsx         - Notification handler + channel setup
app/app/(tabs)/settings.tsx - Notification + Health Connect toggles wired
app/app/(tabs)/insights.tsx - Health data grid, patterns, nudge cards
```

### EAS Build Execution (Session 89)

17. **Expo account + EAS project setup**
    - Created Expo account: username `inputx`
    - `eas init --non-interactive --force` linked project: @inputx/feel-good-app (ID: 3d60e1af)
    - **Lesson:** `eas build` requires stdin for interactive prompts. Use `--non-interactive` in automated contexts.

18. **First build - FAILED (216MB)**
    - EAS archives from git root (`/home/aipass`), not CWD
    - Nested project path lost: build server couldn't find `package.json` at expected location
    - **Lesson:** EAS uses the nearest `.git` parent as project root. If app is nested inside a larger repo, it uploads the entire parent.

19. **Fix: local git init**
    - `git init` inside `/home/aipass/projects/feel_good_app/app/`
    - Created `.easignore`: `_snapshots/`, `.expo/`, `node_modules/`, `*.log`
    - Second build: 354KB upload, succeeded in ~1 min
    - **Lesson:** For nested Expo projects, create a local git root inside the app/ directory. EAS then uses that as project root.

20. **Dev client connection**
    - APK installed → expo-dev-client launcher shows "Development Servers" screen
    - Old Metro on port 8081 needed killing (PID 1071051)
    - Restarted with tunnel mode: `nohup npx expo start --tunnel --dev-client`
    - Tunnel URL via ngrok: `https://2m0hzry-inputx-8081.exp.direct`
    - **Lesson:** Dev builds need Metro with `--dev-client` flag. Tunnel mode (`--tunnel`) for AP-isolated networks.

### Known Issues

| Issue | Status | Details |
|-------|--------|---------|
| HRV permission | Needs rebuild | App declares `READ_HEART_RATE_VARIABILITY_RMSSD`, Android needs `READ_HEART_RATE_VARIABILITY`. Fails gracefully (empty array). |
| Health Connect | Working | HR, steps, sleep all readable. HRV blocked by permission name mismatch. |
| Notifications | Untested on device | Code complete, needs manual testing of scheduled triggers. |
| AI Correlations | Needs data | Engine works with 5+ entries. Patrick needs to log mood entries for correlations to appear. |

---

## Phase 5: Tasks, History Edit, Weather (Session 92)

### What We Built

21. **Daily Tasks/Goals Feature**
    - `src/features/tasks/types.ts` - DailyTask + TaskPatternInsight types
    - `src/store/taskStore.ts` - Zustand + AsyncStorage store (addTask, setPreMood, completeTask, removeTask)
    - `src/features/tasks/components/TaskItem.tsx` - Task card with pre/post mood tracking + delta indicator
    - `src/features/tasks/components/TaskList.tsx` - Container with collapsible quick-add from activity tags
    - `src/features/tasks/hooks/useTaskInsights.ts` - Pattern analytics (completion rates, avg mood deltas)
    - Integrated on home screen + insights tab (Task Patterns section)

22. **History Edit/Delete**
    - Added `editEntry()` and `deleteEntry()` to moodStore.ts
    - Rewrote history.tsx: tap-to-expand cards, inline mood edit (5-emoji picker), delete with Alert confirm
    - Added inline note editing (TextInput with Save/Cancel)

23. **Weather Integration**
    - `src/features/weather/types.ts` - WeatherData, WMO weather codes → emoji mapping
    - `src/features/weather/weatherService.ts` - IP-based geolocation + Open-Meteo API (free, no key)
    - `src/store/weatherStore.ts` - Weather state with 15-min cache
    - `src/features/weather/WeatherCard.tsx` - Compact card (icon, temp, condition, feels-like, humidity)
    - Auto-attaches weather snapshot to mood entries for future correlation
    - Weather badge on history cards (icon + temp next to timestamp)
    - Added `WeatherSnapshot` interface to mood types

### Issues Hit

| Issue | What Happened | Fix | Time Lost |
|-------|--------------|-----|-----------|
| Zustand infinite render loop | `useTaskStore((s) => s.getTodayTasks())` called function inside selector, returning new array ref every render | Select `s.tasks` raw + `useMemo` filter in component | ~5 min |
| Unicode escapes in JSX | `\u2713`, `\u2191` etc rendered as literal text in JSX text nodes | Wrap in JS expressions: `{'✓'}`, `{'↑'}` | ~3 min |
| expo-location crash | Installing expo-location broke app ("unmatched route") - native module not in dev client build | Switched to IP-based geolocation (no native deps) | ~3 min |
| IP geolocation failure | ipapi.co returned "Location unavailable" from phone | Added 3 fallback services: ipwho.is, freeipapi.com, ipapi.co | ~2 min |

### Key Learnings

- **Zustand selector rule:** NEVER call functions inside selectors that return new references (arrays, objects). Always select raw state and derive with `useMemo`.
- **JSX unicode:** Raw `\uXXXX` in JSX text renders as literal string. Must use `{'actual_char'}` in a JS expression. Inside JS string literals (like function returns), `'\uXXXX'` works fine.
- **Native modules need dev client rebuild.** `expo-location`, camera, etc. can't hot reload. Need `npx expo prebuild && npx expo run:android` or EAS build. IP geolocation is a pure-JS workaround for weather.
- **Hot reload is insanely fast.** Edit → save → live on phone in seconds via Metro tunnel. Perfect for iterative UX work.
- **Open-Meteo API** is completely free, no key, no signup. WMO weather codes map to conditions + emojis cleanly.
- **Home screen order matters.** Moved MoodPicker above TaskList so "How are you feeling?" is the first thing users see.

### Files Created

```
src/features/tasks/types.ts
src/store/taskStore.ts
src/features/tasks/components/TaskItem.tsx
src/features/tasks/components/TaskList.tsx
src/features/tasks/hooks/useTaskInsights.ts
src/features/weather/types.ts
src/features/weather/weatherService.ts
src/store/weatherStore.ts
src/features/weather/WeatherCard.tsx
```

### Files Modified

```
src/features/mood/types.ts        - Added WeatherSnapshot interface
src/store/moodStore.ts            - Added editEntry(), deleteEntry()
app/(tabs)/index.tsx              - Added WeatherCard, TaskList, weather auto-attach on save
app/(tabs)/history.tsx            - Rewritten: expand/collapse, edit mood, edit note, delete, weather badge
app/(tabs)/insights.tsx           - Added Task Patterns section
```

### Still Planned

- [ ] expo-location proper integration (needs dev client rebuild + plugin in app.json)
- [ ] Weather-mood correlation in insights
- [ ] Design session (colors, spacing, overall look)
- [ ] LLM integration for smart journaling
- [ ] Production build

---

## Phase 5b: Health Connect Deep Fix (Session 92 continued)

### What We Built

24. **Custom Config Plugin: withHealthConnectPermissionDelegate.js**
    - expo-health-connect v0.1.1 only handles AndroidManifest entries (permission rationale activity + activity alias)
    - Missing CRITICAL `HealthConnectPermissionDelegate.setPermissionDelegate(this)` in MainActivity.kt
    - This is the #1 reported issue with expo-health-connect on Expo (causes "lateinit property requestPermission has not been initialized" crash)
    - Created `plugins/withHealthConnectPermissionDelegate.js` using `@expo/config-plugins` `withMainActivity` mod
    - Injects import + `setPermissionDelegate(this)` into `onCreate()`
    - Added to app.json plugins array
    - Also added `android.permission.health.READ_RESTING_HEART_RATE` to permissions

25. **EAS Cloud Build #2**
    - Build ID: `c43d7737-4f71-461f-96e3-895b8b127441`
    - Upload: 365KB, succeeded
    - APK installed on Patrick's Samsung Galaxy FE 24
    - Health Connect shows Feel Good App with access granted

### Issues Hit

| Issue | What Happened | Fix | Time Lost |
|-------|--------------|-----|-----------|
| HealthConnectPermissionDelegate missing | expo-health-connect plugin doesn't inject the required `setPermissionDelegate` call into MainActivity | Created custom config plugin `withHealthConnectPermissionDelegate.js` | ~15 min (research + fix) |
| Samsung Health ≠ Health Connect | Samsung Health tracks data (steps, HR) in its OWN data store. Health Connect is a SEPARATE Android system. Samsung Health does NOT auto-sync to Health Connect | User must manually enable: Samsung Health → Settings → Health Connect → enable per data type | ~10 min (investigation) |
| No insights despite "connected" | Health Connect toggle was green, app listed in HC settings, but no data appearing | Root cause: Samsung Health hasn't synced data TO Health Connect. Data exists in Samsung Health but never reached the Health Connect API our app reads from | ongoing |

### Key Learnings

- **expo-health-connect v0.1.1 is incomplete.** It handles AndroidManifest entries but NOT the critical MainActivity PermissionDelegate injection. Always check what config plugins actually do vs what the native library requires.
- **Samsung Health is NOT Health Connect.** Samsung has its own health data silo. Health Connect is Android's system-level health API. Samsung Health CAN sync to Health Connect, but it must be manually enabled by the user in Samsung Health settings.
- **Data flow chain:** Samsung Health → (manual sync enable) → Health Connect → (our API: readRecords) → Feel Good App. Break at any link = no data.
- **Custom Expo config plugins are powerful.** `withMainActivity` lets you inject Kotlin code into MainActivity.kt at build time. Pattern: find the string to inject after, use `.replace()` to insert code.

### Files Created

```
plugins/withHealthConnectPermissionDelegate.js  - Custom config plugin for PermissionDelegate
```

### Files Modified

```
app.json  - Added custom plugin + resting heart rate permission
```

### Pending: Samsung Health → Health Connect Sync

Patrick needs to enable sync on his Samsung Galaxy FE 24:
1. Open Samsung Health → Settings → Health Connect
2. Enable syncing for: Steps, Heart Rate, Sleep
3. After enabling, toggle Health Connect off/on in Feel Good App to force re-sync
4. If data still doesn't appear, add debug logging to `syncHealthData()` to check raw API responses

---

### Still Planned

- [ ] Verify Health Connect data after Samsung Health sync enabled
- [ ] expo-location proper integration (needs dev client rebuild + plugin in app.json)
- [ ] Weather-mood correlation in insights
- [ ] Design session (colors, spacing, overall look)
- [ ] LLM integration for smart journaling
- [ ] Production build

---

*This doc grows with the project. When we're done, distill into a reusable flow template for app builds.*
