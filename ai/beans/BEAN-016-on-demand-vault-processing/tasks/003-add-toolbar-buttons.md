# Task 003: Add Transcribe and Summarize Buttons to Toolbar and Detail Panel

## Owner
Developer

## Depends On
001

## Description
Add "Transcribe" and "Summarize" buttons to the vault table toolbar (table_controls layout) and the recording detail panel actions group. Buttons should be enabled/disabled based on recording state via `_update_processing_buttons()`.

## Acceptance Criteria
- Transcribe button in toolbar and detail panel
- Summarize button in toolbar and detail panel
- Buttons disabled when no recording selected
- Transcribe disabled when transcript already exists or no audio file
- Summarize disabled when summary already exists (and transcript exists)
- Buttons disabled during processing

## Status
Done
