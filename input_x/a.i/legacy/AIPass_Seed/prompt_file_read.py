def get_prompt():
    """Returns the minimal prompt text for file reading capability."""
    return """
# File Reading

You can read files within the project directory using these commands:
- `read file <file_path>` - Read the file (may be truncated for large files)
- `read file <file_path> full` - Read the entire file, word-for-word (no truncation)
- `read file <file_path> from line <start> to <end>` - Read a range of lines
- `read file <file_path> page <n>` - Read a paginated section

Examples:
- `read file main.py`
- `read file main.py full`
- `read file config.py from line 1 to 20`
- `read file test.txt page 2`

Notes:
- By default, large files may be truncated to ensure system performance.
- Use the `full` option to request the entire file content, but be aware of possible context/token limits.
- If a file is truncated, you will see a '(truncated)' notice in the output.

Security: You can only read files within the project boundary.
"""
