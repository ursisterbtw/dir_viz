#!/usr/bin/env python3
"""
Test runner for flowcharter and mermaider test suites.

This script provides a convenient way to run all tests with proper
configuration and reporting.
"""

import argparse
import sys
import unittest
from pathlib import Path


def discover_and_run_tests(test_pattern="test_*.py", verbosity=2, failfast=False):
    """
    Discover and run tests matching the pattern.

    Args:
        test_pattern: Pattern to match test files
        verbosity: Test output verbosity level
        failfast: Stop on first failure

    Returns:
        True if all tests pass, False otherwise
    """
    # Get the directory containing this script
    test_dir = Path(__file__).parent

    # Discover tests only in tests directory
    loader = unittest.TestLoader()
    tests_only_dir = test_dir / "tests"
    suite = loader.discover(
        start_dir=str(tests_only_dir), pattern=test_pattern, top_level_dir=str(test_dir)
    )

    # Run tests
    runner = unittest.TextTestRunner(
        verbosity=verbosity,
        failfast=failfast,
        buffer=True,  # Capture stdout/stderr during tests
    )

    result = runner.run(suite)

    # Return success status
    return result.wasSuccessful()


def run_specific_test_module(module_name, verbosity=2):
    """
    Run tests from a specific module.

    Args:
        module_name: Name of the test module (without .py extension)
        verbosity: Test output verbosity level

    Returns:
        True if all tests pass, False otherwise
    """
    try:
        # Import the test module
        test_module = __import__(module_name)

        # Create test suite from module
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromModule(test_module)

        # Run tests
        runner = unittest.TextTestRunner(verbosity=verbosity, buffer=True)
        result = runner.run(suite)

        return result.wasSuccessful()

    except ImportError as e:
        print(f"Error importing test module '{module_name}': {e}")
        return False


def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(
        description="Run tests for flowcharter and mermaider tools"
    )

    parser.add_argument(
        "--module", "-m", help="Run tests from specific module (e.g., test_flowcharter)"
    )

    parser.add_argument(
        "--pattern",
        "-p",
        default="test_*.py",
        help="Pattern to match test files (default: test_*.py)",
    )

    parser.add_argument(
        "--verbosity",
        "-v",
        type=int,
        choices=[0, 1, 2],
        default=2,
        help="Test output verbosity (0=quiet, 1=normal, 2=verbose)",
    )

    parser.add_argument(
        "--failfast", "-f", action="store_true", help="Stop on first test failure"
    )

    parser.add_argument(
        "--list", "-l", action="store_true", help="List available test modules and exit"
    )

    args = parser.parse_args()

    # List available test modules
    if args.list:
        test_dir = Path(__file__).parent / "tests"
        test_files = list(test_dir.glob("test_*.py"))

        print("Available test modules:")
        for test_file in sorted(test_files):
            module_name = test_file.stem
            print(f"  {module_name}")

        return 0

    # Run specific module or discover all tests
    if args.module:
        module_name = args.module
        if not module_name.startswith("tests."):
            module_name = f"tests.{module_name}"
        success = run_specific_test_module(module_name, args.verbosity)
    else:
        success = discover_and_run_tests(
            test_pattern=args.pattern, verbosity=args.verbosity, failfast=args.failfast
        )

    # Exit with appropriate code
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
