"""
Unit tests for AudioRecorder class.
"""

import unittest
import tempfile
import shutil
import os
from pathlib import Path
from unittest.mock import MagicMock

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from audio.recorder import AudioRecorder, AudioException, RecordingException


class TestAudioRecorder(unittest.TestCase):
    """Test cases for AudioRecorder class."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.orig_dir = os.getcwd()
        os.chdir(self.temp_dir)

        # Get the mock pyaudio from sys.modules (installed by conftest)
        self.mock_pyaudio_module = sys.modules['pyaudio']
        self.mock_pa = MagicMock()
        self.mock_pa.get_sample_size.return_value = 2
        self.mock_pyaudio_module.PyAudio.return_value = self.mock_pa

        self.recorder = AudioRecorder(
            sample_rate=44100,
            chunk_size=1024,
            channels=1,
        )

    def tearDown(self):
        """Clean up test fixtures."""
        self.recorder.cleanup()
        os.chdir(self.orig_dir)
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_initialization(self):
        """Test recorder initialization."""
        self.assertFalse(self.recorder.is_recording)

    def test_start_recording_already_recording(self):
        """Test starting recording when already recording."""
        self.recorder.is_recording = True

        with self.assertRaises(RuntimeError):
            self.recorder.start_recording()

    def test_stop_recording_not_recording(self):
        """Test stopping recording when not recording."""
        result = self.recorder.stop_recording()
        self.assertIsNone(result)

    def test_cleanup(self):
        """Test cleanup functionality."""
        # Should not raise any exceptions
        self.recorder.cleanup()

        # Multiple cleanups should be safe (idempotent)
        self.recorder.cleanup()

    def test_validate_output_path_valid(self):
        """Test _validate_output_path with a valid path."""
        recordings_dir = self.temp_dir / "recordings"
        recordings_dir.mkdir()
        valid_path = recordings_dir / "recording-test.wav"
        self.assertTrue(self.recorder._validate_output_path(valid_path))

    def test_validate_output_path_invalid_extension(self):
        """Test _validate_output_path rejects non-wav files."""
        recordings_dir = self.temp_dir / "recordings"
        recordings_dir.mkdir()
        invalid_path = recordings_dir / "test.mp3"
        self.assertFalse(self.recorder._validate_output_path(invalid_path))

    def test_validate_output_path_traversal(self):
        """Test _validate_output_path rejects path traversal."""
        path = Path("../etc/passwd.wav")
        self.assertFalse(self.recorder._validate_output_path(path))

    def test_audio_callback_appends_frames(self):
        """Test _audio_callback appends data when recording."""
        self.recorder.is_recording = True
        result = self.recorder._audio_callback(b'test_data', 1024, {}, 0)
        self.assertEqual(result, (b'test_data', self.mock_pyaudio_module.paContinue))
        self.assertEqual(self.recorder.frames, [b'test_data'])

    def test_audio_callback_ignores_when_not_recording(self):
        """Test _audio_callback does not append when not recording."""
        self.recorder.is_recording = False
        self.recorder._audio_callback(b'test_data', 1024, {}, 0)
        self.assertEqual(self.recorder.frames, [])


if __name__ == '__main__':
    unittest.main()
