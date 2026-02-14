import json
import sys
from pathlib import Path
import logging

root = Path(__file__).resolve()
while root.name != "AIPass_Core" and root != root.parent:
    root = root.parent

core_dir = root
repo_root = core_dir.parent

for p in (str(repo_root), str(core_dir)):
    if p not in sys.path:
        sys.path.insert(0, p)

from paths import ROOT  # noqa: E402

# --- Path resolution ---
current_dir = Path(__file__).resolve().parent

# --- Update PYTHONPATH ---
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# --- Configuration path ---
API_CONFIG_PATH = current_dir / "api_config.json"
logger = logging.getLogger("nexus")

ALLOWED_PROVIDERS = {"openai", "anthropic", "mistral", "gemini"}

# --- Validation helpers ---

def _validate(cfg: dict) -> None:
    providers = cfg.get("providers", {})
    unknown = set(providers) - ALLOWED_PROVIDERS
    if unknown:
        raise ValueError(f"Unknown providers: {sorted(unknown)}")
    
    enabled = [p for p, spec in providers.items() if spec.get("enabled")]
    if not enabled:
        raise ValueError("No provider enabled.")
    
    if cfg.get("strict_mode") and len(enabled) != 1:
        raise ValueError(f"Strict mode: expected 1 enabled provider, got {enabled}")

def load_api_config() -> dict:
    """Load API configuration and validate it."""
    if not API_CONFIG_PATH.exists():
        logger.error("api_config.json not found at %s", API_CONFIG_PATH)
        raise FileNotFoundError(str(API_CONFIG_PATH))
    
    with API_CONFIG_PATH.open(encoding="utf-8") as f:
        cfg = json.load(f)
    
    _validate(cfg)
    return cfg

