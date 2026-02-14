def get_prompt():
    """Returns the minimal prompt text for file deletion capability."""
    return """
# File Deletion

You can delete files and folders within the project directory using these commands:
- `delete file <file_path>` - Delete a file
- `delete folder <folder_path>` - Delete a folder (non-recursive)
- `delete folder <folder_path> recursive` - Delete a folder and all its contents

Examples:
- `delete file test.py`
- `delete folder old_directory`
- `delete folder old_directory recursive`

Security: You can only delete files and folders within the project boundary. Use with caution!
"""
