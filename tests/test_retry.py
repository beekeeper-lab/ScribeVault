"""
Unit tests for the retry utility module.
"""

import sys
import os
import unittest
from unittest.mock import patch, MagicMock, call

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import openai  # noqa: E402
from utils.retry import (  # noqa: E402
    retry_on_transient_error, is_retryable_error, APIRetryError,
)


def _make_rate_limit_error():
    """Create a mock RateLimitError (HTTP 429)."""
    response = MagicMock()
    response.status_code = 429
    response.headers = {}
    response.json.return_value = {"error": {"message": "Rate limit exceeded"}}
    return openai.RateLimitError(
        message="Rate limit exceeded",
        response=response,
        body={"error": {"message": "Rate limit exceeded"}},
    )


def _make_api_status_error(status_code):
    """Create a mock APIStatusError with the given status code."""
    response = MagicMock()
    response.status_code = status_code
    response.headers = {}
    msg = f"Server error {status_code}"
    response.json.return_value = {"error": {"message": msg}}
    return openai.APIStatusError(
        message=msg,
        response=response,
        body={"error": {"message": msg}},
    )


def _make_timeout_error():
    """Create a mock APITimeoutError."""
    request = MagicMock()
    return openai.APITimeoutError(request=request)


def _make_connection_error():
    """Create a mock APIConnectionError."""
    request = MagicMock()
    return openai.APIConnectionError(request=request)


def _make_auth_error():
    """Create a mock AuthenticationError (HTTP 401) — not retryable."""
    response = MagicMock()
    response.status_code = 401
    response.headers = {}
    response.json.return_value = {"error": {"message": "Invalid API key"}}
    return openai.AuthenticationError(
        message="Invalid API key",
        response=response,
        body={"error": {"message": "Invalid API key"}},
    )


class TestIsRetryableError(unittest.TestCase):
    """Tests for the is_retryable_error function."""

    def test_rate_limit_error_is_retryable(self):
        self.assertTrue(is_retryable_error(_make_rate_limit_error()))

    def test_timeout_error_is_retryable(self):
        self.assertTrue(is_retryable_error(_make_timeout_error()))

    def test_connection_error_is_retryable(self):
        self.assertTrue(is_retryable_error(_make_connection_error()))

    def test_server_500_is_retryable(self):
        self.assertTrue(is_retryable_error(_make_api_status_error(500)))

    def test_server_502_is_retryable(self):
        self.assertTrue(is_retryable_error(_make_api_status_error(502)))

    def test_server_503_is_retryable(self):
        self.assertTrue(is_retryable_error(_make_api_status_error(503)))

    def test_auth_error_not_retryable(self):
        self.assertFalse(is_retryable_error(_make_auth_error()))

    def test_bad_request_not_retryable(self):
        self.assertFalse(is_retryable_error(_make_api_status_error(400)))

    def test_generic_exception_not_retryable(self):
        self.assertFalse(is_retryable_error(ValueError("bad value")))


class TestRetryDecorator(unittest.TestCase):
    """Tests for the retry_on_transient_error decorator."""

    @patch('utils.retry.time.sleep')
    def test_success_no_retry(self, mock_sleep):
        """Successful call should not trigger any retries."""
        mock_func = MagicMock(return_value="ok")
        decorated = retry_on_transient_error()(mock_func)

        result = decorated()

        self.assertEqual(result, "ok")
        mock_func.assert_called_once()
        mock_sleep.assert_not_called()

    @patch('utils.retry.time.sleep')
    def test_retry_on_rate_limit_then_success(self, mock_sleep):
        """Should retry on RateLimitError and succeed on second attempt."""
        mock_func = MagicMock(
            side_effect=[_make_rate_limit_error(), "ok"]
        )
        decorated = retry_on_transient_error()(mock_func)

        result = decorated()

        self.assertEqual(result, "ok")
        self.assertEqual(mock_func.call_count, 2)
        mock_sleep.assert_called_once_with(1.0)

    @patch('utils.retry.time.sleep')
    def test_retry_on_500_then_success(self, mock_sleep):
        """Should retry on 500 error and succeed on second attempt."""
        mock_func = MagicMock(
            side_effect=[_make_api_status_error(500), "ok"]
        )
        decorated = retry_on_transient_error()(mock_func)

        result = decorated()

        self.assertEqual(result, "ok")
        self.assertEqual(mock_func.call_count, 2)

    @patch('utils.retry.time.sleep')
    def test_retry_on_timeout_then_success(self, mock_sleep):
        """Should retry on timeout and succeed on second attempt."""
        mock_func = MagicMock(
            side_effect=[_make_timeout_error(), "ok"]
        )
        decorated = retry_on_transient_error()(mock_func)

        result = decorated()

        self.assertEqual(result, "ok")
        self.assertEqual(mock_func.call_count, 2)

    @patch('utils.retry.time.sleep')
    def test_retry_on_connection_error_then_success(self, mock_sleep):
        """Should retry on connection error and succeed on second attempt."""
        mock_func = MagicMock(
            side_effect=[_make_connection_error(), "ok"]
        )
        decorated = retry_on_transient_error()(mock_func)

        result = decorated()

        self.assertEqual(result, "ok")
        self.assertEqual(mock_func.call_count, 2)

    @patch('utils.retry.time.sleep')
    def test_exponential_backoff_timing(self, mock_sleep):
        """Should use exponential backoff: 1s, 2s, 4s."""
        mock_func = MagicMock(
            side_effect=[
                _make_rate_limit_error(),
                _make_rate_limit_error(),
                _make_rate_limit_error(),
                "ok",
            ]
        )
        decorated = retry_on_transient_error(max_retries=3)(mock_func)

        result = decorated()

        self.assertEqual(result, "ok")
        self.assertEqual(mock_func.call_count, 4)
        mock_sleep.assert_has_calls([call(1.0), call(2.0), call(4.0)])

    @patch('utils.retry.time.sleep')
    def test_max_retries_exhausted(self, mock_sleep):
        """Should raise APIRetryError after max retries exhausted."""
        error = _make_rate_limit_error()
        mock_func = MagicMock(side_effect=error)
        decorated = retry_on_transient_error(max_retries=3)(mock_func)

        with self.assertRaises(APIRetryError) as ctx:
            decorated()

        self.assertIn("failed after 3 retries", str(ctx.exception))
        self.assertEqual(ctx.exception.original_error, error)
        # 1 initial + 3 retries = 4 calls
        self.assertEqual(mock_func.call_count, 4)
        # 3 sleeps (before retries 1, 2, 3)
        self.assertEqual(mock_sleep.call_count, 3)

    @patch('utils.retry.time.sleep')
    def test_non_retryable_error_propagates_immediately(self, mock_sleep):
        """Non-retryable errors should propagate without retry."""
        auth_error = _make_auth_error()
        mock_func = MagicMock(side_effect=auth_error)
        decorated = retry_on_transient_error()(mock_func)

        with self.assertRaises(openai.AuthenticationError):
            decorated()

        mock_func.assert_called_once()
        mock_sleep.assert_not_called()

    @patch('utils.retry.time.sleep')
    def test_custom_max_retries(self, mock_sleep):
        """Should respect custom max_retries parameter."""
        mock_func = MagicMock(side_effect=_make_rate_limit_error())
        decorated = retry_on_transient_error(max_retries=1)(mock_func)

        with self.assertRaises(APIRetryError):
            decorated()

        # 1 initial + 1 retry = 2 calls
        self.assertEqual(mock_func.call_count, 2)

    @patch('utils.retry.time.sleep')
    def test_custom_base_delay(self, mock_sleep):
        """Should respect custom base_delay parameter."""
        mock_func = MagicMock(
            side_effect=[_make_rate_limit_error(), "ok"]
        )
        decorated = retry_on_transient_error(base_delay=0.5)(mock_func)

        result = decorated()

        self.assertEqual(result, "ok")
        mock_sleep.assert_called_once_with(0.5)

    @patch('utils.retry.time.sleep')
    def test_generic_exception_not_retried(self, mock_sleep):
        """ValueError and other non-API exceptions should not be retried."""
        mock_func = MagicMock(side_effect=ValueError("bad input"))
        decorated = retry_on_transient_error()(mock_func)

        with self.assertRaises(ValueError):
            decorated()

        mock_func.assert_called_once()
        mock_sleep.assert_not_called()


if __name__ == '__main__':
    unittest.main()
