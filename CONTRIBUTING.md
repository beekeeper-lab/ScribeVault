# Contributing to ScribeVault

## Development Setup

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd ScribeVault
   ```

2. **Set up environment**:
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```

3. **Configure API key**:
   Launch the application and enter your OpenAI API key when prompted, or use the Settings dialog. Keys are stored securely via platform keyring with Fernet encryption.

## Code Style

- Follow PEP 8 standards
- Use type hints for function parameters and return values
- Write descriptive docstrings for all public methods
- Add comments for complex logic

## Testing

- Test on multiple platforms (Linux, macOS, Windows)
- Verify audio recording functionality
- Test with various audio file formats
- Validate transcription accuracy

## Pull Request Process

1. Create a feature branch from main
2. Make your changes with proper tests
3. Update documentation if needed
4. Submit a pull request with clear description

## Security

- Never commit API keys or secrets
- Validate all user inputs
- Use secure coding practices
- Report security issues privately

## Architecture Guidelines

- Maintain separation of concerns
- Use dependency injection where appropriate
- Handle errors gracefully
- Keep UI responsive with threading
