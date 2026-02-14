# Guest Portal - Multi-Bot Telegram Access to AIPass

Dedicated Telegram bots that let other people chat with AIPass. Each person gets their own bot, their own AI branch trained on AIPass knowledge, and persistent memories that build over time.

## Status: Idea Stage

First user: Patrick's brother. Low restriction, shared code repo, explore freely.

## Concept

Reuse the existing Telegram bridge architecture (bridge.py + spawner.py) with:
- Separate bot per person (via @BotFather)
- Dedicated branch with AIPass knowledge
- User-specific memories that persist across chats
- Optional code repo access for hands-on exploration

## Project Structure

```
guest_portal/
├── docs/           # Setup guides, knowledge base docs
├── notepad.md      # Ideas and planning notes
└── README.md       # This file
```

## Next Steps

- [ ] Create Telegram bot via @BotFather
- [ ] Design branch structure (knowledge base + user memories)
- [ ] Deploy bridge instance with new bot token
- [ ] Set up shared repo for code browsing
- [ ] Test with Patrick's brother
