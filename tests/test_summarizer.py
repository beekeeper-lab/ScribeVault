"""
Unit tests for SummarizerService, including re-generation and style fix.
"""

import unittest
from unittest.mock import patch, MagicMock
import tempfile
import shutil
from pathlib import Path

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from ai.summarizer import SummarizerService  # noqa: E402


def _make_mock_response(content: str):
    """Create a mock OpenAI response."""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = content
    return mock_response


class TestSummarizeWithPrompt(unittest.TestCase):
    """Tests for the new summarize_with_prompt method."""

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    @patch("ai.summarizer.openai.OpenAI")
    def setUp(self, mock_openai_cls):
        self.mock_client = MagicMock()
        mock_openai_cls.return_value = self.mock_client
        self.service = SummarizerService()

    def test_summarize_with_custom_prompt(self):
        """Custom prompt is sent as system message."""
        self.mock_client.chat.completions.create.return_value = (
            _make_mock_response("Action item 1\nAction item 2")
        )

        result = self.service.summarize_with_prompt(
            "Meeting transcript...",
            "Extract action items from this transcript.",
        )

        self.assertEqual(result, "Action item 1\nAction item 2")

        # Verify the prompt was used as system message
        call_args = self.mock_client.chat.completions.create.call_args
        messages = call_args[1]["messages"]
        self.assertEqual(
            messages[0]["content"],
            "Extract action items from this transcript.",
        )

    def test_summarize_with_prompt_returns_none_on_error(self):
        """Returns None when API call fails."""
        self.mock_client.chat.completions.create.side_effect = Exception(
            "API error"
        )

        result = self.service.summarize_with_prompt("text", "prompt")
        self.assertIsNone(result)

    def test_summarize_with_prompt_uses_higher_max_tokens(self):
        """Custom prompt summarization uses 1000 max_tokens."""
        self.mock_client.chat.completions.create.return_value = (
            _make_mock_response("result")
        )
        self.service.summarize_with_prompt("text", "prompt")

        call_args = self.mock_client.chat.completions.create.call_args
        self.assertEqual(call_args[1]["max_tokens"], 1000)


class TestStyleParameterFix(unittest.TestCase):
    """Tests for the summary style parameter bug fix."""

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    @patch("ai.summarizer.openai.OpenAI")
    def setUp(self, mock_openai_cls):
        self.mock_client = MagicMock()
        mock_openai_cls.return_value = self.mock_client
        self.service = SummarizerService()
        self.service.markdown_generator = None  # Disable markdown gen

    def test_meeting_with_default_style_uses_structured(self):
        """Meetings with default 'concise' style use structured summary."""
        self.mock_client.chat.completions.create.return_value = (
            _make_mock_response("Structured meeting summary")
        )

        result = self.service.generate_summary_with_markdown(
            {"transcription": "Meeting text...", "category": "meeting"},
            style="concise",
        )

        self.assertEqual(
            result["summary"],
            "Structured meeting summary",
        )
        # Verify structured prompt was used (longer prompt text)
        call_args = self.mock_client.chat.completions.create.call_args
        system_msg = call_args[1]["messages"][0]["content"]
        self.assertIn("structured", system_msg.lower())

    def test_meeting_with_explicit_style_uses_style(self):
        """Meetings with explicit non-default style respect it."""
        self.mock_client.chat.completions.create.return_value = (
            _make_mock_response("Bullet point summary")
        )

        result = self.service.generate_summary_with_markdown(
            {"transcription": "Meeting text...", "category": "meeting"},
            style="bullet_points",
        )

        self.assertEqual(result["summary"], "Bullet point summary")
        # Verify bullet_points style was used, not structured
        call_args = self.mock_client.chat.completions.create.call_args
        system_msg = call_args[1]["messages"][0]["content"]
        self.assertIn("bullet", system_msg.lower())

    def test_meeting_with_detailed_style(self):
        """Meetings with 'detailed' style use detailed prompt."""
        self.mock_client.chat.completions.create.return_value = (
            _make_mock_response("Detailed summary")
        )

        result = self.service.generate_summary_with_markdown(
            {"transcription": "Meeting text...", "category": "meeting"},
            style="detailed",
        )

        self.assertEqual(result["summary"], "Detailed summary")
        call_args = self.mock_client.chat.completions.create.call_args
        system_msg = call_args[1]["messages"][0]["content"]
        self.assertIn("detailed", system_msg.lower())

    def test_custom_prompt_overrides_all(self):
        """Custom template_prompt overrides style and category logic."""
        self.mock_client.chat.completions.create.return_value = (
            _make_mock_response("Custom result")
        )

        result = self.service.generate_summary_with_markdown(
            {"transcription": "Meeting text...", "category": "meeting"},
            style="concise",
            template_prompt="List all mentioned technologies.",
        )

        self.assertEqual(result["summary"], "Custom result")
        call_args = self.mock_client.chat.completions.create.call_args
        system_msg = call_args[1]["messages"][0]["content"]
        self.assertEqual(
            system_msg,
            "List all mentioned technologies.",
        )

    def test_non_meeting_with_concise_style(self):
        """Non-meeting recordings with concise style use concise prompt."""
        self.mock_client.chat.completions.create.return_value = (
            _make_mock_response("Concise note")
        )

        result = self.service.generate_summary_with_markdown(
            {"transcription": "Note text...", "category": "note"},
            style="concise",
        )

        self.assertEqual(result["summary"], "Concise note")
        call_args = self.mock_client.chat.completions.create.call_args
        system_msg = call_args[1]["messages"][0]["content"]
        self.assertIn("concise", system_msg.lower())

    def test_call_category_default_uses_structured(self):
        """Call category with default style uses structured summary."""
        self.mock_client.chat.completions.create.return_value = (
            _make_mock_response("Call structured")
        )

        self.service.generate_summary_with_markdown(
            {"transcription": "Call text...", "category": "call"},
            style="concise",
        )

        call_args = self.mock_client.chat.completions.create.call_args
        system_msg = call_args[1]["messages"][0]["content"]
        self.assertIn("structured", system_msg.lower())

    def test_interview_with_bullet_points_style(self):
        """Interview with bullet_points style respects it."""
        self.mock_client.chat.completions.create.return_value = (
            _make_mock_response("Interview bullets")
        )

        self.service.generate_summary_with_markdown(
            {"transcription": "Interview text...", "category": "interview"},
            style="bullet_points",
        )

        call_args = self.mock_client.chat.completions.create.call_args
        system_msg = call_args[1]["messages"][0]["content"]
        self.assertIn("bullet", system_msg.lower())

    def test_empty_transcription_returns_error(self):
        """Empty transcription returns error in result."""
        result = self.service.generate_summary_with_markdown(
            {"transcription": "", "category": "note"},
        )
        self.assertIsNotNone(result["error"])
        self.assertIsNone(result["summary"])

    def test_missing_transcription_returns_error(self):
        """Missing transcription key returns error."""
        result = self.service.generate_summary_with_markdown(
            {"category": "note"},
        )
        self.assertIsNotNone(result["error"])


class TestSummaryHistoryStorage(unittest.TestCase):
    """Tests for summary history in VaultManager."""

    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())

        from vault.manager import VaultManager

        self.vault_manager = VaultManager(vault_dir=self.temp_dir)

    def tearDown(self):
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_add_summary_creates_history(self):
        """add_summary creates a summary_history entry."""
        rec_id = self.vault_manager.add_recording(
            filename="test.wav",
            transcription="Some text",
        )

        self.vault_manager.add_summary(
            rec_id,
            "Summary 1",
            template_name="Brief Summary",
        )

        recordings = self.vault_manager.get_recordings()
        rec = recordings[0]

        self.assertEqual(rec["summary"], "Summary 1")
        self.assertEqual(len(rec["summary_history"]), 1)
        self.assertEqual(rec["summary_history"][0]["content"], "Summary 1")
        self.assertEqual(
            rec["summary_history"][0]["template_name"],
            "Brief Summary",
        )

    def test_add_multiple_summaries(self):
        """Multiple summaries append to history."""
        rec_id = self.vault_manager.add_recording(filename="test.wav")

        self.vault_manager.add_summary(rec_id, "First summary")
        self.vault_manager.add_summary(
            rec_id,
            "Second summary",
            template_name="Action Items",
        )
        self.vault_manager.add_summary(
            rec_id,
            "Third summary",
            template_name="Custom",
        )

        recordings = self.vault_manager.get_recordings()
        rec = recordings[0]

        # Latest summary is the main one
        self.assertEqual(rec["summary"], "Third summary")
        # All three in history
        self.assertEqual(len(rec["summary_history"]), 3)
        self.assertEqual(rec["summary_history"][0]["content"], "First summary")
        self.assertEqual(
            rec["summary_history"][1]["content"],
            "Second summary",
        )
        self.assertEqual(rec["summary_history"][2]["content"], "Third summary")

    def test_add_summary_invalid_recording(self):
        """add_summary raises for non-existent recording."""
        from vault.manager import VaultException

        with self.assertRaises(VaultException):
            self.vault_manager.add_summary(99999, "summary")

    def test_summary_history_has_timestamps(self):
        """Each history entry has a created_at timestamp."""
        rec_id = self.vault_manager.add_recording(filename="test.wav")
        self.vault_manager.add_summary(rec_id, "Summary")

        recordings = self.vault_manager.get_recordings()
        entry = recordings[0]["summary_history"][0]
        self.assertIn("created_at", entry)
        self.assertIsNotNone(entry["created_at"])

    def test_summary_history_preserves_prompt(self):
        """History entries store the prompt used."""
        rec_id = self.vault_manager.add_recording(filename="test.wav")
        self.vault_manager.add_summary(
            rec_id,
            "Summary",
            template_name="Custom",
            prompt_used="Extract action items",
        )

        recordings = self.vault_manager.get_recordings()
        entry = recordings[0]["summary_history"][0]
        self.assertEqual(entry["prompt_used"], "Extract action items")

    def test_empty_summary_history_returns_list(self):
        """Recordings without history return empty list."""
        self.vault_manager.add_recording(filename="test.wav")
        recordings = self.vault_manager.get_recordings()
        self.assertEqual(recordings[0]["summary_history"], [])


if __name__ == "__main__":
    unittest.main()
