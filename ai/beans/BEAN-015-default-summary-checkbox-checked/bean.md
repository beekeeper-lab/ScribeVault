# BEAN-015: Default AI Summary Checkbox to Checked

## Metadata

| Field     | Value        |
|-----------|--------------|
| **ID**        | BEAN-015     |
| **Title**     | Default AI Summary Checkbox to Checked |
| **Type**      | enhancement |
| **Priority**  | P2 |
| **Status**    | Approved     |
| **Created**   | 2026-02-10   |
| **Started**   | —            |
| **Completed** | —            |
| **Duration**  | —            |

## Problem Statement

The "Generate AI Summary" checkbox on the main recording page defaults to unchecked. This means new users (or users who haven't explicitly toggled it) won't get AI summaries for their recordings unless they manually check the box each session. Since summarization is a core value proposition of ScribeVault, the default should encourage its use.

## Goal

The "Generate AI Summary" checkbox is checked by default on first launch and for any user who hasn't explicitly saved a preference, so recordings automatically include AI summaries when the summarizer service is available.

## Scope

### In Scope

- Change the default value of the `recording/generate_summary` QSettings key from `False` to `True`
- Ensure the checkbox still respects a user's explicitly saved preference (if they uncheck it, it stays unchecked)

### Out of Scope

- Changing summarizer initialization logic
- Adding new UI elements
- Changing behavior when API key is not configured (existing warning is sufficient)

## Acceptance Criteria

- [ ] On first launch (no saved settings), the "Generate AI Summary" checkbox is checked
- [ ] If a user unchecks the box and restarts, it remains unchecked (saved preference respected)
- [ ] If summarizer service is unavailable, the pipeline gracefully skips summarization (existing behavior, no regression)
- [ ] Existing tests still pass

## Tasks

| # | Task | Owner | Depends On | Status |
|---|------|-------|------------|--------|
| 1 |      |       |            | TODO   |
| 2 |      |       |            | TODO   |
| 3 |      |       |            | TODO   |

## Telemetry

| Metric           | Value |
|------------------|-------|
| **Total Tasks**      | —     |
| **Total Duration**   | —     |
| **Total Tokens In**  | —     |
| **Total Tokens Out** | —     |

## Notes

One-line change at `src/gui/qt_main_window.py` line 744: change `False` to `True` in the QSettings default value. No dependencies on other beans.
