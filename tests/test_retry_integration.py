"""
Integration tests verifying retry logic is correctly wired into
the summarizer and whisper services.
"""

import sys
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import openai  # noqa: E402
from ai.summarizer import SummarizerService  # noqa: E402
from transcription.whisper_service import (  # noqa: E402
    WhisperService, TranscriptionException,
)


def _make_rate_limit_error():
    """Create a mock RateLimitError (HTTP 429)."""
    response = MagicMock()
    response.status_code = 429
    response.headers = {}
    body = {"error": {"message": "Rate limit exceeded"}}
    response.json.return_value = body
    return openai.RateLimitError(
        message="Rate limit exceeded",
        response=response,
        body=body,
    )


def _make_chat_response(content="Test summary"):
    """Create a mock chat completion response."""
    response = MagicMock()
    response.choices = [MagicMock()]
    response.choices[0].message.content = content
    return response


class TestSummarizerRetryIntegration(unittest.TestCase):
    """Test retry behavior in SummarizerService."""

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    @patch('utils.retry.time.sleep')
    @patch('ai.summarizer.openai.OpenAI')
    def test_summarize_retries_then_succeeds(
        self, mock_openai_cls, mock_sleep
    ):
        """Summarizer retries on transient error then succeeds."""
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client

        mock_client.chat.completions.create.side_effect = [
            _make_rate_limit_error(),
            _make_chat_response("Retried summary"),
        ]

        service = SummarizerService()
        result = service.summarize_text("Some transcript text")

        self.assertEqual(result, "Retried summary")
        self.assertEqual(
            mock_client.chat.completions.create.call_count, 2
        )
        mock_sleep.assert_called_once_with(1.0)

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    @patch('utils.retry.time.sleep')
    @patch('ai.summarizer.openai.OpenAI')
    def test_summarize_exhausts_retries_returns_none(
        self, mock_openai_cls, mock_sleep
    ):
        """Summarizer returns None after exhausting retries."""
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client

        mock_client.chat.completions.create.side_effect = (
            _make_rate_limit_error()
        )

        service = SummarizerService()
        result = service.summarize_text("Some transcript text")

        self.assertIsNone(result)
        self.assertEqual(
            mock_client.chat.completions.create.call_count, 4
        )

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    @patch('utils.retry.time.sleep')
    @patch('ai.summarizer.openai.OpenAI')
    def test_categorize_retries_then_succeeds(
        self, mock_openai_cls, mock_sleep
    ):
        """Categorize retries on transient error then succeeds."""
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client

        mock_client.chat.completions.create.side_effect = [
            _make_rate_limit_error(),
            _make_chat_response("meeting"),
        ]

        service = SummarizerService()
        result = service.categorize_content("A meeting about X")

        self.assertEqual(result, "meeting")
        self.assertEqual(
            mock_client.chat.completions.create.call_count, 2
        )


class TestWhisperRetryIntegration(unittest.TestCase):
    """Test retry behavior in WhisperService."""

    def _make_temp_audio(self):
        """Create a temporary audio file for testing."""
        f = tempfile.NamedTemporaryFile(
            suffix=".wav", delete=False
        )
        f.write(b"fake audio data")
        f.close()
        return Path(f.name)

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    @patch('utils.retry.time.sleep')
    @patch('transcription.whisper_service.openai.OpenAI')
    def test_transcribe_api_retries_then_succeeds(
        self, mock_openai_cls, mock_sleep
    ):
        """Whisper API transcription retries and succeeds."""
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client

        mock_client.audio.transcriptions.create.side_effect = [
            _make_rate_limit_error(),
            "Transcribed text after retry",
        ]

        service = WhisperService(use_local=False)
        audio_path = self._make_temp_audio()

        try:
            result = service._transcribe_api(audio_path)
            self.assertEqual(result, "Transcribed text after retry")
            self.assertEqual(
                mock_client.audio.transcriptions.create.call_count,
                2,
            )
            mock_sleep.assert_called_once_with(1.0)
        finally:
            os.unlink(audio_path)

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    @patch('utils.retry.time.sleep')
    @patch('transcription.whisper_service.openai.OpenAI')
    def test_transcribe_api_exhausts_retries_raises(
        self, mock_openai_cls, mock_sleep
    ):
        """Whisper raises TranscriptionException after retries."""
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client

        mock_client.audio.transcriptions.create.side_effect = (
            _make_rate_limit_error()
        )

        service = WhisperService(use_local=False)
        audio_path = self._make_temp_audio()

        try:
            with self.assertRaises(TranscriptionException) as ctx:
                service._transcribe_api(audio_path)

            self.assertIn(
                "failed after multiple retries",
                str(ctx.exception),
            )
            self.assertEqual(
                mock_client.audio.transcriptions.create.call_count,
                4,
            )
        finally:
            os.unlink(audio_path)

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    @patch('utils.retry.time.sleep')
    @patch('transcription.whisper_service.openai.OpenAI')
    def test_timestamps_retries_then_succeeds(
        self, mock_openai_cls, mock_sleep
    ):
        """Whisper timestamp transcription retries and succeeds."""
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client

        mock_result = {"text": "Hello", "words": []}
        mock_client.audio.transcriptions.create.side_effect = [
            _make_rate_limit_error(),
            mock_result,
        ]

        service = WhisperService(use_local=False)
        audio_path = self._make_temp_audio()

        try:
            result = service._transcribe_api_with_timestamps(
                audio_path
            )
            self.assertEqual(result, mock_result)
            self.assertEqual(
                mock_client.audio.transcriptions.create.call_count,
                2,
            )
        finally:
            os.unlink(audio_path)


if __name__ == '__main__':
    unittest.main()
