#!/bin/bash

# ScribeVault Setup Script
# This script sets up the development environment for ScribeVault

echo "🔧 Setting up ScribeVault development environment..."

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: python3 is not installed or not in PATH"
    exit 1
fi

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

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env and add your OpenAI API key"
echo "2. Run 'python main.py' to start ScribeVault"
echo ""
echo "For VS Code development:"
echo "- Use Ctrl+Shift+P and select 'Tasks: Run Task' -> 'Run ScribeVault'"
echo "- Or use the terminal: source venv/bin/activate && python main.py"
