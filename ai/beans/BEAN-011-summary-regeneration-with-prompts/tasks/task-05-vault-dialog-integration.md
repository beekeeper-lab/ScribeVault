# Task 05: Integrate Re-generation into Vault Dialog

## Metadata

| Field | Value |
|-------|-------|
| Task ID | BEAN-011-T05 |
| Owner | developer |
| Status | TODO |
| Depends On | T01, T02, T03, T04 |
| Blocks | T06 |

## Description

Wire up the re-generation flow in `src/gui/qt_vault_dialog.py` so that when the user triggers re-generation from the summary viewer, the vault dialog handles the API call, stores the result, and updates the UI.

## Acceptance Criteria

- [ ] VaultDialog passes summarizer service and template manager to SummaryViewerDialog
- [ ] Re-generation signal from viewer triggers summarizer call in vault dialog
- [ ] New summary is stored in vault via `add_summary()`
- [ ] Recording details panel refreshes after re-generation
- [ ] Error handling for failed re-generation (no API key, network error, etc.)

## Technical Notes

- Use a worker thread (QThread) for the API call to avoid UI freeze
- Connect SummaryViewerDialog.regenerate_requested signal to VaultDialog handler
- Pass PromptTemplateManager and SummarizerService to SummaryViewerDialog constructor
