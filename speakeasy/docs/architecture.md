# Speakeasy Architecture

**Last Updated:** 2026-02-11
**Build Status:** Phase 6 Complete - Seed Audit 99%

---

## Overview

Speakeasy follows the AIPass 3-layer architecture pattern:
1. **Entry Point** - Auto-discovery orchestrator
2. **Modules** - Business logic orchestration
3. **Handlers** - Pure implementation functions

**Design Principle:** Handlers implement logic, modules orchestrate. No cross-dependencies in handlers.

---

## Entry Point

### `apps/speakeasy.py`

Main orchestrator with auto-discovery:
- Scans `modules/` directory for Python files with `handle_command()` function
- Routes commands to discovered modules automatically
- No manual imports or routing configuration needed
- Provides service commands: `start`, `stop`, `status`
- Rich CLI help system

**Service Mode:** When started, initializes Qt application and runs voice-to-text service in system tray.

---

## Modules (Business Logic Orchestration)

Modules coordinate between handlers to implement workflows. They use Prax logging and orchestrate multiple handlers.

### `audio_module.py`
Orchestrates the recording and transcription pipeline:
- Coordinates `audio_handler` for recording
- Coordinates `transcription_handler` for Whisper transcription
- Manages end-to-end voice-to-text workflow
- Handles Whisper model caching and lifecycle

### `config_module.py`
Configuration management orchestration:
- Coordinates `config_handler` for YAML operations
- Provides config validation and defaults
- Manages config file creation and updates
- Exposes `get_config()` for other modules

### `input_module.py`
Input handling orchestration:
- Coordinates `hotkey_handler` for keyboard shortcuts
- Coordinates `input_handler` for text injection
- Coordinates `cursor_lock_handler` for visual feedback
- Manages hotkey registration and text injection workflow

### `ui_module.py`
User interface orchestration:
- Coordinates `ui_handler` for Qt widgets
- Manages system tray, status window, settings dialog
- Handles UI lifecycle (show/hide/quit)
- Bridges UI events to module actions

---

## Handlers (Pure Implementation)

Handlers provide pure functions with no dependencies on other handlers. No Prax imports, no state management.

### Audio Processing

#### `audio_handler.py`
Low-level audio recording:
- Records audio using sounddevice
- Voice Activity Detection (VAD) using webrtcvad
- Auto-stops on silence detection
- Returns raw audio data as numpy array
- Functions: `record_audio()`, `detect_voice_activity()`

#### `transcription_handler.py`
Whisper transcription:
- Creates and manages WhisperModel instances
- Transcribes audio to text using faster-whisper
- Post-processes transcription (capitalize, punctuate)
- Memory cleanup after transcription
- Functions: `create_whisper_model()`, `transcribe_audio()`, `postprocess_text()`

### Input/Output

#### `hotkey_handler.py`
Keyboard shortcut handling:
- Registers system-wide hotkeys using pynput
- Callback-based hotkey detection
- Functions: `register_hotkey()`, `unregister_hotkey()`

#### `input_handler.py`
Text injection:
- Types transcribed text into active application
- Uses pynput keyboard controller
- Handles clipboard-based paste as fallback
- Functions: `inject_text()`, `type_text()`, `paste_text()`

#### `cursor_lock_handler.py`
Visual feedback during recording:
- Locks cursor position to prevent movement
- Provides visual indicator that recording is active
- Unlocks cursor when recording stops
- Functions: `lock_cursor()`, `unlock_cursor()`

### UI Components

#### `ui_handler.py`
Qt widget creation:
- Pure functions that create Qt widgets
- System tray icon with menu
- Status window (shows recording state)
- Settings dialog
- Functions: `create_tray_icon()`, `create_status_window()`, `create_settings_dialog()`

### Configuration

#### `config_handler.py`
YAML configuration operations:
- Load/save YAML files
- Validate config structure
- Provide default values
- Functions: `load_config()`, `save_config()`, `validate_config()`, `get_default_config()`

#### `json_handler.py`
JSON operations for data storage:
- Generic JSON read/write utilities
- Used for non-config data files
- Functions: `load_json()`, `save_json()`

---

## Data Flow

### Voice-to-Text Workflow

```
1. User presses hotkey
   └─> hotkey_handler detects key press
   └─> ui_module updates status window

2. Recording starts
   └─> cursor_lock_handler locks cursor position
   └─> audio_handler begins recording with VAD

3. User speaks, then stops
   └─> audio_handler detects silence via VAD
   └─> Recording stops, returns audio data

4. Transcription
   └─> transcription_handler transcribes audio using Whisper
   └─> Post-processing (capitalize, punctuate)

5. Text injection
   └─> input_handler types text into active app
   └─> cursor_lock_handler unlocks cursor
   └─> ui_module updates status window
```

### Configuration System

```
1. First run
   └─> config_module checks for config.yaml
   └─> config_handler generates default config
   └─> config_handler saves to speakeasy_json/config.yaml

2. Subsequent runs
   └─> config_module.get_config() called
   └─> config_handler loads config.yaml
   └─> config_handler validates structure
   └─> Returns config dict to caller

3. Runtime changes
   └─> ui_module settings dialog modified
   └─> config_module updates config
   └─> config_handler saves to disk
```

### Service Lifecycle

```
1. Start: python3 speakeasy.py start
   └─> speakeasy.py creates Qt application
   └─> config_module loads configuration
   └─> ui_module creates tray icon and status window
   └─> input_module registers hotkeys
   └─> audio_module initializes Whisper model
   └─> Qt event loop runs

2. Runtime
   └─> Hotkey pressed
   └─> audio_module orchestrates recording + transcription
   └─> input_module injects text
   └─> Cycle repeats

3. Stop: python3 speakeasy.py stop
   └─> Sends SIGTERM to running process
   └─> Qt application cleanup
   └─> Hotkeys unregistered
   └─> Process exits
```

---

## Key Design Patterns

### Auto-Discovery
- Entry point scans `modules/` for files with `handle_command()`
- No manual routing configuration
- Add new module = automatic integration

### Thin Modules, Pure Handlers
- Modules orchestrate, handlers implement
- Handlers are pure functions (no state, no cross-deps)
- Enables testing handlers in isolation

### Configuration as Code
- YAML for user-facing config
- Defaults in code, overrides from file
- Validation on load

### Model Caching
- Whisper model loaded once, reused for all transcriptions
- Reduces latency after first transcription
- Memory cleanup via `gc.collect()` after use

---

## Directory Structure

```
/home/aipass/speakeasy/
├── apps/
│   ├── speakeasy.py          # Entry point
│   ├── modules/              # Orchestration layer
│   │   ├── audio_module.py
│   │   ├── config_module.py
│   │   ├── input_module.py
│   │   └── ui_module.py
│   └── handlers/             # Implementation layer
│       ├── audio_handler.py
│       ├── transcription_handler.py
│       ├── hotkey_handler.py
│       ├── input_handler.py
│       ├── cursor_lock_handler.py
│       ├── ui_handler.py
│       ├── config_handler.py
│       └── json/
│           └── json_handler.py
├── speakeasy_json/           # Runtime data
│   └── config.yaml           # User configuration
├── docs/
│   └── architecture.md       # This file
├── tests/                    # Test files
├── requirements.txt
└── README.md
```

---

## Derived From WhisperWriter

Speakeasy is derived from [WhisperWriter by savbell](https://github.com/savbell/whisper-writer) (GPL-3.0).

**What we kept:**
- Core concept: hotkey → record → VAD → transcribe → inject
- faster-whisper for local transcription
- webrtcvad for voice activity detection
- PyQt5 for system tray

**What we changed:**
- Complete architectural restructure (3-layer pattern)
- Module auto-discovery system
- Simplified configuration (YAML vs complex nested config)
- Integration with AIPass infrastructure
- Handler/module separation for testability

**License:** Both projects are GPL-3.0, allowing derivative works under the same license.

---

## References

- **WhisperWriter:** https://github.com/savbell/whisper-writer
- **faster-whisper:** https://github.com/SYSTRAN/faster-whisper
- **OpenAI Whisper:** https://github.com/openai/whisper
- **AIPass Code Standards:** `/home/aipass/aipass_core/standards/code_standards.md`
