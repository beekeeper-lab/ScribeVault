#!/usr/bin/env python3
"""
ScribeVault Health Check - Identify and fix common issues
"""

import sys
import os
from pathlib import Path
import subprocess

def check_imports():
    """Check all critical imports."""
    print("🔍 Checking Imports...")
    
    # Add src to path
    sys.path.insert(0, str(Path.cwd() / "src"))
    
    critical_imports = [
        "export.markdown_generator",
        "ai.summarizer", 
        "vault.manager",
        "gui.qt_main_window",
        "audio.recorder",
        "transcription.whisper_service",
        "config.settings"
    ]
    
    errors = []
    for module in critical_imports:
        try:
            __import__(module)
            print(f"  ✅ {module}")
        except Exception as e:
            print(f"  ❌ {module}: {e}")
            errors.append(f"{module}: {e}")
    
    return errors

def check_init_files():
    """Check for missing __init__.py files."""
    print("\n📁 Checking __init__.py files...")
    
    src_path = Path("src")
    missing = []
    
    for directory in src_path.rglob("*"):
        if directory.is_dir() and directory.name != "__pycache__" and not directory.name.startswith("."):
            init_file = directory / "__init__.py"
            if not init_file.exists():
                print(f"  ❌ Missing: {init_file}")
                missing.append(str(init_file))
            else:
                print(f"  ✅ Found: {init_file}")
    
    return missing

def check_syntax():
    """Check Python syntax in all files."""
    print("\n🐍 Checking Python syntax...")
    
    errors = []
    for py_file in Path(".").rglob("*.py"):
        if "__pycache__" in str(py_file) or ".git" in str(py_file):
            continue
            
        try:
            with open(py_file, 'r') as f:
                compile(f.read(), py_file, 'exec')
            print(f"  ✅ {py_file}")
        except SyntaxError as e:
            print(f"  ❌ {py_file}: {e}")
            errors.append(f"{py_file}: {e}")
        except Exception as e:
            print(f"  ⚠️  {py_file}: {e}")
    
    return errors

def clean_cache():
    """Clean Python cache files."""
    print("\n🧹 Cleaning cache files...")
    
    # Remove __pycache__ directories
    for cache_dir in Path(".").rglob("__pycache__"):
        try:
            import shutil
            shutil.rmtree(cache_dir)
            print(f"  🗑️  Removed: {cache_dir}")
        except Exception as e:
            print(f"  ⚠️  Could not remove {cache_dir}: {e}")
    
    # Remove .pyc files
    for pyc_file in Path(".").rglob("*.pyc"):
        try:
            pyc_file.unlink()
            print(f"  🗑️  Removed: {pyc_file}")
        except Exception as e:
            print(f"  ⚠️  Could not remove {pyc_file}: {e}")

def check_dependencies():
    """Check if required packages are installed."""
    print("\n📦 Checking dependencies...")
    
    required = [
        ("PySide6", "PySide6"),
        ("openai", "openai"),
        ("python-dotenv", "dotenv"),
        ("pyaudio", "pyaudio"),
        ("requests", "requests"),
        ("Pillow", "PIL")
    ]
    
    missing = []
    for package_name, import_name in required:
        try:
            __import__(import_name)
            print(f"  ✅ {package_name}")
        except ImportError:
            print(f"  ❌ {package_name}")
            missing.append(package_name)
    
    return missing

def main():
    """Run comprehensive health check."""
    print("🏥 ScribeVault Health Check")
    print("=" * 50)
    
    os.chdir(Path(__file__).parent)
    
    all_issues = []
    
    # Check imports
    import_errors = check_imports()
    all_issues.extend(import_errors)
    
    # Check __init__.py files
    missing_inits = check_init_files()
    all_issues.extend(missing_inits)
    
    # Check syntax
    syntax_errors = check_syntax()
    all_issues.extend(syntax_errors)
    
    # Clean cache
    clean_cache()
    
    # Check dependencies
    missing_deps = check_dependencies()
    all_issues.extend(missing_deps)
    
    print("\n" + "=" * 50)
    print("📊 SUMMARY")
    print("=" * 50)
    
    if not all_issues:
        print("🎉 No issues found! ScribeVault is healthy.")
    else:
        print(f"❌ Found {len(all_issues)} issues:")
        for i, issue in enumerate(all_issues, 1):
            print(f"  {i}. {issue}")
    
    print("\n💡 If VS Code still shows problems:")
    print("1. Restart VS Code")
    print("2. Reload the window (Ctrl+Shift+P → 'Developer: Reload Window')")
    print("3. Check VS Code Python interpreter settings")

if __name__ == "__main__":
    main()
