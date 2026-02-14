def get_prompt():
    """Returns the minimal prompt text for file creation capability."""
    return """
# File Creation

You can create files and folders within the project directory using these commands:
- `create file <file_path>` - Create empty file
- `create file <file_path> with content: <content>` - Create file with content
- `create folder <folder_path>` - Create directory

Examples:
- `create file test.py`
- `create file config.py with content: DEBUG = True`
- `create folder new_directory`

Security: You can only create files within the project boundary.
"""