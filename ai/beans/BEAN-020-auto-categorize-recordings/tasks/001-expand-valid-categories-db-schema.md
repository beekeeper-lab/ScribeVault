# Task 001: Expand VALID_CATEGORIES and update DB schema/migration

## Owner: Developer
## Depends On: —
## Status: TODO

### Description
- Add `call`, `presentation`, `uncategorized` to VALID_CATEGORIES in `src/vault/manager.py`
- Remove `other` from VALID_CATEGORIES
- Update `_create_table()` CHECK constraint to match new categories
- Update `_normalize_category()` to default to `uncategorized` instead of `other`
- Add DB migration: rename existing `other` rows to `uncategorized`
- Update `_migrate_from_archived()` to use new CHECK constraint

### Acceptance Criteria
- VALID_CATEGORIES = {meeting, interview, lecture, note, call, presentation, uncategorized}
- New databases use updated CHECK constraint
- Existing `other` values migrate to `uncategorized`
