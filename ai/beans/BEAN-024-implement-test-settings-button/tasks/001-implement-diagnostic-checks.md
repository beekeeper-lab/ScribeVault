# Task 001: Implement Diagnostic Check Functions

| Field | Value |
|-------|-------|
| Owner | Developer |
| Status | TODO |
| Depends On | — |

## Description

Create a `SettingsDiagnostics` class in `src/gui/settings_diagnostics.py` with pure-logic diagnostic check methods:

1. `check_openai_api_key(settings_manager)` — validate API key format and live connectivity (reuse `validate_openai_api_key_live()`)
2. `check_directory(path, label)` — verify directory exists and is writable
3. `check_microphone(device_index)` — test PyAudio open/close on selected device
4. `run_all_checks(settings_manager, recordings_dir, vault_dir, device_index, needs_api_key)` — orchestrate all checks, return list of results

Each check returns a `DiagnosticResult` dataclass with: name, passed (bool), message, status ("pass"/"fail"/"skip"/"warning").

Include timeout handling for the API key check (10-second limit).

## Acceptance Criteria

- [ ] All four check functions implemented
- [ ] Results returned as structured data (not UI-coupled)
- [ ] Timeout prevents hanging on slow API response
- [ ] Checks that don't apply return "skip" status
