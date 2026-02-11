# Task 005: Unit Tests for On-Demand Processing

## Owner
Tech-QA

## Depends On
004

## Description
Write unit tests in `tests/test_on_demand_processing.py` covering:
- TranscriptionWorker and OnDemandSummarizationWorker
- Button enable/disable logic
- Auto-chaining (summarize triggers transcription first)
- Error handling (missing audio, API failure)
- VaultDialog constructor with new whisper_service parameter

## Acceptance Criteria
- All new code has test coverage
- Existing tests still pass
- Tests use mocking for services (no real API calls)

## Status
Done
