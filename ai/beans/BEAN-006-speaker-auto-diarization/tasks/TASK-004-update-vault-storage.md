# TASK-004: Update Vault Storage for Diarized Transcription

## Metadata

| Field     | Value        |
|-----------|--------------|
| Task      | TASK-004     |
| Bean      | BEAN-006     |
| Owner     | developer    |
| Priority  | 4            |
| Status    | TODO         |
| Depends   | TASK-001     |
| Started   | —            |
| Completed | —            |
| Duration  | —            |
| Tokens    | —            |

## Description

Update the vault storage layer to store diarized transcription alongside the raw transcription. The recording data dict should include a `diarized_transcription` field.

Look at how `transcription` is currently stored in the recording data dict and the markdown generator, and add `diarized_transcription` as an additional field. The vault should store both so that speaker labels are preserved.

## Acceptance Criteria

- [ ] Recording data dict supports `diarized_transcription` field
- [ ] Diarized transcription is passed through the processing pipeline
- [ ] Existing recordings without diarization continue to work (backward compatible)
