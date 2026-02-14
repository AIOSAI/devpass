import sys
import os
import cortex_on_off
import langchain_enhancer
from config import get_openai_config
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from profile.profile_prompt import get_profile_prompt
from live_chat_context import add_to_context, get_context
from openai_interface import get_response

# Initialize LangChain client exactly like Nexus
def get_langchain_client():
    try:
        openai_config = get_openai_config()
        api_key = openai_config["api_key"]
        return langchain_enhancer.make_langchain_client("openai", api_key, openai_config["model"], openai_config["temperature"])
    except Exception as err:
        print(f"LangChain unavailable: {err}")
        return None

print("LangChain enhanced reasoning ready")

# --- Token usage breakdown aggregation ---
TURN_TOKEN_BREAKDOWN = []
from usage_monitor import get_usage_monitor, analyze_prompt_contributions
from prompt_file_read import get_prompt as get_file_read_prompt
from prompt_file_create import get_prompt as get_file_create_prompt
from prompt_file_cache import get_prompt as get_file_cache_prompt
from prompt_outline import get_prompt as get_outline_prompt
from prompt_analyze_code import get_prompt as get_analyze_prompt
from void.toolsService import read_file_sync, create_file_sync, create_folder_sync, delete_file_sync, delete_folder_sync, rewrite_file_sync
import re
from file_cache import cache_file_content, read_cached_file, clear_cache, read_all_cache
# Outline/code analysis dependencies
from void.outlineModel import OutlineModel, OutlineModelService
from void.modelService import WorkbenchModelService
from void.documentSymbolsOutline import DocumentSymbolsOutline
from void.cancellation import CancellationToken
try:
    from void.uri import URI
except ImportError:
    class URI:
        @staticmethod
        def file(path):
            return path  # Simple fallback
        pass
import asyncio

# Minimal stubs for service dependencies
class StubService:
    def for_feature(self, *args, **kwargs):
        return StubService()  # Return another stub
    
    @property
    def document_symbol_provider(self):
        return StubService()
    
    def ordered(self, *args, **kwargs):
        return []
    
    def on_model_removed(self, callback):
        return StubService()  # Return disposable stub
    
    def get(self, *args, **kwargs):
        return None
    
    def dispose(self):
        pass
    
    def on_did_change(self, callback):
        return StubService()  # Return disposable stub

class StubTextModel:
    def __init__(self, uri):
        self.uri = uri
        self.id = str(uri)
    def get_version_id(self):
        return 1

# Check if main is enabled
ENABLED = cortex_on_off.load_registry().get(__name__.split('.')[-1], {}).get("enabled", True)

if not ENABLED:
    # Module disabled - don't execute
    exit()


# Add all feature prompts to system prompt
from prompt_file_read import get_prompt as get_file_read_prompt
from prompt_file_cache import get_prompt as get_file_cache_prompt
from prompt_file_create import get_prompt as get_file_create_prompt

print("Seed is ready. Type 'exit' to quit.\n")

# Track which files were read with 'full' command during this session
full_read_files = set()

# Session memory for outline capabilities
session_memory = {
    'last_outline': None,
    'last_analysis': None, 
    'last_dependency_trace': None,
    'outline_history': [],
    'analysis_history': [],
    'dependency_history': []
}

def add_to_session_memory(operation_type, file_path, result):
    """Store operation results in session memory"""
    timestamp = __import__('datetime').datetime.now().strftime("%H:%M:%S")
    entry = {
        'timestamp': timestamp,
        'file_path': file_path,
        'result': result
    }
    
    if operation_type == 'outline':
        session_memory['last_outline'] = entry
        session_memory['outline_history'].append(entry)
    elif operation_type == 'analysis':
        session_memory['last_analysis'] = entry
        session_memory['analysis_history'].append(entry)
    elif operation_type == 'dependency':
        session_memory['last_dependency_trace'] = entry
        session_memory['dependency_history'].append(entry)
    
    # Keep only last 10 entries in history
    for key in ['outline_history', 'analysis_history', 'dependency_history']:
        if len(session_memory[key]) > 10:
            session_memory[key] = session_memory[key][-10:]

def get_session_context():
    """Generate context string about recent operations for LLM awareness"""
    context_parts = []
    
    if session_memory['last_outline']:
        last = session_memory['last_outline']
        outline_details = [f"Last outline operation: {last['file_path']} at {last['timestamp']}"]
        
        # Add detailed outline information
        try:
            from pathlib import Path
            import json
            outline_log_path = Path(__file__).parent / "outline_log.json"
            if outline_log_path.exists():
                with open(outline_log_path, "r", encoding="utf-8") as f:
                    log = json.load(f)
                if log:
                    latest = log[0]
                    outline_details.append(f"Outline details for {latest['file_path']}:")
                    if 'outline' in latest and 'children' in latest['outline']:
                        for sym in latest['outline']['children']:
                            kind = sym.get('kind')
                            name = sym.get('name')
                            rng = sym.get('range', {})
                            start = rng.get('startLineNumber')
                            end = rng.get('endLineNumber')
                            outline_details.append(f"- {kind}: {name} (lines {start}-{end})")
        except Exception as e:
            outline_details.append(f"(Error retrieving outline details: {e})")
            
        context_parts.extend(outline_details)

    # Add analysis log details
    if session_memory['last_analysis']:
        last = session_memory['last_analysis']
        analysis_details = [f"Last analysis operation: {last['file_path']} at {last['timestamp']}"]
        try:
            from pathlib import Path
            import json
            analyze_log_path = Path(__file__).parent / "analyze_log.json"
            if analyze_log_path.exists():
                with open(analyze_log_path, "r", encoding="utf-8") as f:
                    log = json.load(f)
                if log:
                    latest = log[0]
                    analysis_details.append(f"Analysis details for {latest['file_path']}:")
                    if 'analysis' in latest and isinstance(latest['analysis'], dict):
                        analysis_data = latest['analysis']
                        # File summary
                        if analysis_data.get('file_summary'):
                            analysis_details.append(f"File summary: {analysis_data['file_summary']}")
                        # Stats
                        stats = analysis_data.get('stats', {})
                        analysis_details.append(f"Stats: {stats.get('total_lines', 0)} lines, {stats.get('num_functions', 0)} functions, {stats.get('num_classes', 0)} classes, {stats.get('num_imports', 0)} imports")
                        # Functions with summaries
                        functions = analysis_data.get('functions', [])
                        if functions:
                            analysis_details.append("Functions:")
                            for func in functions[:5]:  # Limit to first 5 for brevity
                                name = func.get('name', '?')
                                start = func.get('start', '?')
                                end = func.get('end', '?')
                                complexity = func.get('cyclomatic_complexity', '?')
                                summary = func.get('summary', '')
                                analysis_details.append(f"- {name} (lines {start}-{end}, complexity: {complexity})")
                                if summary:
                                    analysis_details.append(f"  Summary: {summary}")
                        # Classes with summaries
                        classes = analysis_data.get('classes', [])
                        if classes:
                            analysis_details.append("Classes:")
                            for cls in classes[:3]:  # Limit to first 3 for brevity
                                name = cls.get('name', '?')
                                start = cls.get('start', '?')
                                end = cls.get('end', '?')
                                summary = cls.get('summary', '')
                                analysis_details.append(f"- {name} (lines {start}-{end})")
                                if summary:
                                    analysis_details.append(f"  Summary: {summary}")
        except Exception as e:
            analysis_details.append(f"(Error retrieving analysis details: {e})")
        context_parts.extend(analysis_details)
    
    if session_memory['last_dependency_trace']:
        last = session_memory['last_dependency_trace']
        trace_details = [f"Last dependency trace: {last['file_path']} at {last['timestamp']}"]
        try:
            from pathlib import Path
            import json
            trace_log_path = Path(__file__).parent / "trace_log.json"
            if trace_log_path.exists():
                with open(trace_log_path, "r", encoding="utf-8") as f:
                    log = json.load(f)
                if log:
                    latest = log[0]
                    trace_details.append(f"Dependency trace for {latest['file_path']}:")
                    trace_data = latest.get('trace')
                    if isinstance(trace_data, dict):
                        for k, v in trace_data.items():
                            trace_details.append(f"- {k}: {v}")
                    elif isinstance(trace_data, list):
                        for item in trace_data[:10]:
                            trace_details.append(f"- {item}")
                    elif trace_data:
                        trace_details.append(str(trace_data))
        except Exception as e:
            trace_details.append(f"(Error retrieving trace details: {e})")
        context_parts.extend(trace_details)
    
    if context_parts:
        return "RECENT OPERATIONS:\n" + "\n".join(context_parts) + "\n\n"
    return ""

import re

def print_outline_summary(outline_entry):
    if not outline_entry:
        print("No outline found in log.")
        return
    print(f"Last outline for {outline_entry.get('file_path')} at {outline_entry.get('timestamp')}")
    outline = outline_entry.get('outline', {})
    children = outline.get('children', [])
    if not children:
        print("(No symbols found)")
        return
    print("Top-level symbols:")
    for sym in children:
        kind = sym.get('kind')
        name = sym.get('name')
        rng = sym.get('range', {})
        start = rng.get('startLineNumber')
        end = rng.get('endLineNumber')
        print(f"- {kind}: {name} (lines {start}-{end})")

def build_system_prompt():
    # Load profile.json for identity and personality
    prompt_parts = []
    
    try:
        import json
        from pathlib import Path
        profile_path = Path(__file__).parent / "profile" / "profile.json"
        with profile_path.open("r", encoding="utf-8") as f:
            profile_data = json.load(f)
            
        # Basic identity from profile
        identity_parts = [f"You are {profile_data.get('name', 'Seed')}, {profile_data.get('persona', 'a modular AI system')}."]
        if traits := profile_data.get("traits"):
            identity_parts.append("Traits: " + ", ".join(traits) + ".")
        if rules := profile_data.get("rules"):
            identity_parts.append("Rules: " + " · ".join(rules) + ".")
        
        prompt_parts.append("\n".join(identity_parts))
    except (FileNotFoundError, json.JSONDecodeError) as e:
        # Fallback if profile.json is missing or invalid
        prompt_parts.append("You are Seed, a modular AI system designed to grow autonomously.")
    
    # Dynamically concatenate all available feature prompts and session context
    # Automatically detect all available prompt components
    try:
        from prompt_file_read import get_prompt
        prompt_parts.append(get_prompt())
    except ImportError:
        pass
    
    try:
        from prompt_file_create import get_prompt
        prompt_parts.append(get_prompt())
    except ImportError:
        pass
    
    try:
        from prompt_file_cache import get_prompt
        prompt_parts.append(get_prompt())
    except ImportError:
        pass
    
    try:
        from prompt_outline import get_prompt
        prompt_parts.append(get_prompt())
    except ImportError:
        pass
    
    try:
        from prompt_analyze_code import get_prompt
        prompt_parts.append(get_prompt())
    except ImportError:
        pass
    
    # Add session context
    prompt_parts.append(get_session_context())
    
    return "".join(prompt_parts)

while True:
    user_input = input("You: ").strip()
    if user_input.lower() in {"exit", "quit"}:
        clear_cache()
        try:
            from outline_log import clear_outline_log
            clear_outline_log()
        except Exception:
            pass
        try:
            from analyze_log import clear_analyze_log
            clear_analyze_log()
        except Exception:
            pass
        print("[Seed] File cache cleared.")
        break

    if re.search(r"(show|what\s*was|can you see).*(last|recent).*outline", user_input, re.I):
        from pathlib import Path
        import json
        outline_log_path = Path(__file__).parent / "outline_log.json"
        if outline_log_path.exists():
            try:
                with open(outline_log_path, "r", encoding="utf-8") as f:
                    log = json.load(f)
                if log:
                    print_outline_summary(log[0])
                else:
                    print("No outline operations found.")
            except Exception as e:
                print(f"Error reading outline log: {e}")
        else:
            print("No outline log found.")
        continue
    if re.search(r"(show|what\s*was|can you see).*(last|recent).*(dependency|trace)", user_input, re.I):
        from pathlib import Path
        import json
        trace_log_path = Path(__file__).parent / "trace_log.json"
        if trace_log_path.exists():
            try:
                with open(trace_log_path, "r", encoding="utf-8") as f:
                    log = json.load(f)
                if log:
                    latest = log[0]
                    print(f"Last dependency trace for {latest.get('file_path')} at {latest.get('timestamp')}")
                    trace_data = latest.get('trace', {})
                    if isinstance(trace_data, dict):
                        for k, v in trace_data.items():
                            print(f"- {k}: {v}")
                    elif isinstance(trace_data, list):
                        for item in trace_data[:10]:
                            print(f"- {item}")
                    elif trace_data:
                        print(str(trace_data))
                else:
                    print("No dependency trace operations found.")
            except Exception as e:
                print(f"Error reading trace log: {e}")
        else:
            print("No trace log found.")
        continue
    if re.search(r"(show|what\s*was|can you see).*(last|recent).*analysis", user_input, re.I):
        from pathlib import Path
        import json
        analyze_log_path = Path(__file__).parent / "analyze_log.json"
        if analyze_log_path.exists():
            try:
                with open(analyze_log_path, "r", encoding="utf-8") as f:
                    log = json.load(f)
                if log:
                    latest = log[0]
                    print(f"Last analysis for {latest.get('file_path')} at {latest.get('timestamp')}")
                    analysis_data = latest.get('analysis', {})
                    if not analysis_data:
                        print("(No analysis data found)")
                    else:
                        # File summary
                        if analysis_data.get('file_summary'):
                            print(f"File summary: {analysis_data['file_summary']}")
                        
                        # Stats
                        stats = analysis_data.get('stats', {})
                        print(f"Stats: {stats.get('total_lines', 0)} lines, {stats.get('num_functions', 0)} functions, {stats.get('num_classes', 0)} classes, {stats.get('num_imports', 0)} imports")
                        
                        # Imports
                        imports = analysis_data.get('imports', [])
                        if imports:
                            print(f"Imports: {', '.join(imports)}")
                        
                        # Functions with summaries
                        functions = analysis_data.get('functions', [])
                        if functions:
                            print("Functions:")
                            for func in functions:
                                name = func.get('name', '?')
                                start = func.get('start', '?')
                                end = func.get('end', '?')
                                complexity = func.get('cyclomatic_complexity', '?')
                                summary = func.get('summary', '')
                                print(f"- {name} (lines {start}-{end}, complexity: {complexity})")
                                if summary:
                                    print(f"  Summary: {summary}")
                        
                        # Classes with summaries
                        classes = analysis_data.get('classes', [])
                        if classes:
                            print("Classes:")
                            for cls in classes:
                                name = cls.get('name', '?')
                                start = cls.get('start', '?')
                                end = cls.get('end', '?')
                                summary = cls.get('summary', '')
                                print(f"- {name} (lines {start}-{end})")
                                if summary:
                                    print(f"  Summary: {summary}")
                                # Show methods if any
                                methods = cls.get('methods', [])
                                if methods:
                                    print(f"  Methods: {', '.join([m.get('name', '?') for m in methods])}")
                else:
                    print("No analysis operations found.")
            except Exception as e:
                print(f"Error reading analyze log: {e}")
        else:
            print("No analyze log found.")
        continue

    # Intercept 'read file <file_path> full'
    match = re.match(r"read file ([^\s]+) full", user_input, re.IGNORECASE)
    if match:
        file_path = match.group(1).strip()
        try:
            from void.file_operations import read_file_full_sync
            from file_cache import cache_file_content
            result = read_file_full_sync(file_path)
            content = result["result"]["content"]
            cache_file_content(file_path, content)
            # Add to the session-wide set of files read with 'full'
            full_read_files.add(file_path)
            print(f"[DEBUG] Full file read and cached: {file_path}")
            print(f"[Seed] Full file content cached and available in context.")
        except Exception as e:
            print(f"Seed (error): {e}")
        continue

    # Intercept 'read file <file_path>' commands
    match = re.match(r"read file (.+)", user_input, re.IGNORECASE)
    if match:
        file_path = match.group(1).strip()
        try:
            result = read_file_sync(file_path)
            if isinstance(result, dict) and 'result' in result and 'content' in result['result']:
                file_content = result['result']['content']
                print(f"[DEBUG] File path resolved: {result['result'].get('path','?')}")
                cache_file_content(file_path, file_content)
                print(f"[Seed] File content cached for: {file_path}")
                if result['result'].get('truncated'):
                    print("[Seed] (output truncated)")
            else:
                print(f"[DEBUG] Unexpected result structure: {result}")
                print(f"Seed (error): Unexpected result format.")
        except Exception as e:
            print(f"Seed (error): {e}")
        continue

    # Intercept 'trace dependencies <file_path>'
    match = re.match(r"trace dependencies ([^\s]+)", user_input, re.IGNORECASE)
    if match:
        file_path = match.group(1).strip()
        try:
            from trace_log import log_trace_operation
            # Simulate a dependency trace result (replace with real logic as needed)
            # For demonstration, let's say we just list imported modules
            import ast
            from pathlib import Path
            abs_path = os.path.abspath(file_path)
            with open(abs_path, 'r', encoding='utf-8') as f:
                source = f.read()
            tree = ast.parse(source, filename=file_path)
            imports = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(f"import {alias.name}")
                elif isinstance(node, ast.ImportFrom):
                    mod = node.module or ''
                    for alias in node.names:
                        imports.append(f"from {mod} import {alias.name}")
            trace_result = {'imports': imports, 'num_imports': len(imports)}
            log_trace_operation(file_path, trace_data=trace_result, caller="user")
            add_to_session_memory('dependency', file_path, trace_result)
            print(f"Dependency trace operation completed for {file_path}. See trace_log.json for details.")
            if imports:
                print("Imports found:")
                for imp in imports:
                    print(f"- {imp}")
            else:
                print("No imports found.")
        except Exception as e:
            log_trace_operation(file_path, error=e, caller="user")
            print(f"Dependency trace operation failed for {file_path}. See trace_log.json for error details.")
        continue

    # Intercept 'show outline <file_path>'
    match = re.match(r"show outline ([^\s]+)", user_input, re.IGNORECASE)
    if match:
        file_path = match.group(1).strip()
        try:
            # Prepare model and outline
            from outline_log import log_outline_operation
            from python_symbol_provider import PythonDocumentSymbolProvider
            # Minimal registry for Python symbols
            class SimpleRegistry:
                def __init__(self, provider):
                    self._provider = provider
                def ordered(self, text_model):
                    return [self._provider]
                def on_did_change(self, cb):
                    class DummyListener:
                        def dispose(self):
                            pass
                    return DummyListener()
            class DummyLanguageFeaturesService:
                def __init__(self, provider):
                    self.document_symbol_provider = SimpleRegistry(provider)
            uri = URI.file(file_path)
            text_model = StubTextModel(uri)
            token = CancellationToken()
            provider = PythonDocumentSymbolProvider()
            outline_service = OutlineModelService(DummyLanguageFeaturesService(provider), StubService(), StubService())
            try:
                outline_model = asyncio.run(outline_service.getOrCreate(text_model, token))
                # Serialize the outline model to a JSON-serializable dict
                def outline_to_dict(element):
                    result = {}
                    if hasattr(element, 'symbol') and getattr(element, 'symbol') is not None:
                        symbol = element.symbol
                        result = {
                            "kind": getattr(symbol, "kind", None),
                            "name": getattr(symbol, "name", None),
                            "range": {
                                "startLineNumber": getattr(getattr(symbol, "range", None), "startLineNumber", None),
                                "endLineNumber": getattr(getattr(symbol, "range", None), "endLineNumber", None)
                            }
                        }
                    result["children"] = [outline_to_dict(child) for child in getattr(element, "children", {}).values()]
                    return result
                outline_dict = outline_to_dict(outline_model)
                log_outline_operation(file_path, outline_data=outline_dict, caller="user")
                print(f"Outline operation completed for {file_path}. See outline_log.json for details.")
                add_to_session_memory('outline', file_path, outline_model)
            except Exception as e:
                log_outline_operation(file_path, error=e, caller="user")
                print(f"Outline operation failed for {file_path}. See outline_log.json for error details.")
        except Exception as e:
            print(f"Seed (outline error): {e}")
        continue

    # Intercept 'analyze code <file_path>'
    match = re.match(r"analyze code ([^\s]+)", user_input, re.IGNORECASE)
    if match:
        file_path = match.group(1).strip()
        try:
            import ast
            import tokenize
            from pathlib import Path
            from analyze_log import log_analyze_operation
            from openai_interface import get_response

            # Read file content
            abs_path = os.path.abspath(file_path)
            with open(abs_path, 'r', encoding='utf-8') as f:
                source = f.read()

            # Parse AST
            tree = ast.parse(source, filename=file_path)
            module_docstring = ast.get_docstring(tree)

            # Extract imports
            imports = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(f"import {alias.name}")
                elif isinstance(node, ast.ImportFrom):
                    mod = node.module or ''
                    for alias in node.names:
                        imports.append(f"from {mod} import {alias.name}")

            # Cyclomatic complexity helper
            def cyclomatic_complexity(node):
                # Count branches: if, for, while, and, or, except, with, assert
                count = 1
                for n in ast.walk(node):
                    if isinstance(n, (ast.If, ast.For, ast.While, ast.And, ast.Or, ast.ExceptHandler, ast.With, ast.Assert, ast.Try)):
                        count += 1
                return count

            # Extract functions and classes
            def get_args(node):
                if hasattr(node, 'args'):
                    return [a.arg for a in node.args.args]
                return []
            def get_doc(node):
                return ast.get_docstring(node)
            functions = []
            classes = []
            for node in tree.body:
                if isinstance(node, ast.FunctionDef):
                    func_code = ast.get_source_segment(source, node)
                    # LLM summary for function
                    func_summary = None
                    try:
                        func_prompt = [
                            {"role": "system", "content": "Summarize the purpose and usage of this Python function in 1-2 sentences."},
                            {"role": "user", "content": func_code or node.name}
                        ]
                        resp = get_response(func_prompt, model=None, temperature=0.2)
                        # Robust extraction and debug output
                        func_summary = None
                        if resp:
                            if isinstance(resp, str):
                                func_summary = resp
                            elif isinstance(resp, dict) and "choices" in resp and resp["choices"]:
                                try:
                                    func_summary = resp["choices"][0].get("message", {}).get("content", None)
                                except Exception as parse_exc:
                                    print(f"[DEBUG] Error parsing LLM response for function summary: {parse_exc}, raw: {resp}")
                            else:
                                print(f"[DEBUG] Unexpected LLM response for function summary: {resp}")
                        if not func_summary:
                            print(f"[DEBUG] No summary returned for function {node.name}")
                    except Exception as e:
                        print(f"[DEBUG] LLM call failed for function {node.name}: {e}")
                        func_summary = None
                    functions.append({
                        'name': node.name,
                        'start': node.lineno,
                        'end': node.end_lineno if hasattr(node, 'end_lineno') else node.lineno,
                        'args': get_args(node),
                        'docstring': get_doc(node),
                        'cyclomatic_complexity': cyclomatic_complexity(node),
                        'summary': func_summary
                    })
                elif isinstance(node, ast.ClassDef):
                    class_code = ast.get_source_segment(source, node)
                    # LLM summary for class
                    class_summary = None
                    try:
                        class_prompt = [
                            {"role": "system", "content": "Summarize the purpose and usage of this Python class in 1-2 sentences."},
                            {"role": "user", "content": class_code or node.name}
                        ]
                        resp = get_response(class_prompt, model=None, temperature=0.2)
                        class_summary = None
                        if resp:
                            if isinstance(resp, str):
                                class_summary = resp
                            elif isinstance(resp, dict) and "choices" in resp and resp["choices"]:
                                try:
                                    class_summary = resp["choices"][0].get("message", {}).get("content", None)
                                except Exception as parse_exc:
                                    print(f"[DEBUG] Error parsing LLM response for class summary: {parse_exc}, raw: {resp}")
                            else:
                                print(f"[DEBUG] Unexpected LLM response for class summary: {resp}")
                        if not class_summary:
                            print(f"[DEBUG] No summary returned for class {node.name}")
                    except Exception as e:
                        print(f"[DEBUG] LLM call failed for class {node.name}: {e}")
                        class_summary = None
                    classes.append({
                        'name': node.name,
                        'start': node.lineno,
                        'end': node.end_lineno if hasattr(node, 'end_lineno') else node.lineno,
                        'docstring': get_doc(node),
                        'summary': class_summary,
                        'methods': [
                            {
                                'name': n.name,
                                'start': n.lineno,
                                'end': n.end_lineno if hasattr(n, 'end_lineno') else n.lineno,
                                'args': get_args(n),
                                'docstring': get_doc(n),
                                'cyclomatic_complexity': cyclomatic_complexity(n),
                                'summary': None  # Optionally add LLM summary for each method
                            }
                            for n in node.body if isinstance(n, ast.FunctionDef)
                        ]
                    })

            # Summary stats
            total_lines = len(source.splitlines())
            stats = {
                'total_lines': total_lines,
                'num_imports': len(imports),
                'num_functions': len(functions),
                'num_classes': len(classes)
            }

            # LLM summary for the file
            file_summary = None
            try:
                file_prompt = [
                    {"role": "system", "content": "Summarize the purpose and main functionality of this Python file in 2-3 sentences."},
                    {"role": "user", "content": source[:5000]}  # Truncate if very large
                ]
                resp = get_response(file_prompt, model=None, temperature=0.2)
                file_summary = None
                if resp:
                    if isinstance(resp, str):
                        file_summary = resp
                    elif isinstance(resp, dict) and "choices" in resp and resp["choices"]:
                        try:
                            file_summary = resp["choices"][0].get("message", {}).get("content", None)
                        except Exception as parse_exc:
                            print(f"[DEBUG] Error parsing LLM response for file summary: {parse_exc}, raw: {resp}")
                    else:
                        print(f"[DEBUG] Unexpected LLM response for file summary: {resp}")
                if not file_summary:
                    print(f"[DEBUG] No summary returned for file {file_path}")
            except Exception as e:
                print(f"[DEBUG] LLM call failed for file summary: {e}")
                file_summary = None

            # Print summary to user
            print(f"[Seed] Analysis for {file_path}:")
            if module_docstring:
                print(f"Module docstring: {module_docstring}")
            print(f"Imports ({len(imports)}): {imports}")
            print(f"Functions ({len(functions)}): {[f['name'] for f in functions]}")
            print(f"Classes ({len(classes)}): {[c['name'] for c in classes]}")
            print(f"Total lines: {total_lines}")
            if file_summary:
                print(f"File summary: {file_summary}")

            analysis_result = {
                'module_docstring': module_docstring,
                'imports': imports,
                'functions': functions,
                'classes': classes,
                'stats': stats,
                'file_summary': file_summary
            }
            log_analyze_operation(file_path, analysis_data=analysis_result, caller="user")
            add_to_session_memory('analysis', file_path, analysis_result)
        except Exception as e:
            from analyze_log import log_analyze_operation
            log_analyze_operation(file_path, error=e, caller="user")
            print(f"Seed (analyze code error): {e}")
        continue

    # Intercept 'create file <file_path> with content: <content>'
    match = re.match(r"create file ([^\s]+) with content: (.+)", user_input, re.IGNORECASE)
    if match:
        file_path = match.group(1).strip()
        content = match.group(2)
        try:
            result = create_file_sync(file_path, content)
            print(f"[DEBUG] File created: {file_path}")
            print(f"Seed (create file result): {result}")
        except Exception as e:
            print(f"Seed (error): {e}")
        continue

    # Intercept 'create file <file_path>' (empty file)
    match = re.match(r"create file ([^\s]+)$", user_input, re.IGNORECASE)
    if match:
        file_path = match.group(1).strip()
        try:
            result = create_file_sync(file_path)
            print(f"[DEBUG] File created: {file_path}")
            print(f"Seed (create file result): {result}")
        except Exception as e:
            print(f"Seed (error): {e}")
        continue

    # Intercept 'edit file <file_path> lines <start>-<end> to: <new_content>'
    match = re.match(r"edit file ([^\s]+) lines (\d+)-(\d+) to:([\s\S]+)", user_input, re.IGNORECASE)
    if match:
        file_path = match.group(1).strip()
        start = int(match.group(2))
        end = int(match.group(3))
        new_content = match.group(4).lstrip(" ")
        try:
            # Read original file
            result = read_file_sync(file_path)
            if not (isinstance(result, dict) and 'result' in result and 'content' in result['result']):
                print(f"Seed (error): Could not read file for editing: {file_path}")
                continue
            orig = result['result']['content'].splitlines(keepends=True)
            # Replace lines (1-based, inclusive)
            if start < 1 or end > len(orig) or start > end:
                print(f"Seed (error): Invalid line range for edit.")
                continue
            replacement = new_content.splitlines(keepends=True)
            new_lines = orig[:start-1] + replacement + orig[end:]
            final_content = ''.join(new_lines)
            result = rewrite_file_sync(file_path, final_content)
            print(f"[DEBUG] File edited (lines {start}-{end}): {file_path}")
            print(f"Seed: File '{file_path}' lines {start}-{end} replaced successfully.")
        except Exception as e:
            print(f"Seed (error): {e}")
        continue

    # Intercept 'edit file <file_path> to: <new_content>' (full replace)
    match = re.match(r"edit file ([^\s]+) to:([\s\S]+)", user_input, re.IGNORECASE)
    if match:
        file_path = match.group(1).strip()
        new_content = match.group(2).lstrip(" ")
        try:
            result = rewrite_file_sync(file_path, new_content)
            print(f"[DEBUG] File edited (full replace): {file_path}")
            print(f"Seed: File '{file_path}' replaced successfully.")
        except Exception as e:
            print(f"Seed (error): {e}")
        continue

    # Intercept 'create folder <folder_path>'
    match = re.match(r"create folder ([^\s]+)", user_input, re.IGNORECASE)
    if match:
        folder_path = match.group(1).strip()
        try:
            result = create_folder_sync(folder_path)
            print(f"[DEBUG] Folder created: {folder_path}")
            print(f"Seed (create folder result): {result}")
        except Exception as e:
            print(f"Seed (error): {e}")
        continue

    # Intercept 'delete file <file_path>'
    match = re.match(r"delete file ([^\s]+)", user_input, re.IGNORECASE)
    if match:
        file_path = match.group(1).strip()
        try:
            result = delete_file_sync(file_path)
            deleted = result.get('result', {}).get('deleted', False)
            if deleted:
                print(f"[DEBUG] File deleted: {file_path}")
                print(f"Seed: File '{file_path}' deleted successfully.")
            else:
                print(f"[DEBUG] File not deleted (missing or error): {file_path}")
                print(f"Seed: File '{file_path}' did not exist or could not be deleted.")
        except FileNotFoundError:
            print(f"[DEBUG] File not found: {file_path}")
            print(f"Seed: File '{file_path}' did not exist.")
        except Exception as e:
            print(f"Seed (error): {e}")
        continue

    # Intercept 'delete folder <folder_path> recursive'
    match = re.match(r"delete folder ([^\s]+) recursive", user_input, re.IGNORECASE)
    if match:
        folder_path = match.group(1).strip()
        try:
            result = delete_folder_sync(folder_path, recursive=True)
            deleted = result.get('result', {}).get('deleted', False)
            if deleted:
                print(f"[DEBUG] Folder recursively deleted: {folder_path}")
                print(f"Seed: Folder '{folder_path}' recursively deleted successfully.")
            else:
                print(f"[DEBUG] Folder not deleted (missing or error): {folder_path}")
                print(f"Seed: Folder '{folder_path}' did not exist or could not be deleted.")
        except FileNotFoundError:
            print(f"[DEBUG] Folder not found: {folder_path}")
            print(f"Seed: Folder '{folder_path}' did not exist.")
        except Exception as e:
            print(f"Seed (error): {e}")
        continue

    # Intercept 'delete folder <folder_path>' (non-recursive)
    match = re.match(r"delete folder ([^\s]+)", user_input, re.IGNORECASE)
    if match:
        folder_path = match.group(1).strip()
        try:
            result = delete_folder_sync(folder_path, recursive=False)
            deleted = result.get('result', {}).get('deleted', False)
            if deleted:
                print(f"[DEBUG] Folder deleted: {folder_path}")
                print(f"Seed: Folder '{folder_path}' deleted successfully.")
            else:
                print(f"[DEBUG] Folder not deleted (missing or error): {folder_path}")
                print(f"Seed: Folder '{folder_path}' did not exist or could not be deleted.")
        except FileNotFoundError:
            print(f"[DEBUG] Folder not found: {folder_path}")
            print(f"Seed: Folder '{folder_path}' did not exist.")
        except Exception as e:
            print(f"Seed (error): {e}")
        continue

    # Intercept 'run command <shell command>'
    match = re.match(r"run command ([\s\S]+)", user_input, re.IGNORECASE)
    if match:
        shell_command = match.group(1).strip()
        try:
            from test_simple_executor import run_shell_command
            result = run_shell_command(shell_command, shell='bash', caller='user')
            print(f"[Seed] Command: {shell_command}")
            print(f"[Seed] Exit code: {result['exit_code']}")
            if result['output']:
                print(f"[Seed] Output:\n{result['output']}")
            if result['error']:
                print(f"[Seed] Error:\n{result['error']}")
            # Add execution summary to context for LLM awareness
            summary = (
                f"Command executed: {shell_command}\n"
                f"Exit code: {result['exit_code']}\n"
                f"Output: {result['output'][:500]}\n"
                f"Error: {result['error'][:500]}"
            )
            add_to_context("system", summary)
            continue
        except Exception as e:
            print(f"Seed (error running command): {e}")
            continue

    # Intercept 'run script <file.py>'
    match = re.match(r"run script ([^\s]+)", user_input, re.IGNORECASE)
    if match:
        script_path = match.group(1).strip()
        try:
            from test_simple_executor import run_shell_command
            abs_script_path = os.path.abspath(script_path)
            # Only allow scripts in project root for safety
            project_root = os.path.abspath(os.path.dirname(__file__))
            if not abs_script_path.startswith(project_root):
                print("Seed (error): Script path outside project root is not allowed.")
                continue
            result = run_shell_command(f"python \"{abs_script_path}\"", shell='bash', caller='user')
            print(f"[Seed] Script: {script_path}")
            print(f"[Seed] Exit code: {result['exit_code']}")
            if result['output']:
                print(f"[Seed] Output:\n{result['output']}")
            if result['error']:
                print(f"[Seed] Error:\n{result['error']}")
            # Add execution summary to context for LLM awareness
            summary = (
                f"Script executed: {script_path}\n"
                f"Exit code: {result['exit_code']}\n"
                f"Output: {result['output'][:500]}\n"
                f"Error: {result['error'][:500]}"
            )
            add_to_context("system", summary)
            continue
        except Exception as e:
            print(f"Seed (error running script): {e}")
            continue

    # Intercept 'trace dependencies <module_name>'
    match = re.match(r"trace dependencies ([^\s]+)", user_input, re.IGNORECASE)
    if match:
        module_name = match.group(1).strip()
        try:
            # Convert module name to file path (e.g., void.document_symbols_outline -> void/document_symbols_outline.py)
            file_path = module_name.replace('.', '/') + '.py'
            
            # Read the file and extract import statements
            from void.file_operations import read_file_full_sync
            content = read_file_full_sync(file_path)
            if content is None or not isinstance(content, dict) or 'result' not in content or 'content' not in content['result']:
                print(f"Seed (trace error): Could not read file {file_path}")
                continue
                
            # Parse imports using regex
            import_lines = []
            for line_num, line in enumerate(content['result']['content'].split('\n'), 1):
                line = line.strip()
                if line.startswith('import ') or line.startswith('from '):
                    import_lines.append((line_num, line))
            
            print(f"Dependencies for {module_name}:")
            if import_lines:
                for line_num, import_stmt in import_lines:
                    print(f"  Line {line_num}: {import_stmt}")
            else:
                print("  No import statements found.")
            add_to_session_memory('dependency', file_path, import_lines)
        except Exception as e:
            print(f"Seed (trace dependencies error): {e}")
        continue

    # Session memory query handlers
    if re.match(r"(show|what was|tell me about).*(last|recent).*(outline|dependency|analysis|trace)", user_input, re.IGNORECASE):
        if "outline" in user_input.lower():
            if session_memory['last_outline']:
                last = session_memory['last_outline']
                print(f"Last outline operation: {last['file_path']} at {last['timestamp']}")
                print("You can ask me questions about this outline or request a new one.")
            else:
                print("No outline operations performed in this session.")
        elif "dependency" in user_input.lower() or "trace" in user_input.lower():
            if session_memory['last_dependency_trace']:
                last = session_memory['last_dependency_trace']
                print(f"Last dependency trace: {last['file_path']} at {last['timestamp']}")
                print("Dependencies found:")
                for line_num, import_stmt in last['result']:
                    print(f"  Line {line_num}: {import_stmt}")
            else:
                print("No dependency trace operations performed in this session.")
        elif "analysis" in user_input.lower():
            if session_memory['last_analysis']:
                last = session_memory['last_analysis']
                print(f"Last analysis operation: {last['file_path']} at {last['timestamp']}")
                print("Symbols found:")
                for kind, name, start, end in last['result']:
                    print(f"  - {kind}: {name} (lines {start}-{end})")
            else:
                print("No analysis operations performed in this session.")
        continue

    # Show session history
    if re.match(r"(show|list).*(history|operations)", user_input, re.IGNORECASE):
        print("Session History:")
        all_ops = []
        for op in session_memory['outline_history']:
            all_ops.append(('outline', op))
        for op in session_memory['analysis_history']:
            all_ops.append(('analysis', op))
        for op in session_memory['dependency_history']:
            all_ops.append(('dependency', op))
        
        # Sort by timestamp
        all_ops.sort(key=lambda x: x[1]['timestamp'])
        
        if all_ops:
            for op_type, op in all_ops:
                print(f"  {op['timestamp']} - {op_type}: {op['file_path']}")
        else:
            print("  No operations performed in this session.")
        continue

    add_to_context("user", user_input)

    from prompt_script_exec import get_script_exec_prompt
    # Use build_system_prompt() to ensure all prompts including outline are included
    system_prompt = build_system_prompt() + "\n" + get_script_exec_prompt()
    # Inject file cache contents into LLM context
    cache = read_all_cache()
    cache_content = ""
    if cache:
        # Format each cache entry - don't truncate full reads
        cache_entries = []
        for k, v in cache.items():
            # Don't truncate files that were read with 'full'
            if k in full_read_files:
                cache_entries.append(f"{k}: {v}")
            else:
                cache_entries.append(f"{k}: {v[:500]}{'... (truncated)' if len(v) > 500 else ''}")
        cache_summary = "\n".join(cache_entries)
        cache_content = cache_summary
        cache_message = f"Current file cache:\n{cache_summary}"
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "system", "content": cache_message},
            {"role": "system", "content": get_session_context()}
        ] + get_context()
    else:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "system", "content": get_session_context()}
        ] + get_context()

    # === TOKEN CONTRIBUTION ANALYSIS ===
    # Automatically detect all available prompt components
    prompt_components = {}
    
    # Import all prompt modules and collect their get_prompt functions
    try:
        from prompt_file_read import get_prompt
        prompt_components["file_read_prompt"] = get_prompt()
    except ImportError:
        pass
    
    try:
        from prompt_file_create import get_prompt
        prompt_components["file_create_prompt"] = get_prompt()
    except ImportError:
        pass
    
    try:
        from prompt_file_cache import get_prompt
        prompt_components["file_cache_prompt"] = get_prompt()
    except ImportError:
        pass
    
    try:
        from prompt_outline import get_prompt
        prompt_components["outline_prompt"] = get_prompt()
    except ImportError:
        pass
    
    try:
        from prompt_analyze_code import get_prompt
        prompt_components["analyze_prompt"] = get_prompt()
    except ImportError:
        pass
    
    try:
        from prompt_trace_dependencies import get_prompt
        prompt_components["trace_dependencies_prompt"] = get_prompt()
    except ImportError:
        pass
    
    try:
        from prompt_script_exec import get_script_exec_prompt
        prompt_components["script_exec_prompt"] = get_script_exec_prompt()
    except ImportError:
        pass
    
    # Dynamically analyze all prompt components and session context
    breakdown = analyze_prompt_contributions(
        system_prompt=system_prompt,
        session_context=get_session_context(),
        cache_content=cache_content,
        user_input=user_input,
        context_messages=get_context(),
        **prompt_components
    )

    # Send to LLM
    USE_LANGCHAIN = True
    openai_config = get_openai_config()  # Get fresh config each time
    try:
        if USE_LANGCHAIN:
            lc_client = get_langchain_client()
            if lc_client is not None:
                reply = langchain_enhancer.langchain_enhanced_chat(
                    "openai",
                    lc_client,
                    openai_config["model"],
                    messages,
                    openai_config["temperature"],
                    breakdown=breakdown,
                    token_contributions=breakdown  # Seed passes breakdown as token_contributions too
                )
            else:
                reply = get_response(messages, token_contributions=breakdown)
        else:
            reply = get_response(messages, token_contributions=breakdown)
    except Exception as e:
        print(f"LangChain error, falling back to direct OpenAI: {e}")
        reply = get_response(messages, token_contributions=breakdown)
    
    print(f"Seed: {reply}")
    add_to_context("assistant", reply)
