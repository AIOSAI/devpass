"""
natural_flow.py - Dynamic Conversational System Operator

Replaces all handlers - transforms natural conversation into immediate system operations.
Nexus operates through this layer - no commands, no parsing, just contextual execution.
"""

import os
import re
import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Tuple
import io
import contextlib

import display
import llm_client
from config_loader import load_api_config
from nexus_memory_vectors.vector_memory import search_my_memories, get_memory_summary

# ================================
# EXECUTION CONTEXT
# ================================

class ExecutionContext:
    """Persistent execution context for Nexus operations"""
    
    def __init__(self):
        # Core execution globals
        self.globals = {
            'Path': Path,
            'os': os,
            'json': json,
            'subprocess': subprocess,
            'datetime': datetime,
            'sys': sys,
            're': re,
            # Nexus-specific tracking
            'created_files': [],
            'modified_files': [],
            'executed_scripts': [],
            'last_result': None,
            'last_output': '',
            'working_dir': Path.cwd(),
            'nexus_dir': Path(__file__).parent,
        }
        
        # Operation tracking
        self.operation_history = []
        self.session_start = datetime.now()
        
        # File cache system (restored)
        self.file_cache = []
        self.loaded_files = {}
        self.max_cache_entries = 5
    
    def execute(self, code: str) -> Dict[str, Any]:
        """Execute Python code in persistent context with full capture"""
        
        # Clean the code
        code = code.strip()
        if not code:
            return {'success': False, 'error': 'Empty code block', 'output': ''}
        
        try:
            # Capture both stdout and any return values
            output_buffer = io.StringIO()
            
            with contextlib.redirect_stdout(output_buffer):
                # Execute the code
                exec(code, self.globals)
            
            # Get captured output
            captured_output = output_buffer.getvalue()
            
            # Check for any results stored in last_result
            result_value = self.globals.get('last_result')
            
            # Combine output sources
            full_output = captured_output
            if result_value and str(result_value) not in captured_output:
                full_output += f"\nResult: {result_value}"
            
            # Log successful operation
            self.operation_history.append({
                'timestamp': datetime.now().isoformat(),
                'code': code,
                'success': True,
                'output': full_output,
                'result': result_value
            })
            
            # Update last_output for context
            self.globals['last_output'] = full_output
            
            return {
                'success': True,
                'output': full_output.strip(),
                'result': result_value,
                'code_executed': code
            }
            
        except Exception as e:
            error_msg = f"{type(e).__name__}: {str(e)}"
            
            # Log failed operation
            self.operation_history.append({
                'timestamp': datetime.now().isoformat(),
                'code': code,
                'success': False,
                'error': error_msg
            })
            
            return {
                'success': False,
                'error': error_msg,
                'output': '',
                'code_executed': code
            }
    
    def get_context_summary(self) -> str:
        """Get summary of current execution context"""
        created = len(self.globals.get('created_files', []))
        modified = len(self.globals.get('modified_files', []))
        executed = len(self.globals.get('executed_scripts', []))
        total_ops = len(self.operation_history)
        
        summary_parts = []
        if created > 0:
            summary_parts.append(f"{created} files created")
        if modified > 0:
            summary_parts.append(f"{modified} files modified")
        if executed > 0:
            summary_parts.append(f"{executed} scripts executed")
        if total_ops > 0:
            summary_parts.append(f"{total_ops} total operations")
        
        return " | ".join(summary_parts) if summary_parts else "Clean execution context"
    
    def load_file_to_cache(self, file_path: str) -> Dict[str, Any]:
        """Load a file into the cache system like the old handlers"""
        try:
            # Resolve path
            if not file_path.startswith('/') and not Path(file_path).is_absolute():
                # Relative path - try different base locations
                possible_paths = [
                    Path(file_path),  # Current directory
                    self.globals['nexus_dir'] / file_path,  # Nexus directory
                    self.globals['working_dir'] / file_path,  # Working directory
                ]
                
                file_obj = None
                for p in possible_paths:
                    if p.exists() and p.is_file():
                        file_obj = p
                        break
                
                if file_obj is None:
                    return {
                        'success': False,
                        'error': f"File not found: {file_path} (tried: {', '.join(str(p) for p in possible_paths)})"
                    }
            else:
                file_obj = Path(file_path)
                if not file_obj.exists():
                    return {'success': False, 'error': f"File not found: {file_path}"}
            
            # Read file content
            content = file_obj.read_text(encoding='utf-8', errors='replace')
            
            # Add to cache
            timestamp = datetime.now(timezone.utc).isoformat()
            cache_entry = {
                'path': str(file_obj.resolve()),
                'relative_path': file_path,
                'timestamp': timestamp,
                'content': content,
                'size': len(content)
            }
            
            # Update cache (newest first)
            self.file_cache.insert(0, cache_entry)
            
            # Update loaded_files dict
            self.loaded_files[file_path] = content
            
            # Maintain cache size limit
            if len(self.file_cache) > self.max_cache_entries:
                removed = self.file_cache[self.max_cache_entries:]
                self.file_cache = self.file_cache[:self.max_cache_entries]
                
                # Remove from loaded_files too
                for entry in removed:
                    if entry['relative_path'] in self.loaded_files:
                        del self.loaded_files[entry['relative_path']]
            
            return {
                'success': True,
                'content': content,
                'file_path': str(file_obj.resolve()),
                'size': len(content),
                'cache_entries': len(self.file_cache)
            }
            
        except Exception as e:
            return {'success': False, 'error': f"Error loading file: {e}"}
    
    def clear_file_cache(self):
        """Clear the file cache"""
        self.file_cache.clear()
        self.loaded_files.clear()
        return "File cache cleared successfully"
    
    def get_loaded_files_summary(self) -> str:
        """Get summary of currently loaded files"""
        if not self.file_cache:
            return "No files currently loaded"
        
        summary = [f"Loaded files ({len(self.file_cache)}/{self.max_cache_entries}):"] 
        for entry in self.file_cache:
            size_kb = entry['size'] / 1024
            summary.append(f"- {entry['relative_path']} ({size_kb:.1f}KB)")
        
        return "\n".join(summary)
        
    def force_cortex_refresh(self):
        """Force cortex to refresh and return status"""
        try:
            import cortex_module
            cortex_module.refresh_cortex_summary()
            return True
        except Exception as e:
            return f"Cortex refresh failed: {e}"

# Global execution context
execution_context = ExecutionContext()

# ================================
# INTENT DETECTION
# ================================

def detect_operational_intent(user_input: str) -> Dict[str, Any]:
    """Detect if user input requires system operations and what type"""
    
    lower_input = user_input.lower()
    
    # File operation patterns
    file_operations = {
        'create': ['create', 'make', 'build', 'generate', 'write', 'new'],
        'edit': ['edit', 'modify', 'update', 'change', 'fix', 'revise'],
        'read': ['read', 'show', 'display', 'view', 'open', 'see', 'check'],
        'load': ['load', 'read file', 'open file', 'load file'],  # File loading
        'delete': ['delete', 'remove', 'clear'],
        'list': ['list', 'show files', 'what files'],
        'cache': ['clear cache', 'reset cache', 'file cache']  # Cache operations
    }
    
    # Script/execution patterns
    execution_patterns = [
        'run', 'execute', 'test', 'try', 'launch', 'start'
    ]
    
    # Data processing patterns
    data_patterns = [
        'analyze', 'process', 'parse', 'extract', 'transform', 'calculate'
    ]
    
    # System patterns
    system_patterns = [
        'install', 'setup', 'configure', 'check system', 'status'
    ]
    
    # File type indicators
    file_indicators = ['.py', '.md', '.txt', '.json', '.csv', '.xml', '.yaml', '.log']
    
    # Context references (referencing previous work)
    context_refs = ['that file', 'the script', 'it', 'this', 'what we made']
    
    # Analyze input
    detected_operations = []
    confidence_score = 0
    
    # Check file operations
    for op_type, keywords in file_operations.items():
        if any(keyword in lower_input for keyword in keywords):
            detected_operations.append(op_type)
            confidence_score += 0.8
    
    # Check execution patterns
    if any(pattern in lower_input for pattern in execution_patterns):
        detected_operations.append('execute')
        confidence_score += 0.8
    
    # Check data patterns
    if any(pattern in lower_input for pattern in data_patterns):
        detected_operations.append('data_processing')
        confidence_score += 0.8
    
    # Check system patterns
    if any(pattern in lower_input for pattern in system_patterns):
        detected_operations.append('system')
        confidence_score += 0.8
    
    # File type indicators boost confidence
    if any(indicator in lower_input for indicator in file_indicators):
        confidence_score += 0.8
    
    # Context references boost confidence
    if any(ref in lower_input for ref in context_refs):
        confidence_score += 0.8
    
    # Determine if operational
    is_operational = confidence_score >= 0.8 or len(detected_operations) > 0
    
    return {
        'is_operational': is_operational,
        'operations': detected_operations,
        'confidence': min(confidence_score, 1.0),
        'indicators_found': {
            'file_ops': [op for op in file_operations.keys() if any(kw in lower_input for kw in file_operations[op])],
            'has_file_types': any(indicator in lower_input for indicator in file_indicators),
            'has_context_refs': any(ref in lower_input for ref in context_refs)
        }
    }


def detect_memory_search_intent(user_input: str) -> Tuple[bool, str]:
    """
    Detect if user wants Nexus to search his vector memories.
    
    Returns:
        (is_memory_search, search_query)
    """
    # Convert to lowercase for matching
    text = user_input.lower().strip()
    
    # Memory search trigger phrases
    memory_triggers = [
        "remember when",
        "recall when", 
        "do you remember",
        "we discussed",
        "we talked about",
        "we were chatting about",
        "last week we",
        "remember last",
        "what did we decide",
        "we covered",
        "remember our conversation",
        "remember that time",
        "didn't we talk about"
    ]
    
    # Check for triggers
    for trigger in memory_triggers:
        if trigger in text:
            # Extract the search query (everything after the trigger)
            if trigger in text:
                parts = text.split(trigger, 1)
                if len(parts) > 1:
                    search_query = parts[1].strip()
                    # Clean up common words
                    search_query = search_query.replace("about", "").strip()
                    search_query = search_query.replace("?", "").strip()
                    return True, search_query
            return True, text  # Fallback to full text
    
    return False, ""

# ================================
# CODE GENERATION
# ================================

def generate_operational_code(user_input: str, intent_analysis: Dict[str, Any]) -> str:
    """Generate Python code based on conversational input and detected intent"""
    
    # Build context-aware prompt
    context_info = [
        f"Working directory: {execution_context.globals['working_dir']}",
        f"Nexus directory: {execution_context.globals['nexus_dir']}",
        f"Session context: {execution_context.get_context_summary()}"
    ]
    
    # Add loaded files context
    if execution_context.loaded_files:
        context_info.append(f"Currently loaded files: {', '.join(execution_context.loaded_files.keys())}")
    
    # Add recent files if any
    created_files = execution_context.globals.get('created_files', [])
    if created_files:
        context_info.append(f"Recently created: {', '.join(created_files[-5:])}")
    
    # Build the generation prompt
    prompt_parts = [
        "You are Nexus, a system operator. Generate Python code to fulfill the user's request.",
        "",
        f"User request: {user_input}",
        "",
        f"Detected intent: {intent_analysis['operations']} (confidence: {intent_analysis['confidence']:.2f})",
        "",
        "Context:",
    ]
    prompt_parts.extend(f"- {info}" for info in context_info)
    
    # Add loaded file contents if relevant
    if execution_context.loaded_files:
        prompt_parts.append("\nCurrently loaded files (available for analysis):")
        for file_path, content in execution_context.loaded_files.items():
            content_preview = content[:200] + "..." if len(content) > 200 else content
            prompt_parts.append(f"- {file_path}: {content_preview}")
    
    prompt_parts.extend([
        "",
        "IMPORTANT: Generate executable Python code that directly fulfills the request.",
        "Use these patterns:",
        "",
        "File operations:",
        "- Create: Path('filename.txt').write_text('content')",
        "- Read: content = Path('filename.txt').read_text()",
        "- Modify: content = Path('file.txt').read_text(); Path('file.txt').write_text(content + 'addition')",
        "- List: files = list(Path('.').glob('*'))",
        "",
        "Script execution:",
        "- Run: result = subprocess.run(['python', 'script.py'], capture_output=True, text=True)",
        "",
        "Track your work:",
        "- created_files.append('filename.txt')  # Track new files",
        "- modified_files.append('filename.txt')  # Track changes",
        "- last_result = result  # Store important results",
        "",
        "Respond with Python code in triple backticks:",
        "```python",
        "# Your code here",
        "```"
    ])
    
    prompt = "\n".join(prompt_parts)
    
    # Generate code using LLM
    try:
        cfg = load_api_config()
        active_provider = next(name for name, spec in cfg["providers"].items() if spec.get("enabled"))
        provider_spec = cfg["providers"][active_provider]
        
        api_key = os.getenv(f"{active_provider.upper()}_API_KEY")
        if not api_key:
            raise ValueError(f"No API key for {active_provider}")
        
        client = llm_client.make_client(active_provider, api_key)
        
        messages = [{"role": "user", "content": prompt}]
        
        response = llm_client.chat(
            active_provider,
            client,
            provider_spec["model"],
            messages,
            provider_spec.get("temperature", 0.3)
        )
        
        return response
        
    except Exception as e:
        return f"# Code generation failed: {e}\nprint('Code generation error: {e}')"

# ================================
# CODE EXTRACTION
# ================================

def handle_file_loading_commands(user_input: str, display_module) -> Dict[str, Any]:
    """Handle file loading commands like 'read file path' or 'load file path'"""
    
    # Pattern matching for file loading
    load_patterns = [
        r"(?:read|load|open)\s+file\s+(.+)",
        r"load\s+(.+\.(?:py|json|md|txt|csv|xml|yaml))",
    ]
    
    # Cache management patterns
    cache_patterns = [
        r"(?:clear|reset|empty)\s+(?:file\s+)?cache",
        r"cache\s+(?:clear|reset|empty)",
        r"show\s+(?:file\s+)?cache",
        r"list\s+(?:loaded\s+)?files"
    ]
    
    # Check for file loading
    for pattern in load_patterns:
        match = re.match(pattern, user_input, re.IGNORECASE)
        if match:
            file_path = match.group(1).strip()
            print(f"{display_module.CYAN}[Natural Flow] Loading file: {file_path}{display_module.RESET}")
            
            result = execution_context.load_file_to_cache(file_path)
            
            if result['success']:
                response = f"✓ Loaded **{Path(file_path).name}** into working context.\n"
                response += f"File size: {result['size']:,} characters\n"
                response += f"Cache status: {result['cache_entries']}/{execution_context.max_cache_entries} files loaded\n"
                response += "What would you like to discuss about this file?"
                
                return {
                    'handled': True,
                    'response': response,
                    'operations': [f"load_file('{file_path}')"] 
                }
            else:
                return {
                    'handled': True,
                    'response': f"X Failed to load file: {result['error']}",
                    'operations': []
                }
    
    # Check for cache management
    for pattern in cache_patterns:
        if re.match(pattern, user_input, re.IGNORECASE):
            if 'clear' in user_input.lower() or 'reset' in user_input.lower() or 'empty' in user_input.lower():
                result = execution_context.clear_file_cache()
                return {
                    'handled': True,
                    'response': result,
                    'operations': ['clear_file_cache()']
                }
            elif 'show' in user_input.lower() or 'list' in user_input.lower():
                result = execution_context.get_loaded_files_summary()
                return {
                    'handled': True,
                    'response': result,
                    'operations': ['list_loaded_files()']
                }
    
    # If no file loading or cache commands were matched, return a default response
    return {
        'handled': False,
        'response': None,
        'operations': []
    }
    
def extract_code_blocks(text: str) -> List[str]:
    """Extract Python code blocks from LLM response"""
    code_blocks = []
    
    # Pattern for ```python code blocks
    python_pattern = r'```python\s*\n(.*?)\n```'
    python_matches = re.findall(python_pattern, text, re.DOTALL)
    code_blocks.extend(python_matches)
    
    # Pattern for ``` code blocks (assume Python)
    generic_pattern = r'```\s*\n(.*?)\n```'
    if not python_matches:  # Only if no python blocks found
        generic_matches = re.findall(generic_pattern, text, re.DOTALL)
        # Filter for Python-like content
        for match in generic_matches:
            if any(indicator in match for indicator in ['Path(', 'import ', 'def ', '= ', 'print(']):
                code_blocks.append(match)
    
    # Pattern for single-line operations
    single_line_pattern = r'((?:Path|os|subprocess|json)\([^)]*\)(?:\.[^(]*\([^)]*\))*)'
    single_matches = re.findall(single_line_pattern, text)
    code_blocks.extend(single_matches)
    
    return [code.strip() for code in code_blocks if code.strip()]

# ================================
# VERIFICATION SYSTEM
# ================================

def verify_operations(operations_performed: List[str]) -> Dict[str, Any]:
    """Verify that operations actually completed successfully"""
    verification_results = {
        'files_verified': [],
        'files_missing': [],
        'cortex_updated': False,
        'verification_successful': True
    }
    
    # Check for file operations in the executed code
    for operation in operations_performed:
        # Look for file creation/modification patterns
        file_patterns = [
            r"Path\(['\"]([^'\"]+)['\"]\)\.write_text",
            r"open\(['\"]([^'\"]+)['\"].*w",
        ]
        
        for pattern in file_patterns:
            matches = re.findall(pattern, operation)
            for filename in matches:
                file_path = Path(filename)
                if file_path.exists():
                    verification_results['files_verified'].append(filename)
                else:
                    verification_results['files_missing'].append(filename)
                    verification_results['verification_successful'] = False
    
    # Force cortex refresh if files were created/modified
    if verification_results['files_verified']:
        cortex_result = execution_context.force_cortex_refresh()
        verification_results['cortex_updated'] = cortex_result is True
        if cortex_result is not True:
            verification_results['cortex_error'] = cortex_result
    
    return verification_results

# ================================
# UTILITY FUNCTIONS FOR NEXUS
# ================================

def execute_code(code_string: str) -> Dict[str, Any]:
    """
    Execute Python code in the persistent execution context.
    
    Args:
        code_string: The Python code to execute as a string
        
    Returns:
        Dict containing execution results with keys:
        - success: Whether execution succeeded
        - output: Captured stdout output
        - result: Any return value stored in last_result
        - error: Error message if execution failed
    """
    return execution_context.execute(code_string)

def load_file(file_path: str) -> Dict[str, Any]:
    """
    Load a file into the execution context cache.
    
    Args:
        file_path: Path to the file to load
        
    Returns:
        Dict containing load results with keys:
        - success: Whether file loading succeeded
        - content: File content if successful
        - error: Error message if loading failed
    """
    return execution_context.load_file_to_cache(file_path)

def read_file_content(file_path: str) -> Dict[str, Any]:
    """
    Read a file's content with enhanced path resolution.
    
    Search strategy:
    1. If absolute path provided → use directly
    2. If relative path → search AIPass project tree recursively
    3. Fallback to original local directory search
    
    Args:
        file_path: Path to the file to read
        
    Returns:
        Dict containing:
        - success: Whether file reading succeeded
        - content: File content if successful
        - line_count: Number of lines in the file
        - error: Error message if reading failed
    """
    try:
        # Debug output
        print(f"Attempting to read file: {file_path}")
        
        # Get directory references
        current_dir = Path.cwd()
        nexus_dir = Path(__file__).parent
        working_dir = execution_context.globals.get('working_dir', current_dir)
        
        # Find AIPass_Core root directory
        aipass_root = None
        search_dir = nexus_dir
        while search_dir != search_dir.parent:
            if search_dir.name == "AIPass_Core":
                aipass_root = search_dir
                break
            search_dir = search_dir.parent
        
        print(f"Current directory: {current_dir}")
        print(f"Nexus directory: {nexus_dir}")
        print(f"Working directory: {working_dir}")
        if aipass_root:
            print(f"AIPass_Core root: {aipass_root}")
        
        # List of possible paths to try
        possible_paths = []
        
        # Resolve path
        path_obj = Path(file_path)
        
        # Strategy 1: If it's an absolute path, use it directly
        if path_obj.is_absolute():
            possible_paths.append(path_obj)
            print(f"Using absolute path: {path_obj}")
        else:
            # Strategy 2: Search AIPass project tree recursively
            if aipass_root:
                print(f"Searching AIPass_Core tree for: {file_path}")
                
                # Use glob to search recursively for the filename
                filename = path_obj.name
                search_patterns = [
                    f"**/{filename}",  # Exact filename anywhere
                    f"**/{file_path}",  # Relative path anywhere
                ]
                
                for pattern in search_patterns:
                    try:
                        matches = list(aipass_root.glob(pattern))
                        for match in matches:
                            if match.is_file():
                                possible_paths.append(match)
                                print(f"Found via glob '{pattern}': {match}")
                    except Exception as e:
                        print(f"Glob search failed for '{pattern}': {e}")
            
            # Strategy 3: Original local directory search (fallback)
            # Try as-is (relative to current directory)
            possible_paths.append(current_dir / path_obj)
            
            # Try relative to Nexus directory
            possible_paths.append(nexus_dir / path_obj)
            
            # Try relative to working directory
            possible_paths.append(working_dir / path_obj)
            
            # Try with a.i_core prefix if not already there
            if not str(path_obj).startswith('a.i_core'):
                possible_paths.append(current_dir / 'a.i_core' / path_obj)
            
            # Try with a.i_profiles/Nexus prefix if not already there
            if 'a.i_profiles' not in str(path_obj):
                possible_paths.append(current_dir / 'a.i_core' / 'a.i_profiles' / 'Nexus' / path_obj)
        
        # Remove duplicates while preserving order
        unique_paths = []
        seen = set()
        for p in possible_paths:
            resolved = p.resolve()
            if resolved not in seen:
                seen.add(resolved)
                unique_paths.append(resolved)
        
        # Debug output
        print(f"Trying paths: {[str(p) for p in unique_paths[:10]]}")  # Limit output
        if len(unique_paths) > 10:
            print(f"... and {len(unique_paths) - 10} more paths")
        
        # Try each path
        found_path = None
        for p in unique_paths:
            try:
                if p.exists() and p.is_file():
                    found_path = p
                    print(f"Found file at: {found_path}")
                    break
            except Exception as e:
                # Some paths might be invalid (permissions, etc)
                print(f"Skipping invalid path {p}: {e}")
                continue
        
        if found_path is None:
            # Create a more helpful error message
            tried_summary = []
            if aipass_root:
                tried_summary.append(f"Recursive search in {aipass_root}")
            tried_summary.extend([str(p) for p in unique_paths[:5]])
            if len(unique_paths) > 5:
                tried_summary.append(f"... and {len(unique_paths) - 5} more locations")
            
            return {
                'success': False,
                'error': f"File not found: {file_path}\nTried: {', '.join(tried_summary)}"
            }
        
        # Read file content with error handling for encoding issues
        try:
            content = found_path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            # Try with a more forgiving encoding
            try:
                content = found_path.read_text(encoding='utf-8', errors='replace')
            except Exception:
                # Last resort - read as binary and decode what we can
                binary_content = found_path.read_bytes()
                content = binary_content.decode('utf-8', errors='replace')
        
        # Count lines
        line_count = len(content.splitlines())
        
        print(f"Successfully read file with {line_count} lines")
        
        return {
            'success': True,
            'content': content,
            'line_count': line_count,
            'file_path': str(found_path),
            'size': len(content)
        }
        
    except Exception as e:
        print(f"Error reading file: {str(e)}")
        return {
            'success': False,
            'error': f"Error reading file: {str(e)}"
        }

# ================================
# UTILITY FUNCTIONS
# ================================

def process_natural_input(user_input: str) -> str:
    """Process natural language input with memory search capability."""
    
    # Check for memory search intent
    is_memory_search, search_query = detect_memory_search_intent(user_input)
    
    if is_memory_search and search_query:
        print(f"[Natural Flow] Memory search detected: '{search_query}'")
        try:
            # Search vector memories
            memory_results = search_my_memories(search_query)
            return f"[Nexus] {memory_results}"
        except Exception as e:
            return f"[Nexus] I tried to search my memories but encountered an error: {e}"
    
    # Default response if no specific intent was detected
    return ""

def get_execution_stats() -> Dict[str, Any]:
    """Get comprehensive statistics about execution context"""
    return {
        'session_duration': str(datetime.now() - execution_context.session_start),
        'total_operations': len(execution_context.operation_history),
        'successful_operations': len([op for op in execution_context.operation_history if op.get('success')]),
        'failed_operations': len([op for op in execution_context.operation_history if not op.get('success')]),
        'files_created': len(execution_context.globals.get('created_files', [])),
        'files_modified': len(execution_context.globals.get('modified_files', [])),
        'scripts_executed': len(execution_context.globals.get('executed_scripts', [])),
        'context_summary': execution_context.get_context_summary(),
        'recent_operations': execution_context.operation_history[-5:],
        'available_variables': list(execution_context.globals.keys())
    }

def reset_execution_context() -> None:
    """Reset the execution context (useful for debugging)"""
    global execution_context
    execution_context = ExecutionContext()
    print("Execution context reset")

def debug_last_operation() -> Dict[str, Any]:
    """Get detailed info about the last operation for debugging"""
    if not execution_context.operation_history:
        return {'error': 'No operations performed yet'}
    
    last_op = execution_context.operation_history[-1]
    return {
        'last_operation': last_op,
        'context_globals': {k: str(v)[:100] for k, v in execution_context.globals.items() if not k.startswith('__')},
        'execution_context_summary': execution_context.get_context_summary()
    }

# ================================
# EXPORTS
# ================================

__all__ = [
    'execute_code',
    'load_file',
    'read_file_content',
    'ExecutionContext',
    'get_execution_stats', 
    'reset_execution_context',
    'debug_last_operation',
    'execution_context'  # For direct access if needed
]