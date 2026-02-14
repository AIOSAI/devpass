# SPEAKEASY

**Voice-to-text system using OpenAI Whisper**
System-wide speech recognition. Press hotkey, speak, text appears in any application. Runs 100% locally with faster-whisper.

**Location:** `/home/aipass/speakeasy`
**Profile:** Workshop
**Created:** 2026-02-11
**Build Status:** Stable / At Rest - In daily use (Seed 99%)

---

## What It Does

Speakeasy provides system-wide voice input using OpenAI Whisper for transcription:
- Press Ctrl+Space to toggle recording on/off
- Whisper transcribes your speech locally (base.en model)
- Text is injected directly at your cursor position in any application
- Launch from GNOME Commands panel or terminal
- Recording mode: press_to_toggle (additional modes in handlers but not yet wired)

---

## Architecture

**Pattern:** 3-Layer (AIPass Standard)
- **Entry Point:** `apps/speakeasy.py` - auto-discovery orchestrator
- **Modules:** Business logic orchestration (coordinate between handlers)
- **Handlers:** Implementation details (pure functions, no cross-dependencies)

**Key Design:**
- Handlers implement logic, modules orchestrate
- Auto-discovery: no manual imports or routing needed
- Module interface: `handle_command(command, args) -> bool`

See `/home/aipass/speakeasy/docs/architecture.md` for detailed module/handler descriptions.

---

## Directory Structure

```
/home/aipass/speakeasy
├── ai_mail.local
│   ├── deleted.json
│   ├── inbox.json
│   └── sent.json
├── apps
│   ├── extensions
│   ├── handlers
│   ├── __init__.py
│   ├── json_templates
│   ├── modules
│   ├── plugins
│   └── speakeasy.py
├── .archive
├── artifacts
├── .backup
├── DASHBOARD.local.json
├── dev.local.md
├── docs
│   └── _template.md
├── dropbox
├── .gitignore
├── logs
├── .migrations.json
├── notepad.md
├── pytest.ini
├── README.md
├── requirements.txt
├── SPEAKEASY.id.json
├── speakeasy_json
├── SPEAKEASY.local.json
├── SPEAKEASY.observations.json
├── tests
│   ├── conftest.py
│   └── __init__.py
└── tools

17 directories, 19 files

```

*Auto-generated on file structure changes*

---

## Modules

{{AUTO_GENERATED_MODULES}}

*Scans `apps/modules/*.py` for files with `handle_command()`*

---

## Commands

{{AUTO_GENERATED_COMMANDS}}

*Pulled from drone @SPEAKEASY - branch-specific commands only*

---

## Dependencies

Core libraries (see `requirements.txt` for versions):
- **faster-whisper** - Local Whisper transcription
- **PyQt5** - GUI and system tray
- **pynput** - Keyboard/mouse input handling
- **sounddevice** - Audio recording
- **webrtcvad-wheels** - Voice activity detection
- **PyYAML** - Configuration management
- **rich** - CLI output formatting

Install: `pip install -r requirements.txt`

System Requirements:
- Python 3.12+
- Ubuntu Linux 24.04 LTS (tested)
- Audio input device (microphone)

---

## Key Features

**Working:**
- **Hotkey Toggle:** Ctrl+Space to start/stop recording (press_to_toggle mode)
- **Local Transcription:** OpenAI Whisper via faster-whisper (no cloud, no API keys)
- **Smart Text Input:** Auto-switches between typing and clipboard paste for long texts
- **GNOME Integration:** One-click launch from Commands panel (top bar)
- **Configurable:** YAML config for model selection, VAD sensitivity, hotkeys

**In Handlers (not yet wired to service):**
- Additional recording modes (hold_to_record, voice_activity_detection, continuous)
- Cursor lock during recording
- UI status window and system tray
- Audio feedback sounds

---

## Usage

### Commands

```bash
# Start the voice-to-text service
python3 apps/speakeasy.py start

# Check service status
python3 apps/speakeasy.py status

# Stop the service
python3 apps/speakeasy.py stop

# Show help
python3 apps/speakeasy.py --help
```

### Basic Workflow

1. Click "speakeasy" in GNOME Commands panel (or run `python3 apps/speakeasy.py start`)
2. Press Ctrl+Space to start recording
3. Speak your text
4. Press Ctrl+Space again to stop
5. Text appears at your cursor position

### Configuration

Config file: `config.yaml` (project root)

Key settings:
- `model.name` - Whisper model (tiny, base, small, medium, large) - default: base.en
- `recording.activation_key` - Hotkey binding - default: ctrl+space
- `recording.recording_mode` - press_to_toggle, hold_to_record, voice_activity_detection, continuous
- `input.method` - Text injection method (pynput)
- `input.paste_threshold` - Character count before switching to clipboard paste (default: 5000)

---

## Integration Points

### Depends On
{{DEPENDS_ON}}

### Integrates With
{{INTEGRATES_WITH}}

### Provides To
{{PROVIDES_TO}}

---

## Memory System

### Memory Files
- **SPEAKEASY.id.json** - Branch identity and architecture
- **SPEAKEASY.local.json** - Session history (max 600 lines)
- **SPEAKEASY.observations.json** - Collaboration patterns (max 600 lines)
- **SPEAKEASY.ai_mail.json** - Branch messages
- **docs/** - Technical documentation (markdown)

### Health Monitoring
- 🟢 **Green (Healthy):** Under 80% of limits
- 🟡 **Yellow (Warning):** 80-100% of limits
- 🔴 **Red (Critical):** Over limits (compression needed)

---

## System References

- **Code Standards:** `/home/aipass/aipass_core/standards/code_standards.md`
- **Template Source:** `/home/aipass/aipass_core/branch_operations/templates/`
- **Global Documentation:** `/home/aipass/aipass_os.md`

### Core Systems
- **Flow:** Workflow and PLAN management
- **Drone:** Command orchestration
- **AI Mail:** Branch-to-branch messaging
- **Backup:** System backup and snapshots
- **Prax:** Logging and infrastructure
- **API:** API integration layer

---

## Automation Philosophy

**README represents EXACT CURRENT STATE** - not future plans, not past work

### What Goes Elsewhere
- **Future Plans:** PLAN files in flow system
- **Past Work:** SPEAKEASY.local.json session history
- **Working On:** Active PLANs
- **Patterns Learned:** SPEAKEASY.observations.json
- **Technical Docs:** docs/ directory

### Automation Goal
Minimize AI token spend on updates - automate everything possible. Triggers fire on actual changes, not periodic checks.

---

## Notes

- **Human File:** This README.md is AI-managed Markdown - Patrick reads this directly
- **Current State Only:** Snapshot of branch as it exists RIGHT NOW - no history, no future
- **Auto vs Manual:** Automated sections = script-populated, Manual sections = AI writes when something fundamentally changes

---

## License & Attribution

**Speakeasy** is licensed under the **GNU General Public License v3.0**.

This project is derived from **WhisperWriter** by savbell:
- **Original Project:** https://github.com/savbell/whisper-writer
- **Original License:** GNU General Public License v3.0
- **Original Author:** savbell

Speakeasy is a complete rewrite following AIPass 3-layer architecture standards. The core concepts of VAD-based audio capture, faster-whisper integration, and voice-to-text workflows are derived from WhisperWriter's implementation.

See `LICENSE` for full GPL-3.0 license text.

**Key changes from WhisperWriter:**
- Complete restructure to AIPass 3-layer architecture
- Module auto-discovery system
- Integration with AIPass infrastructure (Prax logging, CLI services)
- Simplified configuration system
- Branch-based memory and session management

---

*Last Updated: 2026-02-12 - Stable / At Rest*
