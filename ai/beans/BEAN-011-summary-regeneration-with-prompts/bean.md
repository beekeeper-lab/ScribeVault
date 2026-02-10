# BEAN-011: Summary Re-generation with Prompt Templates

## Metadata

| Field     | Value        |
|-----------|--------------|
| ID        | BEAN-011     |
| Title     | Summary Re-generation with Prompt Templates |
| Type      | feature |
| Priority  | P2 |
| Status    | Approved   |
| Created   | 2026-02-10   |
| Started   |              |
| Completed |              |
| Duration  |              |

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

- [ ] "Re-generate Summary" button available in vault detail view
- [ ] Built-in prompt templates available in dropdown (at least 5 templates)
- [ ] Free-text prompt input available for custom prompts
- [ ] Custom prompts can be saved as new templates
- [ ] Summary style parameter works correctly for all recording categories
- [ ] Multiple summaries stored per recording (viewable in history)
- [ ] New tests cover re-generation and template management

## Tasks

| # | Task | Owner | Depends On | Status |
|---|------|-------|------------|--------|
| 1 |      |       |            | TODO   |
| 2 |      |       |            | TODO   |
| 3 |      |       |            | TODO   |

## Telemetry

| Metric           | Value |
|------------------|-------|
| Total Tasks      |       |
| Total Duration   |       |
| Total Tokens In  |       |
| Total Tokens Out |       |

## Notes

No dependencies on other beans. Touches `src/ai/summarizer.py`, `src/gui/qt_summary_viewer.py`, `src/gui/qt_vault_dialog.py`, and vault storage.
