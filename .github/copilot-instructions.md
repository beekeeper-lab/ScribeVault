<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit https://code.visualstudio.com/docs/copilot/copilot-customization#_use-a-githubcopilotinstructionsmd-file -->

# ScribeVault Copilot Instructions

This is a Python GUI application for audio recording, transcription, and AI summarization.

## Key Technologies
- **GUI Framework**: CustomTkinter for modern UI
- **Audio**: PyAudio for recording, FFmpeg for processing
- **AI**: OpenAI Whisper for transcription, GPT for summarization
- **Storage**: SQLite for metadata, filesystem for audio files

## Architecture Principles
- **Modular Design**: Separate concerns (GUI, audio, AI, storage)
- **Async Operations**: Non-blocking UI for long-running tasks
- **Error Handling**: Graceful degradation and user feedback
- **Configuration**: Environment-based settings

## Code Style
- Follow PEP 8 standards
- Use type hints
- Document functions with docstrings
- Handle exceptions appropriately
- Use pathlib for file operations

## GUI Guidelines
- Responsive design that works on different screen sizes
- Consistent styling with CustomTkinter themes
- Proper loading states and progress indicators
- Keyboard shortcuts for common actions
- Accessibility considerations
