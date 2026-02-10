# Task 003: Build Speaker Management Panel UI

## Metadata

| Field | Value |
|-------|-------|
| Task ID | BEAN-007-T003 |
| Owner | developer |
| Status | DONE |
| Depends On | T001, T002 |
| Blocks | T004 |

## Description

Create `src/gui/speaker_panel.py` with a `SpeakerPanel` QWidget that shows detected speakers with editable name fields, supports bulk rename, and allows manual insertion of speaker labels. Integrate this panel into `SummaryViewerDialog` as a new "Speakers" tab.

## Acceptance Criteria

- [ ] Speaker panel shows all detected speakers with editable name fields
- [ ] Renaming a speaker triggers bulk update of transcription text
- [ ] Manual speaker label insertion available for un-diarized transcriptions
- [ ] Save button updates the vault recording with new transcription
- [ ] Original transcription is backed up (non-destructive)
- [ ] Panel is accessible from the summary viewer's tab widget
- [ ] UI follows existing PySide6 dark theme patterns
