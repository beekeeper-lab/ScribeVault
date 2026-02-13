# BEAN-041: Fix Dependency Version Bounds for Security

## Metadata

| Field     | Value        |
|-----------|--------------|
| ID        | BEAN-041     |
| Title     | Fix Dependency Version Bounds for Security |
| Type      | bug-fix |
| Priority  | P1 |
| Status    | Unapproved   |
| Created   | 2026-02-13   |
| Started   |              |
| Completed |              |
| Duration  |              |

## Problem Statement

A security audit of `requirements.txt` found that the current version bounds allow installation of packages with known CVEs:

1. **Pillow `>=10.0.0,<12.0.0`** -- CVE-2026-25990 (out-of-bounds write on PSD images) affects all versions < 12.1.1. The upper bound also blocks installing the fix.
2. **cryptography `>=41.0.0,<48.0.0`** -- CVE-2026-26007 (elliptic curve subgroup validation bypass) affects versions < 46.0.5.
3. **torch `>=2.0.0,<3.0.0`** -- CVE-2025-32434 (CRITICAL RCE via `torch.load()` even with `weights_only=True`) affects all versions <= 2.5.1.
4. **openai `>=1.0.0,<2.0.0`** -- The installed version is 2.20.0, violating the upper bound. The venv is running a version the requirements file disallows.

Additionally, the `requirements.lock` file is stale -- last generated 2026-02-10 but the venv has been updated independently. Several packages are missing from the venv entirely (cryptography, keyring, markdown).

## Goal

All dependency version bounds in `requirements.txt` exclude packages with known CVEs. The lock file and venv are in sync with `requirements.txt`.

## Scope

### In Scope

- Update `requirements.txt` version bounds:
  - `Pillow>=12.1.1,<13.0.0` (excludes CVE-2026-25990)
  - `cryptography>=46.0.5,<48.0.0` (excludes CVE-2026-26007)
  - `torch>=2.6.0,<3.0.0` (excludes CVE-2025-32434)
  - `openai>=1.0.0,<3.0.0` (or appropriate bound that matches actual usage)
- Sync the venv: `pip install -r requirements.txt`
- Regenerate `requirements.lock`: `pip freeze > requirements.lock`
- Verify the application still runs with updated dependencies

### Out of Scope

- Removing unused dependencies (covered by BEAN-037)
- Upgrading to major new API versions (e.g., if openai v2 has breaking changes, that's a separate concern)
- Replacing the abandoned `pyqtdarktheme` package (separate concern)
- Adding `pip-audit` to CI/CD

## Acceptance Criteria

- [ ] `Pillow` minimum bound is `>=12.1.1` (CVE-2026-25990 excluded)
- [ ] `cryptography` minimum bound is `>=46.0.5` (CVE-2026-26007 excluded)
- [ ] `torch` minimum bound is `>=2.6.0` (CVE-2025-32434 excluded)
- [ ] `openai` upper bound accommodates the actually-used version
- [ ] `pip install -r requirements.txt` succeeds in a clean venv
- [ ] `requirements.lock` is regenerated and matches the venv
- [ ] All existing tests pass
- [ ] Application launches successfully

## Tasks

| # | Task | Owner | Depends On | Status |
|---|------|-------|------------|--------|
| 1 | Update Pillow version bounds in requirements.txt | developer | | TODO |
| 2 | Update cryptography version bounds | developer | | TODO |
| 3 | Update torch version bounds | developer | | TODO |
| 4 | Update openai version bounds | developer | | TODO |
| 5 | Sync venv and regenerate requirements.lock | developer | 1-4 | TODO |
| 6 | Verify install, tests, and app launch | tech-qa | 5 | TODO |

## Telemetry

| Metric           | Value |
|------------------|-------|
| Total Tasks      |       |
| Total Duration   |       |
| Total Tokens In  |       |
| Total Tokens Out |       |

## Notes

CVE details:
- **CVE-2026-25990 (Pillow)**: Out-of-bounds write when loading specially crafted PSD images. Could lead to arbitrary code execution.
- **CVE-2026-26007 (cryptography)**: Missing subgroup validation for binary elliptic curves. Compromises ECDSA/ECDH on those curves.
- **CVE-2025-32434 (torch)**: CRITICAL (CVSS 9.3). Remote code execution via `torch.load()` even with `weights_only=True`. Affects openai-whisper's model loading.

The openai version drift (2.20.0 installed vs `<2.0.0` pinned) suggests the venv was updated manually without updating requirements.txt. The v2 API has breaking changes -- verify that the codebase works with v2 before widening the bound, or pin back to `<2.0.0` and downgrade the venv.

This bean should be coordinated with BEAN-037 (Unused Dependencies Cleanup) since both modify `requirements.txt`.
