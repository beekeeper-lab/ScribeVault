# Task 003: Wire categorize_content() into recording pipeline

## Owner: Developer
## Depends On: 001
## Status: TODO

### Description
In `src/gui/qt_main_window.py` RecordingWorker.run():
- After transcription succeeds and summarizer is available, call `categorize_content(transcript)`
- Use result as category in recording_data dict
- If result is not in VALID_CATEGORIES, fallback to `uncategorized`
- Pass category to vault_manager.add_recording()

Similarly in RetryStageWorker._retry_summarization() and on_processing_finished().

### Acceptance Criteria
- When summarizer is available and transcript exists, category is auto-detected
- When summarizer is unavailable, category defaults to `uncategorized`
- Unrecognized categories fall back to `uncategorized`
