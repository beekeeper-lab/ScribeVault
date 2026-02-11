# BEAN-023: Update AI Summary Models & Cost Estimation

## Metadata

| Field     | Value        |
|-----------|--------------|
| ID        | BEAN-023     |
| Title     | Update AI Summary Models & Cost Estimation |
| Type      | enhancement  |
| Priority  | P1           |
| Status    | Approved     |
| Created   | 2026-02-10   |
| Started   |              |
| Completed |              |
| Duration  |              |

## Problem Statement

The AI Summary tab in Settings offers outdated GPT models (gpt-3.5-turbo, gpt-4, gpt-4-turbo-preview) that no longer reflect current OpenAI offerings. The cost estimation is hardcoded with stale pricing that doesn't match real API rates. Additionally, the "Service" dropdown only contains "openai" as an option, adding UI clutter with no value. There is no mechanism to update model lists or pricing without a code change.

## Goal

The AI Summary settings tab offers current model options with accurate cost estimates, a way to refresh model/pricing data on demand, and a clean UI free of single-option dropdowns.

## Scope

### In Scope

- Replace model dropdown options with current models (e.g., gpt-4o, gpt-4o-mini, gpt-4-turbo)
- Refactor cost estimation to use a single source of truth (eliminate duplication between dialog and CostEstimator)
- Add an "Update" button that refreshes available models and pricing on demand (e.g., from a local config or API call)
- Display a "Last Updated" date for model/pricing data
- Remove the single-option "Service" dropdown (hardcode "openai" internally until alternatives exist)
- Update the cost comparison dialog with current pricing

### Out of Scope

- Adding non-OpenAI summarization services (e.g., local LLM, Anthropic)
- Dynamic real-time pricing from OpenAI API (use a maintainable static config that can be refreshed)
- Changes to the transcription cost estimates (separate concern)

## Acceptance Criteria

- [ ] Model dropdown lists current OpenAI models (gpt-4o, gpt-4o-mini, at minimum)
- [ ] Legacy models (gpt-3.5-turbo, gpt-4, gpt-4-turbo-preview) are removed or clearly marked as legacy
- [ ] Cost estimation uses a single source of truth — no duplicated pricing constants
- [ ] "Update" button exists and refreshes model list and pricing data
- [ ] "Last Updated" date is displayed near the cost estimation section
- [ ] Single-option "Service" dropdown is removed from the AI Summary tab
- [ ] Cost comparison dialog reflects current model pricing
- [ ] Existing tests pass; new tests cover the refactored cost estimation

## Tasks

| # | Task | Owner | Depends On | Status |
|---|------|-------|------------|--------|
| 1 | Define maintainable model/pricing config structure | | | TODO |
| 2 | Refactor CostEstimator to single source of truth | | 1 | TODO |
| 3 | Update AI Summary tab UI (models, remove Service dropdown) | | 1 | TODO |
| 4 | Add Update button and Last Updated display | | 2, 3 | TODO |
| 5 | Update cost comparison dialog | | 2 | TODO |
| 6 | Write/update tests | | 2, 3, 4 | TODO |

## Telemetry

| Metric           | Value |
|------------------|-------|
| Total Tasks      |       |
| Total Duration   |       |
| Total Tokens In  |       |
| Total Tokens Out |       |

## Notes

- The current CostEstimator class (src/config/settings.py) and the settings dialog (src/gui/qt_settings_dialog.py) both contain hardcoded pricing — these need to be consolidated.
- Consider storing model/pricing data in a JSON file under config/ that can be updated independently.
