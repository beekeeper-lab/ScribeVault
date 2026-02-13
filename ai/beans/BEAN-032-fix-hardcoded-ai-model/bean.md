# BEAN-032: Fix Hardcoded AI Model Selection

## Metadata

| Field     | Value        |
|-----------|--------------|
| ID        | BEAN-032     |
| Title     | Fix Hardcoded AI Model Selection |
| Type      | bug-fix |
| Priority  | P1 |
| Status    | Unapproved   |
| Created   | 2026-02-13   |
| Started   |              |
| Completed |              |
| Duration  |              |

## Problem Statement

The `SummarizerService` hardcodes `model="gpt-3.5-turbo"` at lines 85 and 303-304 of `src/ai/summarizer.py`, completely ignoring the user's model selection from the Settings dialog. The settings UI lets users choose models like `gpt-4o-mini` or `gpt-4o` and shows cost estimates, but those choices have no effect on actual API calls. Users are unknowingly paying for `gpt-3.5-turbo` calls regardless of their selection.

## Goal

The summarizer uses the model configured by the user in Settings. Changes to the model in Settings take effect on the next API call without requiring an application restart.

## Scope

### In Scope

- Pass the configured model from `SummarizationSettings.model` into `SummarizerService`
- Update `_call_chat_api` (line 85) and `summarize_with_prompt` (line 303) to use the configured model
- Ensure `SummarizerService` is re-initialized or updated when settings change in `_apply_settings()`
- Remove duplicate `logger = logging.getLogger(__name__)` assignment (line 6 vs line 17)

### Out of Scope

- Changing the cost estimation logic
- Adding new model options to the settings dialog
- Changing the default model in `SummarizationSettings`

## Acceptance Criteria

- [ ] `SummarizerService` accepts a model parameter and uses it for all API calls
- [ ] Changing the model in Settings takes effect on the next summarization
- [ ] No hardcoded `"gpt-3.5-turbo"` references remain in summarizer.py
- [ ] Duplicate logger assignment is removed
- [ ] Existing tests pass
- [ ] New test verifies the model parameter is forwarded to the API call

## Tasks

| # | Task | Owner | Depends On | Status |
|---|------|-------|------------|--------|
| 1 | Update SummarizerService to accept and use model parameter | developer | | TODO |
| 2 | Wire model from SummarizationSettings into SummarizerService construction | developer | 1 | TODO |
| 3 | Ensure _apply_settings reinitializes summarizer with new model | developer | 2 | TODO |
| 4 | Add test for model parameter forwarding | tech-qa | 1 | TODO |

## Telemetry

| Metric           | Value |
|------------------|-------|
| Total Tasks      |       |
| Total Duration   |       |
| Total Tokens In  |       |
| Total Tokens Out |       |

## Notes

This is a user-facing bug — the Settings dialog creates a false impression that model selection works. BEAN-023 (Update AI Summary Models & Cost Estimation) updated the model options and pricing but didn't fix the underlying hardcoding in the service layer.
