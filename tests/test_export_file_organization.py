"""
Tests for improved export file organization (BEAN-018).

Covers MarkdownGenerator subfolder/title-first naming and
vault export subfolder creation with title-based file naming.
"""

import shutil
import tempfile
import unittest
from pathlib import Path
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from export.markdown_generator import MarkdownGenerator
from export.utils import sanitize_title, create_unique_subfolder


class TestMarkdownGeneratorFileOrganization(unittest.TestCase):
    """Test MarkdownGenerator uses title-first filenames and subfolders."""

    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.generator = MarkdownGenerator(
            export_dir=str(self.temp_dir / "summaries")
        )
        self.sample_data = {
            'title': 'Sprint Planning',
            'created_at': '2026-01-15T09:30:00',
            'category': 'meeting',
            'duration': 1800,
            'summary': 'Team discussed upcoming sprint goals.',
            'transcription': 'Alice: Let us plan the sprint.',
        }

    def tearDown(self):
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_filename_is_title_based(self):
        """Output filename should be {Title}.md, no timestamp prefix."""
        result = self.generator.save_markdown_file(self.sample_data)
        self.assertEqual(result.name, "Sprint_Planning.md")

    def test_file_in_per_recording_subfolder(self):
        """Output should be inside a per-recording subfolder."""
        result = self.generator.save_markdown_file(self.sample_data)
        # Should be at summaries/Sprint_Planning/Sprint_Planning.md
        self.assertEqual(result.parent.name, "Sprint_Planning")

    def test_subfolder_inside_summaries_dir(self):
        """Per-recording subfolder should be inside the summaries directory."""
        result = self.generator.save_markdown_file(self.sample_data)
        summaries_dir = self.temp_dir / "summaries"
        self.assertEqual(result.parent.parent, summaries_dir)

    def test_content_still_valid(self):
        """Generated markdown content should still contain expected data."""
        result = self.generator.save_markdown_file(self.sample_data)
        content = result.read_text(encoding='utf-8')
        self.assertIn('Sprint Planning', content)
        self.assertIn('Team discussed upcoming sprint goals.', content)
        self.assertIn('Alice: Let us plan the sprint.', content)

    def test_special_characters_in_title(self):
        """Titles with special chars should produce safe filenames."""
        data = dict(self.sample_data)
        data['title'] = 'Meeting #3 @HQ!'
        result = self.generator.save_markdown_file(data)
        self.assertEqual(result.name, "Meeting_3_HQ.md")

    def test_no_timestamp_prefix_in_filename(self):
        """Filename should NOT start with a timestamp pattern."""
        result = self.generator.save_markdown_file(self.sample_data)
        # Old format was like 20260115_093000_Sprint_Planning.md
        self.assertFalse(
            result.name[0].isdigit(),
            f"Filename should not start with digit: {result.name}",
        )


class TestVaultExportSubfolderLogic(unittest.TestCase):
    """Test the vault export subfolder creation and naming logic."""

    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_export_creates_titled_subfolder(self):
        """Export should create a subfolder named after the title."""
        title = "Weekly Review"
        safe = sanitize_title(title)
        subfolder = create_unique_subfolder(self.temp_dir, safe)
        self.assertEqual(subfolder.name, "Weekly_Review")
        self.assertTrue(subfolder.exists())

    def test_audio_file_renamed_to_title(self):
        """Audio file should use title-based name with original extension."""
        title = "Daily Standup"
        safe = sanitize_title(title)
        subfolder = create_unique_subfolder(self.temp_dir, safe)

        # Simulate audio copy with new name
        original_filename = "recording_20260115_093000.wav"
        ext = Path(original_filename).suffix
        audio_name = f"{safe}{ext}"
        audio_path = subfolder / audio_name
        audio_path.write_bytes(b"fake audio")

        self.assertEqual(audio_path.name, "Daily_Standup.wav")
        self.assertTrue(audio_path.exists())

    def test_transcription_file_naming(self):
        """Transcription file should be named {Title}_transcription.txt."""
        safe = sanitize_title("Project Kickoff")
        subfolder = create_unique_subfolder(self.temp_dir, safe)
        txt_name = f"{safe}_transcription.txt"
        txt_path = subfolder / txt_name
        txt_path.write_text("Hello world", encoding="utf-8")
        self.assertEqual(txt_path.name, "Project_Kickoff_transcription.txt")

    def test_summary_file_naming(self):
        """Summary file should be named {Title}_summary.md."""
        safe = sanitize_title("Retrospective")
        subfolder = create_unique_subfolder(self.temp_dir, safe)
        md_name = f"{safe}_summary.md"
        md_path = subfolder / md_name
        md_path.write_text("# Summary", encoding="utf-8")
        self.assertEqual(md_path.name, "Retrospective_summary.md")

    def test_duplicate_export_creates_numbered_subfolder(self):
        """Exporting the same title twice creates a _2 suffixed folder."""
        safe = sanitize_title("Standup")
        first = create_unique_subfolder(self.temp_dir, safe)
        second = create_unique_subfolder(self.temp_dir, safe)
        self.assertEqual(first.name, "Standup")
        self.assertEqual(second.name, "Standup_2")


if __name__ == '__main__':
    unittest.main()
