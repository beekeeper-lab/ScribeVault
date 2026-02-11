# BEAN-018: Improved Export File Organization

## Metadata

| Field     | Value        |
|-----------|--------------|
| ID        | BEAN-018     |
| Title     | Improved Export File Organization |
| Type      | enhancement  |
| Priority  | P2           |
| Status    | In Progress  |
| Created   | 2026-02-10   |
| Started   |              |
| Completed |              |
| Duration  |              |

## Problem Statement

When exporting recordings from the vault, all files (audio, transcription, summary) are dumped flat into the user-selected directory with no per-recording subfolder. Filenames in the `MarkdownGenerator` are prefixed with a long timestamp (`20260115_093000_Title.md`) where the first two-thirds of the name is a timestamp that adds little value. Audio files retain their generic `recording_YYYYMMDD_HHMMSS.wav` name. This makes exported files hard to identify and organize, especially when exporting multiple recordings.

## Goal

Exports are organized into descriptive per-recording subfolders named after the recording title. Filenames inside the subfolder lead with the title and use a type suffix (e.g., `Sprint_Planning_transcription.txt`). This applies to both the user-triggered vault Export and the internal `MarkdownGenerator` summary output.

## Scope

### In Scope

- **Vault Export (`export_recording()` in `qt_vault_dialog.py`):**
  - Create a subfolder named after the recording title (sanitized) in the user-selected export directory (e.g., `Sprint_Planning/`)
  - Rename audio file from generic `recording_YYYYMMDD_HHMMSS.wav` to `{Title}.wav` (e.g., `Sprint_Planning.wav`)
  - Name transcription file as `{Title}_transcription.txt` (already close to this, just ensure consistency)
  - Name summary file as `{Title}_summary.md` (already close to this, just ensure consistency)
  - Handle duplicate folder names (e.g., append a short numeric suffix if `Sprint_Planning/` already exists)
- **MarkdownGenerator (`markdown_generator.py`):**
  - Change filename from `{YYYYMMDD_HHMMSS}_{Title}.md` to `{Title}.md` (title-first, drop the timestamp prefix)
  - Organize into per-recording subfolder within `summaries/` using the same title-based naming
  - Update the daily and by-category subdirectory naming to also use title-first filenames
- **Transcription Export (`export_transcription()` in `qt_vault_dialog.py`):**
  - Default filename suggestion should follow the same `{Title}_transcription.{ext}` pattern (already partially done)
- **Safe title sanitization:** Ensure the existing sanitization logic (alphanumeric + spaces/hyphens/underscores, replace spaces with underscores, 50-char limit) is applied consistently across all export paths

### Out of Scope

- Changing how audio files are named in the vault storage itself (only affects export copies)
- Restructuring the vault database or internal storage paths
- Adding user-configurable naming templates
- Batch export improvements

## Acceptance Criteria

- [ ] Vault export creates a subfolder named `{sanitized_title}/` in the selected export directory
- [ ] Audio file inside the subfolder is named `{Title}.{ext}` (not `recording_YYYYMMDD_HHMMSS.wav`)
- [ ] Transcription file is named `{Title}_transcription.txt`
- [ ] Summary file is named `{Title}_summary.md`
- [ ] If a subfolder with the same name already exists, a numeric suffix is appended (e.g., `Sprint_Planning_2/`)
- [ ] MarkdownGenerator output files use `{Title}.md` instead of `{YYYYMMDD_HHMMSS}_{Title}.md`
- [ ] MarkdownGenerator organizes output into a per-recording subfolder within `summaries/`
- [ ] Transcription export default filename suggestion uses `{Title}_transcription` pattern
- [ ] All filenames use the same sanitization logic (alphanumeric, hyphens, underscores, 50-char limit)
- [ ] Existing tests continue to pass
- [ ] New tests cover the subfolder creation and naming logic

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

- Related to BEAN-003 (Vault Delete & Export Implementation) which originally built the export — already Done.
- Related to BEAN-013 (Transcription Export) which added the transcription export feature — already Done.
- Key files to modify:
  - `src/gui/qt_vault_dialog.py` — `export_recording()` (lines 791-910) and `export_transcription()` (lines 912-1001)
  - `src/export/markdown_generator.py` — `_generate_filename()` and directory creation logic (lines 125-129)
  - `src/export/transcription_exporter.py` — default filename logic
- The safe title sanitization function should be extracted into a shared utility to avoid duplication across the three files that currently each have their own copy.
