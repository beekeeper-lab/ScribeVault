# TASK-001: Create Shared Retry Utility Module

## Metadata

| Field     | Value       |
|-----------|-------------|
| Task      | TASK-001    |
| Bean      | BEAN-005    |
| Owner     | developer   |
| Priority  | 1           |
| Depends   | none        |
| Status    | Done        |
| Started   | 2026-02-10 15:55 |
| Completed | 2026-02-10 15:56 |
| Duration  | —           |
| Tokens    | —           |

## Description

Create `src/utils/retry.py` containing a reusable retry decorator/wrapper with exponential backoff. This module will be shared by both the summarizer and whisper service to avoid code duplication.

## Implementation Details

- Create `src/utils/__init__.py` (empty)
- Create `src/utils/retry.py` with:
  - A `retry_on_transient_error` decorator that wraps callables
  - Default config: max 3 retries, base delays of 1s/2s/4s (exponential backoff)
  - Retryable conditions: `openai.RateLimitError` (429), `openai.APIStatusError` with status 500/502/503, `openai.APITimeoutError`, `openai.APIConnectionError`
  - Non-retryable errors (e.g., 401 auth, 400 bad request) should propagate immediately
  - Log each retry attempt at `logging.WARNING` level with attempt number and wait time
  - After exhausting retries, raise a user-friendly error message (not raw API error)
  - Accept configurable `max_retries` and `base_delay` parameters

## Acceptance Criteria

- [ ] `src/utils/retry.py` exists with a decorator/wrapper function
- [ ] Exponential backoff follows 1s, 2s, 4s schedule (base_delay * 2^attempt)
- [ ] Only transient errors (429, 500, 502, 503, timeout, connection) trigger retries
- [ ] Non-retryable errors propagate immediately without retry
- [ ] Each retry attempt is logged at WARNING level
- [ ] Final failure wraps the error in a user-friendly message
- [ ] `max_retries` and `base_delay` are configurable parameters
