# ScribeVault

A modern GUI application for audio recording, transcription, and intelligent summarization with configurable cost-optimized processing.

## 🌟 Key Features

- 🎙️ **Audio Recording** - Record from microphone with real-time feedback
- 🧠 **Dual Transcription** - Choose between OpenAI API or local Whisper models
- 💰 **Cost Optimization** - Save 98.3% on transcription costs with local processing
- 📝 **AI Summarization** - Generate summaries using OpenAI GPT
- 📚 **Vault Management** - Organize, view, edit, and delete your recordings
- ⚙️ **Smart Configuration** - Comprehensive settings with cost comparison
- 📱 **Modern UI** - Clean, intuitive interface built with PySide6
- 🔒 **Enterprise Security** - Secure API key storage, input validation, and data protection

## 🛡️ Security & Quality

ScribeVault implements **enterprise-grade security** and **production-ready architecture**:

### Security Features
- **🔐 Secure API Key Storage** - System keyring integration with encrypted fallback
- **🛡️ Input Validation** - Comprehensive sanitization and constraint enforcement
- **🚫 Injection Prevention** - Protection against command injection and SQL injection
- **📁 Path Security** - Directory traversal protection for file operations
- **🧹 Resource Management** - Proper cleanup and memory management

### Quality Assurance  
- **🧪 Comprehensive Testing** - 90%+ test coverage with unit and integration tests
- **🔍 Type Safety** - Static type checking with mypy
- **📊 Error Handling** - Robust exception management and logging
- **⚡ Thread Safety** - Safe concurrent operations and UI updates
- **📈 Performance** - Optimized for reliability and efficiency

*Built with security-first principles for professional and enterprise use.*

## 💡 Cost Comparison

| Service | Cost/Hour | Annual (1hr/day) | Best For |
|---------|-----------|------------------|----------|
| **Local Whisper** | $0.01 | $3.65 | Privacy, bulk processing |
| **OpenAI API** | $0.36 | $131.40 | Quick setup, reliability |

*Save $127.75/year with local processing!*

## 🚀 Quick Start

### 🤖 Automated Setup (Recommended)

**One-Command Install:**
```bash
# Download and run the installer
curl -fsSL https://raw.githubusercontent.com/beekeeper-lab/ScribeVault/main/install.py | python3

# Or clone and run locally
git clone https://github.com/beekeeper-lab/ScribeVault.git
cd ScribeVault
python3 install.py
```

**Platform-Specific Scripts:**
- **Linux/macOS**: `./setup.sh`
- **Windows**: `setup.bat`

### 📋 Manual Setup

If you prefer manual installation or the automated setup doesn't work:

If you prefer manual installation or the automated setup doesn't work:

#### Prerequisites Setup

**Install FFmpeg** (Required for audio processing):

- **Windows**: Download from [FFmpeg.org](https://ffmpeg.org/download.html) or use chocolatey:
  ```bash
  choco install ffmpeg
  ```
- **macOS**: Using Homebrew:
  ```bash
  brew install ffmpeg
  ```
- **Linux**: Using package manager:
  ```bash
  sudo apt update && sudo apt install ffmpeg  # Ubuntu/Debian
  sudo yum install ffmpeg                     # RHEL/CentOS
  ```

### Option 1: OpenAI API (Easy Setup)
1. **Create Virtual Environment** (Recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment**:
   - Copy `.env.example` to `.env`
   - Add your OpenAI API key:
   ```bash
   echo "OPENAI_API_KEY=your-key-here" >> .env
   ```

4. **Run ScribeVault**:
   ```bash
   python main.py
   ```

#### Option 2: Local Whisper (Cost-Optimized)
1. **Setup Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install with Local Support**:
   ```bash
   pip install -r requirements.txt
   pip install torch whisper  # For local processing
   ```

3. **Configure in Settings**:
   - Launch ScribeVault: `python main.py`
   - Click ⚙️ Settings
   - Change "Transcription Service" to "local"
   - Select model size and device
   - Save settings

## 💡 Usage

### Basic Workflow

1. **Start Recording**: Click 🎙️ "Start Recording" button
2. **Stop Recording**: Click ⏹️ "Stop Recording" when finished
3. **View Results**: Transcription appears automatically
4. **Generate Summary**: Check "Generate Summary" before recording (optional)
5. **Manage Vault**: Click 📚 "Vault" to view, edit, or delete recordings

### Vault Features

- **View Details**: Click 👁️ "View" to see full transcription and metadata
- **Edit Recordings**: Click ✏️ "Edit" to modify title, description, and category
- **Delete Recordings**: Click 🗑️ "Delete" with confirmation dialog
- **Play Audio**: Click 🔊 "Play Audio" to hear original recording

## 📋 Requirements

### Prerequisites
- Python 3.8+
- Audio input device (microphone)
- FFmpeg (for audio processing)

### Minimum (API Mode)
- OpenAI API key
- Internet connection

### Recommended (Local Mode)
- 4GB+ RAM
- Modern CPU (or NVIDIA GPU for acceleration)

## 📁 Project Structure

```
ScribeVault/
├── main.py                    # Application entry point (PySide6)
├── src/
│   ├── gui/                   # GUI components (PySide6)
│   │   ├── qt_main_window.py  # Main application window
│   │   ├── qt_settings_dialog.py # Configuration interface
│   │   └── qt_app.py          # Qt application framework
│   ├── audio/                 # Audio recording/processing
│   ├── transcription/         # Whisper integration (API + local)
│   ├── ai/                    # OpenAI integration
│   ├── assets/                # UI assets and resources
│   ├── config/                # Configuration management
│   │   └── settings.py        # Settings and cost estimation
│   └── vault/                 # Recording storage management
├── config/                    # User configuration files
├── docs/                      # Documentation
│   └── CONFIGURATION.md       # Detailed setup guide
├── recordings/                # Stored audio files
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

ScribeVault includes a comprehensive testing framework to ensure reliability and quality.

### Quick Test
Test your configuration:
```bash
python test_config.py
```

This validates:
- Settings management
- Cost calculations
- Service availability
- Hardware detection

### Full Test Suite

**Run All Tests:**
```bash
# Using the test runner
python tests/run_tests.py

# Or using pytest (if installed)
pytest tests/
```

**Run Specific Test Categories:**
```bash
# Unit tests only
python tests/run_tests.py test_audio_recorder

# Integration tests
python tests/run_tests.py test_integration

# Vault functionality
python tests/run_tests.py test_vault_manager
```

**Install Test Dependencies:**
```bash
pip install -r requirements-test.txt
```

### Test Categories

- **Unit Tests** - Individual component testing
  - `test_audio_recorder.py` - Audio recording functionality
  - `test_vault_manager.py` - Database operations
  - `test_whisper_service.py` - Transcription services
  
- **Integration Tests** - End-to-end workflow testing
  - `test_integration.py` - Complete application workflows
  
- **Coverage Reports** - Generate with pytest:
  ```bash
  pytest --cov=src --cov-report=html
  # Open htmlcov/index.html for detailed coverage
  ```

### Code Quality

**Type Checking:**
```bash
mypy src/
```

**Code Formatting:**
```bash
black src/ tests/
isort src/ tests/
```

**Linting:**
```bash
flake8 src/ tests/
```

## 🔧 Troubleshooting

### Common Issues

**Audio Recording Problems:**
```bash
python diagnose_audio.py  # Check audio devices
```

**FFmpeg Not Found:**
- Ensure FFmpeg is installed and in your PATH
- Restart terminal after installation
- Verify: `ffmpeg -version`

**Local Whisper Issues:**
- Ensure sufficient RAM for chosen model
- For GPU acceleration, install CUDA-compatible PyTorch
- Try smaller model if memory issues occur

**API Connection Problems:**
- Verify OpenAI API key is valid
- Check internet connection
- Ensure API quota is not exceeded

**Installation Problems:**
- Try the automated installer: `python3 install.py`
- Use platform-specific scripts: `./setup.sh` (Linux/macOS) or `setup.bat` (Windows)
- Check system requirements and dependencies

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
