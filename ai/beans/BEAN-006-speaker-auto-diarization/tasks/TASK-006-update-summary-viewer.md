# TASK-006: Update Summary Viewer with Speaker Display

## Metadata

| Field     | Value        |
|-----------|--------------|
| Task      | TASK-006     |
| Bean      | BEAN-006     |
| Owner     | developer    |
| Priority  | 6            |
| Status    | TODO         |
| Depends   | TASK-005     |
| Started   | —            |
| Completed | —            |
| Duration  | —            |
| Tokens    | —            |

## Description

Update `src/gui/qt_summary_viewer.py` to display speaker labels with visual distinction in the transcription view. When a diarized transcription is available, render it with colored/styled speaker labels instead of plain text.

**Visual treatment:**
- Each speaker gets a distinct visual style (bold label, optional color)
- Speaker labels are clearly distinguished from transcription text
- Falls back to plain text display when no diarization data exists

## Acceptance Criteria

- [ ] Summary viewer displays diarized transcription when available
- [ ] Speaker labels have visual distinction (bold, color-coded)
- [ ] Falls back to plain text display for non-diarized transcriptions
- [ ] No crash or visual regression for existing recordings
