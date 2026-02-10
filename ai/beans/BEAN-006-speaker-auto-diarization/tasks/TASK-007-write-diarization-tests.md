# TASK-007: Write Unit Tests for Diarization

## Metadata

| Field     | Value        |
|-----------|--------------|
| Task      | TASK-007     |
| Bean      | BEAN-006     |
| Owner     | tech-qa      |
| Priority  | 7            |
| Status    | TODO         |
| Depends   | TASK-001, TASK-003 |
| Started   | —            |
| Completed | —            |
| Duration  | —            |
| Tokens    | —            |

## Description

Write comprehensive unit tests for the diarization feature covering:

1. `DiarizationService` — test diarize method with mocked audio data
2. `DiarizationResult` — test `to_labeled_text()` formatting
3. `WhisperService.transcribe_with_diarization()` — test integration with mocked Whisper
4. Fallback behavior — test graceful degradation when diarization fails
5. Configuration — test diarization settings enable/disable

Test file: `tests/test_diarization.py`

## Acceptance Criteria

- [ ] `tests/test_diarization.py` exists with test cases
- [ ] Tests cover DiarizationService.diarize() with mocked inputs
- [ ] Tests cover DiarizationResult.to_labeled_text() output format
- [ ] Tests cover fallback behavior when diarization fails
- [ ] Tests cover diarization enabled/disabled configuration
- [ ] All tests pass with `pytest tests/test_diarization.py`
