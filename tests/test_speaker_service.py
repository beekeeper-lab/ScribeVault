"""
Unit tests for speaker management service.
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from transcription.speaker_service import (
    parse_speakers,
    parse_segments,
    rename_speaker,
    insert_speaker_label,
    insert_speaker_at_line,
    build_transcription,
    has_speaker_labels,
)


class TestParseSpeakers(unittest.TestCase):
    """Tests for parse_speakers()."""

    def test_basic_two_speakers(self):
        text = "Speaker 1: Hello\nSpeaker 2: Hi there"
        result = parse_speakers(text)
        self.assertEqual(result, ["Speaker 1", "Speaker 2"])

    def test_named_speakers(self):
        text = "Alice: Hello\nBob: Hi\nAlice: How are you?"
        result = parse_speakers(text)
        self.assertEqual(result, ["Alice", "Bob"])

    def test_empty_string(self):
        self.assertEqual(parse_speakers(""), [])

    def test_none_input(self):
        self.assertEqual(parse_speakers(None), [])

    def test_whitespace_only(self):
        self.assertEqual(parse_speakers("   \n  "), [])

    def test_no_speakers(self):
        text = "This is plain text without any speaker labels."
        self.assertEqual(parse_speakers(text), [])

    def test_single_speaker(self):
        text = "Speaker 1: This is a monologue."
        self.assertEqual(parse_speakers(text), ["Speaker 1"])

    def test_preserves_first_appearance_order(self):
        text = "Bob: First\nAlice: Second\nCharlie: Third\nBob: Again"
        result = parse_speakers(text)
        self.assertEqual(result, ["Bob", "Alice", "Charlie"])


class TestParseSegments(unittest.TestCase):
    """Tests for parse_segments()."""

    def test_basic_segments(self):
        text = "Alice: Hello\nBob: World"
        segments = parse_segments(text)
        self.assertEqual(len(segments), 2)
        self.assertEqual(segments[0].speaker, "Alice")
        self.assertEqual(segments[0].text, "Hello")
        self.assertEqual(segments[1].speaker, "Bob")
        self.assertEqual(segments[1].text, "World")

    def test_empty_string(self):
        self.assertEqual(parse_segments(""), [])

    def test_no_speakers_returns_single_segment(self):
        text = "Plain text without speakers."
        segments = parse_segments(text)
        self.assertEqual(len(segments), 1)
        self.assertEqual(segments[0].speaker, "")
        self.assertEqual(segments[0].text, text)

    def test_multiline_segment(self):
        text = "Alice: Hello there.\nHow are you doing today?"
        segments = parse_segments(text)
        self.assertEqual(len(segments), 1)
        self.assertEqual(segments[0].speaker, "Alice")
        self.assertIn("Hello there.", segments[0].text)

    def test_position_tracking(self):
        text = "Alice: Hi\nBob: Hey"
        segments = parse_segments(text)
        self.assertEqual(segments[0].start_pos, 0)
        self.assertGreater(segments[1].start_pos, 0)


class TestRenameSpeaker(unittest.TestCase):
    """Tests for rename_speaker()."""

    def test_basic_rename(self):
        text = "Speaker 1: Hello\nSpeaker 2: Hi\nSpeaker 1: Bye"
        result = rename_speaker(text, "Speaker 1", "Alice")
        self.assertIn("Alice: Hello", result)
        self.assertIn("Speaker 2: Hi", result)
        self.assertIn("Alice: Bye", result)

    def test_rename_preserves_other_speakers(self):
        text = "Alice: Hello\nBob: Hi"
        result = rename_speaker(text, "Alice", "Carol")
        self.assertIn("Carol: Hello", result)
        self.assertIn("Bob: Hi", result)

    def test_rename_same_name_noop(self):
        text = "Alice: Hello"
        result = rename_speaker(text, "Alice", "Alice")
        self.assertEqual(result, text)

    def test_empty_old_name(self):
        text = "Alice: Hello"
        result = rename_speaker(text, "", "Bob")
        self.assertEqual(result, text)

    def test_empty_new_name(self):
        text = "Alice: Hello"
        result = rename_speaker(text, "Alice", "")
        self.assertEqual(result, text)

    def test_none_transcription(self):
        result = rename_speaker(None, "Alice", "Bob")
        self.assertEqual(result, "")

    def test_empty_transcription(self):
        result = rename_speaker("", "Alice", "Bob")
        self.assertEqual(result, "")

    def test_no_matching_speaker(self):
        text = "Alice: Hello"
        result = rename_speaker(text, "Bob", "Carol")
        self.assertEqual(result, text)

    def test_special_characters_in_name(self):
        text = "Dr. Smith: Patient notes"
        result = rename_speaker(text, "Dr. Smith", "Dr. Jones")
        self.assertIn("Dr. Jones: Patient notes", result)


class TestInsertSpeakerLabel(unittest.TestCase):
    """Tests for insert_speaker_label()."""

    def test_insert_at_beginning(self):
        text = "Hello there"
        result = insert_speaker_label(text, 0, "Alice")
        self.assertTrue(result.startswith("\nAlice: Hello"))

    def test_insert_at_middle(self):
        text = "Hello there world"
        result = insert_speaker_label(text, 6, "Bob")
        self.assertIn("Bob: ", result)

    def test_insert_into_empty(self):
        result = insert_speaker_label("", 0, "Alice")
        self.assertEqual(result, "Alice: ")

    def test_empty_speaker_name(self):
        text = "Hello"
        result = insert_speaker_label(text, 0, "")
        self.assertEqual(result, text)

    def test_none_transcription(self):
        result = insert_speaker_label(None, 0, "Alice")
        self.assertEqual(result, "Alice: ")


class TestInsertSpeakerAtLine(unittest.TestCase):
    """Tests for insert_speaker_at_line()."""

    def test_insert_at_first_line(self):
        text = "Hello world"
        result = insert_speaker_at_line(text, 0, "Alice")
        self.assertEqual(result, "Alice: Hello world")

    def test_insert_at_second_line(self):
        text = "Line 1\nLine 2\nLine 3"
        result = insert_speaker_at_line(text, 1, "Bob")
        lines = result.split('\n')
        self.assertEqual(lines[0], "Line 1")
        self.assertEqual(lines[1], "Bob: Line 2")
        self.assertEqual(lines[2], "Line 3")

    def test_replace_existing_label(self):
        text = "Speaker 1: Hello"
        result = insert_speaker_at_line(text, 0, "Alice")
        self.assertEqual(result, "Alice: Hello")

    def test_empty_transcription(self):
        result = insert_speaker_at_line("", 0, "Alice")
        self.assertEqual(result, "")

    def test_empty_speaker_name(self):
        text = "Hello"
        result = insert_speaker_at_line(text, 0, "")
        self.assertEqual(result, text)

    def test_line_out_of_range_clamps(self):
        text = "Line 1\nLine 2"
        result = insert_speaker_at_line(text, 99, "Alice")
        lines = result.split('\n')
        self.assertEqual(lines[0], "Line 1")
        self.assertEqual(lines[1], "Alice: Line 2")


class TestBuildTranscription(unittest.TestCase):
    """Tests for build_transcription()."""

    def test_basic_build(self):
        segments = [("Alice", "Hello"), ("Bob", "Hi")]
        result = build_transcription(segments)
        self.assertEqual(result, "Alice: Hello\nBob: Hi")

    def test_empty_speaker(self):
        segments = [("", "Plain text"), ("Alice", "Hello")]
        result = build_transcription(segments)
        self.assertEqual(result, "Plain text\nAlice: Hello")

    def test_empty_list(self):
        result = build_transcription([])
        self.assertEqual(result, "")


class TestHasSpeakerLabels(unittest.TestCase):
    """Tests for has_speaker_labels()."""

    def test_with_labels(self):
        self.assertTrue(has_speaker_labels("Speaker 1: Hello"))

    def test_without_labels(self):
        self.assertFalse(has_speaker_labels("Plain text"))

    def test_empty_string(self):
        self.assertFalse(has_speaker_labels(""))

    def test_none_input(self):
        self.assertFalse(has_speaker_labels(None))


class TestSpeakerVaultIntegration(unittest.TestCase):
    """Integration tests: speaker service + vault manager."""

    def setUp(self):
        import tempfile
        from pathlib import Path
        from vault.manager import VaultManager

        self.temp_dir = Path(tempfile.mkdtemp())
        self.vault = VaultManager(vault_dir=self.temp_dir)

    def tearDown(self):
        import shutil
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_rename_and_save(self):
        """Rename speakers, save to vault, reload and verify."""
        original = "Speaker 1: Hello\nSpeaker 2: Hi"
        rec_id = self.vault.add_recording(
            filename="test.wav",
            transcription=original,
        )

        updated = rename_speaker(original, "Speaker 1", "Alice")
        self.vault.update_recording(
            rec_id,
            transcription=updated,
            original_transcription=original,
        )

        recordings = self.vault.get_recordings()
        rec = next(r for r in recordings if r["id"] == rec_id)
        self.assertIn("Alice: Hello", rec["transcription"])
        self.assertEqual(rec["original_transcription"], original)

    def test_insert_and_save(self):
        """Insert speaker label, save to vault, reload and verify."""
        original = "Plain transcription text"
        rec_id = self.vault.add_recording(
            filename="test2.wav",
            transcription=original,
        )

        updated = insert_speaker_at_line(original, 0, "Bob")
        self.vault.update_recording(
            rec_id,
            transcription=updated,
            original_transcription=original,
        )

        recordings = self.vault.get_recordings()
        rec = next(r for r in recordings if r["id"] == rec_id)
        self.assertIn("Bob: ", rec["transcription"])
        self.assertEqual(rec["original_transcription"], original)

    def test_non_destructive_original_preserved(self):
        """Ensure original transcription is preserved after edits."""
        original = "Speaker 1: Meeting notes"
        rec_id = self.vault.add_recording(
            filename="test3.wav",
            transcription=original,
        )

        # Rename twice
        step1 = rename_speaker(original, "Speaker 1", "Alice")
        step2 = rename_speaker(step1, "Alice", "Carol")

        self.vault.update_recording(
            rec_id,
            transcription=step2,
            original_transcription=original,
        )

        recordings = self.vault.get_recordings()
        rec = next(r for r in recordings if r["id"] == rec_id)
        self.assertIn("Carol: Meeting notes", rec["transcription"])
        self.assertEqual(rec["original_transcription"], original)


if __name__ == '__main__':
    unittest.main()
