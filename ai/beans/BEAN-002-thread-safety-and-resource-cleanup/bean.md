# BEAN-002: Thread Safety & Resource Cleanup

## Metadata

| Field     | Value        |
|-----------|--------------|
| ID        | BEAN-002     |
| Title     | Thread Safety & Resource Cleanup |
| Type      | bug-fix |
| Priority  | P0 |
| Status    | Done         |
| Owner     | team-lead    |
| Created   | 2026-02-10   |
| Started   | 2026-02-10 15:39 |
| Completed | 2026-02-10 15:50 |
| Duration  | ~11 min      |

## Problem Statement

Multiple thread-safety issues exist across the codebase:
1. `is_recording` state in `qt_main_window.py` and `main_window.py` is modified from multiple threads without synchronization, causing race conditions.
2. `src/config/settings.py` `save_settings()` is not thread-safe — concurrent saves can corrupt the JSON file.
3. `src/audio/recorder.py` uses `__del__` for resource cleanup, which is unreliable in Python — PyAudio streams may never be properly closed.

## Goal

All shared mutable state is properly synchronized with threading primitives, and resource cleanup uses reliable patterns (context managers or explicit cleanup methods) instead of `__del__`.

## Scope

### In Scope

- Add `threading.Lock` to recording state transitions in GUI modules
- Add `threading.Lock` to `save_settings()` / `load_settings()` in settings manager
- Replace `__del__` in recorder.py with a context manager (`__enter__`/`__exit__`) or explicit `cleanup()` method
- Ensure PyAudio streams are always closed, even on exceptions

### Out of Scope

- Rewriting the recording loop architecture
- Adding async/await patterns
- GUI framework changes

## Acceptance Criteria

- [x] Recording state changes are protected by a threading lock
- [x] Settings save/load is protected by a threading lock
- [x] `__del__` removed from recorder.py; replaced with context manager or explicit cleanup
- [x] PyAudio stream is closed in a `finally` block during recording
- [x] No deadlocks introduced (verified by running full test suite)
- [x] Existing tests still pass

## Tasks

| # | Task | Owner | Depends On | Status |
|---|------|-------|------------|--------|
| 1 | Add threading lock to AudioRecorder | developer | — | DONE |
| 2 | Replace __del__ with context manager and cleanup() | developer | T001 | DONE |
| 3 | Add threading lock to SettingsManager | developer | — | DONE |
| 4 | Add threading lock to GUI recording state | developer | — | DONE |
| 5 | Write tests for thread safety and resource cleanup | tech-qa | T001-T004 | DONE |

## Telemetry

| Metric           | Value |
|------------------|-------|
| Total Tasks      | 5     |
| Total Duration   |       |
| Total Tokens In  |       |
| Total Tokens Out |       |

## Notes

No dependencies on other beans. Touches `src/audio/recorder.py`, `src/config/settings.py`, `src/gui/qt_main_window.py`.
