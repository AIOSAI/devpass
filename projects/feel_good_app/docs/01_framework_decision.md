# Framework Decision: React Native + Expo

## Decision
React Native with Expo (TypeScript)

## Why
- TypeScript/React = where AI assistants (Claude) are strongest. This is our primary development workflow.
- Expo EAS handles building, signing, deploying to both stores with one command. No Xcode wrestling.
- Health data coverage complete: react-native-health (iOS HealthKit) + react-native-health-connect (Android Health Connect)
- All 5 key data types supported on both platforms: heart rate, HRV, steps, sleep stages, temperature
- Largest ecosystem (npm), most AI training data, most tutorials

## Alternatives Considered
- **Flutter**: Close second. Single health plugin is elegant but has Android HRV/temperature gaps. Dart has less AI training data than TypeScript.
- **Kotlin Multiplatform**: Too immature for health APIs. Weakest AI-assisted dev. Skip.
- **Native (Swift + Kotlin)**: Maximum API access but doubles the work. Not practical for AI-assisted solo dev.

## Key Libraries
- react-native-health (iOS HealthKit)
- react-native-health-connect (Android Health Connect)
- expo-router (file-based navigation)
- Zustand (state management)
- Terra API SDK (optional - universal wearable aggregation)

## Project Structure
Standard Expo feature-based structure:
- app/ - Expo Router (file-based routing)
- src/features/ - mood/, health/, insights/ (each self-contained)
- src/shared/ - common components, theme, utils
- src/store/ - global state (Zustand)

## Getting Started
```bash
npx create-expo-app@latest feel-good-app --template blank-typescript
npx expo install react-native-health react-native-health-connect
npx expo prebuild
```

Note: Health libraries require custom dev build (not Expo Go). Use expo-dev-client.
