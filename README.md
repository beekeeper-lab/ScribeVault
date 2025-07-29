# ScribeVault

A modern GUI application for audio recording, transcription, and intelligent summarization.

## Features

- 🎙️ **Audio Recording** - Record from microphone with real-time feedback
- 🧠 **Speech-to-Text** - Powered by OpenAI Whisper
- 📝 **AI Summarization** - Generate summaries using OpenAI GPT
- 📚 **Vault Management** - Organize and search your recordings
- 📱 **Modern UI** - Clean, intuitive interface built with CustomTkinter

## Quick Start

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure API Key**:
   ```bash
   cp .env.example .env
   # Edit .env and add your OpenAI API key
   ```

3. **Run ScribeVault**:
   ```bash
   python main.py
   ```

## Project Structure

```
ScribeVault/
├── main.py              # Application entry point
├── src/
│   ├── gui/             # GUI components
│   ├── audio/           # Audio recording/processing
│   ├── transcription/   # Whisper integration
│   ├── ai/              # OpenAI integration
│   └── vault/           # File management
├── assets/              # Icons, themes
├── config/              # Configuration files
└── tests/               # Unit tests
```

## Requirements

- Python 3.8+
- OpenAI API key
- Audio input device (microphone)
- FFmpeg (for audio processing)

## License

MIT License
