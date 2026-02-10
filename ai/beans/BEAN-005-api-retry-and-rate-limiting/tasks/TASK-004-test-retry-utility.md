# TASK-004: Write Tests for Retry Utility

## Metadata

| Field     | Value       |
|-----------|-------------|
| Task      | TASK-004    |
| Bean      | BEAN-005    |
| Owner     | tech-qa     |
| Priority  | 4           |
| Depends   | TASK-001    |
| Status    | Done        |
| Started   | 2026-02-10 15:58 |
| Completed | 2026-02-10 15:59 |
| Duration  | —           |
| Tokens    | —           |

## Description

Create `tests/test_retry.py` with comprehensive unit tests for the retry utility module.

## Implementation Details

- Test successful call (no retry needed)
- Test retry on RateLimitError (429) — verify 3 retries with correct backoff
- Test retry on APIStatusError with status 500, 502, 503
- Test retry on APITimeoutError
- Test retry on APIConnectionError
- Test non-retryable error (e.g., AuthenticationError 401) propagates immediately
- Test max retries exhausted raises user-friendly error
- Test configurable max_retries and base_delay
- Use `unittest.mock` to mock `time.sleep` so tests run instantly
- Mock OpenAI error classes appropriately

## Acceptance Criteria

- [ ] `tests/test_retry.py` exists with at least 8 test cases
- [ ] All transient error types (429, 500, 502, 503, timeout, connection) are tested
- [ ] Non-retryable error pass-through is tested
- [ ] Max retry exhaustion is tested
- [ ] Exponential backoff timing is verified (via mocked sleep)
- [ ] All tests pass with `pytest tests/test_retry.py`
