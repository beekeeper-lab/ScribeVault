# BEAN-024: Implement Test Settings Button

## Metadata

| Field     | Value        |
|-----------|--------------|
| ID        | BEAN-024     |
| Title     | Implement Test Settings Button |
| Type      | enhancement  |
| Priority  | P2           |
| Status    | Done         |
| Created   | 2026-02-10   |
| Started   | 2026-02-11   |
| Completed | 2026-02-11   |
| Duration  |              |

## Problem Statement

The Settings dialog has a "Test Settings" button at the bottom that currently shows a "not yet implemented" message when clicked. This is misleading — users expect the button to do something useful. The button should either be wired up to actually validate the current settings or be removed entirely. The user has opted to implement it.

## Goal

Clicking "Test Settings" runs a suite of quick diagnostic checks against the current settings and displays clear pass/fail results, giving users confidence their configuration is correct before they start recording.

## Scope

### In Scope

- Test OpenAI API key validity (if transcription or summarization uses OpenAI)
- Verify recordings directory exists and is writable
- Verify vault directory exists and is writable
- Test microphone access (quick open/close of the selected audio input device)
- Display results in a clear pass/fail list within a dialog
- Handle timeouts gracefully (e.g., slow API response)

### Out of Scope

- Full end-to-end recording test (record + transcribe + summarize)
- Network connectivity checks beyond API key validation
- Automatic fix/repair of failed checks
- Testing local Whisper model availability or download

## Acceptance Criteria

- [x] "Test Settings" button triggers actual diagnostic checks (not a placeholder message)
- [x] API key connectivity is tested when OpenAI service is selected
- [x] Storage directories are checked for existence and write permissions
- [x] Microphone device is tested for availability
- [x] Results are displayed in a dialog with clear pass/fail indicators per check
- [x] Checks that don't apply (e.g., API key when using local transcription) are skipped or shown as "N/A"
- [x] A timeout prevents the dialog from hanging on slow responses
- [x] Existing tests pass; new tests cover the diagnostic logic

## Tasks

| # | Task | Owner | Depends On | Status |
|---|------|-------|------------|--------|
| 1 | Implement diagnostic check functions (API, dirs, mic) | Developer | | Done |
| 2 | Create results display dialog | Developer | | Done |
| 3 | Wire "Test Settings" button to run checks and show results | Developer | 1, 2 | Done |
| 4 | Add timeout handling for API checks | Developer | 1 | Done |
| 5 | Write tests for diagnostic logic | Tech-QA | 1 | Done |

## Telemetry

| Metric           | Value |
|------------------|-------|
| Total Tasks      |       |
| Total Duration   |       |
| Total Tokens In  |       |
| Total Tokens Out |       |

## Notes

- The existing `test_settings()` method is at `src/gui/qt_settings_dialog.py` line 985.
- API key validation logic already exists in the Transcription tab — reuse `validate_openai_api_key_live()` from SettingsManager.
- Microphone test can use PyAudio's `open()`/`close()` pattern — no need to actually record audio.
