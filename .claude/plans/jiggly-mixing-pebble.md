# Timed Tasks + Habits Feature

## Context

Patrick's feel_good_app has a daily task system with pre/post mood tracking. He wants two connected features built together:

1. **Timed Tasks** - Optional timer on tasks. When timer expires, the task locks as incomplete (can't mark done). User can re-add with a new timer.
2. **Habits** - When a task fails (timer expires) or is manually skipped, prompt: "What happened?" User logs mood, what they were doing instead, and classifies that activity as a good or bad habit. Over time, patterns emerge.

**Core philosophy:** Non-judgmental. App never says "that was bad." User defines good vs bad. Data builds the picture. Soft nudges, never lectures.

---

## Files to Create (6)

| File | Purpose |
|------|---------|
| `src/features/habits/types.ts` | HabitLog, HabitPattern, HabitClassification types |
| `src/store/habitStore.ts` | Zustand store for habit logs (persisted) |
| `src/features/habits/components/SkipReflection.tsx` | Inline "What happened?" flow |
| `src/features/habits/hooks/useHabitInsights.ts` | Memoized habit pattern aggregation |
| `src/features/tasks/services/taskTimerService.ts` | Timer scheduling via expo-notifications |
| `src/features/mood/components/MiniMoodPicker.tsx` | Extract from TaskItem for reuse |

## Files to Modify (8)

| File | Changes |
|------|---------|
| `src/features/tasks/types.ts` | Add timer + skipped fields to DailyTask |
| `src/store/taskStore.ts` | Add skipTask, addTimedTask, expireTask actions + migration |
| `src/features/tasks/components/TaskItem.tsx` | Skip button, timer countdown, expired state, import shared MiniMoodPicker |
| `src/features/tasks/components/TaskList.tsx` | Timer picker in add flow, skipped section with SkipReflection |
| `app/(tabs)/insights.tsx` | Add Habit Patterns section |
| `app/(tabs)/settings.tsx` | Add Clear Habit History |
| `app/_layout.tsx` | Handle task-expired notification tap |
| `src/features/notifications/notificationService.ts` | Add task-timer channel + scheduling helpers |

All paths relative to `/home/aipass/projects/feel_good_app/app/`

---

## Implementation Steps

### Step 1: Extend DailyTask type

**`src/features/tasks/types.ts`** - Add fields:
```typescript
// Timer fields
timerMinutes: number | null;     // null = no timer
timerStartedAt: string | null;   // ISO timestamp
timerExpired: boolean;           // true when timer ran out

// Skip fields
skipped: boolean;                // user explicitly skipped OR timer expired
skippedAt: string | null;        // ISO timestamp
```

All default to `null`/`false`.

### Step 2: Extend taskStore

**`src/store/taskStore.ts`** - New actions:

- `addTask` updated: accept optional `timerMinutes` param. If provided, set `timerMinutes` and `timerStartedAt: new Date().toISOString()`
- `skipTask(taskId)` - sets `skipped: true`, `skippedAt`
- `expireTask(taskId)` - sets `timerExpired: true`, `skipped: true`, `skippedAt`
- `removeTask` updated: skipped tasks get soft-deleted (`cleared: true`) like completed tasks, preserving history
- `merge` migration: add defaults for all new fields on old data

### Step 3: Create habit types

**`src/features/habits/types.ts`**:
```typescript
export type HabitClassification = 'good' | 'bad';

export interface HabitLog {
  id: string;
  taskId: string;
  taskLabel: string;
  date: string;                    // YYYY-MM-DD
  timestamp: string;               // ISO
  mood: MoodLevel;
  activity: string;                // What they did instead
  classification: HabitClassification;
}

export interface HabitPattern {
  activity: string;
  classification: HabitClassification;
  occurrences: number;
  avgMood: number;
  topMissedTasks: string[];
  lastSeen: string;
}
```

### Step 4: Create habitStore

**`src/store/habitStore.ts`** - Zustand + AsyncStorage persist:
- State: `logs: HabitLog[]`
- Actions: `addLog(...)`, `getRecentLogs(days)`, `clearHistory()`
- Storage key: `'habit-storage'`
- Follow exact pattern of taskStore

### Step 5: Extract MiniMoodPicker

**`src/features/mood/components/MiniMoodPicker.tsx`** - Extract the inline mood picker currently defined inside TaskItem.tsx (the 5-emoji row). Both TaskItem and SkipReflection need it.

Props: `onSelect(mood: MoodLevel)`, `selected: MoodLevel | null`

Update TaskItem.tsx to import from this shared component.

### Step 6: Task timer service

**`src/features/tasks/services/taskTimerService.ts`**:
- `scheduleTaskExpiry(taskId, taskLabel, minutesFromNow)` - schedules notification with data `{ type: 'task-expired', taskId }`
- `scheduleExpiryWarning(taskId, taskLabel, minutesFromNow)` - 5-min warning notification (only if timer >= 15min)
- `cancelTaskTimer(taskId)` - cancels both notifications (for when task completed before expiry)
- `setupTaskTimerChannel()` - creates Android channel `'task-timer'`
- Uses `expo-notifications` `scheduleNotificationAsync` with `trigger: { seconds: ... }`

### Step 7: Timer UI in TaskList add flow

**`src/features/tasks/components/TaskList.tsx`**:
- Add optional timer toggle in the add-task section: "Set a timer?" switch
- When enabled, show duration chips: 30m, 1h, 2h, 4h + custom input
- Pass `timerMinutes` to `addTask()`
- After adding timed task, call `scheduleTaskExpiry()`

### Step 8: Update TaskItem for timer + skip

**`src/features/tasks/components/TaskItem.tsx`** - Three render states:

**Pending (no timer or timer still running):**
- Existing pre-mood + Done flow
- Add "Skip" button (text, subdued style)
- If timed: show countdown text (e.g., "1h 23m left")
- Countdown via `useEffect` + `setInterval` (update every 60s)
- When < 5min remaining, countdown turns warning color

**Expired (timer ran out):**
- "Time's up" indicator, Done button hidden
- Auto-shows SkipReflection component
- "Try Again" button: re-adds same task with new timer picker

**Skipped (manually or expired, reflection not yet done):**
- Shows SkipReflection inline below the task card
- After reflection saved OR dismissed, task moves to cleared section

**Completed:** - Existing behavior (checkmark, mood delta)

### Step 9: SkipReflection component

**`src/features/habits/components/SkipReflection.tsx`**:

Inline expanding card (follows app's expand/collapse pattern, no modals):

1. Header: "You skipped **[task label]**" (neutral framing)
2. Mood: "How are you feeling?" → MiniMoodPicker
3. Activity: "What were you doing instead?" → TextInput + tag chips from `tagStore.activities` as quick-taps
4. Classification: Two equal-weight buttons - "Good Habit" (teal tint) / "Bad Habit" (amber tint)
5. Save → calls `habitStore.addLog()`, then marks task `cleared: true`
6. Dismiss option → skip reflection without logging (non-judgmental, no guilt)

### Step 10: Timer expiry check on foreground

**`app/_layout.tsx`**:
- On AppState 'active': check all timed tasks, expire any past due
- Call `setupTaskTimerChannel()` on mount
- Handle notification tap: if `data.type === 'task-expired'`, navigate to Log tab

**`src/features/tasks/components/TaskList.tsx`**:
- On date rollover or app foreground: check timed tasks and call `expireTask()` for any past due
- This is the reliable fallback (notifications are best-effort)

### Step 11: Habit insights hook

**`src/features/habits/hooks/useHabitInsights.ts`**:
- `useHabitInsights(days = 30)` returns `{ goodHabits: HabitPattern[], badHabits: HabitPattern[] }`
- Groups logs by activity, calculates occurrences, avg mood, top missed tasks
- Sorted by occurrences descending
- Follows exact pattern of `useTaskInsights.ts`

### Step 12: Habit Patterns on Insights tab

**`app/(tabs)/insights.tsx`** - New section after "Task Patterns":
- "Habit Patterns" header
- Bad habits: "[Activity] came up X times when you skipped tasks. Avg mood: Y/5"
- Good habits: "[Activity] appeared X times. Mood: Y/5 - you were happy doing this"
- Non-judgmental framing throughout

### Step 13: Settings cleanup

**`app/(tabs)/settings.tsx`**:
- Add "Clear Habit History" button in Your Data section
- Same `Alert.alert` confirmation pattern as existing clear buttons

---

## Key Design Decisions

- **Inline expansion, not modals** - Matches existing app pattern. SkipReflection expands below the task card.
- **Skip + Timer = two paths to same flow** - Manual skip (user decides they're not doing it) and timer expiry both trigger SkipReflection.
- **Dismiss option on reflection** - Non-judgmental. User can skip the "what happened?" without penalty.
- **Soft-delete skipped tasks** - Changed from hard delete to `cleared: true` so habit history is preserved.
- **Timer countdown in UI, notifications for background** - Timer checked on foreground (reliable), notification is a nudge (best-effort).
- **No new tab** - Habits live on Log tab (alongside tasks) and Insights tab (patterns). Keeps 4-tab layout clean.
- **Separate habitStore** - Clean separation. Task events trigger habit logging, but habit data has its own lifecycle.

---

## Verification

1. **Timer flow:** Add timed task → see countdown → let expire → "Time's up" appears → SkipReflection shows → log habit → see it in Insights
2. **Manual skip flow:** Add task → tap Skip → SkipReflection shows → log habit → see it in Insights
3. **Dismiss flow:** Skip task → SkipReflection shows → tap Dismiss → task clears, no habit logged
4. **Try Again flow:** Timer expires → tap "Try Again" → same task re-added with new timer
5. **Completion cancels timer:** Add timed task → complete before expiry → no notification fires
6. **Insights:** After 3+ habit logs, Habit Patterns section appears on Insights tab
7. **Persistence:** Close and reopen app → habit logs and skipped tasks survive
8. **Migration:** Existing tasks without new fields load correctly with defaults
9. **Background expiry:** Add timed task → close app → timer expires → notification fires → tap → app opens to Log tab with expired task
