#!/bin/bash
# Sends a notification to Patrick via the scheduler bot
# Usage: bash ~/.aipass/notify_telegram.sh "Your message here"

CONFIG="$HOME/.aipass/scheduler_config.json"
TOKEN=$(python3 -c "import json; print(json.load(open('$CONFIG'))['telegram_bot_token'])")
CHAT_ID=$(python3 -c "import json; print(json.load(open('$CONFIG'))['telegram_chat_id'])")

curl -s -X POST "https://api.telegram.org/bot${TOKEN}/sendMessage" \
  -H "Content-Type: application/json" \
  -d "{\"chat_id\": \"${CHAT_ID}\", \"text\": \"$1\"}" > /dev/null 2>&1
