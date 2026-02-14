def get_prompt():
    """Returns the minimal prompt text for file editing capability."""
    return """
# File Editing

You can edit files within the project directory using these commands:
- `edit file <file_path> to: <new_content>` - Replace the entire file with new content
- `edit file <file_path> lines <start>-<end> to: <new_content>` - Replace a range of lines (inclusive) with new content

Examples:
- `edit file test.py to: print('Hello, world!')`
- `edit file config.py lines 1-3 to: DEBUG = False\nLOG_LEVEL = 'info'`

Security: You can only edit files within the project boundary.
"""
