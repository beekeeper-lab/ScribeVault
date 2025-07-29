# ScribeVault

A modern GUI application for audio recording, transcription, and intelligent summarization with configurable cost-optimized processing.

## 🌟 Key Features

- 🎙️ **Audio Recording** - Record from microphone with real-time feedback
- 🧠 **Dual Transcription** - Choose between OpenAI API or local Whisper models
- � **Cost Optimization** - Save 98.3% on transcription costs with local processing
- �📝 **AI Summarization** - Generate summaries using OpenAI GPT
- 📚 **Vault Management** - Organize and search your recordings
- ⚙️ **Smart Configuration** - Comprehensive settings with cost comparison
- 📱 **Modern UI** - Clean, intuitive interface built with CustomTkinter

## 💡 Cost Comparison

| Service | Cost/Hour | Annual (1hr/day) | Best For |
|---------|-----------|------------------|----------|
| **Local Whisper** | $0.01 | $3.65 | Privacy, bulk processing |
| **OpenAI API** | $0.36 | $131.40 | Quick setup, reliability |

*Save $127.75/year with local processing!*

## 🚀 Quick Start

### Option 1: OpenAI API (Easy Setup)
1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure API Key**:
   ```bash
   export OPENAI_API_KEY="your-key-here"
   ```

3. **Run ScribeVault**:
   ```bash
   python main.py
   ```

### Option 2: Local Whisper (Cost-Optimized)
1. **Install with Local Support**:
   ```bash
   pip install -r requirements.txt
   pip install whisper torch  # For local processing
   ```

2. **Configure in Settings**:
   - Launch ScribeVault: `python main.py`
   - Click ⚙️ Settings
   - Change "Transcription Service" to "local"
   - Select model size and device
   - Save settings

## 📋 Requirements

### Minimum (API Mode)
- Python 3.8+
- OpenAI API key
- Internet connection

### Recommended (Local Mode)
- Python 3.8+
- 4GB+ RAM
- Modern CPU (or NVIDIA GPU for acceleration)

## 📁 Project Structure

```
ScribeVault/
├── main.py                    # Application entry point
├── src/
│   ├── gui/                   # GUI components
│   │   ├── main_window.py     # Main application window
│   │   └── settings_window.py # Configuration interface
│   ├── audio/                 # Audio recording/processing
│   ├── transcription/         # Whisper integration (API + local)
│   ├── ai/                    # OpenAI integration
│   ├── config/                # Configuration management
│   │   └── settings.py        # Settings and cost estimation
│   └── vault/                 # Recording storage management
├── config/                    # User configuration files
├── docs/                      # Documentation
│   └── CONFIGURATION.md       # Detailed setup guide
└── tests/                     # Unit tests
```

## ⚙️ Configuration

ScribeVault includes a comprehensive settings system:

- **Service Selection**: Choose between OpenAI API and local Whisper
- **Cost Estimation**: Real-time cost comparison and savings calculation
- **Model Configuration**: Select optimal Whisper model size
- **Hardware Detection**: Automatic CPU/GPU detection for local processing
- **Theme Management**: Dark/light/system theme options

See [Configuration Guide](docs/CONFIGURATION.md) for detailed setup instructions.

## 🧪 Testing

Test your configuration:
```bash
python test_config.py
```

This validates:
- Settings management
- Cost calculations
- Service availability
- Hardware detection

## 📊 Performance Metrics

### Local Whisper Models

| Model | Size | VRAM | Speed | Accuracy | Best Use |
|-------|------|------|-------|----------|----------|
| tiny | 39MB | ~1GB | Fastest | Good | Real-time, drafts |
| base | 74MB | ~1GB | Fast | Better | General use |
| small | 244MB | ~2GB | Medium | Very Good | Most applications |
| medium | 769MB | ~5GB | Slower | Excellent | Professional |
| large | 1550MB | ~10GB | Slowest | Best | Maximum accuracy |

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.
- Audio input device (microphone)
- FFmpeg (for audio processing)

## License

MIT License
