import sys
import os
from pathlib import Path
from typing import Dict, Any
import logging

# --- Path resolution (matches your existing pattern) ---
root = Path(__file__).resolve()
while root.name != "AIPass_Core" and root != root.parent:
    root = root.parent

core_dir = root
repo_root = core_dir.parent

for p in (str(repo_root), str(core_dir)):
    if p not in sys.path:
        sys.path.insert(0, p)

from paths import ROOT  # noqa: E402

# --- Path resolution ---
current_dir = Path(__file__).resolve().parent

# --- Update PYTHONPATH ---
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# --- Import API manager ---
try:
    from api_manager.api_manager import get_api_manager
    api_manager = get_api_manager()
    API_MANAGER_AVAILABLE = True
except ImportError as e:
    print(f"[WARN] API manager unavailable: {e}")
    api_manager = None
    API_MANAGER_AVAILABLE = False

# --- Import usage monitor ---
try:
    # First try the standard import
    try:
        from api_manager.usage_monitor import get_usage_monitor
    except ImportError:
        # If that fails, try with direct path import
        import importlib.util
        usage_monitor_path = Path(core_dir) / "api_manager" / "usage_monitor.py"
        if not usage_monitor_path.exists():
            raise ImportError(f"Could not find usage_monitor.py at {usage_monitor_path}")
        
        spec = importlib.util.spec_from_file_location("usage_monitor", usage_monitor_path)
        if spec is None:
            raise ImportError(f"Could not load spec for {usage_monitor_path}")
        
        usage_monitor_module = importlib.util.module_from_spec(spec)
        if spec.loader is None:
            raise ImportError(f"Loader is None for {usage_monitor_path}")
        spec.loader.exec_module(usage_monitor_module)
        get_usage_monitor = usage_monitor_module.get_usage_monitor
    
    # Get the monitor instance
    usage_monitor = get_usage_monitor()
    USAGE_MONITORING_ENABLED = True
    print(f"[INFO] Usage monitoring enabled")
except Exception as e:
    print(f"[WARN] Usage monitoring unavailable: {e}")
    usage_monitor = None
    USAGE_MONITORING_ENABLED = False

logger = logging.getLogger("nexus")

# --- LangChain imports ---
try:
    from langchain_openai import ChatOpenAI
    LANGCHAIN_AVAILABLE = True
except ImportError as e:
    print(f"[WARN] LangChain not available: {e}")
    LANGCHAIN_AVAILABLE = False
    ChatOpenAI = None

def make_langchain_client(provider: str, api_key: str, model: str = "gpt-4.1-nano", temperature: float = 0.7):
    """Create a LangChain client for the given provider."""
    if not LANGCHAIN_AVAILABLE:
        raise ValueError("LangChain not available")
    
    if provider == "openai":
        if ChatOpenAI is None:
            raise ValueError("LangChain OpenAI not available")
        
        # Use provided parameters or defaults
        # Import the correct SecretStr from pydantic directly
        from pydantic import SecretStr
        
        # Create the ChatOpenAI client with the API key properly typed
        return ChatOpenAI(
            api_key=SecretStr(api_key),
            model=model,
            temperature=temperature
        )
    
    raise ValueError(f"LangChain provider '{provider}' not supported yet")

def langchain_enhanced_chat(provider: str, client, model: str, messages: list, temperature: float) -> str:
    """Send an enhanced chat request using LangChain."""
    if provider == "openai":
        # Update model and temperature
        # client.model_name = model
        # client.temperature = temperature
        
        # Convert messages to LangChain format
        from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
        
        lc_messages = []
        for msg in messages:
            if msg["role"] == "system":
                lc_messages.append(SystemMessage(content=msg["content"]))
            elif msg["role"] == "user":
                lc_messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                lc_messages.append(AIMessage(content=msg["content"]))
        
        # Get response
        response = client.invoke(lc_messages)
        
        # Log usage if available (similar to llm_client.py)
        if USAGE_MONITORING_ENABLED and usage_monitor:
            
            try:
                # Estimate token usage based on input/output text length
                # This is a rough approximation
                try:
                    input_tokens = sum(len(msg["content"].split()) * 1.3 for msg in messages)  # rough token estimate
                    output_tokens = len(response.content.split()) * 1.3 if isinstance(response.content, str) else 0  # rough token estimate
                except Exception as e:
                    logger.warning(f"Error estimating token count: {e}")
                    input_tokens = 0
                    output_tokens = 0
                
                usage_monitor.log_usage(
                    provider="openai",
                    model=model,
                    input_tokens=int(input_tokens),
                    output_tokens=int(output_tokens)
                )
                
            except Exception as e:
                logger.warning(f"Failed to log LangChain token usage: {e}")
                
        
        # With newer LangChain versions, we need to access the content property
        return response.content.strip()
    
    raise ValueError(f"LangChain provider '{provider}' not supported")

def test_langchain_connection():
    """Test the LangChain connection to ensure it works."""
    print("Testing LangChain interface...")
    try:
        # Get API key from the API manager
        if not API_MANAGER_AVAILABLE or api_manager is None:
            print("API manager not available")
            return False
        
        try:
            if not api_manager.has_key("openai"):
                print("No API key found for openai in API manager")
                return False
                
            api_key = api_manager.get_key("openai")
        except Exception as e:
            print(f"Error accessing API manager: {e}")
            return False
        
        client = make_langchain_client("openai", api_key)
        response = langchain_enhanced_chat(
            "openai", 
            client, 
            "gpt-3.5-turbo", 
            [{"role": "user", "content": "Hello, are you working?"}],
            0.7
        )
        print(f"LangChain test response: {response}")
        return True
    except Exception as e:
        print(f"LangChain test failed: {e}")
        return False

if __name__ == "__main__":
    # Test when run directly
    print("Testing LangChain interface...")
    test_langchain_connection()
