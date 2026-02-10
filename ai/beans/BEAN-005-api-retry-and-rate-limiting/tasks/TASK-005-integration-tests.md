# TASK-005: Write Integration Tests for Retry in Services

## Metadata

| Field     | Value       |
|-----------|-------------|
| Task      | TASK-005    |
| Bean      | BEAN-005    |
| Owner     | tech-qa     |
| Priority  | 5           |
| Depends   | TASK-002, TASK-003 |
| Status    | Done        |
| Started   | 2026-02-10 15:59 |
| Completed | 2026-02-10 16:00 |
| Duration  | —           |
| Tokens    | —           |

## Description

Create `tests/test_retry_integration.py` with tests verifying that retry logic is correctly wired into both the summarizer and whisper service.

## Implementation Details

- Test summarizer `summarize_text` retries on transient API error then succeeds
- Test summarizer `summarize_text` exhausts retries and returns None with user-friendly error
- Test whisper `_transcribe_api` retries on transient error then succeeds
- Test whisper `_transcribe_api` exhausts retries and raises TranscriptionException
- Mock `time.sleep` to avoid real delays
- Mock OpenAI client responses to simulate transient then success scenarios
- Verify retry count via mock call counts

## Acceptance Criteria

- [ ] `tests/test_retry_integration.py` exists with at least 4 test cases
- [ ] Summarizer retry+success scenario is tested
- [ ] Summarizer retry+failure scenario is tested
- [ ] Whisper service retry+success scenario is tested
- [ ] Whisper service retry+failure scenario is tested
- [ ] All tests pass with `pytest tests/test_retry_integration.py`
