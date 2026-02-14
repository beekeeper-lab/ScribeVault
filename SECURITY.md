# Security Guidelines for ScribeVault

## API Key Management

ScribeVault stores API keys securely using platform keyring integration with Fernet encryption (via the `cryptography` library). Keys are never stored in plain text.

### How It Works

1. On first use, the app prompts for your OpenAI API key
2. The key is encrypted with Fernet (PBKDF2-derived key with random salt) and stored via `keyring`
3. If `keyring` is unavailable, the encrypted key is written to `.api_keys.enc` with restricted file permissions

### Best Practices

- Never commit API keys or `.api_keys.enc` to version control
- Rotate your API key periodically via the OpenAI dashboard
- Use the Settings dialog to update or remove stored keys

## Path Traversal Protection

All database-sourced file paths are validated with `validate_path_within()` before use. This prevents path traversal attacks (e.g., `../../etc/passwd`) in audio playback, export, and markdown viewing operations.

## HTML Escaping

Summary viewer content is HTML-escaped before rendering to prevent cross-site scripting (XSS) via crafted transcription or summary text.

## File & Directory Permissions

- Vault directories and exported files are created with restricted permissions (owner-only access)
- Audio recordings, transcripts, and summaries are stored locally and never uploaded except to OpenAI for transcription (over HTTPS)

## Dependency Pinning

All dependencies in `requirements.txt` are pinned to specific versions to prevent supply-chain attacks from unexpected upgrades.

## Audio File Security

- Recordings are stored locally in the vault directory
- Files are only sent to OpenAI for transcription (HTTPS)
- Consider encrypting sensitive recordings at rest

## Network Security

- Only connects to OpenAI API endpoints
- All API calls use HTTPS
- No telemetry or analytics data is sent

## Data Privacy

- Transcripts and summaries are stored locally in SQLite
- No user data is shared with third parties
- Audio files remain on your local machine

## Reporting Security Issues

If you find a security vulnerability, please report it privately to the maintainers.
