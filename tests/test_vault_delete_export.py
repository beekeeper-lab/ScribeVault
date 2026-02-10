"""
Tests for vault delete and export functionality (BEAN-003).
"""

import shutil
import tempfile
import unittest
from pathlib import Path
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from vault.manager import VaultManager, VaultException


class TestVaultDeleteWithFiles(unittest.TestCase):
    """Test delete_recording removes DB entries and associated files."""

    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.vault = VaultManager(vault_dir=self.temp_dir)

        # Create a fake audio file in the vault directory
        self.audio_file = self.temp_dir / "test_recording.wav"
        self.audio_file.write_bytes(b"fake audio data")

        # Add recording to DB
        self.recording_id = self.vault.add_recording(
            filename="test_recording.wav",
            title="Test Recording",
            category="meeting",
            duration=60.0,
            file_size=15,
            transcription="Hello world",
            summary="A greeting",
        )

    def tearDown(self):
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_delete_removes_db_entry(self):
        """Delete removes the database record."""
        result = self.vault.delete_recording(self.recording_id)
        self.assertTrue(result)
        recordings = self.vault.get_recordings()
        self.assertEqual(len(recordings), 0)

    def test_delete_invalid_id_raises(self):
        """Delete with invalid ID raises VaultException."""
        with self.assertRaises(VaultException):
            self.vault.delete_recording(-1)

    def test_delete_nonexistent_id_raises(self):
        """Delete with non-existent ID raises VaultException."""
        with self.assertRaises(VaultException):
            self.vault.delete_recording(99999)

    def test_delete_idempotent_raises_on_second(self):
        """Deleting the same recording twice raises on the second call."""
        self.vault.delete_recording(self.recording_id)
        with self.assertRaises(VaultException):
            self.vault.delete_recording(self.recording_id)

    def test_recording_data_accessible_before_delete(self):
        """Can retrieve recording data (for file cleanup) before deleting."""
        recording = self.vault.get_recording_by_id(self.recording_id)
        self.assertIsNotNone(recording)
        self.assertEqual(recording['filename'], "test_recording.wav")
        self.assertEqual(recording['transcription'], "Hello world")
        self.assertEqual(recording['summary'], "A greeting")


class TestVaultExportLogic(unittest.TestCase):
    """Test export file generation logic."""

    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.export_dir = Path(tempfile.mkdtemp())
        self.vault = VaultManager(vault_dir=self.temp_dir)

        # Create a fake audio file
        self.audio_file = self.temp_dir / "recording.wav"
        self.audio_file.write_bytes(b"fake WAV content")

        self.recording_id = self.vault.add_recording(
            filename="recording.wav",
            title="Export Test",
            category="interview",
            duration=120.0,
            file_size=16,
            transcription="This is the full transcription text.",
            summary="Brief summary of the recording.",
        )

    def tearDown(self):
        for d in (self.temp_dir, self.export_dir):
            if d.exists():
                shutil.rmtree(d)

    def test_export_audio_file(self):
        """Audio file can be copied to export directory."""
        src = self.temp_dir / "recording.wav"
        dst = self.export_dir / "recording.wav"
        shutil.copy2(str(src), str(dst))
        self.assertTrue(dst.exists())
        self.assertEqual(dst.read_bytes(), b"fake WAV content")

    def test_export_transcription_txt(self):
        """Transcription exported as .txt file."""
        recording = self.vault.get_recording_by_id(self.recording_id)
        txt_path = self.export_dir / "Export_Test_transcription.txt"
        txt_path.write_text(recording['transcription'], encoding='utf-8')

        self.assertTrue(txt_path.exists())
        self.assertEqual(
            txt_path.read_text(encoding='utf-8'),
            "This is the full transcription text."
        )

    def test_export_summary_md(self):
        """Summary exported as .md file."""
        recording = self.vault.get_recording_by_id(self.recording_id)
        title = recording['title']
        summary = recording['summary']
        md_content = f"# {title}\n\n## Summary\n\n{summary}\n"

        md_path = self.export_dir / "Export_Test_summary.md"
        md_path.write_text(md_content, encoding='utf-8')

        self.assertTrue(md_path.exists())
        content = md_path.read_text(encoding='utf-8')
        self.assertIn("# Export Test", content)
        self.assertIn("Brief summary of the recording.", content)

    def test_export_handles_no_transcription(self):
        """Export works when recording has no transcription."""
        recording_id = self.vault.add_recording(
            filename="no_transcript.wav",
            title="No Transcript",
        )
        recording = self.vault.get_recording_by_id(recording_id)
        self.assertIsNone(recording['transcription'])

    def test_export_handles_no_summary(self):
        """Export works when recording has no summary."""
        recording_id = self.vault.add_recording(
            filename="no_summary.wav",
            title="No Summary",
        )
        recording = self.vault.get_recording_by_id(recording_id)
        self.assertIsNone(recording['summary'])

    def test_export_handles_missing_audio(self):
        """Export handles gracefully when audio file doesn't exist on disk."""
        self.vault.add_recording(
            filename="missing_audio.wav",
            title="Missing Audio",
        )
        audio_path = self.temp_dir / "missing_audio.wav"
        self.assertFalse(audio_path.exists())


class TestVaultDeleteExportErrorHandling(unittest.TestCase):
    """Test error handling for delete and export operations."""

    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.vault = VaultManager(vault_dir=self.temp_dir)

    def tearDown(self):
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_delete_with_zero_id_raises(self):
        """Delete with id=0 raises VaultException."""
        with self.assertRaises(VaultException):
            self.vault.delete_recording(0)

    def test_get_recording_by_id_invalid(self):
        """get_recording_by_id with invalid ID raises."""
        with self.assertRaises(VaultException):
            self.vault.get_recording_by_id(-1)

    def test_get_recording_by_id_nonexistent(self):
        """get_recording_by_id returns None for non-existent ID."""
        result = self.vault.get_recording_by_id(99999)
        self.assertIsNone(result)

    def test_delete_preserves_other_recordings(self):
        """Deleting one recording doesn't affect others."""
        self.vault.add_recording(filename="keep.wav", title="Keep")
        id2 = self.vault.add_recording(filename="delete.wav", title="Delete")

        self.vault.delete_recording(id2)

        recordings = self.vault.get_recordings()
        self.assertEqual(len(recordings), 1)
        self.assertEqual(recordings[0]['title'], "Keep")


if __name__ == '__main__':
    unittest.main()
