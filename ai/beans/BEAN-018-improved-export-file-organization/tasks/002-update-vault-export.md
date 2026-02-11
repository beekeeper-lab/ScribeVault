# Task 002: Update vault export to use subfolders and title-based naming

**Owner:** Developer
**Status:** TODO
**Depends On:** 001

## Description

Update `export_recording()` in `qt_vault_dialog.py` to:
- Create a subfolder `{sanitized_title}/` inside the user-selected export directory
- Handle duplicates with numeric suffix (e.g., `Sprint_Planning_2/`)
- Rename audio file from `recording_YYYYMMDD_HHMMSS.wav` to `{Title}.{ext}`
- Name transcription file as `{Title}_transcription.txt`
- Name summary file as `{Title}_summary.md`

Update `export_transcription()` to use `{Title}_transcription` as default filename suggestion.

## Acceptance Criteria

- [ ] Export creates subfolder
- [ ] Audio renamed to title-based name
- [ ] Transcription and summary use title-based names
- [ ] Duplicate folders get numeric suffix
- [ ] Transcription export default filename updated
