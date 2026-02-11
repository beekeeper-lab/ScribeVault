# BEAN-019: Remove Export Transcript Button from Vault

## Metadata

| Field     | Value        |
|-----------|--------------|
| **ID**        | BEAN-019     |
| **Title**     | Remove Export Transcript Button from Vault |
| **Type**      | enhancement |
| **Priority**  | P3 |
| **Status**    | Approved     |
| **Created**   | 2026-02-10   |
| **Started**   | —            |
| **Completed** | —            |
| **Duration**  | —            |

## Problem Statement

The Recording Vault toolbar has two export buttons: "Export" and "Export Transcript". The general Export already exports the audio file, the transcription as `.txt`, and a full summary as `.md` — making the dedicated Export Transcript button redundant and cluttering the toolbar. However, Export Transcript uniquely supports SRT subtitle format, which should not be lost.

## Goal

Remove the redundant "Export Transcript" button from the vault toolbar and merge SRT subtitle export support into the main Export flow, so users have a single, clear export action with no loss of capability.

## Scope

### In Scope

- Remove the "Export Transcript" button and its click handler wiring from `src/gui/qt_vault_dialog.py` (lines 194-200)
- Add SRT format as an export option within the existing `export_recording()` method
- Keep the `TranscriptionExporter` class in `src/export/transcription_exporter.py` (it provides the SRT export logic used by the main Export)
- Keep the `export_transcription()` method available for programmatic use if needed, but remove its UI trigger

### Out of Scope

- Changing the Export Transcript logic itself (`TranscriptionExporter`)
- Adding new export formats beyond what currently exists
- Changing the export directory picker flow

## Acceptance Criteria

- [ ] The "Export Transcript" button is no longer visible on the vault toolbar
- [ ] The main "Export" button offers SRT as an additional format option when timestamps are present in the transcription
- [ ] Exported SRT files are identical to what the old Export Transcript button produced
- [ ] The toolbar is less cluttered with one fewer button
- [ ] Existing tests still pass

## Tasks

| # | Task | Owner | Depends On | Status |
|---|------|-------|------------|--------|
| 1 | Remove Export Transcript button and wiring from vault dialog UI | Developer | — | TODO |
| 2 | Add SRT export option to the main `export_recording()` method | Developer | 1 | TODO |
| 3 | Verify SRT output matches previous Export Transcript behavior | Tech QA | 2 | TODO |

## Telemetry

| Metric           | Value |
|------------------|-------|
| **Total Tasks**      | 3     |
| **Total Duration**   | —     |
| **Total Tokens In**  | —     |
| **Total Tokens Out** | —     |

## Notes

The "Export Transcript" button was added by BEAN-013 (Transcription Export, Done). This bean consolidates that functionality into the main Export flow. The `TranscriptionExporter` class at `src/export/transcription_exporter.py` provides `export_srt()` and should be reused by the updated `export_recording()` method. The `export_transcription()` method in the dialog can be removed or left as dead code — preference is to remove it cleanly.
