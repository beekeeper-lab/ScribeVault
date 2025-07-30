"""
Test runner for ScribeVault application.

This module provides utilities for running tests with proper path setup.
"""

import sys
import os
import unittest
from pathlib import Path

# Add src directory to path for imports
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

def run_all_tests():
    """Run all tests in the tests directory."""
    print("Running ScribeVault Test Suite")
    print("=" * 50)
    
    # Discover and run tests
    loader = unittest.TestLoader()
    start_dir = Path(__file__).parent
    suite = loader.discover(str(start_dir), pattern='test_*.py')
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 50)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    
    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback}")
    
    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback}")
    
    return result.wasSuccessful()

def run_specific_test(test_name):
    """Run a specific test module."""
    print(f"Running {test_name}")
    print("=" * 50)
    
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromName(test_name)
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run ScribeVault tests")
    parser.add_argument(
        "test", 
        nargs="?", 
        help="Specific test to run (e.g., test_audio_recorder.TestAudioRecorder.test_initialization)"
    )
    parser.add_argument(
        "--list", 
        action="store_true", 
        help="List available tests"
    )
    
    args = parser.parse_args()
    
    if args.list:
        # List available tests
        loader = unittest.TestLoader()
        start_dir = Path(__file__).parent
        suite = loader.discover(str(start_dir), pattern='test_*.py')
        
        print("Available tests:")
        for test_group in suite:
            for test_case in test_group:
                if hasattr(test_case, '_tests'):
                    for test in test_case._tests:
                        print(f"  {test.id()}")
    elif args.test:
        success = run_specific_test(args.test)
        sys.exit(0 if success else 1)
    else:
        success = run_all_tests()
        sys.exit(0 if success else 1)
