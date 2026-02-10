# Task 004: Add Threading Lock to GUI Recording State

## Metadata

| Field | Value |
|-------|-------|
| Task ID | BEAN-002-T004 |
| Owner | developer |
| Status | TODO |
| Depends On | — |

## Description

Add `threading.Lock` to protect `is_recording` state in both GUI modules:
- `src/gui/qt_main_window.py` (PySide6)
- `src/gui/main_window.py` (CustomTkinter)

Both modules modify `is_recording` from multiple threads (main thread for UI, worker threads for processing).

## Acceptance Criteria

- [ ] `threading.Lock` protects `is_recording` in `qt_main_window.py`
- [ ] `threading.Lock` protects `is_recording` in `main_window.py`
- [ ] All state transitions use the lock consistently

## Files

- `src/gui/qt_main_window.py`
- `src/gui/main_window.py`
