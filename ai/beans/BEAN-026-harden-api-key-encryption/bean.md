# BEAN-026: Harden API Key Encryption

## Metadata

| Field     | Value        |
|-----------|--------------|
| ID        | BEAN-026     |
| Title     | Harden API Key Encryption |
| Type      | enhancement  |
| Priority  | P1           |
| Status    | Done         |
| Created   | 2026-02-10   |
| Started   |              |
| Completed |              |
| Duration  |              |

## Problem Statement

BEAN-004 introduced API key secure storage with a three-tier hierarchy (keyring, encrypted config, env variable). However, the XOR-based fallback when `cryptography` is not installed is trivially reversible — it derives a key from the username and hostname via SHA-256, both of which are publicly knowable. Additionally, even the Fernet path uses a deterministic key derived from the same predictable inputs with no random salt. Since `cryptography` and `keyring` are optional dependencies (not in `requirements.txt`), most installations silently fall back to the weak XOR obfuscation.

## Goal

API key storage is cryptographically sound by default for all installations, with no silent fallback to weak obfuscation.

## Scope

### In Scope

- Add `cryptography` and `keyring` to `requirements.txt` as required dependencies
- Add a random salt to Fernet key derivation, stored alongside the encrypted data
- Remove the XOR fallback entirely, or replace it with a prominent GUI warning dialog (not just a log message) that the key is stored insecurely
- Ensure backward compatibility: existing `.api_keys.enc` files encrypted with the old method are migrated on first load

### Out of Scope

- Changing the keyring backend or OS-level credential storage
- Encrypting other data at rest (recordings, transcriptions, summaries)
- Hardware security module (HSM) or TPM integration

## Acceptance Criteria

- [x] `cryptography` and `keyring` appear in `requirements.txt`
- [x] Fernet key derivation includes a random salt stored in or alongside `.api_keys.enc`
- [x] XOR fallback is removed or triggers a visible GUI warning on every app launch when active
- [x] Existing API keys encrypted with old method are automatically migrated to the new scheme
- [x] Unit tests cover: new encryption round-trip, migration from old format, missing-dep warning path
- [x] `pytest tests/` passes, `flake8 src/ tests/` is clean

## Tasks

| # | Task | Owner | Depends On | Status |
|---|------|-------|------------|--------|
| 1 | Add cryptography and keyring to requirements.txt | Developer | | DONE |
| 2 | Add salt-based Fernet key derivation | Developer | 1 | DONE |
| 3 | Remove or warn on XOR fallback | Developer | 2 | DONE |
| 4 | Implement migration for existing .api_keys.enc files | Developer | 2 | DONE |
| 5 | Write unit tests for new encryption and migration | Tech QA | 3, 4 | DONE |

## Telemetry

| Metric           | Value |
|------------------|-------|
| Total Tasks      |       |
| Total Duration   |       |
| Total Tokens In  |       |
| Total Tokens Out |       |

## Notes

Follows up on BEAN-004 (API Key Validation & Secure Storage). The current implementation in `src/config/settings.py` lines 380-427 contains the XOR fallback and predictable key derivation. Key files: `src/config/settings.py`, `tests/test_api_key_validation.py`.
