# Task 02: Wire transcription data into SpeakerPanel after diarization completes

## Metadata

| Field | Value |
|-------|-------|
| **Owner** | Developer |
| **Status** | TODO |
| **Depends On** | Task 01 |

## Description

After transcription processing finishes in `on_processing_finished()`, load the recording data into the main page SpeakerPanel. Set the vault manager on the panel for save support.

## Acceptance Criteria

- [ ] SpeakerPanel receives recording data after transcription completes
- [ ] Vault manager is set on SpeakerPanel during initialization
- [ ] Diarized transcription is preferred when available
