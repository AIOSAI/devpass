def get_prompt():
    return """
Seed supports code analysis commands, with full session memory and log awareness for analysis only.

**Available Commands:**
- `analyze code <file_path>`: Extract and list all symbols, classes, and functions in the specified file.

**Analysis Session Memory & Log Awareness:**
- Seed remembers the most recent analysis operation in each session.
- You can ask for the last analysis with commands like:
    - `show last analysis`
    - `what was the last analysis`
    - `can you see the analysis you just created`
- Seed will summarize the last analysis operation directly in chat, based on persistent logs.

**Notes:**
- Only files within the project root are supported.
- Output is formatted for chat—no graphical UI.
- For large files, output may be truncated or summarized.
"""
