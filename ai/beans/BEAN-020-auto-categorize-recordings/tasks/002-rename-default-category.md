# Task 002: Rename default category from 'other' to 'uncategorized'

## Owner: Developer
## Depends On: 001
## Status: TODO

### Description
Replace all 3 hardcoded `'category': 'other'` in `src/gui/qt_main_window.py`:
- Line 142 (RecordingWorker.run recording_data)
- Line 289 (RetryStageWorker._retry_summarization recording_data)
- Line 887 (on_processing_finished current_recording_data)

### Acceptance Criteria
- All three locations use `'uncategorized'` instead of `'other'`
