# Nexus Skills

Auto-discovered skill handlers for Nexus v2.

## Creating a Skill

1. Create a new `.py` file in this directory
2. Implement `handle_request(user_input: str) -> Optional[str]`
3. Return a string to respond, or `None` to pass to LLM

## Interface

```python
def handle_request(user_input: str) -> Optional[str]:
    """
    Handle user input if this skill matches

    Returns:
        Response string if handled, None to pass through
    """
```

## Disabling Skills

Prefix filename with underscore: `_myskill.py` (skipped by discovery)

## Example Skills

- `_template.py` - Copy this to create new skills
- (Add your skills here)

## Discovery

Skills are discovered at Nexus startup. Restart to pick up new skills.
