# BEAN-031: Fix Broken Test Suite

## Metadata

| Field     | Value        |
|-----------|--------------|
| ID        | BEAN-031     |
| Title     | Fix Broken Test Suite |
| Type      | bug-fix |
| Priority  | P0 |
| Status    | Done  |
| Created   | 2026-02-13   |
| Started   | 2026-02-14   |
| Completed | 2026-02-14   |
| Duration  |              |

## Problem Statement

54 tests are currently failing across 5 test files due to API drift between the source code and test mocks. Tests reference removed/renamed methods (`get_api_key` → `get_openai_api_key`), removed constructor parameters (`output_dir`), missing required arguments (`diarization`), and stale category constants (`"other"` → `"uncategorized"`). Additionally, test isolation issues with `sys.modules['pyaudio']` injection cause tests to fail when run together but pass individually. GUI tests cause segfaults when PySide6 is available but no display server exists.

## Goal

All tests pass when run via `pytest tests/` with zero failures and no segfaults.

## Scope

### In Scope

- Fix `tests/test_audio_recorder.py` (9 failures) — update to match current `AudioRecorder` constructor and method signatures
- Fix `tests/test_whisper_service.py` (11 failures) — update mock from `get_api_key` to `get_openai_api_key`, align with current `WhisperService` constructor
- Fix `tests/test_integration.py` (3 failures) — update `"other"` category references to `"uncategorized"`
- Fix `tests/test_logging_config.py` (2 failures) — add missing `diarization` argument to `AppSettings` construction
- Fix `tests/test_checkpoint.py` and `tests/test_thread_safety.py` test isolation — refactor `sys.modules['pyaudio']` injection to use proper pytest fixtures with cleanup
- Add `QT_QPA_PLATFORM=offscreen` guards or conftest fixtures for GUI tests that segfault
- Remove redundant `tests/run_tests.py` custom test runner

### Out of Scope

- Adding new test coverage for untested modules (qt_main_window, qt_settings_dialog, qt_summary_viewer)
- Fixing lint issues in test files
- Refactoring test structure

## Acceptance Criteria

- [x] `pytest tests/` runs with 0 failures and 0 errors
- [x] No segfaults from GUI tests (either guarded with skip or offscreen platform)
- [x] Tests that pass individually also pass when run in the full suite (isolation fixed)
- [x] `tests/run_tests.py` is removed
- [x] All mock specs align with current class interfaces

## Tasks

| # | Task | Owner | Depends On | Status |
|---|------|-------|------------|--------|
| 1 | Fix test_audio_recorder.py mocks and constructor calls | developer | | DONE |
| 2 | Fix test_whisper_service.py mock API (get_api_key → get_openai_api_key) | developer | | DONE |
| 3 | Fix test_integration.py category constants | developer | | DONE |
| 4 | Fix test_logging_config.py missing diarization arg | developer | | DONE |
| 5 | Fix pyaudio sys.modules test isolation | developer | | DONE |
| 6 | Add GUI test guards for headless environments | developer | | DONE |
| 7 | Remove redundant run_tests.py | developer | | DONE |
| 8 | Verify full suite passes | tech-qa | 1-7 | DONE |

## Telemetry

| Metric           | Value |
|------------------|-------|
| Total Tasks      | 8     |
| Total Duration   |       |
| Total Tokens In  |       |
| Total Tokens Out |       |

## Notes

Failing test breakdown by root cause:
- API signature drift: 20 tests (test_audio_recorder + test_whisper_service)
- Stale constants: 3 tests (test_integration)
- Missing constructor arg: 2 tests (test_logging_config)
- Test isolation (sys.modules): ~17 tests (test_checkpoint + test_thread_safety fail only in full suite)
- GUI segfaults: 12+ tests (test_on_demand_processing, test_main_page_speaker, test_pipeline_status)

### Resolution Summary

1. **conftest.py created** — centralizes pyaudio mock installation and QT_QPA_PLATFORM=offscreen
2. **test_audio_recorder.py rewritten** — removed stale `output_dir` param, `_generate_filename`, `_is_safe_path` references; aligned with current `AudioRecorder` constructor
3. **test_whisper_service.py rewritten** — replaced `get_api_key` with `get_openai_api_key`, added `settings.transcription` mock with proper fields, removed references to non-existent methods
4. **test_integration.py** — changed `"other"` → `"uncategorized"` in 3 locations
5. **test_logging_config.py** — added `DiarizationSettings()` to `AppSettings` construction
6. **test_checkpoint.py / test_thread_safety.py** — removed module-level `sys.modules['pyaudio']` injection; now uses shared conftest mock
7. **test_audio_settings.py** — fixed `TestAudioRecorderDeviceParam` which used `importlib.reload()` that corrupted the shared pyaudio mock for all subsequent tests
8. **tests/run_tests.py removed** — redundant with pytest

Final result: 449 passed, 27 skipped, 0 failures, 0 errors.
