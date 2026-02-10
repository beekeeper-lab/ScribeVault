# Task 004: Update Settings Dialog with API Key Status Indicator and Live Validation

## Metadata

| Field      | Value       |
|------------|-------------|
| Task ID    | BEAN-004-T004 |
| Owner      | developer   |
| Status     | TODO        |
| Depends On | T001        |

## Description

Update the PySide6 settings dialog to show clear API key status (valid/invalid/not configured) and validate the key (format + live check) when the user clicks "Validate" or saves settings. The `APIKeyValidator` thread should use the new live validation method.

## Acceptance Criteria

- [ ] API key status indicator shows: valid (green), invalid (red), not configured (yellow)
- [ ] "Validate" button performs live API check via background thread
- [ ] Save validates format before saving; warns on invalid format
- [ ] Clear status label updates in real-time as user types/validates
- [ ] Missing key shows clear "Not configured" state

## Files to Modify

- `src/gui/qt_settings_dialog.py`
