"""
Unit tests for speaker diarization service.
"""

import unittest
import tempfile
import wave
import struct
import math
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from transcription.diarization import (  # noqa: E402
    DiarizationService,
    DiarizationResult,
    DiarizedSegment,
    SCIPY_AVAILABLE,
)
from config.settings import DiarizationSettings  # noqa: E402


class TestDiarizedSegment(unittest.TestCase):
    """Test cases for DiarizedSegment dataclass."""

    def test_creation(self):
        seg = DiarizedSegment(speaker="Speaker 1", text="Hello", start=0.0, end=1.0)
        self.assertEqual(seg.speaker, "Speaker 1")
        self.assertEqual(seg.text, "Hello")
        self.assertEqual(seg.start, 0.0)
        self.assertEqual(seg.end, 1.0)


class TestDiarizationResult(unittest.TestCase):
    """Test cases for DiarizationResult."""

    def test_empty_result(self):
        result = DiarizationResult()
        self.assertEqual(result.segments, [])
        self.assertEqual(result.num_speakers, 0)
        self.assertEqual(result.to_labeled_text(), "")

    def test_single_speaker(self):
        result = DiarizationResult(
            segments=[
                DiarizedSegment("Speaker 1", "Hello world", 0.0, 2.0),
            ],
            num_speakers=1,
        )
        text = result.to_labeled_text()
        self.assertEqual(text, "Speaker 1: Hello world")

    def test_multiple_speakers(self):
        result = DiarizationResult(
            segments=[
                DiarizedSegment("Speaker 1", "Hello", 0.0, 1.0),
                DiarizedSegment("Speaker 2", "Hi there", 1.0, 2.0),
                DiarizedSegment("Speaker 1", "How are you?", 2.0, 3.0),
            ],
            num_speakers=2,
        )
        text = result.to_labeled_text()
        self.assertIn("Speaker 1: Hello", text)
        self.assertIn("Speaker 2: Hi there", text)
        self.assertIn("Speaker 1: How are you?", text)

    def test_consecutive_same_speaker_merged(self):
        """Consecutive segments from the same speaker should be merged."""
        result = DiarizationResult(
            segments=[
                DiarizedSegment("Speaker 1", "Hello", 0.0, 1.0),
                DiarizedSegment("Speaker 1", "world", 1.0, 2.0),
                DiarizedSegment("Speaker 2", "Hi", 2.0, 3.0),
            ],
            num_speakers=2,
        )
        text = result.to_labeled_text()
        # The first two segments should be merged
        self.assertIn("Speaker 1: Hello world", text)
        self.assertIn("Speaker 2: Hi", text)
        # Should only have 2 speaker lines
        lines = [line for line in text.split("\n") if line.strip()]
        self.assertEqual(len(lines), 2)


class TestDiarizationSettings(unittest.TestCase):
    """Test cases for DiarizationSettings configuration."""

    def test_default_settings(self):
        settings = DiarizationSettings()
        self.assertTrue(settings.enabled)
        self.assertEqual(settings.num_speakers, 0)
        self.assertEqual(settings.sensitivity, 0.5)

    def test_custom_settings(self):
        settings = DiarizationSettings(enabled=False, num_speakers=3, sensitivity=0.8)
        self.assertFalse(settings.enabled)
        self.assertEqual(settings.num_speakers, 3)
        self.assertEqual(settings.sensitivity, 0.8)

    def test_invalid_num_speakers(self):
        with self.assertRaises(ValueError):
            DiarizationSettings(num_speakers=10)

    def test_invalid_sensitivity(self):
        with self.assertRaises(ValueError):
            DiarizationSettings(sensitivity=1.5)


def _create_test_wav(filepath, duration_sec=3.0, sample_rate=16000, num_channels=1):
    """Create a simple test WAV file with a sine wave."""
    n_samples = int(duration_sec * sample_rate)

    with wave.open(str(filepath), "wb") as wf:
        wf.setnchannels(num_channels)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(sample_rate)

        for i in range(n_samples):
            # Generate a sine wave (varying frequency for different "speakers")
            if i < n_samples // 2:
                freq = 300  # Speaker 1 frequency
            else:
                freq = 600  # Speaker 2 frequency
            value = int(16000 * math.sin(2 * math.pi * freq * i / sample_rate))
            data = struct.pack("<h", max(-32768, min(32767, value)))
            if num_channels == 2:
                data = data + data  # duplicate for stereo
            wf.writeframes(data)


@unittest.skipUnless(SCIPY_AVAILABLE, "scipy not installed")
class TestDiarizationService(unittest.TestCase):
    """Test cases for DiarizationService."""

    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.test_wav = self.temp_dir / "test.wav"
        _create_test_wav(self.test_wav, duration_sec=3.0)

    def tearDown(self):
        import shutil
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_initialization(self):
        service = DiarizationService()
        self.assertEqual(service.num_speakers, 0)
        self.assertEqual(service.sensitivity, 0.5)

    def test_initialization_with_params(self):
        service = DiarizationService(num_speakers=3, sensitivity=0.8)
        self.assertEqual(service.num_speakers, 3)
        self.assertEqual(service.sensitivity, 0.8)

    def test_sensitivity_clamped(self):
        service = DiarizationService(sensitivity=2.0)
        self.assertEqual(service.sensitivity, 1.0)

        service2 = DiarizationService(sensitivity=-0.5)
        self.assertEqual(service2.sensitivity, 0.0)

    def test_diarize_with_word_timestamps(self):
        """Test diarization with provided word timestamps."""
        service = DiarizationService(num_speakers=2)

        word_timestamps = [
            {"word": "Hello", "start": 0.0, "end": 0.5},
            {"word": "world", "start": 0.5, "end": 1.0},
            {"word": "How", "start": 1.0, "end": 1.3},
            {"word": "are", "start": 1.3, "end": 1.5},
            {"word": "you", "start": 1.5, "end": 2.0},
            {"word": "doing", "start": 2.0, "end": 2.5},
            {"word": "today", "start": 2.5, "end": 3.0},
        ]

        result = service.diarize(self.test_wav, word_timestamps)

        self.assertIsNotNone(result)
        self.assertIsInstance(result, DiarizationResult)
        self.assertGreater(len(result.segments), 0)
        self.assertGreaterEqual(result.num_speakers, 1)

        # Check that labeled text is formatted properly
        labeled = result.to_labeled_text()
        self.assertIn("Speaker", labeled)
        self.assertIn(":", labeled)

    def test_diarize_without_timestamps(self):
        """Test diarization without word timestamps (uses uniform segments)."""
        service = DiarizationService(num_speakers=2)
        result = service.diarize(self.test_wav)

        self.assertIsNotNone(result)
        self.assertIsInstance(result, DiarizationResult)

    def test_diarize_nonexistent_file(self):
        """Test diarization with non-existent file returns None."""
        service = DiarizationService()
        result = service.diarize(Path("/nonexistent/file.wav"))
        self.assertIsNone(result)

    def test_diarize_stereo_audio(self):
        """Test diarization handles stereo audio."""
        stereo_wav = self.temp_dir / "stereo.wav"
        _create_test_wav(stereo_wav, duration_sec=2.0, num_channels=2)

        service = DiarizationService(num_speakers=2)
        result = service.diarize(stereo_wav)
        self.assertIsNotNone(result)

    def test_diarize_returns_labeled_text(self):
        """Test that diarization result can be formatted as labeled text."""
        service = DiarizationService(num_speakers=2)

        word_timestamps = [
            {"word": "Hello", "start": 0.0, "end": 0.5},
            {"word": "Hi", "start": 1.5, "end": 2.0},
            {"word": "there", "start": 2.0, "end": 2.5},
        ]

        result = service.diarize(self.test_wav, word_timestamps)
        self.assertIsNotNone(result)

        labeled = result.to_labeled_text()
        self.assertIsInstance(labeled, str)
        self.assertGreater(len(labeled), 0)

    def test_single_word_input(self):
        """Test with very few words — should return single speaker."""
        service = DiarizationService()
        word_timestamps = [
            {"word": "Hello", "start": 0.0, "end": 0.5},
        ]
        result = service.diarize(self.test_wav, word_timestamps)
        self.assertIsNotNone(result)
        self.assertEqual(result.num_speakers, 1)


class TestWhisperDiarizationIntegration(unittest.TestCase):
    """Test WhisperService.transcribe_with_diarization integration."""

    @patch('transcription.whisper_service.openai.OpenAI')
    def test_transcribe_with_diarization_disabled(self, mock_openai):
        """Test that diarization is skipped when disabled in settings."""
        from transcription.whisper_service import WhisperService

        mock_settings = MagicMock()
        mock_settings.settings.transcription.service = "openai"
        mock_settings.settings.diarization = DiarizationSettings(enabled=False)
        mock_settings.has_openai_api_key.return_value = True

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            service = WhisperService(mock_settings)

        # Mock transcribe_audio to avoid file I/O
        service.transcribe_audio = MagicMock(return_value="Test transcription")

        result = service.transcribe_with_diarization(Path("test.wav"))

        self.assertEqual(result["transcription"], "Test transcription")
        self.assertIsNone(result["diarized_transcription"])

    def test_fallback_on_diarization_failure(self):
        """Test graceful fallback when diarization fails."""
        from transcription.whisper_service import WhisperService

        mock_settings = MagicMock()
        mock_settings.settings.transcription.service = "openai"
        mock_settings.settings.diarization = DiarizationSettings(enabled=True)
        mock_settings.has_openai_api_key.return_value = True

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            with patch('transcription.whisper_service.openai.OpenAI'):
                service = WhisperService(mock_settings)

        # Mock transcribe_audio to return text
        service.transcribe_audio = MagicMock(return_value="Test transcription")
        # Mock transcribe_with_timestamps to raise exception
        service.transcribe_with_timestamps = MagicMock(side_effect=Exception("fail"))

        result = service.transcribe_with_diarization(Path("test.wav"))

        self.assertEqual(result["transcription"], "Test transcription")
        self.assertIsNone(result["diarized_transcription"])


class TestExtractWordTimestamps(unittest.TestCase):
    """Test _extract_word_timestamps helper."""

    def setUp(self):
        mock_settings = MagicMock()
        mock_settings.settings.transcription.service = "openai"
        mock_settings.settings.diarization = DiarizationSettings()
        mock_settings.has_openai_api_key.return_value = True

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            with patch('transcription.whisper_service.openai.OpenAI'):
                from transcription.whisper_service import WhisperService
                self.service = WhisperService(mock_settings)

    def test_extract_from_api_format(self):
        """Test extracting timestamps from OpenAI API format."""
        mock_result = MagicMock()
        word1 = MagicMock()
        word1.word = "Hello"
        word1.start = 0.0
        word1.end = 0.5
        word2 = MagicMock()
        word2.word = "world"
        word2.start = 0.5
        word2.end = 1.0
        mock_result.words = [word1, word2]

        words = self.service._extract_word_timestamps(mock_result)
        self.assertIsNotNone(words)
        self.assertEqual(len(words), 2)
        self.assertEqual(words[0]["word"], "Hello")
        self.assertEqual(words[1]["word"], "world")

    def test_extract_from_local_format(self):
        """Test extracting timestamps from local Whisper format."""
        local_result = {
            "segments": [
                {
                    "text": "Hello world",
                    "start": 0.0,
                    "end": 1.0,
                    "words": [
                        {"word": "Hello", "start": 0.0, "end": 0.5},
                        {"word": "world", "start": 0.5, "end": 1.0},
                    ],
                }
            ]
        }

        words = self.service._extract_word_timestamps(local_result)
        self.assertIsNotNone(words)
        self.assertEqual(len(words), 2)

    def test_extract_from_none(self):
        """Test extracting timestamps from None returns None."""
        result = self.service._extract_word_timestamps(None)
        self.assertIsNone(result)

    def test_extract_segment_level_fallback(self):
        """Test fallback to segment-level when no word timestamps."""
        local_result = {
            "segments": [
                {"text": "Hello world", "start": 0.0, "end": 1.0},
                {"text": "How are you", "start": 1.0, "end": 2.0},
            ]
        }

        words = self.service._extract_word_timestamps(local_result)
        self.assertIsNotNone(words)
        self.assertEqual(len(words), 2)
        self.assertEqual(words[0]["word"], "Hello world")


if __name__ == '__main__':
    unittest.main()
