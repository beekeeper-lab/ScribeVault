#!/bin/bash

# ScribeVault Setup Script
# Automated setup for ScribeVault audio recording and transcription application

set -e  # Exit on any error

echo "🎙️ ScribeVault Setup Script"
echo "================================"
echo ""

# Detect OS
OS="$(uname -s)"
case "${OS}" in
    Linux*)     MACHINE=Linux;;
    Darwin*)    MACHINE=Mac;;
    CYGWIN*)    MACHINE=Cygwin;;
    MINGW*)     MACHINE=MinGw;;
    *)          MACHINE="UNKNOWN:${OS}"
esac

echo "🔍 Detected OS: $MACHINE"
echo ""

# Check if Python 3 is available
echo "🐍 Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: python3 is not installed or not in PATH"
    echo "Please install Python 3.8+ from https://python.org"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "✅ Found Python $PYTHON_VERSION"
echo ""

# Check FFmpeg
echo "🎵 Checking FFmpeg installation..."
if ! command -v ffmpeg &> /dev/null; then
    echo "⚠️  FFmpeg not found. Installing FFmpeg..."
    case $MACHINE in
        Linux)
            if command -v apt &> /dev/null; then
                echo "📦 Installing FFmpeg via apt..."
                sudo apt update && sudo apt install -y ffmpeg
            elif command -v yum &> /dev/null; then
                echo "📦 Installing FFmpeg via yum..."
                sudo yum install -y ffmpeg
            elif command -v dnf &> /dev/null; then
                echo "📦 Installing FFmpeg via dnf..."
                sudo dnf install -y ffmpeg
            else
                echo "❌ Could not detect package manager. Please install FFmpeg manually."
                exit 1
            fi
            ;;
        Mac)
            if command -v brew &> /dev/null; then
                echo "📦 Installing FFmpeg via Homebrew..."
                brew install ffmpeg
            else
                echo "❌ Homebrew not found. Please install FFmpeg manually:"
                echo "   brew install ffmpeg"
                exit 1
            fi
            ;;
        *)
            echo "❌ Unsupported OS for automatic FFmpeg installation."
            echo "Please install FFmpeg manually from https://ffmpeg.org"
            exit 1
            ;;
    esac
else
    FFMPEG_VERSION=$(ffmpeg -version 2>&1 | head -n1 | awk '{print $3}')
    echo "✅ Found FFmpeg $FFMPEG_VERSION"
fi
echo ""

# Create virtual environment if it doesn't exist
if [[ ! -d "venv" ]]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
else
    echo "📦 Virtual environment already exists"
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "📥 Installing Python dependencies..."
pip install -r requirements.txt

# Test audio system
echo "🎤 Testing audio system..."
if python3 -c "import pyaudio; print('✅ PyAudio working')" 2>/dev/null; then
    echo "✅ Audio system ready"
else
    echo "⚠️  PyAudio installation may have issues. You may need to install system audio libraries."
    case $MACHINE in
        Linux)
            echo "Try: sudo apt install portaudio19-dev python3-pyaudio"
            ;;
        Mac)
            echo "Try: brew install portaudio"
            ;;
    esac
fi
echo ""

# Create .env file if it doesn't exist
if [[ ! -f ".env" ]]; then
    echo "📄 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env and add your OpenAI API key"
else
    echo "📄 .env file already exists"
fi

# Create required directories
echo "📁 Creating required directories..."
mkdir -p recordings
mkdir -p vault
mkdir -p config

# Test configuration
echo "🧪 Testing configuration..."
if python3 test_config.py; then
    echo "✅ Configuration test passed"
else
    echo "⚠️  Configuration test had issues (this is normal if no API key is set)"
fi
echo ""

echo "🎉 Setup complete!"
echo "================================"
echo ""
echo "📋 Next steps:"
echo "1. Edit .env and add your OpenAI API key (for API mode)"
echo "2. Run: source venv/bin/activate && python main.py"
echo ""
echo "🔧 For local Whisper mode:"
echo "- No API key needed"
echo "- Go to Settings → Change transcription service to 'local'"
echo "- Choose model size based on your system capabilities"
echo ""
echo "🆘 If you encounter issues:"
echo "- Run: python diagnose_audio.py (to check audio setup)"
echo "- Check the troubleshooting section in README.md"
echo ""
echo "💡 Pro tip: Bookmark this for easy restart:"
echo "   source venv/bin/activate && python main.py"
