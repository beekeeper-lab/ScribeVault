"""
Unit tests for BEAN-016: On-Demand Vault Processing.

Tests TranscriptionWorker, OnDemandSummarizationWorker,
VaultDialog button state logic, and auto-chaining.
"""

import unittest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import MagicMock

import sys
import os
sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), '..', 'src')
)

from vault.manager import VaultManager


class TestVaultManagerGetAudioPath(unittest.TestCase):
    """Test VaultManager.get_audio_path helper."""

    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.vault_manager = VaultManager(
            vault_dir=self.temp_dir
        )

    def tearDown(self):
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_get_audio_path_exists(self):
        """Returns path when audio file exists."""
        audio_file = self.temp_dir / "test.wav"
        audio_file.write_bytes(b"fake audio")
        recording = {"filename": "test.wav"}
        result = self.vault_manager.get_audio_path(recording)
        self.assertEqual(result, audio_file)

    def test_get_audio_path_missing(self):
        """Returns None when audio file does not exist."""
        recording = {"filename": "missing.wav"}
        result = self.vault_manager.get_audio_path(recording)
        self.assertIsNone(result)

    def test_get_audio_path_no_filename(self):
        """Returns None when no filename in recording."""
        recording = {}
        result = self.vault_manager.get_audio_path(recording)
        self.assertIsNone(result)

    def test_get_audio_path_empty_filename(self):
        """Returns None when filename is empty."""
        recording = {"filename": ""}
        result = self.vault_manager.get_audio_path(recording)
        self.assertIsNone(result)


try:
    import PySide6  # noqa: F401
    HAS_PYSIDE6 = True
except ImportError:
    HAS_PYSIDE6 = False


@unittest.skipUnless(HAS_PYSIDE6, "PySide6 not available")
class TestTranscriptionWorker(unittest.TestCase):
    """Test TranscriptionWorker thread."""

    def test_worker_success_with_diarization(self):
        """Worker emits finished with diarized transcript."""
        from gui.qt_vault_dialog import TranscriptionWorker

        mock_whisper = MagicMock()
        mock_whisper.transcribe_with_diarization.return_value = {
            "transcription": "plain text",
            "diarized_transcription": "Speaker 1: hello",
        }

        worker = TranscriptionWorker(
            mock_whisper, Path("/fake/audio.wav")
        )

        results = []
        worker.finished.connect(results.append)
        worker.run()

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], "Speaker 1: hello")

    def test_worker_success_plain_fallback(self):
        """Worker uses plain transcription if diarized is None."""
        from gui.qt_vault_dialog import TranscriptionWorker

        mock_whisper = MagicMock()
        mock_whisper.transcribe_with_diarization.return_value = {
            "transcription": "plain text",
            "diarized_transcription": None,
        }

        worker = TranscriptionWorker(
            mock_whisper, Path("/fake/audio.wav")
        )

        results = []
        worker.finished.connect(results.append)
        worker.run()

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], "plain text")

    def test_worker_error(self):
        """Worker emits error on exception."""
        from gui.qt_vault_dialog import TranscriptionWorker

        mock_whisper = MagicMock()
        mock_whisper.transcribe_with_diarization.side_effect = (
            RuntimeError("API failed")
        )

        worker = TranscriptionWorker(
            mock_whisper, Path("/fake/audio.wav")
        )

        errors = []
        worker.error.connect(errors.append)
        worker.run()

        self.assertEqual(len(errors), 1)
        self.assertIn("API failed", errors[0])

    def test_worker_no_result(self):
        """Worker emits error when transcription returns None."""
        from gui.qt_vault_dialog import TranscriptionWorker

        mock_whisper = MagicMock()
        mock_whisper.transcribe_with_diarization.return_value = {
            "transcription": None,
            "diarized_transcription": None,
        }

        worker = TranscriptionWorker(
            mock_whisper, Path("/fake/audio.wav")
        )

        errors = []
        worker.error.connect(errors.append)
        worker.run()

        self.assertEqual(len(errors), 1)
        self.assertIn("no result", errors[0])


@unittest.skipUnless(HAS_PYSIDE6, "PySide6 not available")
class TestOnDemandSummarizationWorker(unittest.TestCase):
    """Test OnDemandSummarizationWorker thread."""

    def test_worker_success(self):
        """Worker emits finished with result dict."""
        from gui.qt_vault_dialog import (
            OnDemandSummarizationWorker,
        )

        mock_summarizer = MagicMock()
        mock_summarizer.generate_summary_with_markdown.return_value = {
            "summary": "Test summary",
            "markdown_path": "/tmp/test.md",
            "error": None,
        }

        recording_data = {
            "id": 1,
            "transcription": "some text",
            "category": "meeting",
        }

        worker = OnDemandSummarizationWorker(
            mock_summarizer, recording_data
        )

        results = []
        worker.finished.connect(results.append)
        worker.run()

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["summary"], "Test summary")

    def test_worker_error_from_service(self):
        """Worker emits error when service returns no summary."""
        from gui.qt_vault_dialog import (
            OnDemandSummarizationWorker,
        )

        mock_summarizer = MagicMock()
        mock_summarizer.generate_summary_with_markdown.return_value = {
            "summary": None,
            "markdown_path": None,
            "error": "No transcription",
        }

        worker = OnDemandSummarizationWorker(
            mock_summarizer, {"id": 1}
        )

        errors = []
        worker.error.connect(errors.append)
        worker.run()

        self.assertEqual(len(errors), 1)
        self.assertIn("No transcription", errors[0])

    def test_worker_exception(self):
        """Worker emits error on exception."""
        from gui.qt_vault_dialog import (
            OnDemandSummarizationWorker,
        )

        mock_summarizer = MagicMock()
        mock_summarizer.generate_summary_with_markdown.side_effect = (
            RuntimeError("API error")
        )

        worker = OnDemandSummarizationWorker(
            mock_summarizer, {"id": 1}
        )

        errors = []
        worker.error.connect(errors.append)
        worker.run()

        self.assertEqual(len(errors), 1)
        self.assertIn("API error", errors[0])


@unittest.skipUnless(HAS_PYSIDE6, "PySide6 not available")
class TestVaultDialogButtonStates(unittest.TestCase):
    """Test VaultDialog button enable/disable logic."""

    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.vault_manager = VaultManager(
            vault_dir=self.temp_dir
        )

    def tearDown(self):
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def _make_dialog(self):
        from gui.qt_vault_dialog import VaultDialog
        from unittest.mock import patch
        with patch.object(VaultDialog, 'load_recordings'):
            with patch.object(VaultDialog, 'show_empty_details'):
                return VaultDialog(self.vault_manager)

    def test_buttons_disabled_no_selection(self):
        """Buttons disabled when no recording is selected."""
        dialog = self._make_dialog()
        dialog._update_processing_buttons(None)
        self.assertFalse(dialog.transcribe_button.isEnabled())
        self.assertFalse(dialog.summarize_button.isEnabled())

    def test_transcribe_enabled_with_audio_no_transcript(self):
        """Transcribe enabled when audio exists, no transcript."""
        audio_file = self.temp_dir / "test.wav"
        audio_file.write_bytes(b"fake audio")

        dialog = self._make_dialog()
        recording = {
            "filename": "test.wav",
            "transcription": None,
            "summary": None,
        }
        dialog._update_processing_buttons(recording)
        self.assertTrue(dialog.transcribe_button.isEnabled())

    def test_transcribe_disabled_with_transcript(self):
        """Transcribe disabled when transcript exists."""
        audio_file = self.temp_dir / "test.wav"
        audio_file.write_bytes(b"fake audio")

        dialog = self._make_dialog()
        recording = {
            "filename": "test.wav",
            "transcription": "Existing transcript",
            "summary": None,
        }
        dialog._update_processing_buttons(recording)
        self.assertFalse(dialog.transcribe_button.isEnabled())

    def test_summarize_enabled_no_summary(self):
        """Summarize enabled when no summary exists."""
        audio_file = self.temp_dir / "test.wav"
        audio_file.write_bytes(b"fake audio")

        dialog = self._make_dialog()
        recording = {
            "filename": "test.wav",
            "transcription": "Some transcript",
            "summary": None,
        }
        dialog._update_processing_buttons(recording)
        self.assertTrue(dialog.summarize_button.isEnabled())

    def test_summarize_disabled_with_summary(self):
        """Summarize disabled when summary exists."""
        audio_file = self.temp_dir / "test.wav"
        audio_file.write_bytes(b"fake audio")

        dialog = self._make_dialog()
        recording = {
            "filename": "test.wav",
            "transcription": "Some transcript",
            "summary": "Existing summary",
        }
        dialog._update_processing_buttons(recording)
        self.assertFalse(dialog.summarize_button.isEnabled())

    def test_buttons_disabled_during_processing(self):
        """Buttons disabled during processing."""
        audio_file = self.temp_dir / "test.wav"
        audio_file.write_bytes(b"fake audio")

        dialog = self._make_dialog()
        dialog._processing = True
        recording = {
            "filename": "test.wav",
            "transcription": None,
            "summary": None,
        }
        dialog._update_processing_buttons(recording)
        self.assertFalse(dialog.transcribe_button.isEnabled())
        self.assertFalse(dialog.summarize_button.isEnabled())

    def test_summarize_enabled_no_transcript_auto_chain(self):
        """Summarize enabled when no transcript (auto-chain)."""
        audio_file = self.temp_dir / "test.wav"
        audio_file.write_bytes(b"fake audio")

        dialog = self._make_dialog()
        recording = {
            "filename": "test.wav",
            "transcription": None,
            "summary": None,
        }
        dialog._update_processing_buttons(recording)
        self.assertTrue(dialog.summarize_button.isEnabled())

    def test_buttons_disabled_no_audio(self):
        """Both buttons disabled when no audio file."""
        dialog = self._make_dialog()
        recording = {
            "filename": "missing.wav",
            "transcription": None,
            "summary": None,
        }
        dialog._update_processing_buttons(recording)
        self.assertFalse(dialog.transcribe_button.isEnabled())
        self.assertFalse(dialog.summarize_button.isEnabled())


@unittest.skipUnless(HAS_PYSIDE6, "PySide6 not available")
class TestVaultDialogConstructor(unittest.TestCase):
    """Test VaultDialog accepts whisper_service param."""

    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.vault_manager = VaultManager(
            vault_dir=self.temp_dir
        )

    def tearDown(self):
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def _make_dialog(self, **kwargs):
        from gui.qt_vault_dialog import VaultDialog
        from unittest.mock import patch
        with patch.object(VaultDialog, 'load_recordings'):
            with patch.object(VaultDialog, 'show_empty_details'):
                return VaultDialog(
                    self.vault_manager, **kwargs
                )

    def test_whisper_service_stored(self):
        """VaultDialog stores whisper_service."""
        mock_whisper = MagicMock()
        dialog = self._make_dialog(
            whisper_service=mock_whisper
        )
        self.assertIs(dialog.whisper_service, mock_whisper)

    def test_whisper_service_default_none(self):
        """VaultDialog defaults whisper_service to None."""
        dialog = self._make_dialog()
        self.assertIsNone(dialog.whisper_service)


if __name__ == "__main__":
    unittest.main()
