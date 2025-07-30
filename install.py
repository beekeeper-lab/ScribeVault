#!/usr/bin/env python3
"""
ScribeVault Installer
Cross-platform setup script for ScribeVault application
"""

import os
import sys
import subprocess
import platform
import shutil
from pathlib import Path

def run_command(cmd, check=True, shell=False):
    """Run a command and handle errors"""
    try:
        result = subprocess.run(cmd, check=check, shell=shell, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        return False, e.stdout, e.stderr
    except FileNotFoundError:
        return False, "", f"Command not found: {cmd[0] if isinstance(cmd, list) else cmd}"

def check_python():
    """Check Python version"""
    print("🐍 Checking Python installation...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python 3.8+ required, found {version.major}.{version.minor}")
        return False
    print(f"✅ Found Python {version.major}.{version.minor}.{version.micro}")
    return True

def check_ffmpeg():
    """Check if FFmpeg is installed"""
    print("🎵 Checking FFmpeg installation...")
    success, stdout, stderr = run_command(["ffmpeg", "-version"])
    if success:
        version_line = stdout.split('\n')[0]
        print(f"✅ Found {version_line}")
        return True
    else:
        print("⚠️  FFmpeg not found")
        return False

def install_ffmpeg():
    """Provide FFmpeg installation instructions"""
    system = platform.system()
    print("📦 FFmpeg installation required:")
    
    if system == "Windows":
        print("  Option 1: Download from https://ffmpeg.org/download.html")
        print("  Option 2: choco install ffmpeg")
        print("  Option 3: winget install FFmpeg")
    elif system == "Darwin":  # macOS
        print("  brew install ffmpeg")
    elif system == "Linux":
        print("  Ubuntu/Debian: sudo apt update && sudo apt install ffmpeg")
        print("  RHEL/CentOS: sudo yum install ffmpeg")
        print("  Fedora: sudo dnf install ffmpeg")
    
    return False

def setup_virtual_environment():
    """Create and setup virtual environment"""
    venv_path = Path("venv")
    
    if not venv_path.exists():
        print("📦 Creating virtual environment...")
        success, stdout, stderr = run_command([sys.executable, "-m", "venv", "venv"])
        if not success:
            print(f"❌ Failed to create virtual environment: {stderr}")
            return False
    else:
        print("📦 Virtual environment already exists")
    
    # Determine activation script
    if platform.system() == "Windows":
        pip_path = venv_path / "Scripts" / "pip"
        python_path = venv_path / "Scripts" / "python"
    else:
        pip_path = venv_path / "bin" / "pip"
        python_path = venv_path / "bin" / "python"
    
    # Upgrade pip
    print("⬆️ Upgrading pip...")
    success, stdout, stderr = run_command([str(python_path), "-m", "pip", "install", "--upgrade", "pip"])
    if not success:
        print(f"⚠️  Warning: Could not upgrade pip: {stderr}")
    
    # Install requirements
    print("📥 Installing Python dependencies...")
    if Path("requirements.txt").exists():
        success, stdout, stderr = run_command([str(pip_path), "install", "-r", "requirements.txt"])
        if not success:
            print(f"❌ Failed to install requirements: {stderr}")
            return False
    else:
        print("⚠️  requirements.txt not found")
        return False
    
    return True

def test_audio():
    """Test audio system"""
    print("🎤 Testing audio system...")
    try:
        import pyaudio
        print("✅ Audio system ready")
        return True
    except ImportError:
        print("⚠️  PyAudio not available")
        return False
    except Exception as e:
        print(f"⚠️  Audio system issue: {e}")
        return False

def setup_environment_file():
    """Setup .env file"""
    env_path = Path(".env")
    example_path = Path(".env.example")
    
    if not env_path.exists():
        if example_path.exists():
            print("📄 Creating .env file from template...")
            shutil.copy(example_path, env_path)
            print("⚠️  Please edit .env and add your OpenAI API key")
        else:
            print("📄 Creating basic .env file...")
            with open(env_path, "w") as f:
                f.write("# ScribeVault Configuration\n")
                f.write("OPENAI_API_KEY=your-key-here\n")
            print("⚠️  Please edit .env and add your OpenAI API key")
    else:
        print("📄 .env file already exists")

def create_directories():
    """Create required directories"""
    print("📁 Creating required directories...")
    directories = ["recordings", "vault", "config"]
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)

def test_configuration():
    """Test the configuration"""
    print("🧪 Testing configuration...")
    if Path("test_config.py").exists():
        success, stdout, stderr = run_command([sys.executable, "test_config.py"])
        if success:
            print("✅ Configuration test passed")
        else:
            print("⚠️  Configuration test had issues (normal if no API key is set)")
    else:
        print("⚠️  test_config.py not found, skipping test")

def main():
    """Main installer function"""
    print("🎙️ ScribeVault Installer")
    print("=" * 40)
    print()
    
    # Check prerequisites
    if not check_python():
        sys.exit(1)
    
    if not check_ffmpeg():
        if not install_ffmpeg():
            print("\n❌ Please install FFmpeg and run this script again")
            sys.exit(1)
    
    print()
    
    # Setup environment
    if not setup_virtual_environment():
        sys.exit(1)
    
    # Test audio
    test_audio()
    print()
    
    # Setup files and directories
    setup_environment_file()
    create_directories()
    test_configuration()
    
    print()
    print("🎉 Setup complete!")
    print("=" * 40)
    print()
    print("📋 Next steps:")
    print("1. Edit .env and add your OpenAI API key (for API mode)")
    
    if platform.system() == "Windows":
        print("2. Run: venv\\Scripts\\activate.bat && python main.py")
        print("\n💡 Create a shortcut with: venv\\Scripts\\activate.bat && python main.py")
    else:
        print("2. Run: source venv/bin/activate && python main.py")
        print("\n💡 Pro tip: source venv/bin/activate && python main.py")
    
    print("\n🔧 For local Whisper mode:")
    print("- No API key needed")
    print("- Go to Settings → Change transcription service to 'local'")
    print("- Choose model size based on your system capabilities")
    
    print("\n🆘 If you encounter issues:")
    print("- Run: python diagnose_audio.py (to check audio setup)")
    print("- Check the troubleshooting section in README.md")

if __name__ == "__main__":
    main()
