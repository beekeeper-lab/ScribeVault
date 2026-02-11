# Task 01: Change QSettings default from False to True

| Field      | Value     |
|------------|-----------|
| **Owner**  | Developer |
| **Status** | DONE      |
| **Depends On** | —    |

## Description

In `src/gui/qt_main_window.py` line 744, change the QSettings default value for `recording/generate_summary` from `False` to `True`.

## Acceptance Criteria

- The `settings.value("recording/generate_summary", ...)` call uses `True` as default
- Existing save_settings logic unchanged
