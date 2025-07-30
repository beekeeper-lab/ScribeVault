@echo off
REM ScribeVault Setup Script for Windows
REM Automated setup for ScribeVault audio recording and transcription application

echo 🎙️ ScribeVault Windows Setup Script
echo ===================================
echo.

REM Check if Python is available
echo 🐍 Checking Python installation...
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ❌ Error: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo ✅ Found Python %PYTHON_VERSION%
echo.

REM Check FFmpeg
echo 🎵 Checking FFmpeg installation...
ffmpeg -version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ⚠️  FFmpeg not found
    echo.
    echo Please install FFmpeg:
    echo 1. Download from https://ffmpeg.org/download.html
    echo 2. Or use chocolatey: choco install ffmpeg
    echo 3. Or use winget: winget install FFmpeg
    echo.
    echo After installation, restart this script.
    pause
    exit /b 1
) else (
    echo ✅ Found FFmpeg
)
echo.

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo 📦 Creating virtual environment...
    python -m venv venv
) else (
    echo 📦 Virtual environment already exists
)

REM Activate virtual environment
echo 🔄 Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo ⬆️ Upgrading pip...
python -m pip install --upgrade pip

REM Install requirements
echo 📥 Installing Python dependencies...
pip install -r requirements.txt

REM Test audio system
echo 🎤 Testing audio system...
python -c "import pyaudio; print('✅ PyAudio working')" >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ⚠️  PyAudio may have issues. This is common on Windows.
    echo If you encounter audio problems, try:
    echo - Restarting as administrator
    echo - Installing Microsoft Visual C++ Redistributable
) else (
    echo ✅ Audio system ready
)
echo.

REM Create .env file if it doesn't exist
if not exist ".env" (
    echo 📄 Creating .env file from template...
    copy .env.example .env >nul
    echo ⚠️  Please edit .env and add your OpenAI API key
) else (
    echo 📄 .env file already exists
)

REM Create required directories
echo 📁 Creating required directories...
if not exist "recordings" mkdir recordings
if not exist "vault" mkdir vault
if not exist "config" mkdir config

REM Test configuration
echo 🧪 Testing configuration...
python test_config.py >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo ✅ Configuration test passed
) else (
    echo ⚠️  Configuration test had issues ^(this is normal if no API key is set^)
)
echo.

echo 🎉 Setup complete!
echo ================================
echo.
echo 📋 Next steps:
echo 1. Edit .env and add your OpenAI API key ^(for API mode^)
echo 2. Run: venv\Scripts\activate.bat ^&^& python main.py
echo.
echo 🔧 For local Whisper mode:
echo - No API key needed
echo - Go to Settings → Change transcription service to 'local'
echo - Choose model size based on your system capabilities
echo.
echo 🆘 If you encounter issues:
echo - Run: python diagnose_audio.py ^(to check audio setup^)
echo - Check the troubleshooting section in README.md
echo.
echo 💡 Pro tip: Create a shortcut with this command:
echo    venv\Scripts\activate.bat ^&^& python main.py
echo.
pause
