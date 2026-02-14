# =============================================
# META DATA HEADER
# Name: code_search.py
# Date: 2025-07-21
# Version: 0.2.0
# 
# CHANGELOG:
#   - v0.1.0 (2025-07-21): Initial AI-powered codebase search engine
#   - v0.2.0 (2025-07-21): Improved AI prompting with stratified sampling
# =============================================

"""
Code Search Skill

AI-powered semantic search through scanned codebase analysis.
Intelligently searches across multiple projects with balanced results.
"""

import sys
import os
import json
import time
import requests
import re
import random
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict

# System integration imports
sys.path.append(str(Path(__file__).parent.parent))
from prax.prax_logger import system_logger as logger

# Test logger immediately
logger.info("code_search skill imported and logger working")

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
CONFIG_FILE = JSON_DIR / "code_search_config.json"

def load_config() -> Dict:
    """Load configuration from JSON file, create default if missing"""
    if not CONFIG_FILE.exists():
        logger.info(f"Configuration file not found, creating default: {CONFIG_FILE}")
        
        # Create default configuration
        default_config = {
            "model": "gpt-4.1-nano",
            "analysis_file": "code_sniffer_analysis.md",
            "output_dir": "search_results",
            "actual_base_path": "C:\\AIPass-Ecosystem",
            "max_results": 10,
            "temperature": 0.1,
            "timeout_seconds": 30,
            "max_description_words": 30
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
        
        # Convert relative paths to absolute
        config["analysis_file"] = str(SCRIPT_DIR / config["analysis_file"])
        config["output_dir"] = str(SCRIPT_DIR / config["output_dir"])
        
        return config
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        raise

# Load configuration
CONFIG = load_config()

# =============================================
# CORE FUNCTIONALITY
# =============================================

def load_codebase_analysis() -> Optional[List[Dict]]:
    """Load and parse the scanned codebase analysis"""
    analysis_path = Path(CONFIG["analysis_file"])
    
    if not analysis_path.exists():
        logger.error(f"Analysis file not found: {analysis_path}")
        return None
    
    logger.info(f"Loading analysis from: {analysis_path}")
    
    try:
        with open(analysis_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse the markdown to extract file entries
        entries = []
        current_file = None
        current_description = None
        
        for line in content.split('\n'):
            # Check for file headers (## filepath)
            if line.startswith('## ') and not line.startswith('## Total Files'):
                if current_file and current_description:
                    entries.append({
                        'file': current_file,
                        'description': current_description.strip()
                    })
                
                current_file = line[3:].strip()  # Remove "## "
                current_description = ""
            elif current_file and line.strip() and not line.startswith('#'):
                if current_description:
                    current_description += " " + line.strip()
                else:
                    current_description = line.strip()
        
        # Don't forget the last entry
        if current_file and current_description:
            entries.append({
                'file': current_file,
                'description': current_description.strip()
            })
        
        logger.info(f"Successfully loaded {len(entries)} code files from analysis")
        return entries
        
    except Exception as e:
        logger.error(f"Failed to load analysis file: {e}")
        return None

def truncate_description(description: str, max_words: int) -> str:
    """Truncate description to specified word count"""
    words = description.split()
    if len(words) <= max_words:
        return description
    
    truncated = ' '.join(words[:max_words])
    return f"{truncated}..."

def ai_search(query: str, codebase_entries: List[Dict]) -> List[int]:
    """Use AI to search through codebase entries with improved prompting to reduce bias"""
    logger.info(f"Starting AI search for query: '{query}' across {len(codebase_entries)} files")
    
    # Get API key
    api_key = get_api_key()
    if not api_key:
        logger.error("Could not get OpenAI API key")
        raise RuntimeError("OpenAI API key not available")
    
    # For large datasets, sample to reduce token usage and bias
    max_files = 300  # Reasonable limit for token constraints
    if len(codebase_entries) > max_files:
        logger.info(f"Large dataset detected ({len(codebase_entries)} files), sampling {max_files} files")
        
        # Stratified sampling to ensure fair representation
        codex_files = [(i, entry) for i, entry in enumerate(codebase_entries) if 'codex-main' in entry['file']]
        void_files = [(i, entry) for i, entry in enumerate(codebase_entries) if 'void-main' in entry['file']]
        other_files = [(i, entry) for i, entry in enumerate(codebase_entries) if 'codex-main' not in entry['file'] and 'void-main' not in entry['file']]
        
        # Calculate proportional sampling
        total_files = len(codebase_entries)
        codex_sample_size = min(len(codex_files), int(max_files * len(codex_files) / total_files))
        void_sample_size = min(len(void_files), int(max_files * len(void_files) / total_files))
        other_sample_size = max_files - codex_sample_size - void_sample_size
        
        # Sample from each group
        sampled_entries = []
        if codex_files:
            sampled_entries.extend(random.sample(codex_files, codex_sample_size))
        if void_files:
            sampled_entries.extend(random.sample(void_files, min(void_sample_size, len(void_files))))
        if other_files and other_sample_size > 0:
            sampled_entries.extend(random.sample(other_files, min(other_sample_size, len(other_files))))
        
        # Sort by original index to maintain some order
        sampled_entries.sort(key=lambda x: x[0])
        
        logger.info(f"Sampled {len(sampled_entries)} files: {codex_sample_size} codex, {void_sample_size} void, {other_sample_size} other")
    else:
        # Use all files for smaller datasets
        sampled_entries = [(i, entry) for i, entry in enumerate(codebase_entries)]
    
    # Create a condensed representation for AI analysis
    codebase_text = ""
    for original_idx, entry in sampled_entries:
        short_desc = truncate_description(entry['description'], 12)  # Very short for token efficiency
        codebase_text += f"[{original_idx}] {entry['file']}: {short_desc}\n"
    
    # IMPROVED PROMPT: Explicitly mention both projects and require diversity
    prompt = f"""You are searching a codebase containing TWO main projects: "codex-main" and "void-main".

Query: "{query}"

Files to search:
{codebase_text}

IMPORTANT REQUIREMENTS:
1. Search for files semantically related to "{query}"
2. Consider both "codex-main" and "void-main" projects equally
3. Look at file paths, names, and descriptions for relevance
4. Return diverse results from BOTH projects when possible
5. Maximum {CONFIG['max_results']} results

Return ONLY the indices (numbers in brackets) as comma-separated values.
Example: "5,12,28,45,67"
If no relevant matches found, return "NONE"
"""

    try:
        logger.info("Sending request to OpenAI API")
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": CONFIG["model"],
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 200,  # Increased token limit
                "temperature": CONFIG["temperature"]
            },
            timeout=CONFIG.get("timeout_seconds", 30)
        )
        
        if response.status_code == 200:
            result = response.json()
            answer = result['choices'][0]['message']['content'].strip()
            
            # Log API usage for monitoring
            if get_usage_monitor and 'usage' in result:
                try:
                    get_usage_monitor().log_usage(
                        provider="openai",
                        model=CONFIG["model"],
                        input_tokens=result['usage']['prompt_tokens'],
                        output_tokens=result['usage']['completion_tokens'],
                        system="code_search"
                    )
                    logger.info(f"[code_search] Usage: {result['usage']['prompt_tokens']} in, {result['usage']['completion_tokens']} out")
                except Exception as e:
                    logger.error(f"Failed to log usage: {e}")
            
            logger.info(f"AI response: {answer}")
            
            if answer == "NONE":
                logger.info("No relevant matches found")
                return []
            
            # Parse the indices
            try:
                indices = [int(x.strip()) for x in answer.split(',')]
                # Filter valid indices
                valid_indices = [i for i in indices if 0 <= i < len(codebase_entries)]
                logger.info(f"Found {len(valid_indices)} valid matches")
                return valid_indices[:CONFIG['max_results']]
            except ValueError:
                logger.error(f"Could not parse AI response: {answer}")
                return []
        else:
            logger.error(f"API error: {response.status_code} - {response.text}")
            return []
            
    except Exception as e:
        logger.error(f"Search error: {e}")
        return []

def generate_search_results(query: str, results: List[int], codebase_entries: List[Dict]) -> Path:
    """Generate markdown file with search results"""
    # Create output directory
    output_dir = Path(CONFIG["output_dir"])
    output_dir.mkdir(exist_ok=True)
    
    # Generate filename
    safe_query = re.sub(r'[^\w\s-]', '', query).strip()
    safe_query = re.sub(r'[-\s]+', '_', safe_query)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"search_{safe_query}_{timestamp}.md"
    output_path = output_dir / filename
    
    # Count projects in results
    project_counts = {}
    for idx in results:
        if idx < len(codebase_entries):
            file_path = codebase_entries[idx]['file']
            if 'codex-main' in file_path:
                project_counts['codex-main'] = project_counts.get('codex-main', 0) + 1
            elif 'void-main' in file_path:
                project_counts['void-main'] = project_counts.get('void-main', 0) + 1
            else:
                project_counts['other'] = project_counts.get('other', 0) + 1
    
    # Generate content
    content = f"""# Code Search Results 

**Query:** `{query}`  
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Results Found:** {len(results)}  
**Searched:** {CONFIG["analysis_file"]}  

**Project Distribution:**
"""
    
    for project, count in project_counts.items():
        content += f"- {project}: {count} files\n"
    
    content += "\n---\n\n"

    if not results:
        content += "❌ **No relevant files found for this query.**\n\n"
        content += "Try:\n"
        content += "- Using different keywords\n"
        content += "- Broader search terms\n" 
        content += "- Technical concepts related to your search\n"
    else:
        for i, idx in enumerate(results, 1):
            if idx >= len(codebase_entries):
                continue
                
            entry = codebase_entries[idx]
            
            # Create file link (files are in the scanning folder)
            file_path = entry['file']
            # Files are actually stored in the scanning directory
            scanning_file_path = os.path.join(str(SCRIPT_DIR), "scanning", file_path)
            
            # Truncate description for quick reading
            description = truncate_description(entry['description'], CONFIG.get('max_description_words', 30))
            
            content += f"## {i}. {file_path}\n\n"
            content += f"**Index:** `{idx}`\n\n"  # Show the index for debugging
            content += f"**Description:** {description}\n\n"
            content += f"**File Path:** `{file_path}`\n\n"
            content += f"**Scanned Location:** `{scanning_file_path}`\n\n"
            
            # Add clickable links
            if os.path.exists(scanning_file_path):
                # VS Code link (opens directly in VS Code)
                vscode_link = f"vscode://file/{scanning_file_path.replace(os.sep, '/')}"
                # File protocol link (opens in default application)  
                file_link = f"file:///{scanning_file_path.replace(os.sep, '/')}"
                
                content += f"**🔗 Links:**\n"
                content += f"- [Open in VS Code]({vscode_link})\n"
                content += f"- [Open File]({file_link})\n\n"
            else:
                content += f"**📁 File not found in scanning folder**\n\n"
            
            content += "---\n\n"
    
    # Write results
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"Results saved to: {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"Failed to save results: {e}")
        raise

def search_codebase(query: str) -> Optional[Path]:
    """Main search function"""
    logger.info(f"Starting codebase search for: '{query}'")
    
    # Load codebase analysis
    codebase_entries = load_codebase_analysis()
    if not codebase_entries:
        logger.error("Failed to load codebase analysis")
        return None
    
    start_time = time.time()
    
    # Perform AI search
    result_indices = ai_search(query, codebase_entries)
    
    # Generate results
    output_path = generate_search_results(query, result_indices, codebase_entries)
    
    # Log completion
    elapsed = time.time() - start_time
    logger.info(f"Search completed in {elapsed:.1f}s, found {len(result_indices)} results")
    
    return output_path

# =============================================
# CLI INTERFACE
# =============================================

def main():
    """Command line interface"""
    logger.info("Code Search Engine started")
    
    print("AI Code Search Engine v0.2.0")
    print("=" * 50)
    
    # Get search query
    if len(sys.argv) > 1:
        query = ' '.join(sys.argv[1:])
    else:
        query = input("\nEnter search query: ").strip()
    
    if not query:
        print("No search query provided")
        logger.warning("No search query provided")
        return
    
    print(f"\nSearching for: '{query}'")
    print("AI is analyzing codebase...")
    
    try:
        output_path = search_codebase(query)
        if output_path:
            print(f"\nSearch completed!")
            print(f"Results saved to: {output_path}")
        else:
            print(f"\nSearch failed - check logs")
    except Exception as e:
        print(f"\nSearch error: {e}")
        logger.error(f"Search failed: {e}")

if __name__ == "__main__":
    main()
