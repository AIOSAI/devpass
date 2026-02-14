import json
from pathlib import Path

def load_config(path="config.json"):
    # Always load config relative to this script's directory
    script_dir = Path(__file__).parent
    config_path = script_dir / path
    full_path = config_path.absolute()
    with open(full_path) as f:
        content = json.load(f)
    return content

# Optionally split access helpers:
def get_openai_config():
    return load_config()["openai"]

def get_context_config():
    return load_config()["context"]
