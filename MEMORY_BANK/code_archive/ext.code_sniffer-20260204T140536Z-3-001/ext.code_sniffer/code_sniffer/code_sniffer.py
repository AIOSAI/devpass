#!/usr/bin/env python3

# =============================================
# META DATA HEADER
# Name: code_sniffer.py
# Date: 2025-07-21
# Version: 1.0.0
# 
# CHANGELOG:
#   - v1.0.0 (2025-07-21): Initial codebase analysis tool with JSON config
# =============================================

"""
Code Sniffer

AI-powered codebase analysis tool that generates descriptions of code files.
Uses configurable JSON settings and follows AIPass ecosystem patterns.
"""

import os
import sys
import json
import time
import requests
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict

# System integration imports
sys.path.append(str(Path(__file__).parent.parent))
from prax.prax_logger import system_logger as logger

# Test logger immediately
logger.info("code_sniffer imported and logger working")

# API Usage Monitoring integration
try:
    from prax.prax_api_usage_monitor import get_usage_monitor
    logger.info("API Usage Monitor integration enabled")
except ImportError as e:
    logger.error(f"Failed to import usage monitor: {e}")
    get_usage_monitor = None

# =============================================
# CONFIGURATION SECTION
# =============================================

def get_api_key() -> Optional[str]:
    """Get API key from external file"""
    try:
        env_file = Path("C:/aipass_api_keys_live/.env")
        if not env_file.exists():
            logger.error("API key file not found: C:/aipass_api_keys_live/.env")
            return None
            
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith("OPENAI=") or line.startswith("openai="):
                    api_key = line.split("=", 1)[1].strip()
                    if api_key:
                        return api_key
                        
        logger.error("OpenAI API key not found in .env file")
        return None
    except Exception as e:
        logger.error(f"API key retrieval error: {e}")
        return None

# Get script directory
SCRIPT_DIR = Path(__file__).parent

# JSON directory (following AIPass patterns: {module}_json)
JSON_DIR = SCRIPT_DIR / "code_sniffer_json"
JSON_DIR.mkdir(exist_ok=True)

# Configuration file path following prax pattern: {module_name}_config.json
CONFIG_FILE = JSON_DIR / "code_sniffer_config.json"

def load_config() -> Dict:
    """Load configuration from JSON file, create default if missing"""
    if not CONFIG_FILE.exists():
        logger.info(f"Configuration file not found, creating default: {CONFIG_FILE}")
        
        # Create default configuration
        default_config = {
            "model": "gpt-4.1-nano",
            "base_path": str(SCRIPT_DIR / "scanning"),
            "output_file": "code_sniffer_analysis.md",
            "progress_file": "code_sniffer_progress.json",
            "code_extensions": [".py", ".ts", ".js", ".tsx", ".jsx", ".vue", ".php", ".rb", ".go", ".rust", ".cpp", ".c", ".h", ".java", ".cs"],
            "ignore_dirs": [
                "node_modules", "__pycache__", ".git", ".vscode", ".idea",
                "dist", "build", "target", "bin", "obj", ".venv",
                "backups", "archive", "trash", "research_review", 
                "mcp-servers", "tests"
            ],
            "ignore_files": ["__init__.py"],
            "max_file_size_kb": 500,
            "temperature": 0.1,
            "timeout_seconds": 30,
            "max_description_words": 50
        }
        
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)
            logger.info("Default configuration file created")
        except Exception as e:
            logger.error(f"Failed to create default configuration: {e}")
            raise
    
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
        logger.info("Configuration loaded successfully")
        return config
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        raise

# Load configuration
CONFIG = load_config()

# =============================================
# CORE FUNCTIONALITY
# =============================================

def load_progress() -> Dict:
    """Load scan progress from JSON file"""
    progress_file = JSON_DIR / CONFIG["progress_file"]
    
    if progress_file.exists():
        try:
            with open(progress_file, 'r', encoding='utf-8') as f:
                progress = json.load(f)
            logger.info(f"Loaded progress: {len(progress.get('completed', []))} files completed")
            return progress
        except Exception as e:
            logger.warning(f"Could not load progress file: {e}")
            return {"completed": []}
    else:
        logger.info("No progress file found, starting fresh scan")
        return {"completed": []}

def save_progress(progress: Dict) -> None:
    """Save scan progress to JSON file"""
    progress_file = JSON_DIR / CONFIG["progress_file"]
    
    try:
        with open(progress_file, 'w', encoding='utf-8') as f:
            json.dump(progress, f, indent=2, ensure_ascii=False)
        logger.info(f"Progress saved: {len(progress.get('completed', []))} files completed")
    except Exception as e:
        logger.error(f"Failed to save progress: {e}")

def find_code_files() -> List[str]:
    """Find all code files to analyze"""
    base_path = Path(CONFIG["base_path"])
    
    if not base_path.exists():
        logger.error(f"Base path does not exist: {base_path}")
        raise FileNotFoundError(f"Base path not found: {base_path}")
    
    logger.info(f"Scanning for code files in: {base_path}")
    code_files = []
    
    for root, dirs, files in os.walk(base_path):
        # Filter out ignored directories
        dirs[:] = [d for d in dirs if d not in CONFIG["ignore_dirs"]]
        
        root_path = Path(root)
        
        for file in files:
            # Check if file has code extension
            if any(file.endswith(ext) for ext in CONFIG["code_extensions"]):
                # Skip ignored files
                if file not in CONFIG["ignore_files"]:
                    file_path = root_path / file
                    relative_path = file_path.relative_to(base_path)
                    code_files.append(str(relative_path))
    
    logger.info(f"Found {len(code_files)} code files to analyze")
    return code_files

def analyze_file(file_path: str) -> Optional[str]:
    """Analyze a single file with AI via direct API call"""
    api_key = get_api_key()
    if not api_key:
        logger.error("Cannot analyze file: no API key available")
        return None
        
    base_path = Path(CONFIG["base_path"])
    full_path = base_path / file_path
    
    # Check file size
    try:
        file_size_kb = full_path.stat().st_size / 1024
        if file_size_kb > CONFIG.get("max_file_size_kb", 500):
            logger.warning(f"Skipping large file ({file_size_kb:.1f}KB): {file_path}")
            return f"Large file ({file_size_kb:.1f}KB) - skipped for performance"
    except Exception as e:
        logger.error(f"Could not check file size for {file_path}: {e}")
        return None
    
    # Read file content
    try:
        with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except Exception as e:
        logger.error(f"Could not read file {file_path}: {e}")
        return None
    
    # Prepare AI prompt
    prompt = f"""Analyze this code file and provide a concise, informative description of its purpose and main functionality.

File: {file_path}
Content:
{content}

Please provide a brief description (maximum {CONFIG.get('max_description_words', 50)} words) that explains:
1. What this file does
2. Its main purpose and functionality  
3. Key technologies or patterns it uses

Keep the description concise and focused, suitable for quick scanning in a codebase overview."""

    try:
        logger.info(f"Analyzing file with AI: {file_path}")
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": CONFIG["model"],
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 200,
                "temperature": CONFIG.get("temperature", 0.1)
            },
            timeout=CONFIG.get("timeout_seconds", 30)
        )
        
        if response.status_code == 200:
            result = response.json()
            description = result['choices'][0]['message']['content'].strip()
            
            # Log API usage for monitoring
            if get_usage_monitor and 'usage' in result:
                try:
                    get_usage_monitor().log_usage(
                        provider="openai",
                        model=CONFIG["model"],
                        input_tokens=result['usage']['prompt_tokens'],
                        output_tokens=result['usage']['completion_tokens'],
                        system="code_sniffer"
                    )
                    logger.info(f"[code_sniffer] Usage logged: {result['usage']['prompt_tokens']} in, {result['usage']['completion_tokens']} out")
                except Exception as e:
                    logger.error(f"Failed to log usage: {e}")
            
            logger.info(f"Successfully analyzed: {file_path}")
            return description
        else:
            logger.error(f"API error for {file_path}: {response.status_code}")
            return None
            
    except Exception as e:
        logger.error(f"Analysis error for {file_path}: {e}")
        return None

def process_files() -> None:
    """Main processing function"""
    logger.info("Starting file processing")
    
    # Load progress and find files
    progress = load_progress()
    completed = set(progress.get("completed", []))
    code_files = find_code_files()
    
    # Filter out completed files
    remaining_files = [f for f in code_files if f not in completed]
    logger.info(f"Found {len(remaining_files)} files to process")
    
    if not remaining_files:
        logger.info("No new files to process")
        return
    
    # Prepare output file
    output_path = SCRIPT_DIR / CONFIG["output_file"]
    
    # Write header for new file or continue existing
    with open(output_path, 'w' if not progress["completed"] else 'a', encoding='utf-8') as f:
        if not progress["completed"]:
            # Write header for new file
            f.write(f"# Codebase Analysis Report\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Base Path: {CONFIG['base_path']}\n")
            f.write(f"Total Files: {len(code_files)}\n\n")
            f.write("---\n\n")
        
        # Process each file
        for i, file_path in enumerate(remaining_files):
            print(f"Processing [{i+1:3d}/{len(remaining_files):3d}] ({((i+1)/len(remaining_files)*100):5.1f}%) - {file_path}")
            
            description = analyze_file(file_path)
            if description:
                f.write(f"## {file_path}\n\n")
                f.write(f"{description}\n\n")
                f.flush()  # Ensure content is written immediately
                
                # Update progress
                progress["completed"].append(file_path)
                save_progress(progress)
            else:
                logger.warning(f"Failed to analyze: {file_path}")
    
    logger.info(f"Processing complete! Analyzed {len(progress['completed'])} files")
    print(f"\n📁 Results saved to: {output_path}")
    print(f"📊 Processed {len(progress['completed'])} files")

# =============================================
# CLI INTERFACE
# =============================================

def main():
    """Command line interface"""
    logger.info("Code Sniffer started")
    
    print("🔍 Code Sniffer v1.0.0")
    print("=" * 40)
    
    # Show configuration
    print(f"Base path: {CONFIG['base_path']}")
    print(f"Model: {CONFIG['model']}")
    print(f"Output: {CONFIG['output_file']}")
    print(f"Extensions: {', '.join(CONFIG['code_extensions'])}")
    print("-" * 40)
    
    # Start timing
    start_time = time.time()
    start_datetime = datetime.now()
    print(f"Scan started: {start_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        process_files()
        
        # End timing
        end_time = time.time()
        elapsed = end_time - start_time
        minutes = int(elapsed // 60)
        seconds = elapsed % 60
        
        print()
        print("=" * 50)
        print(f"✅ Scan completed in {minutes}m {seconds:.1f}s")
        
    except Exception as e:
        logger.error(f"Scan failed: {e}")
        print(f"\n❌ Scan failed: {e}")

if __name__ == "__main__":
    main()
