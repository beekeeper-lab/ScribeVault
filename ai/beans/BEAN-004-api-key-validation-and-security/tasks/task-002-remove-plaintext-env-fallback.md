# Task 002: Remove Plaintext .env Fallback for API Key Storage

## Metadata

| Field      | Value       |
|------------|-------------|
| Task ID    | BEAN-004-T002 |
| Owner      | developer   |
| Status     | TODO        |
| Depends On | —           |

## Description

Remove the plaintext `.env` file fallback from `save_openai_api_key`. When keyring is unavailable, use an encrypted config file instead. The `_update_env_file` method should be removed. `get_openai_api_key` should stop falling back to `os.getenv` for stored keys (environment variable can still be used as a read-only override for CI/dev but never written to).

## Acceptance Criteria

- [ ] `save_openai_api_key` no longer writes to `.env` file
- [ ] `_update_env_file` method removed
- [ ] When keyring unavailable, keys stored in encrypted config (using `cryptography.fernet` or similar)
- [ ] `get_openai_api_key` reads from: keyring → encrypted config → env var (read-only fallback)
- [ ] Clear warning logged when using encrypted config vs keyring

## Files to Modify

- `src/config/settings.py`
