# BEAN-004: API Key Validation & Secure Storage

## Metadata

| Field     | Value        |
|-----------|--------------|
| ID        | BEAN-004     |
| Title     | API Key Validation & Secure Storage |
| Type      | bug-fix |
| Priority  | P1 |
| Status    | Done         |
| Owner     | team-lead    |
| Created   | 2026-02-10   |
| Started   | 2026-02-10 15:39 |
| Completed | 2026-02-10   |
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

- [x] API key is validated (format + live check) when saved in settings
- [x] Invalid key shows clear error message to user
- [x] Plaintext .env fallback removed; keys stored only via keyring or encrypted config
- [x] `.env` is listed in `.gitignore`
- [x] Settings dialog shows key status (valid/invalid/not configured)
- [x] App startup gracefully handles missing key with user-friendly message
- [x] Existing tests still pass; new tests cover validation logic

## Tasks

| # | Task | Owner | Depends On | Status |
|---|------|-------|------------|--------|
| 1 | Add live API key validation to SettingsManager | developer | — | Done |
| 2 | Remove plaintext .env fallback for API key storage | developer | — | Done |
| 3 | Update SummarizerService to use SettingsManager for API key | developer | T001 | Done |
| 4 | Update settings dialog with API key status indicator | developer | T001 | Done |
| 5 | Write tests for API key validation logic | tech-qa | T001,T002,T003 | Done |

## Telemetry

| Metric           | Value |
|------------------|-------|
| Total Tasks      |       |
| Total Duration   |       |
| Total Tokens In  |       |
| Total Tokens Out |       |

## Notes

No dependencies on other beans. Touches `src/config/settings.py`, `src/ai/summarizer.py`, `src/gui/qt_settings_dialog.py`.
