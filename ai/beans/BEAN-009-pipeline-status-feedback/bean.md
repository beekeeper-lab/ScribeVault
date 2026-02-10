# BEAN-009: Pipeline Status Feedback to User

## Metadata

| Field     | Value        |
|-----------|--------------|
| ID        | BEAN-009     |
| Title     | Pipeline Status Feedback to User |
| Type      | enhancement |
| Priority  | P2 |
| Status    | Done   |
| Created   | 2026-02-10   |
| Started   | 2026-02-10 15:54 |
| Completed | 2026-02-10 16:03 |
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

- [x] Main window shows status indicators for each pipeline stage
- [x] Failed stages show specific error message (not generic "error occurred")
- [x] User can retry individual failed stages from the UI
- [x] Pipeline status is stored with recording in vault
- [x] Status panel updates in real-time as each stage completes
- [x] New tests cover status tracking and display

## Tasks

| # | Task | Owner | Depends On | Status |
|---|------|-------|------------|--------|
| 1 | Create PipelineStatus Data Model | developer | none | DONE |
| 2 | Enhance RecordingWorker with Stage-Level Signals | developer | TASK-001 | DONE |
| 3 | Create Pipeline Status Panel Widget | developer | TASK-001 | DONE |
| 4 | Integrate Status Panel into Main Window | developer | TASK-002, TASK-003 | DONE |
| 5 | Persist Pipeline Status in Vault | developer | TASK-002 | DONE |
| 6 | Write Tests for Pipeline Status | tech-qa | TASK-001, TASK-002, TASK-005 | DONE |

## Telemetry

| Metric           | Value |
|------------------|-------|
| Total Tasks      | 6     |
| Total Duration   |       |
| Total Tokens In  |       |
| Total Tokens Out |       |

## Notes

No dependencies on other beans. Touches `src/gui/qt_main_window.py` and vault storage.
