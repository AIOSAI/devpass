# Health Data APIs & Smart Ring Integration

## Architecture Decision
Ring -> Companion App -> OS Health Store (HealthKit / Health Connect) -> Our App

This is the recommended primary path. Works with ANY ring that syncs to platform health stores. No partnerships needed.

## Apple HealthKit (iOS)

### Available Data Types
| Metric | Type Identifier | Notes |
|---|---|---|
| Heart Rate | heartRate | Continuous BPM samples |
| HRV | heartRateVariabilitySDNN | Standard deviation of heartbeat intervals |
| Steps | stepCount | Cumulative count |
| Sleep Stages | sleepAnalysis | asleepREM, asleepCore (light), asleepDeep, awake, inBed |
| Wrist Temperature | appleSleepingWristTemperature | iOS 16+, Apple Watch Series 8+ |
| Body Temperature | bodyTemperature | Manual or device-reported |
| SpO2 | oxygenSaturation | Blood oxygen percentage |
| Resting Heart Rate | restingHeartRate | Daily average |
| Respiratory Rate | respiratoryRate | Breaths per minute |

### Permissions
- Granular per data type (read/write separate)
- Privacy-first: app CANNOT determine if user denied read permission (appears as no data)
- Background delivery via HKObserverQuery possible
- User controls everything in Settings > Privacy > Health

## Health Connect (Android)

### Available Data Types
| Metric | Record Class | Notes |
|---|---|---|
| Heart Rate | HeartRateRecord | |
| HRV | HeartRateVariabilityRmssdRecord | RMSSD method |
| Steps | StepsRecord | |
| Sleep (with stages) | SleepSessionRecord | LIGHT, DEEP, REM, AWAKE_IN_BED |
| Skin Temperature | SkinTemperatureRecord | Feature-flag gated |
| Body Temperature | BodyTemperatureRecord | |
| SpO2 | OxygenSaturationRecord | |
| Active Calories | ActiveCaloriesBurnedRecord | |

### Key Notes
- Android 14+: Health Connect built into OS (no extra app)
- Samsung Health SDK deprecated July 2025 -> use Health Connect
- Google Fit API sunset June 2025 -> use Health Connect
- 30-day historical limit by default for new apps
- Samsung Health auto-syncs to Health Connect

## Smart Ring Comparison

| Ring | Direct API | HealthKit Sync | Health Connect Sync | Best Data Access |
|---|---|---|---|---|
| Oura Ring | YES (public, OAuth 2.0) | Yes | Yes | Direct API (richest) |
| Ultrahuman Ring Air | Partner-only (gated) | Yes | Yes | Health stores (easiest) |
| RingConn | No public API | Yes | Yes (migrating) | Health stores only |
| Samsung Galaxy Ring | No | N/A | Via Samsung Health | Health Connect |
| Amazfit Helio | No | Yes | Yes | Health stores only |

### Oura API v2 (Best Direct API)
- Base URL: https://api.ouraring.com/v2/usercollection/
- Auth: OAuth 2.0
- Endpoints: daily_activity, daily_sleep, daily_readiness, daily_stress, heartrate, sleep (stages), vo2_max, and more
- CAVEAT: Gen3/Ring4 users WITHOUT active Oura subscription can't access API data

### Ultrahuman
- UltraSignal: Raw sensor platform (partner/invite only)
- Partnership API: REST + OAuth 2.0 (partner onboarding required)
- Terra API: Has direct Ultrahuman integration (webhook-based)
- Easiest path: Just read from HealthKit/Health Connect

### Recommendation for Patrick's Ring Choice
- **Ultrahuman Ring Air**: Good hardware, syncs to health stores, partner API available if we grow. Patrick was already considering this.
- **Oura**: Best developer API but requires user subscription for API access (paywall).
- **RingConn**: Cheapest for prototyping, but no API. Health stores only.
- **Any ring works** for MVP since we read from HealthKit/Health Connect.

## Layered Architecture
```
LAYER 1 (Primary - all rings): HealthKit + Health Connect
LAYER 2 (Enhanced - Oura users): Oura API v2 (readiness, stress, resilience scores)
LAYER 3 (Future): Ultrahuman Partnership API or Terra API for backend aggregation
```
