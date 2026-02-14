# --- API key management ---

from pathlib import Path
import logging
import sys

root = Path(__file__).resolve()
while root.name != "AIPass_Core" and root != root.parent:
    root = root.parent

core_dir = root
repo_root = core_dir.parent

for p in (str(repo_root), str(core_dir)):
    if p not in sys.path:
        sys.path.insert(0, p)

from paths import KEYS_DIR  # noqa: E402
from .key_loader import KeyLoader  # noqa: E402

logger = logging.getLogger(__name__)

class APIManager:
    def __init__(self, keys_file_path=None):
        if keys_file_path is None:
            keys_file_path = KEYS_DIR / ".env"
        self.keys_file_path = Path(keys_file_path)
        self.keys = {}
        self._load_keys()
    
    def _load_keys(self):
        """Load API keys from the keys file"""
        if not self.keys_file_path.exists():
            raise FileNotFoundError(f"Key file not found: {self.keys_file_path}")
        try:
            loader = KeyLoader(self.keys_file_path)
            self.keys = loader.load_keys()
            logger.info("Loaded %d API keys from %s", len(self.keys), self.keys_file_path)
        except Exception as e:
            logger.error("Error loading API keys: %s", e)
            self.keys = {}
    
    def get_key(self, provider):
        """Get API key for a specific provider"""
        if provider not in self.keys:
            raise ValueError(f"No API key found for provider: {provider}")
        return self.keys[provider]
    
    def list_providers(self):
        """List all available providers"""
        return list(self.keys.keys())
    
    def has_key(self, provider):
        """Check if a provider key exists"""
        return provider in self.keys

# Singleton instance
_api_manager = None

def get_api_manager():
    """Get the singleton API manager instance"""
    global _api_manager
    if _api_manager is None:
        _api_manager = APIManager()
    return _api_manager
