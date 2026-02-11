# Task 01: Define Model/Pricing Config Structure

## Owner: Developer
## Status: TODO
## Depends On: —

## Description
Create `config/model_pricing.json` as the single source of truth for AI model data and pricing. This file will be loaded by CostEstimator and the settings dialog.

## Acceptance Criteria
- JSON file with current OpenAI model names, pricing per 1K tokens (input/output), and metadata
- Includes `last_updated` timestamp
- Covers: gpt-4o, gpt-4o-mini, gpt-4-turbo
- Whisper pricing included
