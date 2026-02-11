# BEAN-020: Auto-Categorize Recordings

## Metadata

| Field     | Value        |
|-----------|--------------|
| **ID**        | BEAN-020     |
| **Title**     | Auto-Categorize Recordings |
| **Type**      | enhancement |
| **Priority**  | P2 |
| **Status**    | In Progress  |
| **Created**   | 2026-02-10   |
| **Started**   | 2026-02-11 00:38            |
| **Completed** | —            |
| **Duration**  | —            |

## Problem Statement

All recordings are hardcoded to category `'other'` in three places in `qt_main_window.py` (lines 142, 289, 887). The summarizer service already has a `categorize_content()` method (`src/ai/summarizer.py:181`) that uses OpenAI to infer the category from transcription text, but it is never called during the recording pipeline — it's dead code. As a result, every recording appears as "Other" in the vault, making the category filter dropdown useless. Additionally, the default "other" label is unclear — "uncategorized" better conveys that no classification has been performed.

## Goal

When the AI summarizer is available and a transcription exists, recordings are automatically categorized using the existing `categorize_content()` method. When the summarizer is unavailable, recordings default to "uncategorized". The vault filter dropdown and database schema are updated to support the expanded category set.

## Scope

### In Scope

- Wire `categorize_content()` into the recording pipeline in `qt_main_window.py` (all 3 locations where `'category': 'other'` is hardcoded)
- Rename the default category from `'other'` to `'uncategorized'`
- Expand `VALID_CATEGORIES` in `src/vault/manager.py` to include `call` and `presentation` (returned by the AI categorizer)
- Update the database CHECK constraint to accept the new categories (migration for existing data: `'other'` → `'uncategorized'`)
- Update the vault dialog category filter dropdown (`qt_vault_dialog.py`) to include `call`, `presentation`, and `uncategorized`
- Update the edit recording dialog's category combo box to match
- Align `categorize_content()` prompt to only return categories that are in the valid set

### Out of Scope

- Changing the AI categorization logic or model
- Adding user-defined custom categories
- Re-categorizing existing recordings retroactively (beyond the `other` → `uncategorized` rename)
- Changing the summarization pipeline itself

## Acceptance Criteria

- [ ] When the AI summarizer is available, new recordings are automatically categorized based on transcription content
- [ ] When the AI summarizer is unavailable, recordings default to "uncategorized" (not "other")
- [ ] The VALID_CATEGORIES set includes: meeting, interview, lecture, note, call, presentation, uncategorized
- [ ] The database CHECK constraint accepts all valid categories
- [ ] Existing recordings with category "other" are migrated to "uncategorized"
- [ ] The vault filter dropdown shows all valid categories
- [ ] The edit recording dialog's category combo box shows all valid categories
- [ ] If `categorize_content()` returns an unrecognized value, it falls back to "uncategorized"
- [ ] Existing tests still pass

## Tasks

| # | Task | Owner | Depends On | Status |
|---|------|-------|------------|--------|
| 1 | Expand VALID_CATEGORIES and update DB schema/migration in vault manager | Developer | — | TODO |
| 2 | Rename default category from 'other' to 'uncategorized' across codebase | Developer | 1 | TODO |
| 3 | Wire categorize_content() into recording pipeline in qt_main_window.py | Developer | 1 | TODO |
| 4 | Update vault dialog filter dropdown and edit dialog category combo | Developer | 1 | TODO |
| 5 | Align categorize_content() prompt to match expanded valid category set | Developer | 1 | TODO |
| 6 | Test auto-categorization with and without summarizer available | Tech QA | 3, 5 | TODO |

## Telemetry

| Metric           | Value |
|------------------|-------|
| **Total Tasks**      | 6     |
| **Total Duration**   | —     |
| **Total Tokens In**  | —     |
| **Total Tokens Out** | —     |

## Notes

The `categorize_content()` method at `src/ai/summarizer.py:181` already exists and works — it just needs to be called. The current prompt asks the AI to return one of: meeting, lecture, interview, note, call, presentation, other. Task 5 should update this prompt to return "uncategorized" instead of "other" and ensure it matches the expanded valid set. The 3 hardcoded `'category': 'other'` locations in `qt_main_window.py` are at lines 142, 289, and 887. No dependencies on other beans.
