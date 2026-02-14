#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: audio_handler.py - Audio capture and VAD handler
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
Audio capture and Voice Activity Detection (VAD) handler.

Provides pure functions for audio recording with WebRTC VAD.
Based on whisper-writer/src/result_thread.py patterns.
"""

import time
import numpy as np
import sounddevice as sd
import webrtcvad
from collections import deque
from threading import Event


def create_audio_stream(sample_rate=16000, device=None):
    """
    Create and return a sounddevice InputStream.

    Args:
        sample_rate: Audio sample rate in Hz (default: 16000)
        device: Audio device index or name (None for default)

    Returns:
        sounddevice.InputStream object

    Raises:
        Exception: If stream creation fails
    """
    frame_duration_ms = 30  # 30ms frame duration for WebRTC VAD
    frame_size = int(sample_rate * (frame_duration_ms / 1000.0))

    stream = sd.InputStream(
        samplerate=sample_rate,
        channels=1,
        dtype='int16',
        blocksize=frame_size,
        device=device
    )

    return stream


def is_speech(frame, vad, sample_rate=16000):
    """
    Check if a single audio frame contains speech using WebRTC VAD.

    Args:
        frame: numpy int16 array containing audio frame
        vad: webrtcvad.Vad object
        sample_rate: Audio sample rate in Hz (default: 16000)

    Returns:
        bool: True if speech detected, False otherwise
    """
    return vad.is_speech(frame.tobytes(), sample_rate)


def record_audio(sample_rate=16000, silence_duration=900, vad_aggressiveness=2,
                 min_duration=100, device=None, initial_skip_ms=150,
                 energy_threshold=0, stop_event=None,
                 recording_mode="press_to_toggle"):
    """
    Record audio with mode-dependent stop behavior.

    Recording modes:
        - press_to_toggle / hold_to_record: Records until stop_event is set
          (user presses hotkey again or releases key). No VAD auto-stop.
        - voice_activity_detection / continuous: Uses WebRTC VAD to auto-stop
          after detecting speech followed by silence.

    Args:
        sample_rate: Audio sample rate in Hz (default: 16000)
        silence_duration: Duration of silence in ms to stop recording (default: 900)
        vad_aggressiveness: VAD aggressiveness level 0-3 (default: 2)
        min_duration: Minimum recording duration in ms (default: 100)
        device: Audio device index or name (None for default)
        initial_skip_ms: Initial frames to skip to avoid activation sound (default: 150)
        energy_threshold: Energy threshold for noise gating (default: 0=disabled)
        stop_event: threading.Event to signal recording should stop (default: None)
        recording_mode: Recording mode (default: "press_to_toggle")

    Returns:
        numpy.ndarray: int16 audio data, or None if recording too short
    """
    frame_duration_ms = 30  # 30ms frame duration for WebRTC VAD
    frame_size = int(sample_rate * (frame_duration_ms / 1000.0))
    silence_frames = int(silence_duration / frame_duration_ms)

    # Calculate initial frames to skip
    initial_frames_to_skip = int((initial_skip_ms / 1000.0) * sample_rate / frame_size)

    # Create VAD only for modes that use it (matches old WhisperWriter behavior)
    vad = None
    speech_detected = False
    silent_frame_count = 0
    if recording_mode in ('voice_activity_detection', 'continuous'):
        vad_aggressiveness = max(0, min(3, vad_aggressiveness))
        vad = webrtcvad.Vad(vad_aggressiveness)

    # Audio buffer and recording storage
    audio_buffer = deque(maxlen=frame_size)
    recording = []

    # Event for signaling data ready
    data_ready = Event()

    def audio_callback(indata, frames, time_info, status):
        """Callback for audio stream - called for each audio block."""
        if status:
            pass
        audio_buffer.extend(indata[:, 0])
        data_ready.set()

    # Record audio
    with sd.InputStream(samplerate=sample_rate, channels=1, dtype='int16',
                        blocksize=frame_size, device=device,
                        callback=audio_callback):
        # Clear any stale data from previous recording session
        time.sleep(0.05)
        audio_buffer.clear()
        data_ready.clear()

        while True:
            if stop_event and stop_event.is_set():
                break
            data_ready.wait(timeout=0.1)
            data_ready.clear()

            if len(audio_buffer) < frame_size:
                continue

            # Extract frame
            frame = np.array(list(audio_buffer), dtype=np.int16)
            audio_buffer.clear()
            recording.extend(frame)

            # Skip initial frames to avoid activation key sound
            if initial_frames_to_skip > 0:
                initial_frames_to_skip -= 1
                continue

            # VAD auto-stop only for vad/continuous modes
            if vad:
                passes_energy_check = True
                if energy_threshold > 0:
                    frame_energy = np.sqrt(np.mean(frame.astype(np.float32) ** 2))
                    passes_energy_check = frame_energy >= energy_threshold

                if passes_energy_check:
                    if vad.is_speech(frame.tobytes(), sample_rate):
                        silent_frame_count = 0
                        if not speech_detected:
                            speech_detected = True
                    else:
                        silent_frame_count += 1
                else:
                    silent_frame_count += 1

                if speech_detected and silent_frame_count > silence_frames:
                    break
            # For press_to_toggle/hold_to_record: loop continues until stop_event

    # Convert to numpy array
    audio_data = np.array(recording, dtype=np.int16)
    duration = len(audio_data) / sample_rate

    # Check minimum duration
    if (duration * 1000) < min_duration:
        return None

    return audio_data


def test_microphone(duration=3, sample_rate=16000):
    """
    Test microphone by recording and analyzing audio levels.

    Args:
        duration: Duration to record in seconds (default: 3)
        sample_rate: Audio sample rate in Hz (default: 16000)

    Returns:
        dict: Test results with keys:
            - success: bool
            - sample_rate: int
            - duration: float
            - samples: int
            - max_amplitude: int
            - rms_level: float
    """
    recording = sd.rec(
        int(duration * sample_rate),
        samplerate=sample_rate,
        channels=1,
        dtype='int16'
    )
    sd.wait()

    audio_data = recording.flatten()
    max_amplitude = np.max(np.abs(audio_data))
    rms_level = np.sqrt(np.mean(audio_data.astype(np.float32) ** 2))

    return {
        'success': True,
        'sample_rate': sample_rate,
        'duration': duration,
        'samples': len(audio_data),
        'max_amplitude': int(max_amplitude),
        'rms_level': float(rms_level)
    }
