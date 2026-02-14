def get_prompt():
    """Returns the prompt text for file cache awareness and usage."""
    return """
# File Cache Awareness

Seed maintains a file cache in `file_cache.json` to store the contents of recently read files during this session. You may use this cache to reference file contents, summarize, analyze, or answer questions about files without re-reading them from disk.

- The cache is reset at the end of every chat session.
- Each entry is keyed by the file path and contains the file's content as a string.
- Use the cache to answer questions about files or to recall previously read files.
- Do not assume the cache is always complete; always check for the file path key before using its content.

Example usage:
- To summarize a file, use its content from the cache.
- To compare two files, retrieve both from the cache by their paths.

Security: Only files within the project boundary are cached.
"""
