# Task 005: Verify Clean Codebase — No CustomTkinter Remnants

## Metadata

| Field | Value |
|-------|-------|
| Task ID | BEAN-012-T005 |
| Owner | tech-qa |
| Status | Done |
| Depends On | T001, T002, T003, T004 |

## Description

Final verification that no CustomTkinter references remain anywhere in the codebase. Run tests and lint to confirm nothing is broken.

## Steps

1. Search entire codebase for `customtkinter` (case-insensitive) — should only appear in bean docs and migration history
2. Search for imports of deleted modules (`main_window`, `settings_window`, `assets` from gui)
3. Search for `main_qt` references — should be zero after rename
4. Run `pytest tests/` — all tests must pass
5. Run `flake8 src/ tests/` — no lint errors

## Acceptance Criteria

- [ ] No `customtkinter` imports anywhere in source code
- [ ] No references to deleted files in source code
- [ ] No `main_qt.py` references in source code or docs (except migration history)
- [ ] All tests pass
- [ ] Lint passes
