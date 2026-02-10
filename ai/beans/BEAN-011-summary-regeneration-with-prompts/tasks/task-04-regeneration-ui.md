# Task 04: Add Re-generation UI to Summary Viewer

## Metadata

| Field | Value |
|-------|-------|
| Task ID | BEAN-011-T04 |
| Owner | developer |
| Status | TODO |
| Depends On | T01, T02, T03 |
| Blocks | T06 |

## Description

Add a "Re-generate Summary" UI to `src/gui/qt_summary_viewer.py` with template selection dropdown, custom prompt input, and re-generate button.

## Acceptance Criteria

- [ ] "Re-generate Summary" button in the summary viewer footer
- [ ] Template dropdown with built-in + custom templates from PromptTemplateManager
- [ ] Free-text input area for custom prompts
- [ ] "Save as Template" button to save custom prompts
- [ ] Summary history panel showing previous summaries with timestamps
- [ ] Re-generation triggers summarizer with selected template/prompt
- [ ] UI updates with new summary after re-generation

## Technical Notes

- Add a new "Re-generate" group/section to the Summary tab in SummaryViewerDialog
- Use QComboBox for template dropdown, QTextEdit for custom prompt
- Signal/slot: re-generate button emits signal, parent handles the actual API call
- Summary history: simple QListWidget showing timestamp + template name, clicking loads that summary
