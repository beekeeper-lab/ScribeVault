# Task 005: Write Tests for API Key Validation Logic

## Metadata

| Field      | Value       |
|------------|-------------|
| Task ID    | BEAN-004-T005 |
| Owner      | tech-qa     |
| Status     | TODO        |
| Depends On | T001, T002, T003 |

## Description

Write comprehensive unit tests for the API key validation logic including format validation, live validation (mocked), encrypted config storage, and the updated SummarizerService initialization.

## Acceptance Criteria

- [ ] Tests for `validate_openai_api_key` format checks (valid, invalid, edge cases)
- [ ] Tests for `validate_openai_api_key_live` with mocked OpenAI client
- [ ] Tests for encrypted config fallback (keyring unavailable scenario)
- [ ] Tests for `SummarizerService` init with/without settings manager
- [ ] Tests for `get_openai_api_key` priority chain (keyring → encrypted → env)
- [ ] All existing tests still pass
- [ ] New tests pass with `pytest tests/`

## Files to Create/Modify

- `tests/test_api_key_validation.py` (new)
