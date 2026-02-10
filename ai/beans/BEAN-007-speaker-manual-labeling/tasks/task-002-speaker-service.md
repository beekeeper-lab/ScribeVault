# Task 002: Implement Speaker Management Service

## Metadata

| Field | Value |
|-------|-------|
| Task ID | BEAN-007-T002 |
| Owner | developer |
| Status | DONE |
| Depends On | T001 |
| Blocks | T003, T004 |

## Description

Create `src/transcription/speaker_service.py` with logic for parsing speaker labels from transcriptions, renaming speakers (bulk update), and inserting speaker labels into un-diarized text.

## Acceptance Criteria

- [ ] Parse transcription text to extract unique speakers and segments
- [ ] Rename a speaker across all occurrences in a transcription
- [ ] Insert speaker labels at arbitrary positions in un-diarized text
- [ ] Preserve original transcription text for backup/undo
- [ ] Handle edge cases: empty text, no speakers, malformed labels
