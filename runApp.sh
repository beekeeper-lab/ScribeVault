#!/bin/bash

# ScribeVault Run Script
# Safely stop any running instance, activate venv, and start the application

set -e  # Exit on any error

echo "🎙️ ScribeVault Runner"
echo "===================="
echo ""

# Function to check if ScribeVault is running
check_running() {
    if pgrep -f "python.*main.py" > /dev/null; then
        return 0  # Running
    else
        return 1  # Not running
    fi
}

# Stop any existing ScribeVault processes
echo "🔍 Checking for running ScribeVault instances..."
if check_running; then
    echo "⏹️  Stopping existing ScribeVault processes..."
    pkill -f "python.*main.py" || true
    
    # Wait a moment for processes to stop
    sleep 2
    
    # Check if still running and force kill if necessary
    if check_running; then
        echo "🔨 Force stopping stubborn processes..."
        pkill -9 -f "python.*main.py" || true
        sleep 1
    fi
    
    echo "✅ Existing processes stopped"
else
    echo "✅ No existing processes found"
fi
echo ""

# Check if we're in the right directory
if [[ ! -f "main.py" ]]; then
    echo "❌ Error: main.py not found. Please run this script from the ScribeVault directory."
    exit 1
fi

# Check if virtual environment exists
if [[ ! -d "venv" ]]; then
    echo "❌ Error: Virtual environment not found."
    echo "Please run setup.sh first to create the virtual environment."
    exit 1
fi

# Check if virtual environment is already active
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "✅ Virtual environment already active: $(basename $VIRTUAL_ENV)"
else
    echo "🔄 Activating virtual environment..."
    source venv/bin/activate
    echo "✅ Virtual environment activated"
fi
echo ""

# Verify Python environment
echo "🐍 Verifying Python environment..."
PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
echo "✅ Using Python $PYTHON_VERSION"

# Check if main dependencies are available
echo "📦 Checking key dependencies..."
if python -c "import PySide6; print('✅ PySide6 available')" 2>/dev/null; then
    true
else
    echo "❌ PySide6 not found. Please run setup.sh to install dependencies."
    exit 1
fi

if python -c "import pyaudio; print('✅ PyAudio available')" 2>/dev/null; then
    true
else
    echo "⚠️  PyAudio may have issues. Audio recording might not work properly."
fi
echo ""

# Start the application
echo "🚀 Starting ScribeVault (PySide6 Version)..."
echo "Press Ctrl+C to stop the application"
echo "===================="
echo ""

# Run the PySide6 application and capture exit code
python main.py
EXIT_CODE=$?

echo ""
echo "===================="
if [[ $EXIT_CODE -eq 0 ]]; then
    echo "✅ ScribeVault closed normally"
else
    echo "⚠️  ScribeVault exited with code $EXIT_CODE"
fi
echo "🏁 Run script completed"
