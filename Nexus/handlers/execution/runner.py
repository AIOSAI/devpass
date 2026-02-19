#!/home/aipass/.venv/bin/python3
# -*- coding: utf-8 -*-
"""
META:
  app: Nexus
  layer: handlers
  purpose: Code extraction and execution orchestrator for Natural Flow
  status: Active

Code extraction and execution orchestrator for Nexus Natural Flow.

Parses code blocks out of LLM responses (various markdown formats),
executes them inside an ``ExecutionContext``, and returns structured
results.  This is the glue between the LLM's conversational output and
the persistent Python environment.

Rebuilt from v1 natural_flow.py extract_code_blocks / execute_code into
a standalone module for Nexus v2.
"""

import re
import sys
import logging
from pathlib import Path
from typing import Any, Dict, List

AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))

from handlers.execution.context import ExecutionContext

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Code extraction
# ---------------------------------------------------------------------------

def extract_code_blocks(text: str) -> List[str]:
    """Extract executable Python code blocks from an LLM response.

    Supports three formats (tried in priority order):

    1. Fenced ``python`` blocks  -- \\`\\`\\`python ... \\`\\`\\`
    2. Generic fenced blocks     -- \\`\\`\\` ... \\`\\`\\`  (only if no
       python blocks were found and content looks like Python)
    3. Inline single-line calls  -- bare ``Path(...)``, ``os.*(...)`` etc.

    Args:
        text: The full LLM response string.

    Returns:
        List of code strings ready for execution (may be empty).
    """
    blocks: List[str] = []

    # --- 1. ```python ... ``` ---
    python_pattern = r"```python\s*\n(.*?)\n```"
    python_matches = re.findall(python_pattern, text, re.DOTALL)
    blocks.extend(python_matches)

    # --- 2. ``` ... ``` (generic, only when no python blocks found) ---
    if not python_matches:
        generic_pattern = r"```\s*\n(.*?)\n```"
        generic_matches = re.findall(generic_pattern, text, re.DOTALL)
        python_indicators = (
            "Path(", "import ", "def ", "= ", "print(",
            "os.", "subprocess.", "json.", "for ", "if ",
            "with open",
        )
        for match in generic_matches:
            if any(ind in match for ind in python_indicators):
                blocks.append(match)

    # --- 3. Single-line operation calls ---
    if not blocks:
        single_pattern = (
            r"((?:Path|os|subprocess|json|re)"
            r"\([^)]*\)(?:\.[^(]*\([^)]*\))*)"
        )
        single_matches = re.findall(single_pattern, text)
        blocks.extend(single_matches)

    # Strip and deduplicate while preserving order
    seen: set = set()
    cleaned: List[str] = []
    for block in blocks:
        stripped = block.strip()
        if stripped and stripped not in seen:
            seen.add(stripped)
            cleaned.append(stripped)

    return cleaned


# ---------------------------------------------------------------------------
# Code execution
# ---------------------------------------------------------------------------

def run_code(code: str, context: ExecutionContext,
             timeout: int = 30) -> Dict[str, Any]:
    """Execute a single code block inside the given context.

    This is a thin convenience wrapper around
    ``ExecutionContext.execute()`` that adds logging.

    Args:
        code:    Python source to run.
        context: The persistent execution context.
        timeout: Max seconds before the block is killed (default 30).

    Returns:
        Result dict from ``ExecutionContext.execute()``.
    """
    logger.info("Executing code block (%d chars)", len(code))
    result = context.execute(code, timeout=timeout)

    if result["success"]:
        logger.info("Code block succeeded (output: %d chars)",
                     len(result.get("output", "")))
    else:
        logger.warning("Code block failed: %s", result.get("error", "unknown"))

    return result


# ---------------------------------------------------------------------------
# Full orchestration
# ---------------------------------------------------------------------------

def handle_execution_request(
    user_input: str,
    llm_response: str,
    context: ExecutionContext,
    timeout: int = 30,
    auto_execute: bool = True,
) -> Dict[str, Any]:
    """End-to-end pipeline: extract code from the LLM reply and run it.

    1. Extract code blocks from *llm_response*.
    2. If *auto_execute* is ``True``, run each block sequentially in
       *context*.
    3. Return a summary of what happened.

    Args:
        user_input:   The original user message (for logging / context).
        llm_response: The LLM's reply text that may contain code blocks.
        context:      The persistent execution context.
        timeout:      Max seconds per code block.
        auto_execute: If ``False``, extract but do not run (dry-run mode).

    Returns:
        Dict with keys:

        * ``blocks_found``  -- number of code blocks extracted.
        * ``blocks_executed`` -- number actually run.
        * ``results``       -- list of per-block result dicts.
        * ``all_success``   -- ``True`` if every executed block succeeded.
        * ``combined_output`` -- concatenated stdout from all blocks.
        * ``code_blocks``   -- the raw extracted code strings.
    """
    code_blocks = extract_code_blocks(llm_response)

    response: Dict[str, Any] = {
        "blocks_found": len(code_blocks),
        "blocks_executed": 0,
        "results": [],
        "all_success": True,
        "combined_output": "",
        "code_blocks": code_blocks,
    }

    if not code_blocks:
        logger.info("No code blocks found in LLM response for: %s",
                     user_input[:80])
        return response

    if not auto_execute:
        logger.info("Dry-run mode -- %d blocks extracted but not executed",
                     len(code_blocks))
        return response

    outputs: List[str] = []

    for idx, block in enumerate(code_blocks):
        logger.info("Running block %d/%d", idx + 1, len(code_blocks))
        result = run_code(block, context, timeout=timeout)
        response["results"].append(result)
        response["blocks_executed"] += 1

        if result["success"]:
            output = result.get("output", "")
            if output:
                outputs.append(output)
        else:
            response["all_success"] = False
            error = result.get("error", "unknown error")
            outputs.append(f"[Error in block {idx + 1}]: {error}")
            # Continue executing remaining blocks -- one failure should
            # not prevent the rest from running.

    response["combined_output"] = "\n".join(outputs).strip()
    return response
