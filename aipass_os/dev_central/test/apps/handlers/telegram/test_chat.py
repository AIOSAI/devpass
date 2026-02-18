#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: test_chat.py - Test Bot Telegram Launcher
# Date: 2026-02-15
# Version: 2.0.0
# Category: test/handlers/telegram
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
Test Bot Telegram Launcher (@aipass_test_bot)

Thin wrapper around the shared direct_chat module. All chat logic,
command handling, tmux management, and polling lives in direct_chat.py.
This file only provides the test-specific configuration.
"""

import sys
from pathlib import Path

# Ensure aipass_core is importable
AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))

from api.apps.modules.telegram_chat import run_direct_chat

TEST_ROOT = Path(__file__).resolve().parent.parent.parent.parent
# /home/aipass/aipass_os/dev_central/test

sys.exit(run_direct_chat(
    branch_name="test",
    session_name="telegram-test",
    config_path=Path.home() / ".aipass" / "test_bot_config.json",
    work_dir=TEST_ROOT,
    log_dir=TEST_ROOT / "logs",
    data_dir=TEST_ROOT / "test_json",
    bot_name="AIPass Test Bot",
))
