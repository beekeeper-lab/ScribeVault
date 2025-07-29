# Security Guidelines for ScribeVault

## API Key Management

⚠️ **IMPORTANT**: Never commit your `.env` file to git!

### Setup Instructions:
1. Copy `.env.example` to `.env`
2. Add your OpenAI API key to `.env`
3. The `.env` file is git-ignored for security

### Environment Variables:
- `OPENAI_API_KEY`: Your OpenAI API key (keep secret!)

## Audio File Security

- Recordings are stored locally in the `recordings/` directory
- Files are not uploaded anywhere except to OpenAI for transcription
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
