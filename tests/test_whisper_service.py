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
        self.mock_settings = MagicMock(spec=SettingsManager)
        self.mock_settings.get_api_key.return_value = "test-api-key"
        self.mock_settings.get_setting.return_value = "openai"  # Default to OpenAI
        
        self.whisper_service = WhisperService(self.mock_settings)
    
    def tearDown(self):
        """Clean up test fixtures."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_initialization(self):
        """Test WhisperService initialization."""
        self.assertEqual(self.whisper_service.settings_manager, self.mock_settings)
        self.assertIsNotNone(self.whisper_service.logger)
    
    def test_initialization_no_api_key(self):
        """Test initialization without API key."""
        self.mock_settings.get_api_key.return_value = None
        
        # Should not raise error during initialization
        service = WhisperService(self.mock_settings)
        self.assertIsNotNone(service)
    
    @patch('transcription.whisper_service.openai.OpenAI')
    def test_transcribe_audio_openai_success(self, mock_openai_client):
        """Test successful OpenAI transcription."""
        # Create test audio file
        test_audio = self.temp_dir / "test.wav"
        test_audio.write_bytes(b"fake audio data")
        
        # Mock OpenAI response
        mock_client = MagicMock()
        mock_openai_client.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.text = "This is a test transcription."
        mock_client.audio.transcriptions.create.return_value = mock_response
        
        # Test transcription
        result = self.whisper_service.transcribe_audio(test_audio)
        
        self.assertEqual(result, "This is a test transcription.")
        mock_client.audio.transcriptions.create.assert_called_once()
    
    @patch('transcription.whisper_service.openai.OpenAI')
    def test_transcribe_audio_openai_api_error(self, mock_openai_client):
        """Test OpenAI API error handling."""
        test_audio = self.temp_dir / "test.wav"
        test_audio.write_bytes(b"fake audio data")
        
        # Mock OpenAI client to raise exception
        mock_client = MagicMock()
        mock_openai_client.return_value = mock_client
        mock_client.audio.transcriptions.create.side_effect = Exception("API Error")
        
        with self.assertRaises(TranscriptionException):
            self.whisper_service.transcribe_audio(test_audio)
    
    def test_transcribe_audio_no_api_key(self):
        """Test transcription without API key."""
        self.mock_settings.get_api_key.return_value = None
        
        test_audio = self.temp_dir / "test.wav"
        test_audio.write_bytes(b"fake audio data")
        
        with self.assertRaises(TranscriptionException):
            self.whisper_service.transcribe_audio(test_audio)
    
    def test_transcribe_audio_invalid_file(self):
        """Test transcription with invalid file."""
        # Non-existent file
        with self.assertRaises(TranscriptionException):
            self.whisper_service.transcribe_audio(Path("/nonexistent/file.wav"))
        
        # Directory instead of file
        with self.assertRaises(TranscriptionException):
            self.whisper_service.transcribe_audio(self.temp_dir)
    
    @patch('transcription.whisper_service.whisper.load_model')
    def test_transcribe_audio_local_success(self, mock_load_model):
        """Test successful local Whisper transcription."""
        # Configure for local transcription
        self.mock_settings.get_setting.return_value = "local"
        
        test_audio = self.temp_dir / "test.wav"
        test_audio.write_bytes(b"fake audio data")
        
        # Mock Whisper model
        mock_model = MagicMock()
        mock_load_model.return_value = mock_model
        mock_model.transcribe.return_value = {"text": "Local transcription result"}
        
        result = self.whisper_service._transcribe_with_local_whisper(test_audio)
        
        self.assertEqual(result, "Local transcription result")
        mock_model.transcribe.assert_called_once()
    
    @patch('transcription.whisper_service.whisper.load_model')
    def test_transcribe_audio_local_error(self, mock_load_model):
        """Test local Whisper transcription error handling."""
        self.mock_settings.get_setting.return_value = "local"
        
        test_audio = self.temp_dir / "test.wav"
        test_audio.write_bytes(b"fake audio data")
        
        # Mock model loading error
        mock_load_model.side_effect = Exception("Model loading failed")
        
        with self.assertRaises(TranscriptionException):
            self.whisper_service._transcribe_with_local_whisper(test_audio)
    
    def test_validate_audio_file_valid(self):
        """Test audio file validation with valid file."""
        test_audio = self.temp_dir / "test.wav"
        test_audio.write_bytes(b"fake audio data")
        
        # Should not raise exception
        self.whisper_service._validate_audio_file(test_audio)
    
    def test_validate_audio_file_invalid(self):
        """Test audio file validation with invalid files."""
        # Non-existent file
        with self.assertRaises(TranscriptionException):
            self.whisper_service._validate_audio_file(Path("/nonexistent.wav"))
        
        # Directory
        with self.assertRaises(TranscriptionException):
            self.whisper_service._validate_audio_file(self.temp_dir)
        
        # Invalid extension
        invalid_file = self.temp_dir / "test.txt"
        invalid_file.write_text("not audio")
        
        with self.assertRaises(TranscriptionException):
            self.whisper_service._validate_audio_file(invalid_file)
    
    def test_file_size_validation(self):
        """Test audio file size validation."""
        # Create file larger than 25MB (mock)
        large_file = self.temp_dir / "large.wav"
        large_file.write_bytes(b"x" * (26 * 1024 * 1024))  # 26MB
        
        with self.assertRaises(TranscriptionException):
            self.whisper_service._validate_audio_file(large_file)
    
    def test_transcription_service_selection(self):
        """Test transcription service selection logic."""
        # Test OpenAI selection
        self.mock_settings.get_setting.return_value = "openai"
        self.mock_settings.get_api_key.return_value = "test-key"
        
        service = self.whisper_service._get_transcription_service()
        self.assertEqual(service, "openai")
        
        # Test local selection
        self.mock_settings.get_setting.return_value = "local"
        
        service = self.whisper_service._get_transcription_service()
        self.assertEqual(service, "local")
        
        # Test fallback to local when no API key
        self.mock_settings.get_setting.return_value = "openai"
        self.mock_settings.get_api_key.return_value = None
        
        service = self.whisper_service._get_transcription_service()
        self.assertEqual(service, "local")


if __name__ == '__main__':
    unittest.main()
