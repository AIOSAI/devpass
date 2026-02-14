import sys
from pathlib import Path
from typing import Dict, Any
import logging

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
except Exception as e:
    print(f"[WARN] Usage monitoring unavailable: {e}")
    usage_monitor = None
    USAGE_MONITORING_ENABLED = False

logger = logging.getLogger("nexus")

ACTIVE_PROVIDER = None
STRICT_MODE = False


# --- Provider imports ---
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    OpenAI = None

def make_client(provider: str, api_key: str):
    """Return an SDK client for the given provider."""
    if provider == "openai":
        if not OPENAI_AVAILABLE:
            raise ValueError("OpenAI SDK not available")
        if OpenAI is None:
            raise ValueError("OpenAI SDK not properly initialized")
        return OpenAI(api_key=api_key)
    if provider == "anthropic":
        try:
            import anthropic
        except ImportError as e:
            raise NotImplementedError("Anthropic SDK not installed") from e
        return anthropic.Anthropic(api_key=api_key)
    if provider == "mistral":
        try:
            from mistralai.client import MistralClient
        except ImportError as e:
            raise NotImplementedError("Mistral SDK not installed") from e
        return MistralClient(api_key=api_key)
    if provider == "gemini":
        try:
            import google.generativeai as genai
        except ImportError as e:
            raise NotImplementedError("Gemini SDK not installed") from e
        # Configure API key - add type ignore to suppress IDE error
        genai.configure(api_key=api_key)  # type: ignore
        return genai
    raise ValueError(f"Unknown provider {provider}")


def chat(provider: str, client, model: str, messages: list, temperature: float) -> str:
    """Send a chat completion request."""
    if STRICT_MODE:
        assert provider == ACTIVE_PROVIDER

    if provider == "openai":
        resp = client.chat.completions.create(model=model, messages=messages, temperature=temperature)
        
        # Log token usage automatically
        if USAGE_MONITORING_ENABLED and usage_monitor and hasattr(resp, 'usage'):
            try:
                usage_monitor.log_usage(
                    provider="openai",
                    model=model,
                    input_tokens=resp.usage.prompt_tokens,
                    output_tokens=resp.usage.completion_tokens
                )
            except Exception as e:
                logger.warning(f"Failed to log token usage: {e}")
        
        return resp.choices[0].message.content.strip()
        
    if provider == "anthropic":
        resp = client.messages.create(
            model=model, 
            messages=messages, 
            temperature=temperature,
            max_tokens=4096
        )
        return resp.content[0].text
    if provider == "mistral":
        resp = client.chat(model=model, messages=messages, temperature=temperature)
        return resp["choices"][0]["message"]["content"]
    if provider == "gemini":
        mdl = client.GenerativeModel(model)
        sess = mdl.start_chat(history=messages[:-1])
        reply = sess.send_message(messages[-1]["content"])
        return reply.text
    raise ValueError(f"Unknown provider {provider}")

