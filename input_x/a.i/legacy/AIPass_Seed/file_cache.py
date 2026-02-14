import json
import os

CACHE_FILENAME = os.path.join(os.path.dirname(__file__), "file_cache.json")

def cache_file_content(file_path, content, cache_path=CACHE_FILENAME):
    """Cache file content by file path in file_cache.json."""
    cache = {}
    if os.path.exists(cache_path):
        with open(cache_path, "r", encoding="utf-8") as f:
            try:
                cache = json.load(f)
            except Exception:
                cache = {}
    cache[file_path] = content
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2)

def read_cached_file(file_path, cache_path=CACHE_FILENAME):
    """Read cached file content by file path from file_cache.json."""
    if os.path.exists(cache_path):
        with open(cache_path, "r", encoding="utf-8") as f:
            cache = json.load(f)
        if file_path in cache:
            return cache[file_path]
        else:
            raise FileNotFoundError(f"No cached content for: {file_path}")
    else:
        raise FileNotFoundError("Cache file does not exist.")

def clear_cache(cache_path=CACHE_FILENAME):
    """Clear the file cache (truncate file_cache.json)."""
    with open(cache_path, "w", encoding="utf-8") as f:
        f.write("{}\n")

def read_all_cache(cache_path=CACHE_FILENAME):
    """Return the entire file cache as a dict."""
    if os.path.exists(cache_path):
        with open(cache_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}
