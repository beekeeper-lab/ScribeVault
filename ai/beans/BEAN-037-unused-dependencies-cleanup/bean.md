# BEAN-037: Unused Dependencies Cleanup

## Metadata

| Field     | Value        |
|-----------|--------------|
| ID        | BEAN-037     |
| Title     | Unused Dependencies Cleanup |
| Type      | enhancement |
| Priority  | P2 |
| Status    | Unapproved   |
| Created   | 2026-02-13   |
| Started   |              |
| Completed |              |
| Duration  |              |

## Problem Statement

Both `requirements.txt` and `requirements-test.txt` contain dependencies that are not used anywhere in the codebase:

**requirements.txt:**
- `Pillow>=10.0.0,<12.0.0` — no `PIL` or `Pillow` import found in any source file
- `python-dotenv>=1.0.0,<2.0.0` — `load_dotenv()` is called but may be unnecessary if API keys are managed through keyring/encrypted config (per BEAN-004/BEAN-026)

**requirements-test.txt:**
- `pytest-asyncio>=0.21.0` — no async tests exist
- `factory-boy>=3.2.0` — no factories used in any test
- `freezegun>=1.2.0` — no time-freezing used in any test
- `responses>=0.20.0` — no HTTP response mocking with `responses` library
- `pytest-benchmark>=4.0.0` — no benchmark tests exist
- `pytest-httpserver>=1.0.0` — no HTTP server tests exist

Additionally, `requirements-test.txt` does not use the same pinning strategy as `requirements.txt` (no upper version bounds).

## Goal

Both requirements files contain only actually-used dependencies, with consistent pinning strategy.

## Scope

### In Scope

- Remove `Pillow` from `requirements.txt` (verify no usage exists)
- Evaluate `python-dotenv` — remove if `load_dotenv()` calls are removed in favor of keyring-only key management, or keep if env var fallback is intentional
- Remove 6 unused test dependencies from `requirements-test.txt`
- Apply consistent version pinning (>=min,<max) to remaining test dependencies
- Verify the application and test suite still work after removals

### Out of Scope

- Adding new dependencies
- Upgrading existing dependency versions
- Creating a `pyproject.toml` (separate concern)
- Removing `load_dotenv()` calls from source code (that's part of BEAN-033 scope)

## Acceptance Criteria

- [ ] `Pillow` is removed from `requirements.txt`
- [ ] Unused test dependencies (pytest-asyncio, factory-boy, freezegun, responses, pytest-benchmark, pytest-httpserver) are removed
- [ ] Remaining test dependencies use `>=min,<max` pinning strategy
- [ ] `pip install -r requirements.txt` succeeds
- [ ] `pip install -r requirements-test.txt` succeeds
- [ ] All tests still pass after dependency removal

## Tasks

| # | Task | Owner | Depends On | Status |
|---|------|-------|------------|--------|
| 1 | Verify Pillow is unused and remove from requirements.txt | developer | | TODO |
| 2 | Evaluate python-dotenv necessity and decide keep/remove | developer | | TODO |
| 3 | Remove 6 unused test dependencies | developer | | TODO |
| 4 | Apply consistent pinning to requirements-test.txt | developer | 3 | TODO |
| 5 | Verify install and test suite | tech-qa | 1-4 | TODO |

## Telemetry

| Metric           | Value |
|------------------|-------|
| Total Tasks      |       |
| Total Duration   |       |
| Total Tokens In  |       |
| Total Tokens Out |       |

## Notes

The `python-dotenv` decision depends on whether the project wants to support `.env` files as a key configuration method. With keyring (BEAN-004) and encrypted config (BEAN-026) in place, `.env` may be a legacy pattern. However, it's also useful for development environments. Recommend keeping it but documenting its purpose.
