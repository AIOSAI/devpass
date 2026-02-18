#!/bin/bash
cd /home/aipass/aipass_os/dev_central/test
/usr/bin/python3 apps/handlers/telegram/test_chat.py >> logs/test_chat.log 2>&1
