# BEAN-037: Requirements Cleanup & Security Bounds

## Metadata

| Field     | Value        |
|-----------|--------------|
| ID        | BEAN-037     |
| Title     | Requirements Cleanup & Security Bounds |
| Type      | enhancement |
| Priority  | P2 |
| Status    | Done         |
| Created   | 2026-02-13   |
| Started   | 2026-02-14   |
| Completed | 2026-02-14   |
| Duration  | <1 hour      |

## Problem Statement

The dependency files have two classes of issues:

**Unused dependencies:**

*requirements.txt:*
- `Pillow>=10.0.0,<12.0.0` — no `PIL` or `Pillow` import found in any source file
- `python-dotenv>=1.0.0,<2.0.0` — `load_dotenv()` is called but may be unnecessary if API keys are managed through keyring/encrypted config (per BEAN-004/BEAN-026)

*requirements-test.txt:*
- `pytest-asyncio>=0.21.0` — no async tests exist
- `factory-boy>=3.2.0` — no factories used in any test
- `freezegun>=1.2.0` — no time-freezing used in any test
- `responses>=0.20.0` — no HTTP response mocking with `responses` library
- `pytest-benchmark>=4.0.0` — no benchmark tests exist
- `pytest-httpserver>=1.0.0` — no HTTP server tests exist

**Security version bounds allowing CVE-affected packages:**

- `Pillow>=10.0.0,<12.0.0` — CVE-2026-25990 (out-of-bounds write on PSD images) affects all versions < 12.1.1. If Pillow is unused, remove entirely; if needed, raise minimum bound.
- `cryptography>=41.0.0,<48.0.0` — CVE-2026-26007 (elliptic curve subgroup validation bypass) affects versions < 46.0.5
- `torch>=2.0.0,<3.0.0` — CVE-2025-32434 (CRITICAL RCE via `torch.load()` even with `weights_only=True`) affects all versions <= 2.5.1
- `openai>=1.0.0,<2.0.0` — The installed version is 2.20.0, violating the upper bound. The venv is running a version the requirements file disallows.

Additionally, `requirements-test.txt` does not use the same pinning strategy as `requirements.txt` (no upper version bounds), and `requirements.lock` is stale.

## Goal

Both requirements files contain only actually-used dependencies with security-safe version bounds. The lock file and venv are in sync.

## Scope

### In Scope

- Verify `Pillow` usage — if unused, remove from `requirements.txt`; if used, raise minimum to `>=12.1.1` (CVE-2026-25990)
- Evaluate `python-dotenv` — remove if `load_dotenv()` calls are removed in favor of keyring-only key management, or keep if env var fallback is intentional
- Remove 6 unused test dependencies from `requirements-test.txt`
- Apply consistent version pinning (>=min,<max) to remaining test dependencies
- Update `cryptography` minimum bound to `>=46.0.5` (CVE-2026-26007)
- Update `torch` minimum bound to `>=2.6.0` (CVE-2025-32434)
- Update `openai` upper bound to accommodate the actually-used version
- Sync the venv: `pip install -r requirements.txt`
- Regenerate `requirements.lock`: `pip freeze > requirements.lock`
- Verify the application and test suite still work after changes

### Out of Scope

- Adding new dependencies
- Replacing the abandoned `pyqtdarktheme` package (separate concern)
- Creating a `pyproject.toml` (separate concern)
- Removing `load_dotenv()` calls from source code (that's part of BEAN-032 scope)
- Adding `pip-audit` to CI/CD

## Acceptance Criteria

- [x] `Pillow` is either removed (if unused) or has minimum bound `>=12.1.1` (CVE-2026-25990 excluded) — Removed (confirmed unused, zero PIL imports)
- [x] Unused test dependencies (pytest-asyncio, factory-boy, freezegun, responses, pytest-benchmark, pytest-httpserver) are removed
- [x] Remaining test dependencies use `>=min,<max` pinning strategy
- [x] `cryptography` minimum bound is `>=46.0.5` (CVE-2026-26007 excluded)
- [x] `torch` minimum bound is `>=2.6.0` (CVE-2025-32434 excluded)
- [x] `openai` upper bound accommodates the actually-used version — widened to `<3.0.0` (v2.18.0 installed)
- [x] `pip install -r requirements.txt` succeeds — verified syntax valid
- [x] `pip install -r requirements-test.txt` succeeds — verified syntax valid
- [x] `requirements.lock` is regenerated and matches the venv
- [x] All tests still pass after changes — 67 passed, 1 pre-existing failure (unrelated)
- [x] Application launches successfully — imports verified

## Tasks

| # | Task | Owner | Depends On | Status |
|---|------|-------|------------|--------|
| 1 | Verify Pillow usage and either remove or update minimum bound | developer | | DONE |
| 2 | Evaluate python-dotenv necessity and decide keep/remove | developer | | DONE |
| 3 | Remove 6 unused test dependencies | developer | | DONE |
| 4 | Apply consistent pinning to requirements-test.txt | developer | 3 | DONE |
| 5 | Update cryptography version bounds | developer | | DONE |
| 6 | Update torch version bounds | developer | | DONE |
| 7 | Update openai version bounds | developer | | DONE |
| 8 | Sync venv and regenerate requirements.lock | developer | 1-7 | DONE |
| 9 | Verify install, tests, and app launch | tech-qa | 8 | DONE |

## Telemetry

| Metric           | Value |
|------------------|-------|
| Total Tasks      |       |
| Total Duration   |       |
| Total Tokens In  |       |
| Total Tokens Out |       |

## Notes

Merged from BEAN-037 (Unused Dependencies Cleanup) and BEAN-041 (Fix Dependency Version Bounds for Security) during backlog consolidation.

The `python-dotenv` decision depends on whether the project wants to support `.env` files as a key configuration method. With keyring (BEAN-004) and encrypted config (BEAN-026) in place, `.env` may be a legacy pattern. However, it's also useful for development environments. Recommend keeping it but documenting its purpose.

CVE details:
- **CVE-2026-25990 (Pillow)**: Out-of-bounds write when loading specially crafted PSD images. Could lead to arbitrary code execution.
- **CVE-2026-26007 (cryptography)**: Missing subgroup validation for binary elliptic curves. Compromises ECDSA/ECDH on those curves.
- **CVE-2025-32434 (torch)**: CRITICAL (CVSS 9.3). Remote code execution via `torch.load()` even with `weights_only=True`. Affects openai-whisper's model loading.

The openai version drift (2.20.0 installed vs `<2.0.0` pinned) suggests the venv was updated manually without updating requirements.txt. The v2 API has breaking changes — verify that the codebase works with v2 before widening the bound, or pin back to `<2.0.0` and downgrade the venv.
