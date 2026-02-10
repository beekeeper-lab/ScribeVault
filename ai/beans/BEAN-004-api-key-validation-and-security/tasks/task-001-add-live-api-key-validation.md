# Task 001: Add Live API Key Validation to SettingsManager

## Metadata

| Field      | Value       |
|------------|-------------|
| Task ID    | BEAN-004-T001 |
| Owner      | developer   |
| Status     | TODO        |
| Depends On | —           |

## Description

Add a `validate_openai_api_key_live` method to `SettingsManager` that makes a lightweight OpenAI API call (e.g., `client.models.list()`) to verify the key is active and valid, not just format-checking. Update the existing `validate_openai_api_key` to be more robust with format checks.

## Acceptance Criteria

- [ ] `validate_openai_api_key` checks format (starts with `sk-`, minimum length)
- [ ] New `validate_openai_api_key_live` method tests key against the OpenAI API
- [ ] Returns a tuple of (is_valid: bool, message: str) for clear feedback
- [ ] Handles network errors, auth errors, and other exceptions gracefully

## Files to Modify

- `src/config/settings.py`
