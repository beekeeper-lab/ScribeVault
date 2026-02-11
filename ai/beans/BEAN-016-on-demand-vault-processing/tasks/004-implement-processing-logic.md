# Task 004: Implement On-Demand Processing Logic

## Owner
Developer

## Depends On
002, 003

## Description
Implement `transcribe_selected()` and `summarize_selected()` methods:

- `transcribe_selected()`: validates audio file exists, launches TranscriptionWorker, stores result in vault, refreshes detail panel.
- `summarize_selected()`: if no transcript exists, auto-chains transcription first; launches OnDemandSummarizationWorker, stores result in vault, opens SummaryViewerDialog.
- Status bar updates during processing.
- Error handling with QMessageBox for failures.

## Acceptance Criteria
- All acceptance criteria from bean.md related to button behavior
- Auto-chaining works (summarize triggers transcribe first if needed)
- SummaryViewerDialog opens after summarization
- Progress indication via status bar
- Error dialogs for missing audio, API failures
- Partial results preserved (transcript saved even if summarization fails)

## Status
Done
