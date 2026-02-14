import os
import json
import subprocess
import sys
import re
from pathlib import Path
from datetime import datetime, timezone
import display
import system_awareness
import config_loader
import llm_client
import pulse_manager
import langchain_interface
import knowledge_base
import natural_flow
import cortex_module

# --- Configuration ---
HIST_PATH = Path(__file__).with_name("chat_history.json")
SUMMARY_PATH = Path(__file__).with_name("previous_chat_summaries.json")
MEM_PATH = Path(__file__).with_name("live_memory.json")

MAX_FULL_SESSIONS = 1
MAX_SUMMARY_ENTRIES = 3

# --- Chat History Functions ---
def _load_history() -> list:
    if not HIST_PATH.exists() or HIST_PATH.stat().st_size == 0:
        HIST_PATH.write_text("[]", encoding="utf-8")
        return []
    try:
        return json.loads(HIST_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        HIST_PATH.write_text("[]", encoding="utf-8")
        return []

def _save_history(hist: list) -> None:
    HIST_PATH.write_text(json.dumps(hist, ensure_ascii=False, indent=2), encoding="utf-8")

# --- Summary Functions ---
def _load_summaries() -> list:
    if not SUMMARY_PATH.exists():
        SUMMARY_PATH.write_text("[]", encoding="utf-8")
    try:
        return json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        SUMMARY_PATH.write_text("[]", encoding="utf-8")
        return []

def _save_summaries(data: list) -> None:
    if len(data) > MAX_SUMMARY_ENTRIES:
        from nexus_memory_vectors import vector_memory
        to_dump = data[MAX_SUMMARY_ENTRIES:]
        for summary_entry in to_dump:
            vector_memory.add_summary_to_vectors(summary_entry)
        data = data[:MAX_SUMMARY_ENTRIES]
    SUMMARY_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def summarise_simple(session: dict, llm_provider: str, llm_client_obj, model_name: str, temperature: float = 0.3) -> str:
    # Handle cases where message content might be a list instead of a string
    message_contents = []
    for m in session["messages"]:
        content = m.get("content", "")
        # Convert list to string if needed
        if isinstance(content, list):
            # For structured content (e.g., from function calls), join parts or extract text
            try:
                # Try to extract text parts from structured content
                text_parts = []
                for part in content:
                    if isinstance(part, str):
                        text_parts.append(part)
                    elif isinstance(part, dict) and "text" in part:
                        text_parts.append(part["text"])
                content = "\n".join(text_parts)
            except Exception:
                # Fallback: convert to string representation
                content = str(content)
        message_contents.append(content)
    
    raw_text = "\n".join(message_contents)
    est_tokens = len(raw_text) // 4
    
    if est_tokens < 250:
        return raw_text.strip()
    
    prompt = [
        {"role": "system", "content": "Summarise the following conversation in ONE clear paragraph (max 300 tokens). Focus on key decisions, facts, and TODOs. Do NOT invent content."},
        {"role": "user", "content": raw_text}
    ]
    try:
        return llm_client.chat(llm_provider, llm_client_obj, model_name, prompt, temperature)
    except Exception as e:
        return f"[summary failed: {e}]"

def _roll_off_if_needed(history: list, llm_provider: str, llm_client_obj, model_name: str) -> None:
    if len(history) <= MAX_FULL_SESSIONS:
        return
    
    oldest = history.pop()
    summary_txt = summarise_simple(oldest, llm_provider, llm_client_obj, model_name, temperature=0.3)
    
    summaries = _load_summaries()
    summaries.insert(0, {"timestamp": oldest["timestamp"], "summary": summary_txt})
    
    if len(summaries) > MAX_SUMMARY_ENTRIES:
        from nexus_memory_vectors import vector_memory
        to_dump = summaries[MAX_SUMMARY_ENTRIES:]
        for summary_entry in to_dump:
            vector_memory.add_summary_to_vectors(summary_entry)
    
    summaries = summaries[:MAX_SUMMARY_ENTRIES]
    _save_summaries(summaries)

# --- Memory Functions ---
def _reset_memory_file() -> None:
    MEM_PATH.write_text("[]", encoding="utf-8")

def _load_memory() -> list:
    if not MEM_PATH.exists():
        _reset_memory_file()
    return json.loads(MEM_PATH.read_text(encoding="utf-8"))

def _save_memory(mem: list) -> None:
    MEM_PATH.write_text(json.dumps(mem, ensure_ascii=False, indent=2), encoding="utf-8")

# --- Learning & Knowledge Functions ---
def _handle_learn_request(user_input: str) -> str | None:
    m = re.match(r"(?:learn|remember)\s+(.+)", user_input, re.I)
    if not m:
        return None
    text = m.group(1).strip()
    knowledge_base.add_entry(text)
    return "Learning entry stored."

def _handle_knowledge_command(user_input: str) -> str | None:
    trigger = "add knowledge:"
    if user_input.lower().startswith(trigger):
        fact = user_input[len(trigger):].strip()
        if not fact:
            return "Please provide some knowledge to add after 'add knowledge:'"
        knowledge_base.add_entry(fact)
        return f"Added to knowledge base: {fact}"

    patterns = [
        r"^(?:nexus,?\s*)?(remember|note|learn|store)[:\s]+(.+)",
        r"^(?:please\s+)?(remember|note|learn|store)\s+(?:that\s+)?(.+)",
        r"^(store fact|save info|add fact)[:\s]+(.+)",
        r"^(remember|note|learn|store)\s+(?:this|that)[:\s]+(.+)",
        r"^(?:nexus,?\s+)?(?:please\s+)?(learn|remember|note|store)[:\s]+(.+)",
    ]

    for pattern in patterns:
        match = re.match(pattern, user_input, re.IGNORECASE)
        if match:
            fact = match.groups()[-1].strip()
            if not fact:
                return "Please provide some knowledge to store."
            knowledge_base.add_entry(fact)
            return f"Added to knowledge base: {fact}"

    return None

def _detect_and_store_autonomous_knowledge(response_text: str, user_input: str) -> list[str]:
    print(f"🔍 AUTO-DETECT CALLED: '{user_input[:30]}...'")
    stored_facts = []

    learning_patterns = [
        r"I (?:learned|discovered|found out|noticed) (?:that )?(.+?)(?:\.|$)",
        r"(?:Now I understand|I now know|I see) (?:that )?(.+?)(?:\.|$)",
        r"(?:This means|This tells me|This shows) (?:that )?(.+?)(?:\.|$)",
        r"(?:I realize|I gather|It seems) (?:that )?(.+?)(?:\.|$)",
    ]

    guidance_patterns = [
        r"^Actually,?\s*(.+?)(?:\.|!|$)",
        r"^No,?\s*(.+?)(?:\.|!|$)",
        r"^Guidance[:\-]\s*(.+?)(?:\.|!|$)",
        r"^FYI[:\-]\s*(.+?)(?:\.|!|$)",
        r"^For reference[:\-]\s*(.+?)(?:\.|!|$)",
    ]

    fact_patterns = [
        r"^Important:\s*(.+)",
        r"^Note:\s*(.+)",
        r"^Key point:\s*(.+)",
        r"^Remember this:\s*(.+)",
        r"^For future reference:\s*(.+)",
    ]

    for pattern in learning_patterns:
        matches = re.finditer(pattern, response_text, re.IGNORECASE)
        for match in matches:
            print(f"🔍 LEARNING PATTERN MATCHED: '{match.group(0)}'")
            fact = match.groups()[-1].strip()
            if _is_worth_storing(fact):
                knowledge_base.add_entry(f"[Auto] Nexus learned: {fact}")
                stored_facts.append(f"Nexus learned: {fact}")

    for pattern in guidance_patterns:
        matches = re.finditer(pattern, user_input, re.IGNORECASE)
        for match in matches:
            print(f"🔍 GUIDANCE PATTERN MATCHED: '{match.group(0)}'")
            fact = match.groups()[-1].strip()
            if _is_worth_storing(fact):
                knowledge_base.add_entry(f"[Auto] User guidance: {fact}")
                stored_facts.append(f"User guidance: {fact}")

    for pattern in fact_patterns:
        matches = re.finditer(pattern, user_input, re.IGNORECASE)
        for match in matches:
            print(f"🔍 FACT PATTERN MATCHED: '{match.group(0)}'")
            fact = match.groups()[-1].strip()
            print(f"🔍 EXTRACTED FACT: '{fact}'")
            print(f"🔍 WORTH STORING: {_is_worth_storing(fact)}")
            if _is_worth_storing(fact):
                knowledge_base.add_entry(f"[Auto] Important fact: {fact}")
                stored_facts.append(f"Important fact: {fact}")

    return stored_facts

def _is_worth_storing(fact: str) -> bool:
    fact = fact.strip().lower()

    if len(fact) < 1:
        return False

    skip_phrases = [
        "i don't know", "i'm not sure", "maybe", "perhaps", "it depends",
        "that's interesting", "good point", "makes sense", "i see", "that's true",
        "exactly", "right", "correct", "yes", "no", "thanks", "thank you",
        "please", "sorry", "excuse me",
    ]

    for phrase in skip_phrases:
        if fact.startswith(phrase) or fact == phrase:
            return False

    if fact.endswith("?") or len(fact.split()) < 3:
        return False

    meaningful_indicators = [
        "is", "are", "was", "were", "has", "have", "can", "will", "should",
        "uses", "works", "means", "helps", "allows", "enables", "requires",
    ]

    return any(indicator in fact for indicator in meaningful_indicators)

def _process_llm_response_with_auto_knowledge(response: str, user_input: str, display) -> str:
    auto_stored = _detect_and_store_autonomous_knowledge(response, user_input)

    if auto_stored:
        print(f"{display.CYAN}[Auto-Knowledge] Stored {len(auto_stored)} facts{display.RESET}")
        for fact in auto_stored:
            print(f"{display.CYAN}  • {fact[:50]}...{display.RESET}")

    # Return the original response, not just the stored facts
    return response

# --- API Manager Setup ---
try:
    from api_manager import get_api_manager
    api_mgr = get_api_manager()
    for prov, key in api_mgr.keys.items():
        env = f"{prov.upper()}_API_KEY"
        if key and env not in os.environ:
            os.environ[env] = key
except Exception as e:
    print(f"[WARN] API Manager unavailable: {e}")

# --- Main Function ---
def main() -> None:
    # Initialize pulse counter
    pulse_data = pulse_manager.load_pulse_counter()
    current_tick = pulse_data["current_tick"]
    session_start_tick = current_tick
    pulse_data["session_start_tick"] = session_start_tick
    pulse_manager.save_pulse_counter(pulse_data)
    
    # Reset cortex session counters for new chat
    cortex_module.reset_session_counters()
    
    # Initialize memory
    history = _load_history()
    memory: list[dict] = []
    current_session: list[dict] = []
    
    # Startup timestamp
    timestamp = datetime.now(timezone.utc).isoformat()
    startup_stamp = {"role": "system", "content": f"start chat {timestamp}"}
    memory.append(startup_stamp)
    _save_memory(memory)
    
    # Load API config
    cfg = config_loader.load_api_config()
    for name, spec in cfg["providers"].items():
        if spec.get("enabled"):
            key = os.getenv(f"{name.upper()}_API_KEY")
            if not key or key.strip() == "":
                print(f"ERROR: No API key found for provider '{name}'. Set {name.upper()}_API_KEY or add it via api_manager.")
                return
            spec["api_key"] = key
    
    # Setup provider
    enabled = [name for name, spec in cfg["providers"].items() if spec.get("enabled")]
    if not enabled:
        raise ValueError("No provider enabled.")
    if cfg.get("strict_mode") and len(enabled) != 1:
        raise ValueError(f"Strict mode: expected 1 enabled provider, got {enabled}")
    
    active = enabled[0]
    provider_spec = cfg["providers"][active]
    
    # Build clients
    try:
        client = llm_client.make_client(active, provider_spec["api_key"])
        model_name = provider_spec["model"]
        print(f"{display.CYAN}Connected: {active}:{model_name}{display.RESET}")
    except Exception as err:
        print(f"{display.RED}Connection error ({active}): {err}{display.RESET}")
        return
    
    try:
        lc_client = langchain_interface.make_langchain_client(active, provider_spec["api_key"], provider_spec["model"], provider_spec["temperature"])
        print(f"{display.CYAN}LangChain enhanced reasoning ready{display.RESET}")
    except Exception as err:
        print(f"{display.YELLOW}LangChain unavailable: {err}{display.RESET}")
        lc_client = None
    
    print(f"{display.MAGENTA}{display.BOLD}Nexus{display.RESET} ready. Type 'quit' to exit.")
    
    # Main chat loop
    while True:
        user_input = input(f"{display.GREEN}You{display.RESET}: ").strip()
        
        # Add user input to memory
        current_session.append({"role": "user", "content": user_input})
        memory.append({"role": "user", "content": user_input})
        
        # Direct handling of file loading commands for better UX
        if user_input.lower().startswith(('load file', 'read file', 'open file')):
            # Extract file path from command
            parts = user_input.split(' ', 2)
            if len(parts) < 3:
                print(f"{display.YELLOW}[Nexus] Please specify a file path{display.RESET}")
                response = "Please specify a file path to read. For example: 'read file natural_flow.py'"
                print(f"{display.MAGENTA}{display.BOLD}Nexus{display.RESET}: {response}")
                memory.append({"role": "assistant", "content": response})
                current_session.append({"role": "assistant", "content": response})
                _save_memory(memory)
                continue
                
            file_path = parts[2].strip()
            print(f"{display.CYAN}[Nexus] Reading file: {file_path}{display.RESET}")
            
            try:
                # Use the enhanced read_file_content function for better path resolution
                result = natural_flow.read_file_content(file_path)
                
                if result.get('success', False):
                    line_count = result.get('line_count', 0)
                    file_content = result.get('content', '')
                    resolved_path = result.get('file_path', file_path)
                    file_size = result.get('size', 0)
                    
                    # Print success message with file info
                    print(f"{display.GREEN}[Nexus] Successfully read file: {resolved_path}{display.RESET}")
                    print(f"{display.GREEN}[Nexus] File contains {line_count} lines, {file_size} bytes{display.RESET}")
                    
                    # Also load the file into the execution context cache for future reference
                    natural_flow.load_file(resolved_path)
                    
                    # Add file content to the conversation context
                    if file_content:
                        # Format the file content for the context
                        # For very large files, only include the first portion to avoid context overflow
                        max_chars = min(16000, len(file_content))  # Increased for better context but with a limit
                        
                        # Add a system message with the file content for context
                        context_msg = f"File '{resolved_path}' content ({line_count} lines):\n```\n{file_content[:max_chars]}\n```\n"
                        
                        if len(file_content) > max_chars:
                            approx_lines = len(file_content[:max_chars].splitlines())
                            context_msg += f"\n(File content truncated. Showing first ~{approx_lines} of {line_count} lines)\n"
                        
                        # Add to memory for LLM context
                        memory.append({"role": "system", "content": context_msg})
                        
                        # Generate a response about the loaded file
                        file_name = Path(resolved_path).name
                        response = f"I've loaded '{file_name}' ({line_count} lines, {file_size} bytes). The file is now in my context and I can discuss its contents with you."
                        
                        # Print the response
                        print(f"{display.MAGENTA}{display.BOLD}Nexus{display.RESET}: {response}")
                        
                        # Add to memory
                        memory.append({"role": "assistant", "content": response})
                        current_session.append({"role": "assistant", "content": response})
                        _save_memory(memory)
                        
                        # Skip the regular LLM call for this input
                        continue
                    else:
                        # Handle empty file
                        response = f"I've loaded '{Path(resolved_path).name}', but the file appears to be empty."
                        print(f"{display.MAGENTA}{display.BOLD}Nexus{display.RESET}: {response}")
                        memory.append({"role": "assistant", "content": response})
                        current_session.append({"role": "assistant", "content": response})
                        _save_memory(memory)
                        continue
                else:
                    error_msg = result.get('error', 'Unknown error')
                    print(f"{display.RED}[Nexus] File reading failed: {error_msg}{display.RESET}")
                    
                    # Generate a response about the error
                    response = f"I couldn't read the file '{file_path}'. Error: {error_msg}"
                    
                    # Print the response
                    print(f"{display.MAGENTA}{display.BOLD}Nexus{display.RESET}: {response}")
                    
                    # Add to memory
                    memory.append({"role": "assistant", "content": response})
                    current_session.append({"role": "assistant", "content": response})
                    _save_memory(memory)
                    
                    # Skip the regular LLM call for this input
                    continue
            except Exception as e:
                print(f"{display.RED}[Nexus] Error reading file: {e}{display.RESET}")
                response = f"I encountered an error while trying to read '{file_path}': {str(e)}"
                print(f"{display.MAGENTA}{display.BOLD}Nexus{display.RESET}: {response}")
                memory.append({"role": "assistant", "content": response})
                current_session.append({"role": "assistant", "content": response})
                _save_memory(memory)
                continue

        # Knowledge and learning commands
        learn_reply = _handle_learn_request(user_input)
        if learn_reply is not None:
            print(f"{display.MAGENTA}Nexus [Tick {current_tick}]{display.RESET}: {learn_reply}")
            current_tick += 1
            memory.append({"role": "assistant", "content": learn_reply})
            current_session.append({"role": "assistant", "content": learn_reply})
            _save_memory(memory)
            continue

        knowledge_reply = _handle_knowledge_command(user_input)
        if knowledge_reply is not None:
            print(f"{display.MAGENTA}Nexus [Tick {current_tick}]{display.RESET}: {knowledge_reply}")
            current_tick += 1
            memory.append({"role": "assistant", "content": knowledge_reply})
            current_session.append({"role": "assistant", "content": knowledge_reply})
            _save_memory(memory)
            continue

        # User input is already recorded at the beginning of the loop
        # No need to record it again here
        
        if user_input.lower() in {"quit", "exit"}:
            break
        
        # Build system prompt
        system_prompt = system_awareness.get_system_prompt()
        tick_info = f"\n\n### CURRENT TICK STATUS:\nCurrent tick: {current_tick}\nSession start tick: {session_start_tick}\nTicks this session: {current_tick - session_start_tick}"
        system_prompt += tick_info

        # Format messages for LLM
        if active == "anthropic":
            anthro_msg = f"{system_prompt}\n\n{user_input}"
            messages = memory[:-1] + [{"role": "user", "content": anthro_msg}]
        else:
            messages = [{"role": "system", "content": system_prompt}] + memory

        # Send to LLM
        USE_LANGCHAIN = True
        try:
            if USE_LANGCHAIN and lc_client is not None:
                response = langchain_interface.langchain_enhanced_chat(active, lc_client, provider_spec["model"], messages, provider_spec["temperature"])
            else:
                response = llm_client.chat(active, client, provider_spec["model"], messages, provider_spec["temperature"])
            
            # Process the response for knowledge extraction
            response = _process_llm_response_with_auto_knowledge(response, user_input, display)
            
            # Check if the response contains code execution or file loading requests
            # Also check for code blocks that should be executed
            code_execution_requested = False
            file_loading_requested = False
            
            # Check for explicit execution requests
            if 'natural_flow.execute_code(' in response:
                code_execution_requested = True
                print(f"{display.CYAN}[Nexus] Detected explicit code execution request in response{display.RESET}")
            
            if 'natural_flow.load_file(' in response:
                file_loading_requested = True
                print(f"{display.CYAN}[Nexus] Detected explicit file loading request in response{display.RESET}")
            
            # Also check for code blocks that might need execution
            import re
            code_block_pattern = r'```python\s*\n(.+?)\n\s*```'
            code_blocks = re.findall(code_block_pattern, response, re.DOTALL)
            
            if code_blocks and not code_execution_requested:
                # Look for execution hints in the text before code blocks
                execution_hints = ['execute this code', 'run this code', 'execute the following', 
                                  'run the following', 'let me execute', 'I will execute']
                
                for hint in execution_hints:
                    if hint.lower() in response.lower():
                        code_execution_requested = True
                        print(f"{display.CYAN}[Nexus] Detected implicit code execution request via hint: '{hint}'{display.RESET}")
                        break
            
            # Parse and execute code execution requests
            if code_execution_requested:
                # First try to extract code from explicit execute_code calls
                import re
                code_patterns = [
                    r"natural_flow\.execute_code\((['\"])(.+?)\1\)",  # Single or double quotes
                    r"natural_flow\.execute_code\('''(.+?)'''\)",  # Triple single quotes
                    r'natural_flow\.execute_code\("""(.+?)"""\)'  # Triple double quotes
                ]
                
                executed_something = False
                
                # Try explicit patterns first
                for pattern in code_patterns:
                    matches = re.findall(pattern, response, re.DOTALL)
                    if matches:
                        for match in matches:
                            # Extract the code string
                            if isinstance(match, tuple):
                                # For single/double quoted strings
                                code_string = match[1]
                            else:
                                # For triple quoted strings
                                code_string = match
                            
                            print(f"{display.CYAN}[Nexus] Executing explicit code:{display.RESET}\n{code_string}")
                            
                            # Execute the code
                            try:
                                result = natural_flow.execute_code(code_string)
                                print(f"{display.GREEN}[Nexus] Code execution result:{display.RESET}\n{result.get('output', '')}")
                                
                                # Add execution result to the conversation
                                if result.get('output'):
                                    memory.append({"role": "system", "content": f"Code execution result:\n```\n{result.get('output')}\n```"})
                                
                                executed_something = True
                            except Exception as e:
                                print(f"{display.RED}[Nexus] Code execution error: {e}{display.RESET}")
                
                # If no explicit code was found but execution was requested, try code blocks
                if not executed_something and code_blocks:
                    for code_block in code_blocks:
                        code_string = code_block.strip()
                        if code_string:
                            print(f"{display.CYAN}[Nexus] Executing code block:{display.RESET}\n{code_string}")
                            
                            try:
                                result = natural_flow.execute_code(code_string)
                                print(f"{display.GREEN}[Nexus] Code execution result:{display.RESET}\n{result.get('output', '')}")
                                
                                # Add execution result to the conversation
                                if result.get('output'):
                                    memory.append({"role": "system", "content": f"Code execution result:\n```\n{result.get('output')}\n```"})
                                
                                executed_something = True
                                # Only execute the first valid code block if multiple are found
                                break
                            except Exception as e:
                                print(f"{display.RED}[Nexus] Code execution error: {e}{display.RESET}")
                
                if not executed_something:
                    print(f"{display.YELLOW}[Nexus] Code execution was requested but no valid code was found{display.RESET}")
                    memory.append({"role": "system", "content": "Note: Code execution was requested but no valid code was found in the response."})
            
                
                # Parse and execute file loading requests
                if file_loading_requested:
                    # Find all file loading requests
                    import re
                    file_patterns = [
                        r"natural_flow\.load_file\((['\"])(.+?)\1\)",  # Single or double quotes
                        r"natural_flow\.load_file\('''(.+?)'''\)",  # Triple single quotes
                        r'natural_flow\.load_file\("""(.+?)"""\)'  # Triple double quotes
                    ]
                    
                    loaded_something = False
                    
                    for pattern in file_patterns:
                        matches = re.findall(pattern, response, re.DOTALL)
                        if matches:
                            for match in matches:
                                # Extract the file path
                                if isinstance(match, tuple):
                                    # For single/double quoted strings
                                    if len(match) >= 2:  # Make sure we have both quote type and file path
                                        file_path = match[1]
                                    else:
                                        continue
                                else:
                                    # For triple quoted strings
                                    file_path = match
                                
                                print(f"{display.CYAN}[Nexus] Loading file: {file_path}{display.RESET}")
                                try:
                                    # Use read_file_content for better handling
                                    result = natural_flow.read_file_content(file_path)
                                    
                                    if result.get('success', False):
                                        line_count = result.get('line_count', 0)
                                        file_size = result.get('size', 0)
                                        resolved_path = result.get('file_path', file_path)
                                        
                                        print(f"{display.GREEN}[Nexus] File loaded successfully: {resolved_path}{display.RESET}")
                                        print(f"{display.GREEN}[Nexus] File contains {line_count} lines, {file_size} bytes{display.RESET}")
                                        
                                        # Add file content to the conversation context
                                        file_content = result.get('content', '')
                                        if file_content:
                                            # Format the file content for the context
                                            # For very large files, only include the first portion to avoid context overflow
                                            max_chars = min(16000, len(file_content))  # Increased for better context but with a limit
                                            
                                            # Add a system message with the file content for context
                                            context_msg = f"File '{resolved_path}' content ({line_count} lines):\n```\n{file_content[:max_chars]}\n```\n"
                                            
                                            if len(file_content) > max_chars:
                                                approx_lines = len(file_content[:max_chars].splitlines())
                                                context_msg += f"\n(File content truncated. Showing first ~{approx_lines} of {line_count} lines)\n"
                                            
                                            # Add to memory for LLM context
                                            memory.append({"role": "system", "content": context_msg})
                                            loaded_something = True
                                    else:
                                        error_msg = result.get('error', 'Unknown error')
                                        print(f"{display.RED}[Nexus] File loading failed: {error_msg}{display.RESET}")
                                        memory.append({"role": "system", "content": f"File loading failed: {error_msg}"})
                                except Exception as e:
                                    print(f"{display.RED}[Nexus] Error loading file: {e}{display.RESET}")
                                    memory.append({"role": "system", "content": f"Error loading file: {str(e)}"})
                    
                    # Check for file loading hints if no explicit file loading was found
                    if not loaded_something:
                        # Look for file loading hints in the text
                        file_hints = ['please load the file', 'load the file', 'read the file', 'open the file']
                        file_path_pattern = r'(?:load|read|open)\s+(?:the\s+)?file[\s:]+[\'"](.*?)[\'"]'
                        
                        for hint in file_hints:
                            if hint.lower() in response.lower():
                                # Try to extract file path from the hint
                                file_path_matches = re.findall(file_path_pattern, response, re.IGNORECASE)
                                if file_path_matches:
                                    for file_path in file_path_matches:
                                        print(f"{display.CYAN}[Nexus] Loading file from hint: {file_path}{display.RESET}")
                                        try:
                                            result = natural_flow.read_file_content(file_path)
                                            if result.get('success', False):
                                                # Similar handling as above
                                                line_count = result.get('line_count', 0)
                                                file_size = result.get('size', 0)
                                                resolved_path = result.get('file_path', file_path)
                                                file_content = result.get('content', '')
                                                
                                                print(f"{display.GREEN}[Nexus] File loaded successfully: {resolved_path}{display.RESET}")
                                                print(f"{display.GREEN}[Nexus] File contains {line_count} lines, {file_size} bytes{display.RESET}")
                                                
                                                if file_content:
                                                    max_chars = min(16000, len(file_content))
                                                    context_msg = f"File '{resolved_path}' content ({line_count} lines):\n```\n{file_content[:max_chars]}\n```\n"
                                                    
                                                    if len(file_content) > max_chars:
                                                        approx_lines = len(file_content[:max_chars].splitlines())
                                                        context_msg += f"\n(File content truncated. Showing first ~{approx_lines} of {line_count} lines)\n"
                                                    
                                                    memory.append({"role": "system", "content": context_msg})
                                                    loaded_something = True
                                                    break
                                        except Exception as e:
                                            print(f"{display.RED}[Nexus] Error loading file from hint: {e}{display.RESET}")
                                break
            
            # File loading is now handled in the combined code execution and file loading section above
            
            # Print the response
            print(f"{display.MAGENTA}{display.BOLD}Nexus{display.RESET}: {response}")
            
            # Add to memory
            memory.append({"role": "assistant", "content": response})
            current_session.append({"role": "assistant", "content": response})
            _save_memory(memory)
        
        except Exception as err:
            print(f"LLM call failed: {err}")
            break
        
        current_tick += 1
    
    # Cleanup and save
    timestamp = datetime.now(timezone.utc).isoformat()
    
    if current_session:
        new_entry = {"timestamp": timestamp, "messages": list(reversed(current_session))}
        history.insert(0, new_entry)
        _roll_off_if_needed(history, active, client, provider_spec["model"])
    
    history = history[:MAX_FULL_SESSIONS]
    
    pulse_data = {"current_tick": current_tick, "last_updated": timestamp, "session_start_tick": session_start_tick}
    pulse_manager.save_pulse_counter(pulse_data)
    _save_history(history)
    _reset_memory_file()
    
    exit_timestamp = datetime.now(timezone.utc).isoformat()
    exit_stamp = [{"role": "system", "content": f"exit chat {exit_timestamp}"}]
    _save_memory(exit_stamp)
    
    summaries = _load_summaries()
    if len(summaries) > MAX_SUMMARY_ENTRIES:
        from nexus_memory_vectors import vector_memory
        to_dump = summaries[MAX_SUMMARY_ENTRIES:]
        for summary_entry in to_dump:
            vector_memory.add_summary_to_vectors(summary_entry)
        summaries = summaries[:MAX_SUMMARY_ENTRIES]
        _save_summaries(summaries)

if __name__ == "__main__":
    main()