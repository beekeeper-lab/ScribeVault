# BEAN-011: Summary Re-generation with Prompt Templates

## Metadata

| Field     | Value        |
|-----------|--------------|
| ID        | BEAN-011     |
| Title     | Summary Re-generation with Prompt Templates |
| Type      | feature |
| Priority  | P2 |
| Status    | Done   |
| Created   | 2026-02-10   |
| Started   | 2026-02-10 16:19 |
| Completed | 2026-02-10 16:36 |
| Duration  | 17m          |

## Problem Statement

Once a summary is generated, there is no way to regenerate it with a different prompt or style. The summary style parameter is also ignored for meeting-category recordings (hardcoded to `generate_structured_summary()`). Users want to:
1. Re-run summaries on existing transcriptions with different prompts
2. Use saved prompt templates (e.g., "Action Items", "Key Decisions", "Brief Summary")
3. Write custom prompts for one-off re-generation
4. Save custom prompts as reusable templates

## Goal

Users can regenerate summaries on any existing transcription using either predefined templates or custom prompts, and save custom prompts for reuse.

## Scope

### In Scope

- Add "Re-generate Summary" button to vault detail / summary viewer
- Provide built-in prompt templates: Action Items, Key Decisions, Brief Summary, Detailed Notes, Meeting Minutes
- Free-text prompt input for custom re-generation
- Save/load custom prompt templates (stored in config)
- Fix: summary style parameter respected for all recording categories (not just non-meetings)
- Store multiple summaries per recording (original + re-generated)

### Out of Scope

- Different AI models for re-generation (use configured model)
- Batch re-generation across multiple recordings
- Prompt sharing/export

## Acceptance Criteria

- [x] "Re-generate Summary" button available in vault detail view
- [x] Built-in prompt templates available in dropdown (at least 5 templates)
- [x] Free-text prompt input available for custom prompts
- [x] Custom prompts can be saved as new templates
- [x] Summary style parameter works correctly for all recording categories
- [x] Multiple summaries stored per recording (viewable in history)
- [x] New tests cover re-generation and template management

## Tasks

| # | Task | Owner | Depends On | Status |
|---|------|-------|------------|--------|
| 1 | Create Prompt Template Manager | developer | - | DONE |
| 2 | Fix Summary Style Parameter Bug | developer | T01 | DONE |
| 3 | Add Summary History Storage | developer | T01 | DONE |
| 4 | Add Re-generation UI to Summary Viewer | developer | T01,T02,T03 | DONE |
| 5 | Integrate Re-generation into Vault Dialog | developer | T01,T02,T03,T04 | DONE |
| 6 | Write Tests for Re-generation and Templates | tech-qa | T04,T05 | DONE |
| 7 | Final Verification and Cleanup | team-lead | T06 | DONE |

## Telemetry

| Metric           | Value |
|------------------|-------|
| Total Tasks      | 7     |
| Total Duration   |       |
| Total Tokens In  |       |
| Total Tokens Out |       |

## Notes

No dependencies on other beans. Touches `src/ai/summarizer.py`, `src/gui/qt_summary_viewer.py`, `src/gui/qt_vault_dialog.py`, and vault storage.
