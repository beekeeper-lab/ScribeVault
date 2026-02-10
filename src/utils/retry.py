"""
Shared retry utility with exponential backoff for transient API errors.
"""

import functools
import logging
import time

import openai

logger = logging.getLogger(__name__)

# HTTP status codes that are considered transient and worth retrying
RETRYABLE_STATUS_CODES = {429, 500, 502, 503}


def is_retryable_error(error: Exception) -> bool:
    """Determine whether an error is transient and should be retried."""
    if isinstance(error, openai.RateLimitError):
        return True
    if isinstance(error, openai.APITimeoutError):
        return True
    if isinstance(error, openai.APIConnectionError):
        return True
    if isinstance(error, openai.APIStatusError):
        return getattr(error, "status_code", None) in RETRYABLE_STATUS_CODES
    return False


def retry_on_transient_error(max_retries: int = 3, base_delay: float = 1.0):
    """Decorator that retries a function on transient OpenAI API errors.

    Uses exponential backoff: base_delay * 2^attempt (1s, 2s, 4s by default).

    Args:
        max_retries: Maximum number of retry attempts (default 3).
        base_delay: Base delay in seconds for the first retry (default 1.0).

    Returns:
        Decorated function with retry behavior.
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if not is_retryable_error(e):
                        raise
                    if attempt < max_retries:
                        delay = base_delay * (2 ** attempt)
                        logger.warning(
                            "Transient API error (attempt %d/%d): %s. "
                            "Retrying in %.1fs...",
                            attempt + 1,
                            max_retries,
                            str(e),
                            delay,
                        )
                        time.sleep(delay)
                    else:
                        logger.warning(
                            "Transient API error (attempt %d/%d): %s. "
                            "No retries remaining.",
                            attempt + 1,
                            max_retries,
                            str(e),
                        )
            raise APIRetryError(
                f"API request failed after {max_retries} retries. "
                f"Please try again later.",
                original_error=last_error,
            )

        return wrapper

    return decorator


class APIRetryError(Exception):
    """Raised when all retry attempts have been exhausted."""

    def __init__(self, message: str, original_error: Exception = None):
        super().__init__(message)
        self.original_error = original_error
