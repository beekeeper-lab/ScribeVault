# Task 002: Create Results Dialog and Wire Button

| Field | Value |
|-------|-------|
| Owner | Developer |
| Status | TODO |
| Depends On | 001 |

## Description

1. Add a `SettingsTestRunner` QThread subclass that runs `run_all_checks()` in background and emits results via signal.
2. Replace the placeholder `test_settings()` method in `SettingsDialog` to:
   - Disable the button and show progress
   - Launch the runner thread
   - On completion, display a results dialog with pass/fail indicators per check
3. Results dialog shows each check with a colored status icon and message.

## Acceptance Criteria

- [ ] Button triggers actual diagnostic checks
- [ ] Progress indication while checks run
- [ ] Results displayed in dialog with clear pass/fail per check
- [ ] Button re-enabled after checks complete
