# BEAN-021: Fix Redundant Dialog Window Titles

## Metadata

| Field     | Value        |
|-----------|--------------|
| **ID**        | BEAN-021     |
| **Title**     | Fix Redundant Dialog Window Titles |
| **Type**      | bug-fix |
| **Priority**  | P3 |
| **Status**    | Approved     |
| **Created**   | 2026-02-10   |
| **Started**   | —            |
| **Completed** | —            |
| **Duration**  | —            |

## Problem Statement

Several dialog windows redundantly include "ScribeVault" in their window title bar, even though the main window already identifies the application. The OS window manager may further decorate these titles with the app name, creating double or triple repetition (e.g., "ScribeVault - Recordings Vault - ScribeVault"). Dialog titles should be clean and describe only the dialog's purpose.

## Goal

All dialog window titles show just their purpose (e.g., "Recordings Vault", "Settings", "AI Summary Viewer") without the redundant "ScribeVault" prefix. The main application window keeps "ScribeVault" as its title.

## Scope

### In Scope

- `src/gui/qt_vault_dialog.py:92` — change `"ScribeVault - Recordings Vault"` to `"Recordings Vault"`
- `src/gui/qt_settings_dialog.py:57` — change `"ScribeVault Settings"` to `"Settings"`
- `src/gui/qt_summary_viewer.py:60` — change `"ScribeVault - AI Summary Viewer"` to `"AI Summary Viewer"`

### Out of Scope

- Changing the main window title (`qt_main_window.py:468` — "ScribeVault" stays as-is)
- Changing dialog titles that are already clean ("Edit Recording", "Service Cost Comparison")
- Changing in-page header labels
- Adding window icons or other title bar customizations

## Acceptance Criteria

- [ ] Vault dialog window title shows "Recordings Vault"
- [ ] Settings dialog window title shows "Settings"
- [ ] Summary Viewer dialog window title shows "AI Summary Viewer"
- [ ] Main window title remains "ScribeVault"
- [ ] No visual duplication of the app name in any dialog title bar
- [ ] Existing tests still pass

## Tasks

| # | Task | Owner | Depends On | Status |
|---|------|-------|------------|--------|
| 1 | Update setWindowTitle in qt_vault_dialog.py, qt_settings_dialog.py, and qt_summary_viewer.py | Developer | — | TODO |
| 2 | Verify all dialog titles are clean and no regressions | Tech QA | 1 | TODO |

## Telemetry

| Metric           | Value |
|------------------|-------|
| **Total Tasks**      | 2     |
| **Total Duration**   | —     |
| **Total Tokens In**  | —     |
| **Total Tokens Out** | —     |

## Notes

Three one-line changes across three files. No dependencies on other beans.
