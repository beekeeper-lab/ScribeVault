# Task 005: Write Tests for Thread Safety and Resource Cleanup

## Metadata

| Field | Value |
|-------|-------|
| Task ID | BEAN-002-T005 |
| Owner | tech-qa |
| Status | TODO |
| Depends On | T001, T002, T003, T004 |

## Description

Write unit tests verifying:
1. AudioRecorder thread safety (concurrent state changes don't corrupt state)
2. AudioRecorder cleanup works correctly (context manager, explicit cleanup)
3. SettingsManager thread safety (concurrent save/load doesn't corrupt)
4. No deadlocks under concurrent access

## Acceptance Criteria

- [ ] Tests for AudioRecorder lock protection
- [ ] Tests for AudioRecorder cleanup/context manager
- [ ] Tests for SettingsManager lock protection
- [ ] All tests pass with `pytest tests/`
- [ ] `flake8 src/ tests/` passes

## Files

- `tests/test_thread_safety.py` (new)
- `tests/test_audio_recorder.py` (update if needed)
