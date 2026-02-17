#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: assistant_chat.py - Assistant Bot Telegram Launcher
# Date: 2026-02-15
# Version: 2.0.0
# Category: assistant/handlers/telegram
#
# CHANGELOG (Max 5 entries):
#   - v2.0.0 (2026-02-15): Thin launcher - delegates to shared direct_chat.py
#   - v1.1.0 (2026-02-15): Photo/document support (archived)
#   - v1.0.0 (2026-02-15): Initial long-polling + tmux bridge (archived)
#
# CODE STANDARDS:
#   - Thin launcher only - all logic lives in direct_chat.py
#   - Imports from aipass_core/api/apps/handlers/telegram/
# =============================================

"""
Assistant Bot Telegram Launcher (@aipass_assistant_bot)

Thin wrapper around the shared direct_chat module. All chat logic,
command handling, tmux management, and polling lives in direct_chat.py.
This file only provides the assistant-specific configuration.
"""

import sys
from pathlib import Path

# Ensure aipass_core is importable
AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))

from api.apps.modules.telegram_chat import run_direct_chat

ASSISTANT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
# /home/aipass/aipass_os/dev_central/assistant

sys.exit(run_direct_chat(
    branch_name="assistant",
    session_name="telegram-assistant",
    config_path=Path.home() / ".aipass" / "assistant_bot_config.json",
    work_dir=ASSISTANT_ROOT,
    log_dir=ASSISTANT_ROOT / "logs",
    data_dir=ASSISTANT_ROOT / "assistant_json",
    bot_name="AIPass Assistant Bot",
))
