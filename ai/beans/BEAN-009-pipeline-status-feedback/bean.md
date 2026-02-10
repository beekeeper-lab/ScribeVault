# BEAN-009: Pipeline Status Feedback to User

## Metadata

| Field     | Value        |
|-----------|--------------|
| ID        | BEAN-009     |
| Title     | Pipeline Status Feedback to User |
| Type      | enhancement |
| Priority  | P2 |
| Status    | Unapproved   |
| Created   | 2026-02-10   |
| Started   |              |
| Completed |              |
| Duration  |              |

## Problem Statement

The recording to transcription to summarization to save pipeline has multiple stages where errors can occur silently. Currently, each failure is logged but the user sees either "Processing complete!" or nothing. Example: user records, transcription fails, summary is skipped, vault save succeeds -- user sees success but only has an audio file with no text. No indication of which steps worked and which failed.

## Goal

Users see clear, real-time status for each pipeline stage (recording, transcription, summarization, vault save) with explicit success/failure indicators.

## Scope

### In Scope

- Add a pipeline status panel/indicator to the main window
- Show status for each stage: Pending -> Running -> Success / Failed
- Display specific error messages when a stage fails
- Allow user to retry failed stages individually (e.g., re-run transcription without re-recording)
- Persist stage status with the recording in the vault

### Out of Scope

- Progress bars within each stage (e.g., transcription percentage)
- Automatic retry (covered by BEAN-005)
- Email/notification on failure

## Acceptance Criteria

- [ ] Main window shows status indicators for each pipeline stage
- [ ] Failed stages show specific error message (not generic "error occurred")
- [ ] User can retry individual failed stages from the UI
- [ ] Pipeline status is stored with recording in vault
- [ ] Status panel updates in real-time as each stage completes
- [ ] New tests cover status tracking and display

## Tasks

| # | Task | Owner | Depends On | Status |
|---|------|-------|------------|--------|
| 1 |      |       |            | TODO   |
| 2 |      |       |            | TODO   |
| 3 |      |       |            | TODO   |

## Telemetry

| Metric           | Value |
|------------------|-------|
| Total Tasks      |       |
| Total Duration   |       |
| Total Tokens In  |       |
| Total Tokens Out |       |

## Notes

No dependencies on other beans. Touches `src/gui/qt_main_window.py` and vault storage.
