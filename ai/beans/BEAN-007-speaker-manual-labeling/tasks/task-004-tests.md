# Task 004: Write Tests for Speaker Labeling

## Metadata

| Field | Value |
|-------|-------|
| Task ID | BEAN-007-T004 |
| Owner | tech-qa |
| Status | DONE |
| Depends On | T001, T002, T003 |
| Blocks | T005 |

## Description

Write comprehensive tests covering the speaker service logic (parsing, renaming, insertion) and vault integration. Ensure all existing tests continue to pass.

## Acceptance Criteria

- [ ] Tests for speaker parsing from transcription text
- [ ] Tests for bulk speaker rename
- [ ] Tests for manual speaker label insertion
- [ ] Tests for non-destructive backup of original transcription
- [ ] Tests for edge cases (empty text, no speakers, special characters)
- [ ] All existing tests pass (`pytest tests/`)
- [ ] Lint passes (`flake8 src/ tests/`)
