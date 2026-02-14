# --- API key loader ---

import re
import os
from pathlib import Path

class KeyLoader:
    def __init__(self, key_file_path):
        self.key_file_path = Path(key_file_path)
        self.keys = {}
        
    def load_keys(self):
        """Parse the .env file and extract API keys"""
        # Convert Path object to string and use os.path.exists() to check if file exists
        key_file_path_str = str(self.key_file_path)
        
        if not os.path.exists(key_file_path_str):
            raise FileNotFoundError(f"Key file not found: {key_file_path_str}")
            
        # Use standard file open instead of Path.read_text()
        with open(key_file_path_str, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse .env format: KEY=value
        for line in content.strip().split('\n'):
            line = line.strip()
            
            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue
                
            # Split on first = sign
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                # Skip placeholder values
                if value and not value.startswith('your_'):
                    # Map .env keys to legacy provider names
                    if key == 'OPENAI_API_KEY':
                        self.keys['openai'] = value
                    elif key == 'ANTHROPIC_API_KEY':
                        self.keys['anthropic'] = value
                    elif key == 'GOOGLE_API_KEY':
                        self.keys['gemini'] = value
                    elif key == 'MISTRAL_API_KEY':
                        self.keys['mistral'] = value
                    elif key == 'STABILITY_API_KEY':
                        self.keys['stability'] = value
                    elif key == 'COHERE_API_KEY':
                        self.keys['cohere'] = value
                    elif key == 'OPENROUTER_API_KEY':
                        self.keys['openrouter'] = value
        
        return self.keys
