#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: transcription_handler.py - Whisper transcription handler
# Date: 2026-02-11
# Version: 1.0.0
# Category: speakeasy/handlers
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2026-02-11): Initial implementation
#
# CODE STANDARDS:
#   - Handlers implement logic, modules orchestrate
#   - Pure functions, no classes, no Prax imports
# =============================================

"""
Whisper transcription handler using faster-whisper.

Provides pure functions for audio transcription and post-processing.
Based on whisper-writer/src/transcription.py patterns.
"""

import gc
import numpy as np
from faster_whisper import WhisperModel


def create_whisper_model(model_name="base.en", device="auto", compute_type="default"):
    """
    Create and return a faster-whisper model instance.

    Args:
        model_name: Model size ("tiny", "base", "small", "medium", "large", etc.)
                   Can also be a path to a local model directory.
        device: Device to use ("cpu", "cuda", "auto")
        compute_type: Computation type ("default", "int8", "float16", "int8_float16")

    Returns:
        WhisperModel: Initialized faster-whisper model

    Raises:
        Exception: If model initialization fails

    Notes:
        - "auto" device will use CUDA if available, otherwise CPU
        - int8 compute type forces CPU usage
        - Model is downloaded automatically if not found locally
    """
    # Handle int8 compute type - must use CPU
    if compute_type == "int8":
        device = "cpu"

    # Handle auto device selection
    if device == "auto":
        try:
            import torch
            device = "cuda" if torch.cuda.is_available() else "cpu"
        except ImportError:
            device = "cpu"

    try:
        model = WhisperModel(
            model_name,
            device=device,
            compute_type=compute_type
        )
        return model
    except Exception as e:
        # Fallback to CPU if GPU initialization fails
        if device != "cpu":
            model = WhisperModel(
                model_name,
                device="cpu",
                compute_type=compute_type
            )
            return model
        else:
            raise e


def transcribe_audio(audio_data, model, language="en", temperature=0.0,
                     vad_filter=True, initial_prompt=None,
                     condition_on_previous_text=True):
    """
    Transcribe audio data using a faster-whisper model.

    Args:
        audio_data: numpy int16 array containing audio samples
        model: WhisperModel instance created by create_whisper_model()
        language: Language code (e.g., "en", "es", "fr")
        temperature: Sampling temperature (0.0 = deterministic)
        vad_filter: Enable VAD filtering to remove silence
        initial_prompt: Optional prompt to guide transcription style
        condition_on_previous_text: Use previous text as context

    Returns:
        str: Transcribed text

    Raises:
        Exception: If transcription fails

    Notes:
        - Converts int16 to float32 internally
        - Includes garbage collection to mitigate Whisper memory leak
        - VAD filter helps improve accuracy by removing silence
    """
    # Convert int16 to float32 normalized to [-1.0, 1.0]
    audio_data_float = audio_data.astype(np.float32) / 32768.0

    # Transcribe
    segments, info = model.transcribe(
        audio=audio_data_float,
        language=language,
        initial_prompt=initial_prompt,
        condition_on_previous_text=condition_on_previous_text,
        temperature=temperature,
        vad_filter=vad_filter
    )

    # Concatenate all segment texts
    result = ''.join([segment.text for segment in segments])

    # Force garbage collection to mitigate Whisper memory leak
    # See: https://github.com/openai/whisper/discussions/605
    gc.collect()

    return result


def post_process_text(text, remove_trailing_period=False,
                      add_trailing_space=True, remove_capitalization=False):
    """
    Apply post-processing transformations to transcribed text.

    Args:
        text: Transcribed text to process
        remove_trailing_period: Remove trailing period if present
        add_trailing_space: Add trailing space for inline typing
        remove_capitalization: Convert to lowercase

    Returns:
        str: Post-processed text

    Notes:
        - Processing order: strip → remove period → add space → lowercase
        - Useful for inline text insertion workflows
    """
    # Strip whitespace
    text = text.strip()

    # Remove trailing period
    if remove_trailing_period and text.endswith('.'):
        text = text[:-1]

    # Add trailing space
    if add_trailing_space:
        text += ' '

    # Remove capitalization
    if remove_capitalization:
        text = text.lower()

    return text
