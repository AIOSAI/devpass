"""
Prompt generator for script/command execution
"""

def get_script_exec_prompt() -> str:
    return (
        "Seed can execute shell commands and Python scripts in the project root directory. "
        "All executions are logged with output, errors, and exit codes for traceability and monitoring. "
        "Script execution is subject to security checks and may require confirmation for risky operations."
    )

def get_prompt(command: str, shell: str = "bash") -> str:
    """Return a system prompt for safe script/command execution."""
    return f"You are a secure script executor. Run the following {shell} command safely in the project root. Capture all output and errors.\nCommand:\n{command}"
