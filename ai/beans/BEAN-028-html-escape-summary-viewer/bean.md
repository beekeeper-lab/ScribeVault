# BEAN-028: HTML-Escape Dynamic Content in Summary Viewer

## Metadata

| Field     | Value        |
|-----------|--------------|
| ID        | BEAN-028     |
| Title     | HTML-Escape Dynamic Content in Summary Viewer |
| Type      | bug-fix      |
| Priority  | P2           |
| Status    | Done         |
| Created   | 2026-02-10   |
| Started   | 2026-02-10   |
| Completed | 2026-02-10   |
| Duration  |              |

## Problem Statement

The summary viewer (`qt_summary_viewer.py`) embeds transcription text and speaker names directly into HTML strings passed to `QTextBrowser.setHtml()` without escaping. In `_format_diarized_html()` (line ~979), the `text` variable from diarized transcription is interpolated raw into HTML `<p>` tags. While `QTextBrowser` does not execute JavaScript, unescaped content could break rendering, inject misleading HTML, or cause display corruption. The `markdown_to_html()` path (line ~558) using the `markdown` library also produces unescaped HTML from potentially untrusted content.

## Goal

All dynamic text content rendered in `QTextBrowser` is properly HTML-escaped before embedding, preventing HTML injection through transcription content or speaker names.

## Scope

### In Scope

- HTML-escape speaker text in `_format_diarized_html()` using `html.escape()`
- HTML-escape speaker names in the same method
- Review the `markdown_to_html()` path for XSS vectors and sanitize if needed
- Replace the `print()` error handler in `summarizer.py:324` with proper logger call (adjacent fix)

### Out of Scope

- Switching to a full HTML sanitization library (e.g., bleach)
- Changing the rendering widget from `QTextBrowser` to something else
- Sanitizing user-typed content in input fields

## Acceptance Criteria

- [x] `_format_diarized_html()` uses `html.escape()` on both `speaker` and `text` variables before HTML embedding
- [x] Transcription text containing `<script>`, `<img onerror=...>`, or `&` characters renders as literal text, not HTML
- [x] The `print()` call in `summarizer.py:324` is replaced with `logger.error()`
- [x] Unit tests cover: text with HTML entities, text with angle brackets, text with quotes
- [x] `pytest tests/` passes, `flake8 src/ tests/` is clean

## Tasks

| # | Task | Owner | Depends On | Status |
|---|------|-------|------------|--------|
| 1 | Add html.escape() to _format_diarized_html() | Developer | | Done |
| 2 | Review and fix markdown_to_html() path | Developer | | Done |
| 3 | Replace print() with logger in summarizer.py | Developer | | Done |
| 4 | Write unit tests for HTML escaping | Tech QA | 1, 2 | Done |

## Telemetry

| Metric           | Value |
|------------------|-------|
| Total Tasks      | 4     |
| Total Duration   |       |
| Total Tokens In  |       |
| Total Tokens Out |       |

## Notes

Key files: `src/gui/qt_summary_viewer.py` (lines 558, 870, 979), `src/ai/summarizer.py` (line 324). The `html` module from Python's standard library provides `html.escape()` which is sufficient for this use case.
