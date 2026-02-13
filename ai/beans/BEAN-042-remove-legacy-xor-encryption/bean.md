# BEAN-042: Remove Legacy XOR Encryption

## Metadata

| Field     | Value        |
|-----------|--------------|
| ID        | BEAN-042     |
| Title     | Remove Legacy XOR Encryption |
| Type      | bug-fix |
| Priority  | P2 |
| Status    | Unapproved   |
| Created   | 2026-02-13   |
| Started   |              |
| Completed |              |
| Duration  |              |

## Problem Statement

The `SettingsManager` in `src/config/settings.py` (lines 499-504) still contains a legacy XOR decryption code path in `_read_legacy_encrypted_key()`. XOR encryption is trivially breakable -- an attacker who gains read access to a v2 XOR-encrypted config file can recover the API key by XORing with the known key derivation (username-based).

BEAN-026 introduced Fernet (AES-128-CBC with HMAC) encryption with PBKDF2 key derivation, and the code auto-migrates XOR-encrypted keys to Fernet on first read. However, the XOR decryption code path remains, meaning:

1. The application will still accept and decrypt XOR-encrypted files if one somehow exists
2. The code is a security liability in a public repository -- it demonstrates a weak encryption approach
3. It's dead code for any user who has launched the app since BEAN-026 was deployed (auto-migration already happened)

## Goal

The legacy XOR encryption code path is completely removed. Only Fernet (v3) encryption is supported.

## Scope

### In Scope

- Remove the XOR decryption branch from `_read_legacy_encrypted_key()` in `src/config/settings.py`
- Remove the legacy `_derive_key_v1()` method if it exists solely for XOR support
- Update `_read_legacy_encrypted_key()` to only handle Fernet v2 migration (or remove it entirely if v2 is also considered legacy enough)
- Update any related tests
- Add a log warning if an unrecognized encryption version is encountered (rather than silently failing)

### Out of Scope

- Changing the Fernet v3 encryption implementation
- Modifying the keyring integration
- Adding a migration prompt or UI for users with old config files

## Acceptance Criteria

- [ ] No XOR encryption/decryption code exists in `settings.py`
- [ ] Fernet v3 encrypted config files still decrypt correctly
- [ ] Fernet v2 encrypted config files still auto-migrate to v3 (if v2 support is kept)
- [ ] Unrecognized encryption versions produce a clear error message
- [ ] All existing tests pass
- [ ] No `xor` references remain in the security-sensitive code paths

## Tasks

| # | Task | Owner | Depends On | Status |
|---|------|-------|------------|--------|
| 1 | Identify all XOR-related code paths in settings.py | developer | | TODO |
| 2 | Remove XOR decryption code and related key derivation | developer | 1 | TODO |
| 3 | Add error handling for unrecognized encryption versions | developer | 2 | TODO |
| 4 | Update tests to verify XOR path is gone | tech-qa | 2 | TODO |
| 5 | Verify Fernet v3 still works end-to-end | tech-qa | 2 | TODO |

## Telemetry

| Metric           | Value |
|------------------|-------|
| Total Tasks      |       |
| Total Duration   |       |
| Total Tokens In  |       |
| Total Tokens Out |       |

## Notes

The XOR encryption was the original approach before BEAN-004 introduced keyring support and BEAN-026 added Fernet encryption. The auto-migration to Fernet happens transparently on first read, so any user who has run the app post-BEAN-026 already has a Fernet-encrypted config.

The relevant code in `settings.py` around line 499-504:
```python
elif method == "xor":
    xor_bytes = base64.urlsafe_b64decode(encrypted)
    return bytes(
        b ^ legacy_key[i % len(legacy_key)]
        for i, b in enumerate(xor_bytes)
    ).decode()
```

Consider whether v2 Fernet (pre-PBKDF2 salt) should also be removed for simplicity, or kept for one more release cycle.
