# BEAN-022: Vault Header Cleanup

## Metadata

| Field     | Value        |
|-----------|--------------|
| ID        | BEAN-022     |
| Title     | Vault Header Cleanup |
| Type      | bug-fix      |
| Priority  | P3           |
| Status    | Done         |
| Created   | 2026-02-10   |
| Started   | 2026-02-11   |
| Completed | 2026-02-11   |
| Duration  |              |

## Problem Statement

On the Recording Vault screen header, there are two UI issues next to the Category dropdown:

1. The refresh button uses an emoji (🔄) that doesn't render properly on some systems, appearing as a small rectangle or single-pixel artifact.
2. A custom close button (✕) is redundant with the window's built-in title bar close button, wasting header space and potentially confusing users.

## Goal

The vault header is clean and functional: the refresh button uses readable text instead of a potentially broken emoji, and the redundant close button is removed since the window already has a native close control.

## Scope

### In Scope

- Replace the 🔄 emoji on the refresh button with readable text (e.g., "Refresh")
- Remove the custom ✕ close button from the vault header layout (lines 132-141 of `qt_vault_dialog.py`)
- Adjust header layout spacing as needed after removing the close button

### Out of Scope

- Redesigning the vault header layout
- Adding new buttons or controls
- Changing other emoji-based button labels (they render fine)

## Acceptance Criteria

- [x] The refresh button displays readable text ("Refresh") instead of the 🔄 emoji
- [x] The refresh button still triggers `load_recordings()` when clicked
- [x] The custom ✕ close button is removed from the header
- [x] The vault can still be closed via the window's native title bar close button
- [x] No layout or spacing regressions in the header area
- [x] Existing tests continue to pass

## Tasks

| # | Task | Owner | Depends On | Status |
|---|------|-------|------------|--------|
| 1 | Replace refresh button emoji with "Refresh" text | Developer | — | Done |
| 2 | Remove custom close button from header | Developer | — | Done |
| 3 | Run tests and lint verification | Tech-QA | 1, 2 | Done |

## Telemetry

| Metric           | Value |
|------------------|-------|
| Total Tasks      |       |
| Total Duration   |       |
| Total Tokens In  |       |
| Total Tokens Out |       |

## Notes

- Affected file: `src/gui/qt_vault_dialog.py`, lines 126-141 in the `setup_ui()` method.
- The close button at line 133 calls `self.accept()`, which is the same behavior as the window close. No functionality is lost by removing it.
- Very small change — approximately 15 lines affected in a single file.
