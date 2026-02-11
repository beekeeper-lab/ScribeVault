# Task 001: Extract shared title sanitization utility

**Owner:** Developer
**Status:** TODO
**Depends On:** None

## Description

Extract the duplicated title sanitization logic into a shared utility function in `src/export/utils.py`. Currently, three places have identical sanitization: `qt_vault_dialog.py:export_recording`, `qt_vault_dialog.py:export_transcription`, and `markdown_generator.py:save_markdown_file`.

The utility should:
- Accept a raw title string
- Strip non-alphanumeric characters (keeping spaces, hyphens, underscores)
- Replace spaces with underscores
- Truncate to 50 characters
- Return a safe filename-ready string
- Include a helper to create a unique subfolder (with numeric suffix for duplicates)

## Acceptance Criteria

- [ ] `sanitize_title()` function in `src/export/utils.py`
- [ ] `create_unique_subfolder()` function in `src/export/utils.py`
- [ ] All three call sites updated to use the shared utility
