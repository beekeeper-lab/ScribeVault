# TASK-003: Integrate Retry into Whisper Service

## Metadata

| Field     | Value       |
|-----------|-------------|
| Task      | TASK-003    |
| Bean      | BEAN-005    |
| Owner     | developer   |
| Priority  | 3           |
| Depends   | TASK-001    |
| Status    | Done        |
| Started   | 2026-02-10 15:57 |
| Completed | 2026-02-10 15:58 |
| Duration  | —           |
| Tokens    | —           |

## Description

Apply the shared retry utility to the 2 OpenAI API call sites in `src/transcription/whisper_service.py`:
1. `_transcribe_api` (line 136)
2. `_transcribe_api_with_timestamps` (line 205)

## Implementation Details

- Import the retry utility from `src/utils/retry.py`
- Wrap each `self.client.audio.transcriptions.create(...)` call with retry logic
- Keep the existing `TranscriptionException` pattern — the retry wrapper should re-raise as `TranscriptionException` with a user-friendly message after exhausting retries
- The `_transcribe_api_with_timestamps` method currently silently returns None on error; update it to use retry then return None only after retries are exhausted
- Do not change public method signatures

## Acceptance Criteria

- [ ] Both API call sites in whisper service use the shared retry wrapper
- [ ] Transient errors trigger automatic retry with exponential backoff
- [ ] `_transcribe_api` raises `TranscriptionException` with user-friendly message after retries exhausted
- [ ] `_transcribe_api_with_timestamps` retries before returning None
- [ ] Retry attempts are logged at WARNING level
- [ ] Public method signatures are unchanged
