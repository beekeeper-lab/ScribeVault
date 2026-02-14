# BEAN-032: Fix Services Ignoring User Settings

## Metadata

| Field     | Value        |
|-----------|--------------|
| ID        | BEAN-032     |
| Title     | Fix Services Ignoring User Settings |
| Type      | bug-fix |
| Priority  | P1 |
| Status    | In Progress  |
| Created   | 2026-02-13   |
| Started   |              |
| Completed |              |
| Duration  |              |

## Problem Statement

Two core services ignore user-configured settings, falling back to hardcoded or environment-variable values:

1. **SummarizerService** hardcodes `model="gpt-3.5-turbo"` at lines 85 and 303-304 of `src/ai/summarizer.py`, completely ignoring the user's model selection from the Settings dialog. The settings UI lets users choose models like `gpt-4o-mini` or `gpt-4o` and shows cost estimates, but those choices have no effect on actual API calls. Users are unknowingly paying for `gpt-3.5-turbo` calls regardless of their selection.

2. **WhisperService** bypasses the settings manager's secure API key storage. When initialized with a `settings_manager` that has an OpenAI API key available (via keyring or encrypted config), lines 76-85 of `src/transcription/whisper_service.py` bypass the settings manager entirely and read the key directly from `os.getenv("OPENAI_API_KEY")`. This means API keys stored securely via keyring or encrypted config (implemented in BEAN-004 and hardened in BEAN-026) are never used for the OpenAI Whisper client.

## Goal

Both services respect user-configured settings: the summarizer uses the selected model, and WhisperService uses the settings manager's API key. Environment variable fallback only applies when no settings manager is provided.

## Scope

### In Scope

- Pass the configured model from `SummarizationSettings.model` into `SummarizerService`
- Update `_call_chat_api` (line 85) and `summarize_with_prompt` (line 303) to use the configured model
- Ensure `SummarizerService` is re-initialized or updated when settings change in `_apply_settings()`
- Remove duplicate `logger = logging.getLogger(__name__)` assignment (line 6 vs line 17) in summarizer.py
- Update `WhisperService.__init__` (lines 76-85) to use `settings_manager.get_openai_api_key()` when available
- Ensure the fallback to `os.getenv("OPENAI_API_KEY")` only happens when no settings_manager is provided
- Remove redundant `load_dotenv()` call at module level (line 29) in whisper_service.py — it's already called in settings.py

### Out of Scope

- Changing the cost estimation logic
- Adding new model options to the settings dialog
- Changing the default model in `SummarizationSettings`
- Changing the keyring/encryption implementation
- Modifying the settings dialog API key UI
- Adding API key validation/testing to WhisperService

## Acceptance Criteria

- [ ] `SummarizerService` accepts a model parameter and uses it for all API calls
- [ ] Changing the model in Settings takes effect on the next summarization
- [ ] No hardcoded `"gpt-3.5-turbo"` references remain in summarizer.py
- [ ] Duplicate logger assignment is removed
- [ ] `WhisperService` uses `settings_manager.get_openai_api_key()` when settings_manager is provided
- [ ] API key from keyring/encrypted config is correctly passed to `openai.OpenAI(api_key=...)`
- [ ] Environment variable fallback works when no settings_manager is provided
- [ ] Redundant `load_dotenv()` removed from whisper_service.py
- [ ] Existing tests pass
- [ ] New test verifies model parameter is forwarded to the API call
- [ ] New test verifies API key resolution priority (settings_manager > env var)

## Tasks

| # | Task | Owner | Depends On | Status |
|---|------|-------|------------|--------|
| 1 | Update SummarizerService to accept and use model parameter | developer | | TODO |
| 2 | Wire model from SummarizationSettings into SummarizerService construction | developer | 1 | TODO |
| 3 | Ensure _apply_settings reinitializes summarizer with new model | developer | 2 | TODO |
| 4 | Update WhisperService init to use settings_manager.get_openai_api_key() | developer | | TODO |
| 5 | Remove redundant load_dotenv() call from whisper_service.py | developer | 4 | TODO |
| 6 | Add test for model parameter forwarding | tech-qa | 1 | TODO |
| 7 | Add test for API key resolution priority | tech-qa | 4 | TODO |

## Telemetry

| Metric           | Value |
|------------------|-------|
| Total Tasks      |       |
| Total Duration   |       |
| Total Tokens In  |       |
| Total Tokens Out |       |

## Notes

Merged from BEAN-032 (Fix Hardcoded AI Model Selection) and BEAN-033 (Fix WhisperService API Key Bypass) during backlog consolidation.

This is a user-facing bug — the Settings dialog creates a false impression that model selection works. BEAN-023 (Update AI Summary Models & Cost Estimation) updated the model options and pricing but didn't fix the underlying hardcoding in the service layer.

The WhisperService issue is closely related to BEAN-004 (API Key Validation & Secure Storage) and BEAN-026 (Harden API Key Encryption). The secure storage infrastructure exists but WhisperService doesn't use it. Note `load_dotenv()` is called at module level in 3 files (settings.py, summarizer.py, whisper_service.py) — only needs to be called once.
