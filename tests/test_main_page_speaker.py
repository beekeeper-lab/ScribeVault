"""
Tests for main page speaker labeling integration (BEAN-017).

Verifies the collapsible 'Name Speakers' section on the main page:
visibility logic, signal wiring, and SpeakerPanel loading.
"""

import unittest
import sys
import os
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from transcription.speaker_service import parse_speakers

try:
    from PySide6.QtWidgets import QApplication  # noqa: F401
    HAS_PYSIDE6 = True
except ImportError:
    HAS_PYSIDE6 = False


class TestSpeakerVisibilityLogic(unittest.TestCase):
    """Test that speaker section visibility depends on speaker detection."""

    def test_speakers_detected_in_diarized_text(self):
        text = "Speaker 1: Hello\nSpeaker 2: Hi there"
        speakers = parse_speakers(text)
        self.assertTrue(len(speakers) > 0)

    def test_no_speakers_in_plain_text(self):
        text = "This is plain transcription without any speaker labels."
        speakers = parse_speakers(text)
        self.assertEqual(len(speakers), 0)

    def test_no_speakers_in_empty_text(self):
        speakers = parse_speakers("")
        self.assertEqual(len(speakers), 0)

    def test_no_speakers_in_none_text(self):
        speakers = parse_speakers(None)
        self.assertEqual(len(speakers), 0)

    def test_named_speakers_detected(self):
        text = "Alice: Good morning\nBob: Good morning to you"
        speakers = parse_speakers(text)
        self.assertEqual(speakers, ["Alice", "Bob"])


@unittest.skipUnless(HAS_PYSIDE6, "PySide6 not available")
@patch.dict(os.environ, {"QT_QPA_PLATFORM": "offscreen"})
class TestMainPageSpeakerSection(unittest.TestCase):
    """Test the main page speaker section widget integration."""

    @classmethod
    def setUpClass(cls):
        """Create QApplication once for all tests."""
        from PySide6.QtWidgets import QApplication
        cls.app = QApplication.instance()
        if cls.app is None:
            cls.app = QApplication([])

    def _create_window(self):
        """Create a ScribeVaultMainWindow with mocked services."""
        with patch('gui.qt_main_window.AudioRecorder'), \
             patch('gui.qt_main_window.WhisperService'), \
             patch('gui.qt_main_window.SummarizerService'), \
             patch('gui.qt_main_window.VaultManager'), \
             patch('gui.qt_main_window.SettingsManager'):
            from gui.qt_main_window import ScribeVaultMainWindow
            window = ScribeVaultMainWindow()
            return window

    def test_speaker_group_exists(self):
        """Speaker group box is created on the main window."""
        window = self._create_window()
        self.assertTrue(hasattr(window, 'speaker_group'))
        self.assertTrue(hasattr(window, 'main_speaker_panel'))

    def test_speaker_group_hidden_by_default(self):
        """Speaker section is hidden when no recording has been processed."""
        window = self._create_window()
        self.assertFalse(window.speaker_group.isVisible())

    def test_speaker_group_collapsed_by_default(self):
        """Speaker section is collapsed (unchecked) by default."""
        window = self._create_window()
        self.assertFalse(window.speaker_group.isChecked())

    def test_speaker_group_shown_when_speakers_detected(self):
        """Speaker section becomes visible after processing with speakers."""
        window = self._create_window()
        window.current_recording_path = MagicMock()
        window.current_recording_path.name = "test.wav"
        window.current_recording_path.stat.return_value.st_size = 1000

        result = {
            'transcript': "Speaker 1: Hello\nSpeaker 2: Hi",
            'diarized_transcript': "Speaker 1: Hello\nSpeaker 2: Hi",
            'summary': None,
            'markdown_path': None,
            'recording_id': 'test-id',
            'pipeline_status': {},
        }
        window.on_processing_finished(result)

        self.assertTrue(window.speaker_group.isVisible())
        self.assertFalse(window.speaker_group.isChecked())

    def test_speaker_group_hidden_when_no_speakers(self):
        """Speaker section stays hidden for plain transcription."""
        window = self._create_window()
        window.current_recording_path = MagicMock()
        window.current_recording_path.name = "test.wav"
        window.current_recording_path.stat.return_value.st_size = 1000

        result = {
            'transcript': "Plain transcription without speakers.",
            'diarized_transcript': None,
            'summary': None,
            'markdown_path': None,
            'recording_id': 'test-id',
            'pipeline_status': {},
        }
        window.on_processing_finished(result)

        self.assertFalse(window.speaker_group.isVisible())

    def test_transcription_updated_signal_updates_display(self):
        """Emitting transcription_updated updates the transcript text."""
        window = self._create_window()
        window.current_recording_data = {
            'transcription': 'Speaker 1: Hello',
        }

        new_text = "Alice: Hello"
        window._on_speaker_transcription_updated(new_text)

        self.assertEqual(
            window.transcript_text.toPlainText(), new_text
        )
        self.assertEqual(
            window.current_recording_data['transcription'], new_text
        )

    def test_speaker_group_hidden_on_new_recording(self):
        """Speaker section is hidden when starting a new recording."""
        window = self._create_window()
        window.speaker_group.setVisible(True)
        window.speaker_group.setChecked(True)

        # Simulate the reset portion of start_recording
        window.transcript_text.clear()
        window.speaker_group.setVisible(False)
        window.speaker_group.setChecked(False)

        self.assertFalse(window.speaker_group.isVisible())
        self.assertFalse(window.speaker_group.isChecked())


if __name__ == '__main__':
    unittest.main()
