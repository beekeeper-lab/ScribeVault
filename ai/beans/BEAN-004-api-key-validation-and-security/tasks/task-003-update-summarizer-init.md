# Task 003: Update SummarizerService to Use SettingsManager for API Key

## Metadata

| Field      | Value       |
|------------|-------------|
| Task ID    | BEAN-004-T003 |
| Owner      | developer   |
| Status     | TODO        |
| Depends On | T001        |

## Description

`SummarizerService.__init__` currently does `openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))` which can be None. Update it to accept a `SettingsManager` and use `get_openai_api_key()`. Raise a clear error at init time if no key is available. Update all call sites.

## Acceptance Criteria

- [ ] `SummarizerService.__init__` accepts optional `settings_manager` parameter
- [ ] Uses `settings_manager.get_openai_api_key()` when available
- [ ] Raises `ValueError` with user-friendly message if no API key configured
- [ ] All call sites in `qt_main_window.py`, `qt_app.py`, `main_window.py` updated
- [ ] Graceful degradation: app still starts without API key, summarization is just disabled

## Files to Modify

- `src/ai/summarizer.py`
- `src/gui/qt_main_window.py`
- `src/gui/qt_app.py`
- `src/gui/main_window.py`
