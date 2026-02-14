# BEAN-016: On-Demand Vault Processing

## Metadata

| Field     | Value        |
|-----------|--------------|
| ID        | BEAN-016     |
| Title     | On-Demand Vault Processing |
| Type      | feature      |
| Priority  | P1           |
| Status    | Done         |
| Created   | 2026-02-10   |
| Started   | 2026-02-11   |
| Completed | 2026-02-11   |
| Duration  |              |

## Problem Statement

Currently, transcription and summarization only happen during the recording flow (in `RecordingWorker`). If a recording is saved without a transcript (e.g., the user skipped transcription, or it failed), there is no way to generate a transcript from the vault. Similarly, if summarization was skipped or the "Generate AI Summary" checkbox was unchecked, there is no way to create a summary after the fact. This forces users to re-record or manually process audio files outside the application.

## Goal

Users can trigger transcription and summarization on-demand from the Recording Vault screen for any recording that has an associated audio file. The system intelligently chains operations: requesting a summary on a recording without a transcript automatically transcribes first, then summarizes. Custom prompt summarization leverages the existing Summary Viewer dialog (BEAN-011).

## Scope

### In Scope

- Add "Transcribe" button to both the vault table toolbar and the recording detail panel
- Add "Summarize" button to both the vault table toolbar and the recording detail panel
- Buttons always visible; disabled/greyed out when not applicable (e.g., Transcribe disabled if transcript already exists, Summarize disabled if summary already exists and no transcript change)
- Transcribe action: invoke `WhisperService.transcribe_with_diarization()` on the recording's audio file and store the result in the vault database
- Summarize action: invoke `SummarizerService.generate_summary_with_markdown()` on the transcript and store the result in the vault database
- Automatic chaining: if Summarize is clicked and no transcript exists, run transcription first (without prompting the user), then summarize
- Pipeline status feedback during processing (progress indication, disable buttons while processing)
- After summarization completes, open the existing `SummaryViewerDialog` which already supports re-generation with templates and custom prompts (BEAN-011)
- Update the detail panel to refresh after transcription/summarization completes
- Error handling for missing audio files, API failures, and service unavailability

### Out of Scope

- Batch processing (transcribe/summarize multiple recordings at once)
- New custom prompt UI (use existing Summary Viewer from BEAN-011)
- Changes to the recording flow or `RecordingWorker`
- Re-transcription of recordings that already have transcripts (button will be disabled)
- Offline/local-only summarization (requires OpenAI API key as today)

## Acceptance Criteria

- [x] A "Transcribe" button appears in the vault table toolbar and recording detail panel
- [x] A "Summarize" button appears in the vault table toolbar and recording detail panel
- [x] Transcribe button is enabled only when the selected recording has an audio file but no transcript
- [x] Summarize button is enabled only when the selected recording has a transcript but no summary, OR has no transcript and no summary (will auto-chain)
- [x] Clicking Transcribe generates a transcript from the audio file using WhisperService and stores it in the vault
- [x] Clicking Summarize on a recording with a transcript generates a summary and stores it in the vault
- [x] Clicking Summarize on a recording without a transcript automatically transcribes first, then summarizes, without user intervention
- [x] During processing, the buttons are disabled and a progress indicator is shown (pipeline status or status bar)
- [x] After summarization completes, the Summary Viewer dialog opens automatically
- [x] The detail panel refreshes to show newly created transcript/summary content
- [x] If the audio file is missing from disk, a clear error message is shown
- [x] If the API call fails (transcription or summarization), an error dialog is shown and partial results are preserved (e.g., transcript saved even if summarization fails)
- [x] All new functionality has unit tests
- [x] Existing tests continue to pass

## Tasks

| # | Task | Owner | Depends On | Status |
|---|------|-------|------------|--------|
| 1 | Add WhisperService to VaultDialog | Developer | — | Done |
| 2 | Add TranscriptionWorker and OnDemandSummarizationWorker | Developer | 1 | Done |
| 3 | Add Transcribe/Summarize buttons to toolbar and detail panel | Developer | 1 | Done |
| 4 | Implement on-demand processing logic | Developer | 2, 3 | Done |
| 5 | Unit tests for on-demand processing | Tech-QA | 4 | Done |

## Telemetry

| Metric           | Value |
|------------------|-------|
| Total Tasks      |       |
| Total Duration   |       |
| Total Tokens In  |       |
| Total Tokens Out |       |

## Notes

- Depends on BEAN-011 (Summary Re-generation with Prompt Templates) for the Summary Viewer dialog and custom prompt support — already Done.
- Depends on BEAN-006 (Speaker Auto-Diarization) for `transcribe_with_diarization()` — already Done.
- The `RegenerationWorker` pattern in `qt_vault_dialog.py` (lines 625-687) provides a good model for the background processing approach: QThread worker with signals for completion/error.
- Key files to modify: `src/gui/qt_vault_dialog.py` (UI + worker threads), `src/vault/manager.py` (may need audio file path retrieval helper).
- The `WhisperService` and `SummarizerService` are already designed for standalone use outside of `RecordingWorker`, so reuse should be straightforward.
