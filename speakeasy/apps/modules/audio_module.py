#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: audio_module.py - Audio recording and transcription orchestration
# Date: 2026-02-11
# Version: 1.1.0
# Category: speakeasy/modules
#
# CHANGELOG (Max 5 entries):
#   - v1.1.0 (2026-02-11): Fixed imports, thin orchestration, model caching
#   - v1.0.0 (2026-02-11): Initial implementation
#
# CODE STANDARDS:
#   - Handlers implement logic, modules orchestrate
#   - Modules use Prax logger for logging
# =============================================

"""
Audio module - orchestrates recording and transcription pipeline.

Coordinates between audio_handler and transcription_handler to provide
a complete voice-to-text workflow.
"""

import sys
import time
from pathlib import Path

AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))

from prax.apps.modules.logger import system_logger as logger

# Import handlers
sys.path.insert(0, str(Path(__file__).parent.parent))
from handlers import audio_handler
from handlers import transcription_handler

# Module-level model cache
WHISPER_MODEL = None


def handle_command(command, args) -> bool:
    """Command handler for auto-discovery by speakeasy.py.

    Args:
        command: Command string ("record", "transcribe", "test-audio")
        args: Dictionary of arguments

    Returns:
        bool: True if command handled, False otherwise
    """
    global WHISPER_MODEL

    if command in ("record", "transcribe"):
        config = args or {}
        sample_rate = config.get('sample_rate', 16000)

        logger.info("Recording audio...")
        start_time = time.time()
        audio_data = audio_handler.record_audio(
            sample_rate=sample_rate,
            silence_duration=config.get('silence_duration', 900),
            vad_aggressiveness=config.get('vad_aggressiveness', 2),
            min_duration=config.get('min_duration', 100),
            device=config.get('device', None)
        )

        if audio_data is None:
            logger.warning("Recording discarded (too short)")
            return True

        duration = len(audio_data) / sample_rate
        logger.info(f"Recording complete: {duration:.2f}s audio, {time.time() - start_time:.2f}s elapsed")

        if WHISPER_MODEL is None:
            model_name = config.get('model_name', 'base.en')
            logger.info(f"Creating Whisper model: {model_name}")
            WHISPER_MODEL = transcription_handler.create_whisper_model(
                model_name=model_name,
                device=config.get('model_device', 'auto'),
                compute_type=config.get('compute_type', 'default')
            )
            logger.info("Whisper model ready")

        logger.info("Transcribing...")
        start_time = time.time()
        transcription = transcription_handler.transcribe_audio(
            audio_data=audio_data,
            model=WHISPER_MODEL,
            language=config.get('language', 'en'),
            temperature=config.get('temperature', 0.0),
            vad_filter=config.get('vad_filter', True),
            initial_prompt=config.get('initial_prompt', None)
        )
        logger.info(f"Transcription complete in {time.time() - start_time:.2f}s: '{transcription.strip()}'")

        transcription_handler.post_process_text(
            text=transcription,
            remove_trailing_period=config.get('remove_trailing_period', False),
            add_trailing_space=config.get('add_trailing_space', True),
            remove_capitalization=config.get('remove_capitalization', False)
        )
        return True

    elif command == "test-audio":
        duration = args.get('duration', 3) if args else 3
        logger.info(f"Testing microphone for {duration} seconds...")
        result = audio_handler.test_microphone(duration=duration)
        logger.info(f"Test complete - Max amplitude: {result.get('max_amplitude')}, RMS: {result.get('rms_level', 0):.2f}")
        return True

    else:
        return False
