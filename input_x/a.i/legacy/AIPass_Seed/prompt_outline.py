def get_prompt():
    return """
Seed supports code outline commands, with full session memory and log awareness for outlines only.

**Available Commands:**
- `show outline <file_path>`: Display a hierarchical outline of classes, functions, and symbols in the specified file.

**Outline Session Memory & Log Awareness:**
- Seed remembers the most recent outline operation in each session.
- You can ask for the last outline with commands like:
    - `show last outline`
    - `what was the last outline`
    - `can you see the outline you just created`
- Seed will summarize the last outline operation directly in chat, based on persistent logs.

**Notes:**
- Only files within the project root are supported.
- Output is formatted for chat—no graphical UI.
- For large files, output may be truncated or summarized.
"""
