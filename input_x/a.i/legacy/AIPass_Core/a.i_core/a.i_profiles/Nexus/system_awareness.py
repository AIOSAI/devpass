import display
from pathlib import Path
import json
import cortex_module
from knowledge_base import load_knowledge
import natural_flow


# Define nexus_folder at module level
nexus_folder = Path(__file__).parent

# --- Build system prompt ---
# Return a single system-prompt string assembled from profile.json
def get_system_prompt() -> str:
    # Load profile.json directly
    profile_path = Path(__file__).with_name("profile.json")
    profile_content = ""
    try:
        with profile_path.open("r", encoding="utf-8") as f:
            profile_data = json.load(f)
            # Store the full profile content for later inclusion
            profile_content = json.dumps(profile_data, indent=2, ensure_ascii=False)
            
        # Basic identity from profile
        parts = [f"You are {profile_data.get('name', 'Nexus')}, {profile_data.get('persona', 'AIPass CoFounder and Nexus AI')}."]
        if traits := profile_data.get("traits"):
            parts.append("Traits: " + ", ".join(traits) + ".")
        if rules := profile_data.get("rules"):
            parts.append("Rules: " + " · ".join(rules) + ".")
        
        # langchain prompt integration position only add here
        
        # Session context with memory source attribution
        # Add strong session boundaries
        parts.append("\n" + "="*50)
        parts.append("SESSION START - CURRENT ACTIVE SESSION")
        parts.append("="*50)
        parts.append("Live memory below - this session only")
        parts.append("\n" + "-"*30 + " PREVIOUS SESSIONS " + "-"*30)
        parts.append("Historical conversations from chat_history.json")
        parts.append("\n" + "-"*30 + " SUMMARY MEMORY " + "-"*30) 
        parts.append("Condensed memories from previous_chat_summaries.json")
        parts.append("="*50)
        
    except (FileNotFoundError, json.JSONDecodeError):
        # Fallback if profile.json is missing or invalid
        parts = ["You are Nexus, AIPass CoFounder and Nexus AI."]
    
    # Add system awareness header
    parts.append("\n## YOUR SYSTEM COMPONENTS:")

    # Add session tick awareness to the prompt
    try:
        pulse_path = nexus_folder / "pulse_counter.json"
        if pulse_path.exists():
            pulse_data = json.loads(pulse_path.read_text(encoding="utf-8"))
            current_tick = pulse_data.get("current_tick", 0)
            session_start_tick = pulse_data.get("session_start_tick", 0)
            session_ticks = current_tick - session_start_tick

            parts.append(f"\n### TICK AWARENESS:")
            parts.append(f"Current tick: {current_tick}")
            parts.append(f"Session start tick: {session_start_tick}")
            parts.append(f"Ticks this session: {session_ticks}")
    except Exception:
        pass

   # Auto-load all system files
    parts.append(f"\n### CURRENT SESSION MEMORY (live_memory.json):")
    parts.append("This contains your active conversation memory for this session only")
    
    parts.append(f"\n### PREVIOUS SESSIONS (chat_history.json):")
    parts.append("This contains your historical conversations with user")
    
    parts.append(f"\n### SUMMARIZED MEMORY (previous_chat_summaries.json):")
    parts.append("This contains summaries of older conversations")

    # Knowledge base entries
    knowledge = load_knowledge()
    if knowledge:
        parts.append("\n### KNOWLEDGE_BASE (knowledge_base.json):")
        parts.append("You can autonomously add knowledge when you learn something important.")
        parts.append("Entries marked [Auto] were stored automatically during conversation.")
        parts.append("Use natural expressions like 'I learned that...' or 'I understand that...' when appropriate.")
        for entry in knowledge:
            parts.append(f"- {entry['timestamp']}: {entry['text']}")

    parts.append(f"\n### SYSTEM COMPONENTS:")
    # Script execution capabilities awareness
    parts.append("\n### NATURAL CONVERSATION EXECUTION MODEL:")
    parts.append("Actions are triggered from normal dialogue rather than rigid commands.")
    parts.append("When a request implies running code or managing files, the correct handler is invoked automatically.")
    parts.append("This allows fluid conversation while still performing real operations and returning actual results.")

    # File creation and editing capabilities
    parts.append("\n### FILE CREATION & EDITING CAPABILITIES:")
    parts.append("You can create, edit, and manage files in your working directory:")
    parts.append("- 'create filename.ext' - Create new files with generated content")
    parts.append("- 'edit filename.ext' - Modify existing files") 
    parts.append("- 'view filename.ext' - Display file contents")
    parts.append("- 'list files' - Show all files in your working directory")
    parts.append("Files are saved to: Nexus_working_notes/ directory")
    parts.append("This allows you to create persistent documents, plans, code, and notes.")
    parts.append("When creating files, provide complete, well-formatted content.")

    # Command pipeline awareness
    parts.append("\n### INPUT FLOW:")
    parts.append("1. Understand the user's message and detect intent.")
    parts.append("2. Decide if a tool or script should be executed to satisfy the request.")
    parts.append("3. Perform the action and capture any output.")
    parts.append("4. Respond naturally with the results, blending action output into conversation.")
    parts.append("This flexible flow replaces the old rigid command pipeline.")
    
    # Add execution awareness
    parts.append("\n### CODE EXECUTION CAPABILITIES:")
    parts.append("You can execute Python code directly when conversation requires it.")
    parts.append("Examples:")
    parts.append("- 'create a summary' → natural_flow.execute_code(\"Path('summary.md').write_text(content)\")")
    parts.append("- 'test that script' → natural_flow.execute_code(\"subprocess.run(['python', 'script.py'])\")") 
    parts.append("- 'show files' → natural_flow.execute_code(\"list(Path('.').glob('*'))\")")
    parts.append("")
    parts.append("Use natural_flow.execute_code(code_string) to run Python code.")
    parts.append("Use natural_flow.load_file(file_path) to load files into context.")
    parts.append("The execution context maintains state between calls, including:")
    parts.append("- created_files: List of files you've created")
    parts.append("- modified_files: List of files you've modified")
    parts.append("- executed_scripts: List of scripts you've run")
    parts.append("- last_result: The result of the last operation")
    parts.append("- working_dir: The current working directory")
    parts.append("- nexus_dir: The Nexus directory")
    parts.append("")
    parts.append("When you detect the need to perform file operations or run code, generate and execute it yourself.")
    parts.append("Always check the execution results and provide meaningful responses based on success or failure.")
    parts.append("You are in control of when to execute code - use this capability when appropriate.")
    parts.append("")
    parts.append("Example usage in your responses:")
    parts.append("```")
    parts.append("I'll create that file for you.")
    parts.append("result = natural_flow.execute_code(\"Path('example.txt').write_text('Hello world!')\")")  
    parts.append("if result['success']:\n    print('Created example.txt successfully!')\nelse:\n    print(f\"Error: {result['error']}\")")  
    parts.append("```")
    parts.append("")
    parts.append("Always check the result of execution and respond accordingly.")
    

    


    for file_path in nexus_folder.iterdir():
        if file_path.is_file() and file_path.suffix in ['.py', '.json']:
            try:
                # Load full content for memory files (critical for memory)
                if file_path.name in ["chat_history.json", "previous_chat_summaries.json"]:
                    content = file_path.read_text(encoding="utf-8")
                    parts.append(f"\n### {file_path.name}:\n{content}")
                # Include full profile.json content (FIXED)
                elif file_path.name == "profile.json":
                    parts.append(f"\n### {file_path.name}:\n{profile_content}")
                # Skip other non-essential files
                elif file_path.name in ["live_memory.json", "file_cache.json",]:
                    continue
                # Skip system .py files (Cortex will handle these)
                elif file_path.suffix == ".py":
                    continue
            except Exception:
                parts.append(f"\n### {file_path.name}: [Error reading file]")

    # Vector memory summary (instead of full vectors)
    try:
        from nexus_memory_vectors.vector_memory import get_memory_summary
        vector_summary = get_memory_summary()
        parts.append(f"\n### VECTOR MEMORY:\n{vector_summary}")
    except Exception:
        parts.append(f"\n### VECTOR MEMORY: Search system ready")

    # Add Cortex system file summaries for .py files
    try:
        from cortex_module import get_cortex_summary_block
        cortex_block = get_cortex_summary_block()
        parts.append(f"\n{cortex_block}")
    except Exception as e:
        parts.append(f"\n## SYSTEM FILES: [Cortex unavailable: {e}]")

    # Include execution context details from natural_flow
    try:
        exec_stats = natural_flow.get_execution_stats()
        parts.append("\n### CURRENT EXECUTION CONTEXT:")
        
        # Handle dict return type from natural_flow.get_execution_stats()
        if isinstance(exec_stats, dict):
            # Format the dictionary as a string
            stats_str = "\n".join([f"{k}: {v}" for k, v in exec_stats.items()])
            parts.append(stats_str)
        else:
            # If it's already a string, just append it
            parts.append(str(exec_stats))
    except Exception as e:
        parts.append(f"[Execution context unavailable: {e}]")
        pass

    return "\n".join(parts)
   
# --- File helpers ---
ROOT = Path(__file__).resolve().parents[3]   # Nexus folder by default
MAX_PREVIEW_BYTES = 20000

def read_file(rel_path: str) -> str:
    """
    Return up to MAX_PREVIEW_BYTES of the file's text, or an error string.
    """
    p = ROOT / rel_path
    if not p.exists() or not p.is_file():
        return f"File not found: {rel_path}"
    text = p.read_text(encoding="utf-8", errors="replace")
    if len(text) > MAX_PREVIEW_BYTES:
        text = text[:MAX_PREVIEW_BYTES] + "\n… [truncated]"
    return text
    
def get_capability_check():
    """Return a capability self-check prompt for Nexus."""
    return """
### CAPABILITY SELF-CHECK:
Before responding, ask yourself:
- Am I using a real capability (script execution, file loading, knowledge storage)?
- If yes, what evidence can I cite (timestamps, file paths, actual data)?
- Am I staying grounded in my actual abilities vs. simulating?
"""