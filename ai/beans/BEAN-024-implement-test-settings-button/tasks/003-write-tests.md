# Task 003: Write Tests for Diagnostic Logic

| Field | Value |
|-------|-------|
| Owner | Tech-QA |
| Status | TODO |
| Depends On | 001 |

## Description

Write `tests/test_settings_diagnostics.py` covering:

1. Directory check — exists & writable, missing dir, non-writable dir
2. API key check — skipped when not needed, format failure, live success/failure (mocked)
3. Microphone check — success (mocked PyAudio), failure (PyAudio error)
4. `run_all_checks` — integration test with all mocked dependencies
5. Timeout handling — API check that exceeds timeout returns failure

## Acceptance Criteria

- [ ] All diagnostic functions have test coverage
- [ ] Tests pass with `pytest tests/test_settings_diagnostics.py`
- [ ] No tests require real API keys or hardware
