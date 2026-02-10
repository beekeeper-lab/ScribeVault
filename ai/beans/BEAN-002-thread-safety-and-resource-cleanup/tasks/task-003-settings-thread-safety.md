# Task 003: Add Threading Lock to SettingsManager

## Metadata

| Field | Value |
|-------|-------|
| Task ID | BEAN-002-T003 |
| Owner | developer |
| Status | TODO |
| Depends On | — |

## Description

Add `threading.Lock` to `SettingsManager` in `src/config/settings.py` to protect `save_settings()` and `_load_settings()` from concurrent access. Without this, concurrent saves can corrupt the JSON settings file.

## Acceptance Criteria

- [ ] `threading.Lock` added to `SettingsManager.__init__`
- [ ] `save_settings()` acquires lock before writing
- [ ] `_load_settings()` acquires lock before reading
- [ ] Lock scope is minimal (no holding across unnecessary operations)

## Files

- `src/config/settings.py`
