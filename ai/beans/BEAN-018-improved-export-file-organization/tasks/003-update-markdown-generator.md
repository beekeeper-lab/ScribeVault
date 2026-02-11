# Task 003: Update MarkdownGenerator for title-first filenames and subfolders

**Owner:** Developer
**Status:** TODO
**Depends On:** 001

## Description

Update `save_markdown_file()` in `markdown_generator.py` to:
- Change filename from `{YYYYMMDD_HHMMSS}_{Title}.md` to `{Title}.md`
- Create a per-recording subfolder within `summaries/` directory using the sanitized title
- Use the shared `sanitize_title()` utility

## Acceptance Criteria

- [ ] Filename is `{Title}.md` (no timestamp prefix)
- [ ] Output is in a per-recording subfolder `summaries/{Title}/`
- [ ] Uses shared sanitize_title utility
