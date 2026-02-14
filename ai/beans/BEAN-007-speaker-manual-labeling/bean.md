# BEAN-007: Speaker Manual Labeling UI

## Metadata

| Field     | Value        |
|-----------|--------------|
| ID        | BEAN-007     |
| Title     | Speaker Manual Labeling UI |
| Type      | feature |
| Priority  | P1 |
| Status    | Done         |
| Owner     | team-lead    |
| Created   | 2026-02-10   |
| Started   | 2026-02-10 15:54 |
| Completed | 2026-02-10 16:10 |
| Duration  | ~16 min      |

## Problem Statement

Even with auto-diarization, speakers are labeled generically (Speaker 1, Speaker 2). Users need to assign real names to speakers and optionally correct diarization mistakes. There is currently no UI for editing speaker labels in an existing transcription.

## Goal

Users can open a transcription, assign real names to speaker labels, and save the updated transcription. Users can also manually split or merge speaker segments to correct diarization errors.

## Scope

### In Scope

- Add speaker management panel to vault detail view / summary viewer
- List detected speakers with editable name fields (e.g., "Speaker 1" -> "Alice")
- Bulk rename: changing a speaker name updates all occurrences in transcription
- Save updated transcription with real names back to vault
- If no auto-diarization was run, allow user to manually insert speaker labels at any point in the transcription

### Out of Scope

- Voice fingerprinting to auto-identify known speakers
- Speaker profiles that carry across recordings
- Re-running diarization with corrected labels as training data

## Acceptance Criteria

- [x] Speaker management panel shows all detected speakers with editable name fields
- [x] Renaming a speaker updates all occurrences in the transcription
- [x] Updated transcription is saved to vault
- [x] Users can manually insert speaker labels into un-diarized transcriptions
- [x] UI is accessible from vault detail view or summary viewer
- [x] Changes are non-destructive (original transcription preserved as backup)
- [x] New tests cover speaker rename and manual insertion

## Tasks

| # | Task | Owner | Depends On | Status |
|---|------|-------|------------|--------|
| 1 | Implement VaultManager Module | developer | — | DONE |
| 2 | Implement Speaker Management Service | developer | T001 | DONE |
| 3 | Build Speaker Management Panel UI | developer | T001, T002 | DONE |
| 4 | Write Tests for Speaker Labeling | tech-qa | T001, T002, T003 | DONE |
| 5 | Integration Verification & Lint Cleanup | tech-qa | T004 | DONE |

## Telemetry

| Metric           | Value |
|------------------|-------|
| Total Tasks      |       |
| Total Duration   |       |
| Total Tokens In  |       |
| Total Tokens Out |       |

## Notes

No hard dependency on BEAN-006 (Speaker Auto-Diarization) — manual labeling works on any transcription. However, it's more useful when auto-diarization has already identified speaker segments. Touches `src/gui/qt_summary_viewer.py`, `src/gui/qt_vault_dialog.py`, and vault storage.
