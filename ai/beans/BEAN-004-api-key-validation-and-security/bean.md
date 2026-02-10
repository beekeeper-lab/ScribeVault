# BEAN-004: API Key Validation & Secure Storage

## Metadata

| Field     | Value        |
|-----------|--------------|
| ID        | BEAN-004     |
| Title     | API Key Validation & Secure Storage |
| Type      | bug-fix |
| Priority  | P1 |
| Status    | Unapproved   |
| Created   | 2026-02-10   |
| Started   |              |
| Completed |              |
| Duration  |              |

## Problem Statement

Multiple security and usability issues with API key handling:
1. `SummarizerService.__init__()` creates an OpenAI client with `os.getenv("OPENAI_API_KEY")` which can be None — fails silently until first API call.
2. `src/config/settings.py` falls back to storing API keys in plaintext `.env` file when keyring is unavailable.
3. No validation that an API key is actually valid before attempting operations.
4. `.env` may not be in `.gitignore`, risking credential leaks.

## Goal

API keys are validated early, stored securely, and users get clear feedback about key status.

## Scope

### In Scope

- Validate API key format on save in settings dialog
- Test API key validity with a lightweight API call (e.g., list models) when user saves settings
- Remove plaintext `.env` fallback — require keyring or encrypted config
- Add `.env` to `.gitignore` if not already present
- Show clear API key status indicator in settings (valid/invalid/missing)

### Out of Scope

- Supporting multiple API providers
- OAuth flows
- API key rotation

## Acceptance Criteria

- [ ] API key is validated (format + live check) when saved in settings
- [ ] Invalid key shows clear error message to user
- [ ] Plaintext .env fallback removed; keys stored only via keyring or encrypted config
- [ ] `.env` is listed in `.gitignore`
- [ ] Settings dialog shows key status (valid/invalid/not configured)
- [ ] App startup gracefully handles missing key with user-friendly message
- [ ] Existing tests still pass; new tests cover validation logic

## Tasks

| # | Task | Owner | Depends On | Status |
|---|------|-------|------------|--------|
| 1 |      |       |            | TODO   |
| 2 |      |       |            | TODO   |
| 3 |      |       |            | TODO   |

## Telemetry

| Metric           | Value |
|------------------|-------|
| Total Tasks      |       |
| Total Duration   |       |
| Total Tokens In  |       |
| Total Tokens Out |       |

## Notes

No dependencies on other beans. Touches `src/config/settings.py`, `src/ai/summarizer.py`, `src/gui/qt_settings_dialog.py`.
