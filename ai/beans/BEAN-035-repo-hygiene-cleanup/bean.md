# BEAN-035: Root-Level Test Files & Repo Hygiene

## Metadata

| Field     | Value        |
|-----------|--------------|
| ID        | BEAN-035     |
| Title     | Root-Level Test Files & Repo Hygiene |
| Type      | enhancement |
| Priority  | P0 |
| Status    | Approved     |
| Created   | 2026-02-13   |
| Started   |              |
| Completed |              |
| Duration  |              |

## Problem Statement

Multiple repo hygiene issues need attention:

1. **Sensitive user data tracked in git:** The `summaries/` directory contains 2 real business meeting transcripts with potentially sensitive content (company names, people's names, business discussions). This directory is not in `.gitignore`.

2. **12 orphaned root-level scripts:** 9 test/debug files (`test_audio.py`, `test_buttons.py`, `test_config.py`, `test_costs.py`, `test_debug.py`, `test_markdown.py`, `test_markdown_viewer.py`, `test_structured_summary.py`, `test_zero_cost.py`) plus 3 utility scripts (`diagnose_audio.py`, `update_summary.py`, `regenerate_markdown.py`) are tracked but not part of the test suite. Several are empty 1-line files.

3. **`.gitignore` gaps:** Missing patterns for `summaries/`, audio formats (`.flac`, `.ogg`, `.aac`, `.wma`), `.mypy_cache/`, `.pytest_cache/`, `.coverage`, `htmlcov/`. Also missing: `config/.api_keys.enc` (encrypted API key file, reversible with known username+hostname), `config/settings.json`, `config/prompt_templates.json`, and `.claude/settings.local.json` (local-only config convention).

4. **No `.gitattributes`:** Two 2MB PNG images tracked without binary diff settings or LFS.

## Goal

Remove stale root-level files, harden `.gitignore`, and add `.gitattributes` for proper binary file handling.

## Scope

### In Scope

- Remove `summaries/` from git tracking (`git rm --cached`) and add to `.gitignore` — contains real user data with sensitive business content
- Delete 12 root-level scripts: `test_audio.py`, `test_buttons.py`, `test_config.py`, `test_costs.py`, `test_debug.py`, `test_markdown.py`, `test_markdown_viewer.py`, `test_structured_summary.py`, `test_zero_cost.py`, `diagnose_audio.py`, `update_summary.py`, `regenerate_markdown.py`
- Update `.gitignore` to add: `summaries/`, `.flac`, `.ogg`, `.aac`, `.wma`, `.mypy_cache/`, `.pytest_cache/`, `.coverage`, `htmlcov/`, `config/.api_keys.enc`, `config/settings.json`, `config/prompt_templates.json`, `.claude/settings.local.json`
- Remove `.claude/settings.local.json` from git tracking (`git rm --cached`)
- Add `.gitattributes` with binary tracking for PNG files under `src/assets/`
- Optimize the two 2MB PNG images (app_icon.png and logo.png) — a 1024x1024 icon should be <200KB

### Out of Scope

- Migrating existing PNG files to Git LFS (requires repo history rewrite)
- Restructuring the tests/ directory
- Adding CI/CD configuration
- Rewriting git history to purge the summaries from past commits

## Acceptance Criteria

- [ ] `summaries/` is untracked and listed in `.gitignore`
- [ ] No `test_*.py` or utility scripts exist in the project root
- [ ] `.gitignore` includes `summaries/`, audio formats, cache/coverage patterns, `config/.api_keys.enc`, `config/settings.json`, `config/prompt_templates.json`, `.claude/settings.local.json`
- [ ] `.claude/settings.local.json` is untracked
- [ ] `.gitattributes` exists with binary diff settings for image files
- [ ] PNG images optimized to <200KB each
- [ ] `git status` shows a clean working tree after committing changes
- [ ] No test suite regressions

## Tasks

| # | Task | Owner | Depends On | Status |
|---|------|-------|------------|--------|
| 1 | Remove summaries/ from tracking and add to .gitignore | developer | | TODO |
| 2 | Delete 12 root-level test/debug/utility scripts | developer | | TODO |
| 3 | Update .gitignore with all missing patterns | developer | 1 | TODO |
| 4 | Create .gitattributes for binary file handling | developer | | TODO |
| 5 | Optimize PNG images | developer | | TODO |
| 6 | Verify clean state and no regressions | tech-qa | 1-5 | TODO |

## Telemetry

| Metric           | Value |
|------------------|-------|
| Total Tasks      |       |
| Total Duration   |       |
| Total Tokens In  |       |
| Total Tokens Out |       |

## Notes

**HIGH PRIORITY:** The `summaries/` directory contains real business meeting transcripts with company names, people's names, and business discussions. This should be removed from tracking immediately.

The two PNG images (`src/assets/icons/app_icon.png` and `src/assets/images/logo.png`) are both 1024x1024 RGB PNGs at ~2MB each. A properly compressed 1024x1024 PNG should be well under 200KB. Consider using `optipng` or `pngquant` for optimization. Note that removing them from git history would require `git filter-branch` or BFG Repo Cleaner, which is out of scope.

Root-level scripts found: 4 are completely empty (1 line), others are manual/interactive debug scripts that use `input()` and aren't compatible with pytest.
