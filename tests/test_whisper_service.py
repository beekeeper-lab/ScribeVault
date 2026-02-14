"""
Unit tests for WhisperService class.
"""

import unittest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from transcription.whisper_service import WhisperService, TranscriptionException
from config.settings import SettingsManager


class TestWhisperService(unittest.TestCase):
    """Test cases for WhisperService class."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())

        # Mock settings manager
        self.mock_settings = MagicMock()
        self.mock_settings.get_openai_api_key.return_value = "test-api-key"
        self.mock_settings.has_openai_api_key.return_value = True

        # Build a fake settings.transcription object
        mock_transcription = MagicMock()
        mock_transcription.service = "local"
        mock_transcription.local_model = "base"
        mock_transcription.device = "auto"
        mock_transcription.language = "auto"
        self.mock_settings.settings.transcription = mock_transcription

        # Diarization settings
        mock_diarization = MagicMock()
        mock_diarization.enabled = False
        self.mock_settings.settings.diarization = mock_diarization

    def tearDown(self):
        """Clean up test fixtures."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    @patch('transcription.whisper_service.whisper')
    @patch('transcription.whisper_service.LOCAL_WHISPER_AVAILABLE', True)
    def test_initialization(self, mock_whisper):
        """Test WhisperService initialization."""
        mock_whisper.load_model.return_value = MagicMock()
        service = WhisperService(self.mock_settings)
        self.assertEqual(service.settings_manager, self.mock_settings)

    @patch('transcription.whisper_service.whisper')
    @patch('transcription.whisper_service.LOCAL_WHISPER_AVAILABLE', True)
    def test_initialization_no_api_key(self, mock_whisper):
        """Test initialization without API key defaults to local."""
        self.mock_settings.has_openai_api_key.return_value = False
        self.mock_settings.settings.transcription.service = "openai"
        mock_whisper.load_model.return_value = MagicMock()

        service = WhisperService(self.mock_settings)
        self.assertTrue(service.use_local)

    @patch('transcription.whisper_service.openai.OpenAI')
    def test_transcribe_audio_openai_success(self, mock_openai_client):
        """Test successful OpenAI transcription."""
        self.mock_settings.settings.transcription.service = "openai"

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            mock_client = MagicMock()
            mock_openai_client.return_value = mock_client

            service = WhisperService(self.mock_settings)

            test_audio = self.temp_dir / "test.wav"
            test_audio.write_bytes(b"fake audio data")

            service._call_transcription_api = MagicMock(
                return_value="This is a test transcription."
            )

            result = service.transcribe_audio(test_audio)
            self.assertEqual(result, "This is a test transcription.")

    @patch('transcription.whisper_service.openai.OpenAI')
    def test_transcribe_audio_openai_api_error(self, mock_openai_client):
        """Test OpenAI API error handling."""
        self.mock_settings.settings.transcription.service = "openai"

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            mock_client = MagicMock()
            mock_openai_client.return_value = mock_client

            service = WhisperService(self.mock_settings)

            test_audio = self.temp_dir / "test.wav"
            test_audio.write_bytes(b"fake audio data")

            service._call_transcription_api = MagicMock(
                side_effect=Exception("API Error")
            )

            with self.assertRaises(TranscriptionException):
                service.transcribe_audio(test_audio)

    @patch('transcription.whisper_service.whisper')
    @patch('transcription.whisper_service.LOCAL_WHISPER_AVAILABLE', True)
    def test_transcribe_audio_local_success(self, mock_whisper):
        """Test successful local Whisper transcription."""
        mock_model = MagicMock()
        mock_whisper.load_model.return_value = mock_model
        mock_model.transcribe.return_value = {"text": "Local transcription result"}

        service = WhisperService(self.mock_settings)

        test_audio = self.temp_dir / "test.wav"
        test_audio.write_bytes(b"fake audio data")

        result = service.transcribe_audio(test_audio)
        self.assertEqual(result, "Local transcription result")

    @patch('transcription.whisper_service.whisper')
    @patch('transcription.whisper_service.LOCAL_WHISPER_AVAILABLE', True)
    def test_transcribe_audio_local_error(self, mock_whisper):
        """Test local Whisper transcription error handling."""
        mock_model = MagicMock()
        mock_whisper.load_model.return_value = mock_model
        mock_model.transcribe.side_effect = Exception("Model error")

        service = WhisperService(self.mock_settings)

        test_audio = self.temp_dir / "test.wav"
        test_audio.write_bytes(b"fake audio data")

        with self.assertRaises(TranscriptionException):
            service.transcribe_audio(test_audio)

    def test_transcribe_audio_file_not_found(self):
        """Test transcription with non-existent file."""
        with patch('transcription.whisper_service.whisper') as mock_whisper, \
             patch('transcription.whisper_service.LOCAL_WHISPER_AVAILABLE', True):
            mock_model = MagicMock()
            mock_whisper.load_model.return_value = mock_model
            mock_model.transcribe.side_effect = FileNotFoundError("No such file")

            service = WhisperService(self.mock_settings)

            with self.assertRaises(TranscriptionException):
                service.transcribe_audio(Path("/nonexistent/file.wav"))

    @patch('transcription.whisper_service.whisper')
    @patch('transcription.whisper_service.LOCAL_WHISPER_AVAILABLE', True)
    def test_get_service_info_local(self, mock_whisper):
        """Test get_service_info for local service."""
        mock_whisper.load_model.return_value = MagicMock()
        service = WhisperService(self.mock_settings)

        info = service.get_service_info()
        self.assertEqual(info["service"], "local")
        self.assertEqual(info["model"], "base")

    def test_get_service_info_openai(self):
        """Test get_service_info for OpenAI service."""
        self.mock_settings.settings.transcription.service = "openai"

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            with patch('transcription.whisper_service.openai.OpenAI'):
                service = WhisperService(self.mock_settings)

                info = service.get_service_info()
                self.assertEqual(info["service"], "openai")

    @patch('transcription.whisper_service.whisper')
    @patch('transcription.whisper_service.LOCAL_WHISPER_AVAILABLE', True)
    def test_transcribe_with_diarization(self, mock_whisper):
        """Test transcribe_with_diarization returns expected dict structure."""
        mock_model = MagicMock()
        mock_whisper.load_model.return_value = mock_model
        mock_model.transcribe.return_value = {"text": "Hello world"}

        service = WhisperService(self.mock_settings)

        test_audio = self.temp_dir / "test.wav"
        test_audio.write_bytes(b"fake audio data")

        result = service.transcribe_with_diarization(test_audio)

        self.assertIn("transcription", result)
        self.assertIn("diarized_transcription", result)
        self.assertEqual(result["transcription"], "Hello world")


class TestApiKeyResolutionPriority(unittest.TestCase):
    """Tests for API key resolution: settings_manager > env var."""

    @patch('transcription.whisper_service.openai.OpenAI')
    def test_settings_manager_key_used_over_env(self, mock_openai_cls):
        """settings_manager API key is preferred over env var."""
        mock_sm = MagicMock()
        mock_sm.settings.transcription.service = "openai"
        mock_sm.has_openai_api_key.return_value = True
        mock_sm.get_openai_api_key.return_value = "sk-from-settings"

        with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-from-env"}):
            service = WhisperService(settings_manager=mock_sm)

        mock_openai_cls.assert_called_once_with(
            api_key="sk-from-settings"
        )
        self.assertFalse(service.use_local)

    @patch('transcription.whisper_service.openai.OpenAI')
    def test_env_var_fallback_when_no_settings_key(self, mock_openai_cls):
        """Falls back to env var when settings_manager has no key."""
        mock_sm = MagicMock()
        mock_sm.settings.transcription.service = "openai"
        mock_sm.has_openai_api_key.return_value = True
        mock_sm.get_openai_api_key.return_value = None

        with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-from-env"}):
            service = WhisperService(settings_manager=mock_sm)

        mock_openai_cls.assert_called_once_with(
            api_key="sk-from-env"
        )
        self.assertFalse(service.use_local)

    @patch('transcription.whisper_service.openai.OpenAI')
    def test_env_var_used_without_settings_manager(self, mock_openai_cls):
        """Env var is used when no settings_manager is provided."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-from-env"}):
            service = WhisperService()

        mock_openai_cls.assert_called_once_with(
            api_key="sk-from-env"
        )
        self.assertFalse(service.use_local)

    @patch('transcription.whisper_service.openai.OpenAI')
    def test_settings_manager_key_stripped(self, mock_openai_cls):
        """API key from settings_manager is stripped of whitespace."""
        mock_sm = MagicMock()
        mock_sm.settings.transcription.service = "openai"
        mock_sm.has_openai_api_key.return_value = True
        mock_sm.get_openai_api_key.return_value = "  sk-padded  "

        WhisperService(settings_manager=mock_sm)

        mock_openai_cls.assert_called_once_with(
            api_key="sk-padded"
        )


if __name__ == '__main__':
    unittest.main()
