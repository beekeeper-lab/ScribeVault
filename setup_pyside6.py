#!/usr/bin/env python3
"""
PySide6 setup and installation script for ScribeVault.
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, 
                              capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"   Command: {command}")
        print(f"   Error: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8 or higher is required for PySide6")
        print(f"   Current version: {version.major}.{version.minor}.{version.micro}")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} is compatible")
    return True

def setup_virtual_environment():
    """Setup virtual environment if it doesn't exist."""
    venv_path = Path("venv")
    
    if venv_path.exists():
        print("✅ Virtual environment already exists")
        return True
        
    print("🔄 Creating virtual environment...")
    if not run_command(f"{sys.executable} -m venv venv", "Virtual environment creation"):
        return False
        
    return True

def get_pip_command():
    """Get the correct pip command for the platform."""
    if os.name == 'nt':  # Windows
        return "venv\\Scripts\\pip"
    else:  # Unix-like
        return "venv/bin/pip"

def install_dependencies():
    """Install PySide6 and other dependencies."""
    pip_cmd = get_pip_command()
    
    # Upgrade pip first
    if not run_command(f"{pip_cmd} install --upgrade pip", "Pip upgrade"):
        return False
    
    # Install requirements
    if not run_command(f"{pip_cmd} install -r requirements.txt", "PySide6 dependencies installation"):
        return False
        
    return True

def test_pyside6_installation():
    """Test if PySide6 is properly installed."""
    try:
        # Test import
        print("🔄 Testing PySide6 installation...")
        
        test_script = """
import sys
try:
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QIcon
    import qdarktheme
    
    # Create a minimal app to test
    app = QApplication([])
    print("✅ PySide6 components imported successfully")
    print(f"   Qt version: {app.instance().applicationVersion()}")
    app.quit()
    sys.exit(0)
except ImportError as e:
    print(f"❌ PySide6 import failed: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ PySide6 test failed: {e}")
    sys.exit(1)
"""
        
        # Write test script
        test_file = Path("test_pyside6.py")
        test_file.write_text(test_script)
        
        # Run test
        if os.name == 'nt':
            python_cmd = "venv\\Scripts\\python"
        else:
            python_cmd = "venv/bin/python"
            
        result = subprocess.run(f"{python_cmd} test_pyside6.py", 
                              shell=True, capture_output=True, text=True)
        
        # Clean up test file
        test_file.unlink()
        
        if result.returncode == 0:
            print(result.stdout)
            return True
        else:
            print(f"❌ PySide6 test failed:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Error testing PySide6: {e}")
        return False

def create_run_script():
    """Create platform-specific run script."""
    if os.name == 'nt':
        # Windows batch script
        script_content = """@echo off
echo Starting ScribeVault with PySide6...
echo.

cd /d "%~dp0"

if not exist "venv" (
    echo Error: Virtual environment not found
    echo Please run setup_pyside6.py first
    pause
    exit /b 1
)

echo Activating virtual environment...
call venv\\Scripts\\activate.bat

echo Starting ScribeVault...
python main_qt.py

if %ERRORLEVEL% neq 0 (
    echo.
    echo Application exited with error code %ERRORLEVEL%
    pause
)
"""
        script_path = Path("runApp_qt.bat")
    else:
        # Unix shell script
        script_content = """#!/bin/bash

echo "🎙️ Starting ScribeVault with PySide6..."
echo "=================================="
echo ""

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check virtual environment
if [[ ! -d "venv" ]]; then
    echo "❌ Error: Virtual environment not found"
    echo "Please run: python3 setup_pyside6.py"
    exit 1
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Check if PySide6 is available
if ! python -c "import PySide6" 2>/dev/null; then
    echo "❌ Error: PySide6 not found in virtual environment"
    echo "Please run: python3 setup_pyside6.py"
    exit 1
fi

echo "✅ Virtual environment activated"
echo ""

# Start application
echo "🚀 Starting ScribeVault..."
echo "Press Ctrl+C to stop"
echo "=================================="
echo ""

python main_qt.py
EXIT_CODE=$?

echo ""
echo "=================================="
if [[ $EXIT_CODE -eq 0 ]]; then
    echo "✅ ScribeVault closed normally"
else
    echo "⚠️  ScribeVault exited with code $EXIT_CODE"
fi
echo "🏁 Session completed"
"""
        script_path = Path("runApp_qt.sh")
        
    # Write script
    script_path.write_text(script_content)
    
    # Make executable on Unix
    if os.name != 'nt':
        os.chmod(script_path, 0o755)
        
    print(f"✅ Created run script: {script_path}")

def main():
    """Main setup function."""
    print("🎙️ ScribeVault PySide6 Setup")
    print("=" * 40)
    print("")
    
    # Check Python version
    if not check_python_version():
        return 1
        
    # Setup virtual environment
    if not setup_virtual_environment():
        return 1
        
    # Install dependencies
    if not install_dependencies():
        return 1
        
    # Test installation
    if not test_pyside6_installation():
        return 1
        
    # Create run script
    create_run_script()
    
    print("")
    print("=" * 40)
    print("🎉 PySide6 setup completed successfully!")
    print("")
    print("Next steps:")
    if os.name == 'nt':
        print("1. Run: runApp_qt.bat")
    else:
        print("1. Run: ./runApp_qt.sh")
    print("2. Or manually: source venv/bin/activate && python main_qt.py")
    print("")
    print("The new PySide6 interface provides:")
    print("• Native look and feel")
    print("• Better performance")
    print("• Enhanced keyboard shortcuts")
    print("• Professional styling")
    print("• System tray integration")
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
