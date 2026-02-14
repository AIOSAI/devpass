#!/usr/bin/env python3
"""
Branch Prompt Loader - Injects branch-specific prompts based on CWD

When working in a branch directory, loads .aipass/branch_system_prompt.md
and injects the content via additionalContext so Claude sees branch-specific
reminders without cluttering the global system prompt.

Auto-creates .aipass/ directory and placeholder prompt if missing.

Version: 2.1.0
Created: 2025-11-27
Updated: 2025-11-27
"""
import json
from pathlib import Path

AIPASS_ROOT = Path.home()
TEMPLATE_PATH = AIPASS_ROOT / "templates" / "branch_system_prompt.template.md"


def find_branch_root() -> Path | None:
    """
    Find the branch root directory (contains apps/ or is a known branch).
    Stops at /home/aipass (AIPASS root).
    """
    cwd = Path.cwd()

    # Don't create .aipass at the AIPASS root level
    if cwd == AIPASS_ROOT:
        return None

    search_path = cwd
    while search_path > AIPASS_ROOT:
        # Branch indicators: has apps/ directory or has memory files
        has_apps = (search_path / "apps").is_dir()
        has_memory = any(search_path.glob("*.local.json"))

        if has_apps or has_memory:
            return search_path

        search_path = search_path.parent

    return None


def get_template(branch_name: str) -> str:
    """Load template from central location, with fallback."""
    if TEMPLATE_PATH.exists():
        template = TEMPLATE_PATH.read_text()
        return template.replace("{branch_name}", branch_name)
    # Fallback if template missing
    return f"# {branch_name} Branch System Prompt\n\nStatus: NEEDS CONFIGURATION\n"


def ensure_branch_prompt(branch_root: Path) -> Path:
    """
    Ensure .aipass/branch_system_prompt.md exists, creating if needed.
    Returns the path to the prompt file.
    """
    aipass_dir = branch_root / ".aipass"
    prompt_file = aipass_dir / "branch_system_prompt.md"

    # Create .aipass directory if missing
    if not aipass_dir.exists():
        aipass_dir.mkdir(parents=True, exist_ok=True)

    # Create placeholder prompt if missing
    if not prompt_file.exists():
        branch_name = branch_root.name.upper()
        content = get_template(branch_name)
        prompt_file.write_text(content)

    return prompt_file


def main():
    branch_root = find_branch_root()

    if branch_root:
        prompt_file = ensure_branch_prompt(branch_root)
        content = prompt_file.read_text().strip()
        branch_name = branch_root.name.upper()

        # Output plain text directly (like cat does for system_prompt.md)
        print(f"\n# Branch Context: {branch_name}\n<!-- Source: {prompt_file} -->\n{content}")
    else:
        # No branch detected, output nothing
        pass


if __name__ == "__main__":
    main()
