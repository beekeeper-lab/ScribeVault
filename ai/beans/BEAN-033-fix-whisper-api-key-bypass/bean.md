# BEAN-033: Fix WhisperService API Key Bypass

## Metadata

| Field     | Value        |
|-----------|--------------|
| ID        | BEAN-033     |
| Title     | Fix WhisperService API Key Bypass |
| Type      | bug-fix |
| Priority  | P1 |
| Status    | Unapproved   |
| Created   | 2026-02-13   |
| Started   |              |
| Completed |              |
| Duration  |              |

## Problem Statement

When `WhisperService` is initialized with a `settings_manager` that has an OpenAI API key available (via keyring or encrypted config), lines 76-85 of `src/transcription/whisper_service.py` bypass the settings manager entirely and read the key directly from `os.getenv("OPENAI_API_KEY")`. This means API keys stored securely via keyring or encrypted config (implemented in BEAN-004 and hardened in BEAN-026) are never used for the OpenAI Whisper client. Users who configured their key through the Settings UI (which stores to keyring) will get "no API key" errors unless they also set the environment variable.

## Goal

`WhisperService` uses `settings_manager.get_openai_api_key()` when a settings_manager is available, falling back to environment variable only when no settings_manager is provided.

## Scope

### In Scope

- Update `WhisperService.__init__` (lines 76-85) to use `settings_manager.get_openai_api_key()` when available
- Ensure the fallback to `os.getenv("OPENAI_API_KEY")` only happens when no settings_manager is provided
- Remove redundant `load_dotenv()` call at module level (line 29) — it's already called in settings.py

### Out of Scope

- Changing the keyring/encryption implementation
- Modifying the settings dialog API key UI
- Adding API key validation/testing to WhisperService

## Acceptance Criteria

- [ ] `WhisperService` uses `settings_manager.get_openai_api_key()` when settings_manager is provided
- [ ] API key from keyring/encrypted config is correctly passed to `openai.OpenAI(api_key=...)`
- [ ] Environment variable fallback works when no settings_manager is provided
- [ ] Redundant `load_dotenv()` removed from whisper_service.py
- [ ] New test verifies API key resolution priority (settings_manager > env var)

## Tasks

| # | Task | Owner | Depends On | Status |
|---|------|-------|------------|--------|
| 1 | Update WhisperService init to use settings_manager.get_openai_api_key() | developer | | TODO |
| 2 | Remove redundant load_dotenv() call | developer | 1 | TODO |
| 3 | Add test for API key resolution priority | tech-qa | 1 | TODO |

## Telemetry

| Metric           | Value |
|------------------|-------|
| Total Tasks      |       |
| Total Duration   |       |
| Total Tokens In  |       |
| Total Tokens Out |       |

## Notes

This is closely related to BEAN-004 (API Key Validation & Secure Storage) and BEAN-026 (Harden API Key Encryption). The secure storage infrastructure exists but WhisperService doesn't use it. The `SummarizerService` (line 52) has a similar but less severe issue — it falls back to `os.getenv("OPENAI_API_KEY")` but at least accepts an API key parameter. Also note `load_dotenv()` is called at module level in 3 files (settings.py, summarizer.py, whisper_service.py) — only needs to be called once.
