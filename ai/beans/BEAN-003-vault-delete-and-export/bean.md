# BEAN-003: Vault Delete & Export Implementation

## Metadata

| Field     | Value        |
|-----------|--------------|
| ID        | BEAN-003     |
| Title     | Vault Delete & Export Implementation |
| Type      | bug-fix |
| Priority  | P1 |
| Status    | Unapproved   |
| Created   | 2026-02-10   |
| Started   |              |
| Completed |              |
| Duration  |              |

## Problem Statement

In the PySide6 vault dialog (`src/gui/qt_vault_dialog.py`), both `delete_recording()` and `export_recording()` are stubbed out with "coming soon!" message boxes. Users can see their recordings in the vault but cannot manage them — they can't delete unwanted recordings or export recordings for sharing.

## Goal

Users can delete recordings (with confirmation dialog) and export recordings (audio + transcription + summary) to a user-chosen directory.

## Scope

### In Scope

- Implement `delete_recording()` with confirmation dialog, removing audio file, transcription, summary, and vault database entry
- Implement `export_recording()` that exports audio file, transcription text, and summary to a user-chosen directory
- Add error handling for file-not-found, permission errors
- Refresh vault view after delete

### Out of Scope

- Bulk delete/export (one recording at a time)
- Cloud export (e.g., Google Drive)
- Export format options beyond plain files (no ZIP, no PDF)

## Acceptance Criteria

- [ ] Delete button shows confirmation dialog before deleting
- [ ] Delete removes audio file, transcription, summary, and database entry
- [ ] Vault list refreshes after deletion
- [ ] Export opens a directory picker dialog
- [ ] Export copies audio file, transcription (.txt), and summary (.md) to chosen directory
- [ ] Error dialog shown if export/delete fails (e.g., file locked, permission denied)
- [ ] New tests cover delete and export functionality

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

No dependencies on other beans. Touches `src/gui/qt_vault_dialog.py` and vault storage layer.
