"""
Unit tests for AudioRecorder class.
"""

import unittest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
import subprocess

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from audio.recorder import AudioRecorder, AudioException, RecordingException


class TestAudioRecorder(unittest.TestCase):
    """Test cases for AudioRecorder class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.recorder = AudioRecorder(output_dir=self.temp_dir)
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.recorder.cleanup()
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_initialization(self):
        """Test recorder initialization."""
        self.assertFalse(self.recorder.is_recording)
        self.assertTrue(self.temp_dir.exists())
    
    def test_invalid_output_directory(self):
        """Test initialization with invalid output directory."""
        with self.assertRaises(AudioException):
            AudioRecorder(output_dir="/invalid/path/that/does/not/exist")
    
    @patch('audio.recorder.pyaudio.PyAudio')
    def test_start_recording_success(self, mock_pyaudio):
        """Test successful recording start."""
        # Mock PyAudio
        mock_pa = MagicMock()
        mock_pyaudio.return_value = mock_pa
        mock_stream = MagicMock()
        mock_pa.open.return_value = mock_stream
        
        # Start recording
        result = self.recorder.start_recording()
        
        self.assertTrue(self.recorder.is_recording)
        self.assertIsInstance(result, Path)
        self.assertTrue(result.name.endswith('.wav'))
        
        # Verify PyAudio was called correctly
        mock_pa.open.assert_called_once()
        call_args = mock_pa.open.call_args[1]
        self.assertEqual(call_args['format'], self.recorder.pyaudio.paInt16)
        self.assertEqual(call_args['channels'], 1)
        self.assertEqual(call_args['rate'], 44100)
    
    def test_start_recording_already_recording(self):
        """Test starting recording when already recording."""
        self.recorder.is_recording = True
        
        with self.assertRaises(RecordingException):
            self.recorder.start_recording()
    
    @patch('audio.recorder.pyaudio.PyAudio')
    def test_start_recording_pyaudio_error(self, mock_pyaudio):
        """Test recording start with PyAudio error."""
        mock_pyaudio.side_effect = Exception("PyAudio error")
        
        with self.assertRaises(AudioException):
            self.recorder.start_recording()
    
    @patch('audio.recorder.subprocess.run')
    @patch('audio.recorder.pyaudio.PyAudio')
    def test_stop_recording_success(self, mock_pyaudio, mock_subprocess):
        """Test successful recording stop."""
        # Setup mocks
        mock_pa = MagicMock()
        mock_pyaudio.return_value = mock_pa
        mock_stream = MagicMock()
        mock_pa.open.return_value = mock_stream
        mock_subprocess.return_value.returncode = 0
        
        # Start and stop recording
        audio_file = self.recorder.start_recording()
        
        # Mock some audio data
        self.recorder.audio_data = [b'mock_audio_data']
        
        result = self.recorder.stop_recording()
        
        self.assertFalse(self.recorder.is_recording)
        self.assertEqual(result, audio_file)
        
        # Verify stream was closed
        mock_stream.stop_stream.assert_called_once()
        mock_stream.close.assert_called_once()
    
    def test_stop_recording_not_recording(self):
        """Test stopping recording when not recording."""
        with self.assertRaises(RecordingException):
            self.recorder.stop_recording()
    
    @patch('audio.recorder.subprocess.run')
    @patch('audio.recorder.pyaudio.PyAudio')
    def test_stop_recording_ffmpeg_error(self, mock_pyaudio, mock_subprocess):
        """Test recording stop with FFmpeg error."""
        # Setup mocks
        mock_pa = MagicMock()
        mock_pyaudio.return_value = mock_pa
        mock_stream = MagicMock()
        mock_pa.open.return_value = mock_stream
        mock_subprocess.return_value.returncode = 1  # FFmpeg error
        
        # Start recording
        self.recorder.start_recording()
        self.recorder.audio_data = [b'mock_audio_data']
        
        with self.assertRaises(AudioException):
            self.recorder.stop_recording()
    
    def test_cleanup(self):
        """Test cleanup functionality."""
        # Should not raise any exceptions
        self.recorder.cleanup()
        
        # Multiple cleanups should be safe
        self.recorder.cleanup()
    
    def test_generate_filename(self):
        """Test filename generation."""
        filename = self.recorder._generate_filename()
        
        self.assertTrue(filename.startswith('recording_'))
        self.assertTrue(filename.endswith('.wav'))
        
        # Test uniqueness
        filename2 = self.recorder._generate_filename()
        self.assertNotEqual(filename, filename2)
    
    def test_validate_path_security(self):
        """Test path validation for security."""
        # Valid paths
        self.assertTrue(self.recorder._is_safe_path(self.temp_dir / "test.wav"))
        
        # Invalid paths (path traversal attempts)
        self.assertFalse(self.recorder._is_safe_path(Path("../test.wav")))
        self.assertFalse(self.recorder._is_safe_path(Path("/etc/passwd")))
        self.assertFalse(self.recorder._is_safe_path(Path("..\\test.wav")))


if __name__ == '__main__':
    unittest.main()
