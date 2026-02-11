# Task 03: Update AI Summary Tab UI

## Owner: Developer
## Status: TODO
## Depends On: Task 01

## Description
Update `src/gui/qt_settings_dialog.py`:
- Remove Service dropdown (hardcode "openai" internally)
- Replace model dropdown with current models from config
- Update cost estimation to use CostEstimator with model parameter

## Acceptance Criteria
- Service dropdown removed from AI Summary tab
- Model dropdown lists gpt-4o, gpt-4o-mini, gpt-4-turbo
- Cost estimation uses CostEstimator (no inline pricing)
