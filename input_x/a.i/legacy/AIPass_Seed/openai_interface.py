import openai
import os
from config import get_openai_config
from usage_monitor import get_usage_monitor

# Get usage monitor instance
usage_monitor = get_usage_monitor()

def get_response(messages, model=None, temperature=None, token_contributions=None):
    # Load fresh config and client each time
    openai_config = get_openai_config()
    api_key = openai_config["api_key"]
    client = openai.Client(api_key=api_key)
    
    model = model or openai_config["model"]
    temperature = temperature if temperature is not None else openai_config["temperature"]

    # Send the chat completion request
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature
    )

    # Extract and log usage
    if usage_monitor and hasattr(response, "usage"):
        usage = response.usage
        input_tokens = usage.prompt_tokens
        output_tokens = usage.completion_tokens

        # Debug print
        print(f"[usage] input={input_tokens}  output={output_tokens}  total={input_tokens + output_tokens}")

        # Determine caller file/module for breakdown
        import inspect
        stack = inspect.stack()
        # Find first non-openai_interface frame
        caller = next((frame for frame in stack[1:] if not frame.filename.endswith('openai_interface.py')), None)
        caller_file = os.path.basename(caller.filename) if caller else 'unknown'
        breakdown = [{
            "file": caller_file,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens
        }]
        # Log usage live with breakdown
        usage_monitor.log_usage(
            provider="openai",
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            breakdown=breakdown,
            token_contributions=token_contributions
        )

    return response.choices[0].message.content.strip()
