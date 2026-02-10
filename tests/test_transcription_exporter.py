"""
Unit tests for TranscriptionExporter class.
"""

import unittest
import tempfile
import shutil
from pathlib import Path

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from export.transcription_exporter import (
    TranscriptionExporter,
    TranscriptionExportError,
    SIZE_WARNING_THRESHOLD,
)


class TestTranscriptionExporter(unittest.TestCase):
    """Test cases for TranscriptionExporter."""

    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.sample_recording = {
            'title': 'Team Standup',
            'transcription': (
                'Alice: Good morning everyone.\n'
                'Bob: Morning! Let me share my update.\n'
                'Alice: Go ahead.\n'
            ),
            'created_at': '2026-01-15T09:30:00',
            'duration': 325.5,
            'category': 'meeting',
        }

    def tearDown(self):
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    # --- TXT export ---

    def test_export_txt_creates_file(self):
        exporter = TranscriptionExporter(self.sample_recording)
        path = self.temp_dir / 'out.txt'
        result = exporter.export_txt(path)
        self.assertTrue(path.exists())
        self.assertEqual(result, path)

    def test_export_txt_contains_transcription(self):
        exporter = TranscriptionExporter(self.sample_recording)
        path = self.temp_dir / 'out.txt'
        exporter.export_txt(path)
        content = path.read_text(encoding='utf-8')
        self.assertIn('Alice: Good morning everyone.', content)
        self.assertIn('Bob: Morning!', content)

    def test_export_txt_contains_metadata(self):
        exporter = TranscriptionExporter(self.sample_recording)
        path = self.temp_dir / 'out.txt'
        exporter.export_txt(path)
        content = path.read_text(encoding='utf-8')
        self.assertIn('Title: Team Standup', content)
        self.assertIn('Date: 2026-01-15', content)
        self.assertIn('Duration: 5m', content)
        self.assertIn('Category: Meeting', content)

    def test_export_txt_speaker_extraction(self):
        exporter = TranscriptionExporter(self.sample_recording)
        path = self.temp_dir / 'out.txt'
        exporter.export_txt(path)
        content = path.read_text(encoding='utf-8')
        self.assertIn('Speakers:', content)
        self.assertIn('Alice', content)
        self.assertIn('Bob', content)

    # --- Markdown export ---

    def test_export_markdown_creates_file(self):
        exporter = TranscriptionExporter(self.sample_recording)
        path = self.temp_dir / 'out.md'
        result = exporter.export_markdown(path)
        self.assertTrue(path.exists())
        self.assertEqual(result, path)

    def test_export_markdown_has_header(self):
        exporter = TranscriptionExporter(self.sample_recording)
        path = self.temp_dir / 'out.md'
        exporter.export_markdown(path)
        content = path.read_text(encoding='utf-8')
        self.assertIn('# Team Standup', content)
        self.assertIn('**Date**:', content)
        self.assertIn('**Duration**:', content)
        self.assertIn('**Exported**:', content)

    def test_export_markdown_has_transcription_section(self):
        exporter = TranscriptionExporter(self.sample_recording)
        path = self.temp_dir / 'out.md'
        exporter.export_markdown(path)
        content = path.read_text(encoding='utf-8')
        self.assertIn('## Transcription', content)
        self.assertIn('Alice: Good morning everyone.', content)

    # --- SRT export ---

    def test_export_srt_with_segments(self):
        recording = dict(self.sample_recording)
        recording['segments'] = [
            {'start': 0.0, 'end': 2.5, 'text': 'Good morning everyone.'},
            {'start': 3.0, 'end': 6.0, 'text': 'Morning! Let me share.'},
        ]
        exporter = TranscriptionExporter(recording)
        path = self.temp_dir / 'out.srt'
        exporter.export_srt(path)
        self.assertTrue(path.exists())
        content = path.read_text(encoding='utf-8')
        self.assertIn('1\n00:00:00,000 --> 00:00:02,500', content)
        self.assertIn('Good morning everyone.', content)
        self.assertIn('2\n00:00:03,000 --> 00:00:06,000', content)

    def test_export_srt_without_segments_raises(self):
        exporter = TranscriptionExporter(self.sample_recording)
        path = self.temp_dir / 'out.srt'
        with self.assertRaises(TranscriptionExportError):
            exporter.export_srt(path)

    def test_has_timestamps_false_by_default(self):
        exporter = TranscriptionExporter(self.sample_recording)
        self.assertFalse(exporter.has_timestamps())

    def test_has_timestamps_true_with_segments(self):
        recording = dict(self.sample_recording)
        recording['segments'] = [
            {'start': 0.0, 'end': 1.0, 'text': 'Hello'},
        ]
        exporter = TranscriptionExporter(recording)
        self.assertTrue(exporter.has_timestamps())

    # --- Size warning ---

    def test_needs_size_warning_false_for_small(self):
        exporter = TranscriptionExporter(self.sample_recording)
        self.assertFalse(exporter.needs_size_warning())

    def test_needs_size_warning_true_for_large(self):
        recording = dict(self.sample_recording)
        # Create a transcription >50KB
        recording['transcription'] = 'x' * (SIZE_WARNING_THRESHOLD + 1)
        exporter = TranscriptionExporter(recording)
        self.assertTrue(exporter.needs_size_warning())

    def test_get_transcription_size(self):
        exporter = TranscriptionExporter(self.sample_recording)
        expected = len(self.sample_recording['transcription'].encode('utf-8'))
        self.assertEqual(exporter.get_transcription_size(), expected)

    # --- Edge cases ---

    def test_empty_transcription(self):
        recording = {'title': 'Empty', 'transcription': ''}
        exporter = TranscriptionExporter(recording)
        path = self.temp_dir / 'empty.txt'
        exporter.export_txt(path)
        content = path.read_text(encoding='utf-8')
        self.assertIn('Title: Empty', content)

    def test_missing_fields(self):
        recording = {'filename': 'audio.wav'}
        exporter = TranscriptionExporter(recording)
        path = self.temp_dir / 'minimal.txt'
        exporter.export_txt(path)
        content = path.read_text(encoding='utf-8')
        self.assertIn('Title: audio.wav', content)

    def test_special_characters_in_transcription(self):
        recording = {
            'title': 'Special Chars',
            'transcription': 'He said "hello" & she said <goodbye>',
        }
        exporter = TranscriptionExporter(recording)
        path = self.temp_dir / 'special.md'
        exporter.export_markdown(path)
        content = path.read_text(encoding='utf-8')
        self.assertIn('He said "hello" & she said <goodbye>', content)

    def test_no_date_gracefully_handled(self):
        recording = {'title': 'No Date', 'transcription': 'Hello'}
        exporter = TranscriptionExporter(recording)
        path = self.temp_dir / 'nodate.txt'
        exporter.export_txt(path)
        content = path.read_text(encoding='utf-8')
        self.assertNotIn('Date:', content)

    def test_srt_timestamp_format(self):
        result = TranscriptionExporter._srt_timestamp(3661.5)
        self.assertEqual(result, '01:01:01,500')

    def test_srt_timestamp_zero(self):
        result = TranscriptionExporter._srt_timestamp(0.0)
        self.assertEqual(result, '00:00:00,000')

    def test_srt_skips_empty_segments(self):
        recording = dict(self.sample_recording)
        recording['segments'] = [
            {'start': 0.0, 'end': 1.0, 'text': 'Hello'},
            {'start': 1.0, 'end': 2.0, 'text': ''},
            {'start': 2.0, 'end': 3.0, 'text': 'World'},
        ]
        exporter = TranscriptionExporter(recording)
        path = self.temp_dir / 'skip.srt'
        exporter.export_srt(path)
        content = path.read_text(encoding='utf-8')
        # Should have indices 1 and 2 (empty segment skipped)
        self.assertIn('1\n', content)
        self.assertIn('2\n', content)
        self.assertNotIn('3\n', content)


if __name__ == '__main__':
    unittest.main()
