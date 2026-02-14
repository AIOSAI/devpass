#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: test_transcription_handler.py - Test transcription handler functions
# Date: 2026-02-11
# Version: 1.0.0
# Category: speakeasy/tests
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2026-02-11): Initial implementation
#
# CODE STANDARDS:
#   - Test file for speakeasy transcription handler
#   - Mocks faster-whisper library
# =============================================

"""Tests for transcription_handler.py - Whisper transcription functions."""

import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest
import numpy as np

# Add apps directory to path so 'handlers' package resolves
sys.path.insert(0, str(Path(__file__).parent.parent / "apps"))

from handlers.transcription_handler import (
    create_whisper_model,
    transcribe_audio,
    post_process_text
)


class TestCreateWhisperModel:
    """Tests for create_whisper_model function."""

    @patch('handlers.transcription_handler.WhisperModel')
    def test_creates_model_with_defaults(self, mock_whisper_cls):
        """Test model creation with default parameters."""
        mock_model = Mock()
        mock_whisper_cls.return_value = mock_model

        result = create_whisper_model()

        mock_whisper_cls.assert_called_once()
        args = mock_whisper_cls.call_args[0]
        assert args[0] == "base.en"

    @patch('handlers.transcription_handler.WhisperModel')
    def test_creates_model_with_custom_params(self, mock_whisper_cls):
        """Test model creation with custom parameters."""
        mock_model = Mock()
        mock_whisper_cls.return_value = mock_model

        result = create_whisper_model(
            model_name="small.en",
            device="cpu",
            compute_type="int8"
        )

        args = mock_whisper_cls.call_args[0]
        assert args[0] == "small.en"

    @patch('handlers.transcription_handler.WhisperModel')
    def test_int8_forces_cpu(self, mock_whisper_cls):
        """Test int8 compute type forces CPU device."""
        mock_model = Mock()
        mock_whisper_cls.return_value = mock_model

        create_whisper_model(device="cuda", compute_type="int8")

        # Should use cpu due to int8
        kwargs = mock_whisper_cls.call_args[1]
        assert kwargs['device'] == "cpu"

    @patch('handlers.transcription_handler.WhisperModel')
    def test_auto_device_selects_cuda(self, mock_whisper_cls):
        """Test auto device selection chooses CUDA when available."""
        # Mock torch module before it's imported
        with patch.dict('sys.modules', {'torch': MagicMock()}):
            import sys
            mock_torch = sys.modules['torch']
            mock_torch.cuda.is_available.return_value = True
            mock_model = Mock()
            mock_whisper_cls.return_value = mock_model

            create_whisper_model(device="auto")

            kwargs = mock_whisper_cls.call_args[1]
            assert kwargs['device'] == "cuda"

    @patch('handlers.transcription_handler.WhisperModel')
    def test_auto_device_fallback_cpu(self, mock_whisper_cls):
        """Test auto device selection falls back to CPU."""
        # Mock torch module before it's imported
        with patch.dict('sys.modules', {'torch': MagicMock()}):
            import sys
            mock_torch = sys.modules['torch']
            mock_torch.cuda.is_available.return_value = False
            mock_model = Mock()
            mock_whisper_cls.return_value = mock_model

            create_whisper_model(device="auto")

            kwargs = mock_whisper_cls.call_args[1]
            assert kwargs['device'] == "cpu"

    @patch('handlers.transcription_handler.WhisperModel')
    def test_fallback_to_cpu_on_gpu_failure(self, mock_whisper_cls):
        """Test fallback to CPU if GPU initialization fails."""
        # First call with CUDA fails, second call with CPU succeeds
        mock_model = Mock()
        mock_whisper_cls.side_effect = [Exception("CUDA error"), mock_model]

        result = create_whisper_model(device="cuda")

        # Should retry with CPU
        assert mock_whisper_cls.call_count == 2
        assert result == mock_model


class TestTranscribeAudio:
    """Tests for transcribe_audio function."""

    def test_transcribes_audio_successfully(self):
        """Test successful audio transcription."""
        # Mock model
        mock_model = Mock()

        # Mock segments
        segment1 = Mock()
        segment1.text = "Hello "
        segment2 = Mock()
        segment2.text = "world"

        mock_info = Mock()
        mock_model.transcribe.return_value = ([segment1, segment2], mock_info)

        # Create fake audio data
        audio_data = np.array([100, 200, 300], dtype=np.int16)

        result = transcribe_audio(audio_data, mock_model)

        assert result == "Hello world"
        mock_model.transcribe.assert_called_once()

    def test_converts_int16_to_float32(self):
        """Test audio data is converted from int16 to float32."""
        mock_model = Mock()
        mock_segment = Mock()
        mock_segment.text = "test"
        mock_info = Mock()
        mock_model.transcribe.return_value = ([mock_segment], mock_info)

        # Use values within int16 range: -32768 to 32767
        audio_data = np.array([16384, -16384, 0], dtype=np.int16)

        transcribe_audio(audio_data, mock_model)

        # Check that transcribe was called with float32 data normalized to [-1, 1]
        call_kwargs = mock_model.transcribe.call_args[1]
        audio_arg = call_kwargs['audio']
        assert audio_arg.dtype == np.float32
        assert np.max(np.abs(audio_arg)) <= 1.0

    def test_passes_config_parameters(self):
        """Test configuration parameters are passed to model."""
        mock_model = Mock()
        mock_segment = Mock()
        mock_segment.text = "test"
        mock_info = Mock()
        mock_model.transcribe.return_value = ([mock_segment], mock_info)

        audio_data = np.array([100, 200], dtype=np.int16)

        transcribe_audio(
            audio_data,
            mock_model,
            language="es",
            temperature=0.5,
            vad_filter=False,
            initial_prompt="Test prompt"
        )

        call_kwargs = mock_model.transcribe.call_args[1]
        assert call_kwargs['language'] == "es"
        assert call_kwargs['temperature'] == 0.5
        assert call_kwargs['vad_filter'] is False
        assert call_kwargs['initial_prompt'] == "Test prompt"

    def test_concatenates_multiple_segments(self):
        """Test multiple segments are concatenated correctly."""
        mock_model = Mock()

        segments = []
        for text in ["The ", "quick ", "brown ", "fox"]:
            seg = Mock()
            seg.text = text
            segments.append(seg)

        mock_info = Mock()
        mock_model.transcribe.return_value = (segments, mock_info)

        audio_data = np.array([100], dtype=np.int16)
        result = transcribe_audio(audio_data, mock_model)

        assert result == "The quick brown fox"

    def test_empty_segments_return_empty_string(self):
        """Test empty segment list returns empty string."""
        mock_model = Mock()
        mock_info = Mock()
        mock_model.transcribe.return_value = ([], mock_info)

        audio_data = np.array([100], dtype=np.int16)
        result = transcribe_audio(audio_data, mock_model)

        assert result == ""


class TestPostProcessText:
    """Tests for post_process_text function."""

    def test_strips_whitespace(self):
        """Test whitespace is stripped from text."""
        result = post_process_text("  hello world  ", add_trailing_space=False)
        assert result == "hello world"

    def test_removes_trailing_period(self):
        """Test trailing period is removed when enabled."""
        result = post_process_text(
            "Hello world.",
            remove_trailing_period=True,
            add_trailing_space=False
        )
        assert result == "Hello world"

    def test_keeps_trailing_period_when_disabled(self):
        """Test trailing period is kept when option disabled."""
        result = post_process_text(
            "Hello world.",
            remove_trailing_period=False,
            add_trailing_space=False
        )
        assert result == "Hello world."

    def test_adds_trailing_space(self):
        """Test trailing space is added when enabled."""
        result = post_process_text("hello", add_trailing_space=True)
        assert result == "hello "

    def test_no_trailing_space_when_disabled(self):
        """Test no trailing space when disabled."""
        result = post_process_text("hello", add_trailing_space=False)
        assert result == "hello"

    def test_removes_capitalization(self):
        """Test capitalization is removed when enabled."""
        result = post_process_text(
            "Hello World",
            remove_capitalization=True,
            add_trailing_space=False
        )
        assert result == "hello world"

    def test_keeps_capitalization_when_disabled(self):
        """Test capitalization is kept when disabled."""
        result = post_process_text(
            "Hello World",
            remove_capitalization=False,
            add_trailing_space=False
        )
        assert result == "Hello World"

    def test_processing_order(self):
        """Test processing happens in correct order: strip, period, space, lowercase."""
        result = post_process_text(
            "  Hello World.  ",
            remove_trailing_period=True,
            add_trailing_space=True,
            remove_capitalization=True
        )
        assert result == "hello world "

    def test_all_defaults(self):
        """Test with default parameters."""
        result = post_process_text("Hello world")
        # Default: strip, no period removal, add space, no lowercase
        assert result == "Hello world "

    def test_only_period_no_removal(self):
        """Test period in middle of text is not removed."""
        result = post_process_text(
            "Hello. World.",
            remove_trailing_period=True,
            add_trailing_space=False
        )
        assert result == "Hello. World"
