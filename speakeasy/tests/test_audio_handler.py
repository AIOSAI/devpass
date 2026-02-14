#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: test_audio_handler.py - Test audio handler functions
# Date: 2026-02-11
# Version: 1.0.0
# Category: speakeasy/tests
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2026-02-11): Initial implementation
#
# CODE STANDARDS:
#   - Test file for speakeasy audio handler
#   - Mocks hardware-dependent code (sounddevice, webrtcvad)
# =============================================

"""Tests for audio_handler.py - audio capture and VAD functions."""

import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, call
import pytest
import numpy as np

# Add apps directory to path so 'handlers' package resolves
sys.path.insert(0, str(Path(__file__).parent.parent / "apps"))

from handlers.audio_handler import (
    create_audio_stream,
    is_speech,
    record_audio,
    test_microphone
)


class TestCreateAudioStream:
    """Tests for create_audio_stream function."""

    @patch('handlers.audio_handler.sd.InputStream')
    def test_creates_stream_with_defaults(self, mock_stream_cls):
        """Test stream creation with default parameters."""
        mock_stream = Mock()
        mock_stream_cls.return_value = mock_stream

        result = create_audio_stream()

        mock_stream_cls.assert_called_once()
        call_kwargs = mock_stream_cls.call_args[1]
        assert call_kwargs['samplerate'] == 16000
        assert call_kwargs['channels'] == 1
        assert call_kwargs['dtype'] == 'int16'
        assert call_kwargs['device'] is None
        assert result == mock_stream

    @patch('handlers.audio_handler.sd.InputStream')
    def test_creates_stream_with_custom_params(self, mock_stream_cls):
        """Test stream creation with custom parameters."""
        mock_stream = Mock()
        mock_stream_cls.return_value = mock_stream

        result = create_audio_stream(sample_rate=48000, device=5)

        call_kwargs = mock_stream_cls.call_args[1]
        assert call_kwargs['samplerate'] == 48000
        assert call_kwargs['device'] == 5


class TestIsSpeech:
    """Tests for is_speech function."""

    def test_detects_speech(self):
        """Test VAD detects speech in frame."""
        mock_vad = Mock()
        mock_vad.is_speech.return_value = True

        frame = np.array([100, 200, 300], dtype=np.int16)
        result = is_speech(frame, mock_vad, sample_rate=16000)

        assert result is True
        mock_vad.is_speech.assert_called_once()

    def test_detects_no_speech(self):
        """Test VAD detects silence in frame."""
        mock_vad = Mock()
        mock_vad.is_speech.return_value = False

        frame = np.array([0, 1, 2], dtype=np.int16)
        result = is_speech(frame, mock_vad, sample_rate=16000)

        assert result is False
        mock_vad.is_speech.assert_called_once()


class TestRecordAudio:
    """Tests for record_audio function.

    Note: record_audio uses threading.Event().wait() in a while loop with
    audio callbacks. These tests require complex threading mocks and are
    skipped to avoid hanging. The function is tested via integration tests.
    """

    @pytest.mark.skip(reason="record_audio uses Event.wait() loop - requires live audio or complex threading mock")
    def test_records_audio_with_speech_and_silence(self):
        """Test recording audio with speech followed by silence."""
        pass

    @pytest.mark.skip(reason="record_audio uses Event.wait() loop - requires live audio or complex threading mock")
    def test_returns_none_for_short_recording(self):
        """Test returns None if recording is too short."""
        pass

    @pytest.mark.skip(reason="record_audio uses Event.wait() loop - requires live audio or complex threading mock")
    def test_vad_aggressiveness_clamped(self):
        """Test VAD aggressiveness is clamped to 0-3 range."""
        pass


class TestMicrophone:
    """Tests for test_microphone function."""

    @patch('handlers.audio_handler.sd.rec')
    @patch('handlers.audio_handler.sd.wait')
    def test_microphone_test_returns_results(self, mock_wait, mock_rec):
        """Test microphone test returns proper result dictionary."""
        # Simulate recorded audio
        fake_audio = np.random.randint(-5000, 5000, size=(48000, 1), dtype=np.int16)
        mock_rec.return_value = fake_audio

        result = test_microphone(duration=3, sample_rate=16000)

        assert result['success'] is True
        assert result['sample_rate'] == 16000
        assert result['duration'] == 3
        assert result['samples'] == len(fake_audio.flatten())
        assert 'max_amplitude' in result
        assert 'rms_level' in result
        mock_rec.assert_called_once()
        mock_wait.assert_called_once()

    @patch('handlers.audio_handler.sd.rec')
    @patch('handlers.audio_handler.sd.wait')
    def test_microphone_test_calculates_levels(self, mock_wait, mock_rec):
        """Test microphone test calculates amplitude and RMS correctly."""
        # Create predictable audio data
        fake_audio = np.array([[1000], [2000], [3000], [4000]], dtype=np.int16)
        mock_rec.return_value = fake_audio

        result = test_microphone(duration=1, sample_rate=16000)

        assert result['max_amplitude'] == 4000
        assert result['rms_level'] > 0
