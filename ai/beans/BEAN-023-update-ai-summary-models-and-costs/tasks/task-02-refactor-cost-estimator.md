# Task 02: Refactor CostEstimator to Single Source of Truth

## Owner: Developer
## Status: TODO
## Depends On: Task 01

## Description
Refactor `CostEstimator` in `src/config/settings.py` to load pricing from `config/model_pricing.json` instead of hardcoded constants. Add model-aware cost estimation that accepts a model name parameter.

## Acceptance Criteria
- CostEstimator loads pricing from JSON config
- `estimate_summary_cost` accepts a model parameter
- No duplicated pricing constants remain
- Backward-compatible API
