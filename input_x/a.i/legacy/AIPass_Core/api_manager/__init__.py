from .api_manager import APIManager

# --- API manager singleton ---
_manager = None

def get_api_manager():
    """Get the singleton API manager instance"""
    global _manager
    if _manager is None:
        _manager = APIManager()
    return _manager

# Convenience function
def get_key(provider):
    """Quick access to get a key"""
    return get_api_manager().get_key(provider)

__all__ = ['APIManager', 'get_api_manager', 'get_key']

