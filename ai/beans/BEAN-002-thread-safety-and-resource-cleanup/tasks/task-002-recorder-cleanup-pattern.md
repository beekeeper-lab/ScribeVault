# Task 002: Replace __del__ with Context Manager and Explicit Cleanup

## Metadata

| Field | Value |
|-------|-------|
| Task ID | BEAN-002-T002 |
| Owner | developer |
| Status | TODO |
| Depends On | T001 |

## Description

Remove the unreliable `__del__` method from `AudioRecorder` in `src/audio/recorder.py`. Replace it with:
1. An explicit `cleanup()` method that reliably releases all resources
2. Context manager protocol (`__enter__`/`__exit__`) for `with` statement usage
3. `finally` blocks in recording methods to ensure PyAudio streams are always closed

## Acceptance Criteria

- [ ] `__del__` removed from AudioRecorder
- [ ] `cleanup()` method properly closes stream, terminates FFmpeg, terminates PyAudio
- [ ] `__enter__`/`__exit__` implemented for context manager protocol
- [ ] PyAudio stream is closed in `finally` blocks in `_try_pyaudio_recording`
- [ ] Multiple `cleanup()` calls are safe (idempotent)

## Files

- `src/audio/recorder.py`
