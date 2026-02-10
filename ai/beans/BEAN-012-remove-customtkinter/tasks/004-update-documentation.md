# Task 004: Update Documentation

## Metadata

| Field | Value |
|-------|-------|
| Task ID | BEAN-012-T004 |
| Owner | developer |
| Status | Done |
| Depends On | T002 |

## Description

Update all documentation to reflect that PySide6 is now the single GUI framework and `main.py` is the sole entry point.

## Files to Update

### README.md
- Line 13: Change "CustomTkinter" to "PySide6"
- Lines 109, 126: Already reference `python main.py` (OK after rename)
- Lines 168-173: Update project structure to show PySide6 files instead of CustomTkinter files

### CLAUDE.md
- Line 9: Change "GUI components (CustomTkinter + PySide6)" to "GUI components (PySide6)"
- Line 67-68: Remove `python main.py  # Launch original GUI` line, keep only PySide6 entry

## Acceptance Criteria

- [ ] No references to CustomTkinter remain in README.md
- [ ] No references to CustomTkinter remain in CLAUDE.md
- [ ] Project structure in README.md shows PySide6 files
- [ ] Single entry point `python main.py` documented
