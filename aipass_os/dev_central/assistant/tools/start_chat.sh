#!/bin/bash
# ===================AIPASS====================
# Start the assistant Telegram chat listener
# Runs assistant_chat.py, logging to logs/assistant_chat.log
# =============================================

cd /home/aipass/aipass_os/dev_central/assistant
/home/aipass/.venv/bin/python3 apps/handlers/telegram/assistant_chat.py >> logs/assistant_chat.log 2>&1
