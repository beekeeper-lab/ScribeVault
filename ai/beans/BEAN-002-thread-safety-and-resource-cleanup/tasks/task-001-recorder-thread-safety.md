# Task 001: Add Threading Lock to AudioRecorder

## Metadata

| Field | Value |
|-------|-------|
| Task ID | BEAN-002-T001 |
| Owner | developer |
| Status | TODO |
| Depends On | — |

## Description

Add `threading.Lock` to `src/audio/recorder.py` to protect `is_recording` state transitions and `frames` list access from race conditions. The `_audio_callback` runs on a separate thread and reads `is_recording` while `start_recording`/`stop_recording` modify it from the main thread.

## Acceptance Criteria

- [ ] `threading.Lock` protects all `is_recording` state changes
- [ ] `frames` list access is protected during concurrent callback/stop operations
- [ ] No deadlocks (lock is never held across blocking calls)

## Files

- `src/audio/recorder.py`
