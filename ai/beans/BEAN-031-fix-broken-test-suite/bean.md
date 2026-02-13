# BEAN-031: Fix Broken Test Suite

## Metadata

| Field     | Value        |
|-----------|--------------|
| ID        | BEAN-031     |
| Title     | Fix Broken Test Suite |
| Type      | bug-fix |
| Priority  | P0 |
| Status    | Unapproved   |
| Created   | 2026-02-13   |
| Started   |              |
| Completed |              |
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

- [ ] `pytest tests/` runs with 0 failures and 0 errors
- [ ] No segfaults from GUI tests (either guarded with skip or offscreen platform)
- [ ] Tests that pass individually also pass when run in the full suite (isolation fixed)
- [ ] `tests/run_tests.py` is removed
- [ ] All mock specs align with current class interfaces

## Tasks

| # | Task | Owner | Depends On | Status |
|---|------|-------|------------|--------|
| 1 | Fix test_audio_recorder.py mocks and constructor calls | developer | | TODO |
| 2 | Fix test_whisper_service.py mock API (get_api_key → get_openai_api_key) | developer | | TODO |
| 3 | Fix test_integration.py category constants | developer | | TODO |
| 4 | Fix test_logging_config.py missing diarization arg | developer | | TODO |
| 5 | Fix pyaudio sys.modules test isolation | developer | | TODO |
| 6 | Add GUI test guards for headless environments | developer | | TODO |
| 7 | Remove redundant run_tests.py | developer | | TODO |
| 8 | Verify full suite passes | tech-qa | 1-7 | TODO |

## Telemetry

| Metric           | Value |
|------------------|-------|
| Total Tasks      |       |
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
