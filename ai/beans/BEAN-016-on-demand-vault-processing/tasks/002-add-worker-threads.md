# Task 002: Add TranscriptionWorker and OnDemandSummarizationWorker

## Owner
Developer

## Depends On
001

## Description
Create two QThread worker classes following the RegenerationWorker pattern:

1. **TranscriptionWorker** — calls `whisper_service.transcribe_with_diarization(audio_path)`, emits `finished(str)` with transcript or `error(str)`.
2. **OnDemandSummarizationWorker** — calls `summarizer_service.generate_summary_with_markdown(recording_data)`, emits `finished(dict)` with result dict or `error(str)`.

## Acceptance Criteria
- Workers run in background threads
- Proper signal/slot pattern
- Error handling wraps all exceptions

## Status
Done
