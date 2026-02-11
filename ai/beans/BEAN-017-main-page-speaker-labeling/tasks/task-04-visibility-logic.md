# Task 04: Add visibility logic — show section only when speakers detected

## Metadata

| Field | Value |
|-------|-------|
| **Owner** | Developer |
| **Status** | TODO |
| **Depends On** | Task 02 |

## Description

Show the "Name Speakers" section only when the transcription contains speaker labels (detected via `parse_speakers()`). Hide it when no speakers are present. Auto-collapse when first shown.

## Acceptance Criteria

- [ ] Section visible only when speakers detected in transcription
- [ ] Section hidden when no speakers in transcription
- [ ] Section hidden and reset when starting a new recording
- [ ] Uses parse_speakers() from speaker_service for detection
