#!/usr/bin/env python3
"""
Test runner utility for Tinel testing suite.

Copyright 2025 Infenia Private Limited
Licensed under the Apache License, Version 2.0
"""

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional


class TestRunner:
    """Utility for running different categories of tests."""

    def __init__(self):
        """Initialize the test runner."""
        self.project_root = Path(__file__).parent.parent
        self.tests_dir = self.project_root / "tests"

    def run_unit_tests(self, verbose: bool = False, coverage: bool = True) -> int:
        """Run unit tests.

        Args:
            verbose: Enable verbose output
            coverage: Enable coverage reporting

        Returns:
            Exit code from pytest
        """
        cmd = ["python", "-m", "pytest", "-m", "unit"]

        if verbose:
            cmd.append("-v")

        if coverage:
            cmd.extend(["--cov=tinel", "--cov-report=term-missing"])

        # Run only unit tests (fast)
        cmd.extend(
            [
                "--durations=10",
                "tests/unit/",
            ]
        )

        return self._run_command(cmd)

    def run_integration_tests(self, verbose: bool = False) -> int:
        """Run integration tests.

        Args:
            verbose: Enable verbose output

        Returns:
            Exit code from pytest
        """
        cmd = ["python", "-m", "pytest", "-m", "integration"]

        if verbose:
            cmd.append("-v")

        cmd.extend(
            [
                "--durations=10",
                "tests/integration/",
            ]
        )

        return self._run_command(cmd)

    def run_performance_tests(self, verbose: bool = False) -> int:
        """Run performance tests.

        Args:
            verbose: Enable verbose output

        Returns:
            Exit code from pytest
        """
        cmd = ["python", "-m", "pytest", "-m", "performance"]

        if verbose:
            cmd.append("-v")

        cmd.extend(
            [
                "--durations=20",  # Show more slow tests for performance analysis
                "tests/performance/",
            ]
        )

        return self._run_command(cmd)

    def run_security_tests(self, verbose: bool = False) -> int:
        """Run security tests.

        Args:
            verbose: Enable verbose output

        Returns:
            Exit code from pytest
        """
        cmd = ["python", "-m", "pytest", "-m", "security"]

        if verbose:
            cmd.append("-v")

        cmd.extend(
            [
                "--durations=10",
                "tests/security/",
            ]
        )

        return self._run_command(cmd)

    def run_all_tests(self, verbose: bool = False, coverage: bool = True) -> int:
        """Run all tests.

        Args:
            verbose: Enable verbose output
            coverage: Enable coverage reporting

        Returns:
            Exit code from pytest
        """
        cmd = ["python", "-m", "pytest"]

        if verbose:
            cmd.append("-v")

        if coverage:
            cmd.extend(
                [
                    "--cov=tinel",
                    "--cov-report=term-missing",
                    "--cov-report=html:htmlcov",
                    "--cov-report=xml:coverage.xml",
                ]
            )

        cmd.extend(
            [
                "--durations=20",
                "tests/",
            ]
        )

        return self._run_command(cmd)

    def run_fast_tests(self, verbose: bool = False) -> int:
        """Run only fast tests (unit tests).

        Args:
            verbose: Enable verbose output

        Returns:
            Exit code from pytest
        """
        cmd = ["python", "-m", "pytest", "-m", "unit", "--tb=short"]

        if verbose:
            cmd.append("-v")

        cmd.extend(
            [
                "tests/unit/",
            ]
        )

        return self._run_command(cmd)

    def run_slow_tests(self, verbose: bool = False) -> int:
        """Run slow tests (integration, performance, security).

        Args:
            verbose: Enable verbose output

        Returns:
            Exit code from pytest
        """
        cmd = ["python", "-m", "pytest", "-m", "integration or performance or security"]

        if verbose:
            cmd.append("-v")

        cmd.extend(
            [
                "--durations=20",
                "tests/",
            ]
        )

        return self._run_command(cmd)

    def run_tests_by_module(self, module: str, verbose: bool = False) -> int:
        """Run tests for a specific module.

        Args:
            module: Module name (e.g., 'system', 'cpu_analyzer')
            verbose: Enable verbose output

        Returns:
            Exit code from pytest
        """
        cmd = ["python", "-m", "pytest"]

        if verbose:
            cmd.append("-v")

        # Find test files matching the module
        test_patterns = [
            f"tests/unit/test_{module}.py",
            f"tests/integration/test_{module}_integration.py",
            f"tests/performance/test_{module}_performance.py",
            f"tests/security/test_{module}_security.py",
        ]

        # Add existing test files to command
        for pattern in test_patterns:
            test_file = self.project_root / pattern
            if test_file.exists():
                cmd.append(str(test_file))

        if len(cmd) == 2:  # Only base command, no test files found
            print(f"No test files found for module: {module}")
            return 1

        return self._run_command(cmd)

    def run_tests_with_coverage_report(self) -> int:
        """Run all tests and generate comprehensive coverage report.

        Returns:
            Exit code from pytest
        """
        cmd = [
            "python",
            "-m",
            "pytest",
            "--cov=tinel",
            "--cov-report=term-missing",
            "--cov-report=html:htmlcov",
            "--cov-report=xml:coverage.xml",
            "--cov-fail-under=85",
            "tests/",
        ]

        result = self._run_command(cmd)

        if result == 0:
            print("\n" + "=" * 60)
            print("Coverage report generated:")
            print(f"  HTML: {self.project_root}/htmlcov/index.html")
            print(f"  XML:  {self.project_root}/coverage.xml")
            print("=" * 60)

        return result

    def lint_tests(self) -> int:
        """Run linting on test files.

        Returns:
            Exit code from linting tools
        """
        print("Running test linting...")

        # Run ruff on test files
        cmd = ["python", "-m", "ruff", "check", "tests/"]
        result = self._run_command(cmd)

        if result != 0:
            return result

        # Run mypy on test files
        cmd = ["python", "-m", "mypy", "tests/", "--ignore-missing-imports"]
        return self._run_command(cmd)

    def format_tests(self) -> int:
        """Format test files.

        Returns:
            Exit code from formatting tools
        """
        print("Formatting test files...")

        # Run ruff formatter
        cmd = ["python", "-m", "ruff", "format", "tests/"]
        result = self._run_command(cmd)

        if result != 0:
            return result

        # Run black formatter
        cmd = ["python", "-m", "black", "tests/"]
        return self._run_command(cmd)

    def check_test_requirements(self) -> Dict[str, bool]:
        """Check if test requirements are installed.

        Returns:
            Dictionary of requirement name to availability
        """
        requirements = {
            "pytest": self._check_import("pytest"),
            "pytest-cov": self._check_import("pytest_cov"),
            "pytest-mock": self._check_import("pytest_mock"),
            "psutil": self._check_import("psutil"),
        }

        return requirements

    def install_test_requirements(self) -> int:
        """Install test requirements.

        Returns:
            Exit code from pip install
        """
        print("Installing test requirements...")

        requirements = [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "pytest-mock>=3.10.0",
            "psutil>=5.9.0",
        ]

        cmd = ["python", "-m", "pip", "install"] + requirements
        return self._run_command(cmd)

    def generate_test_report(self, output_file: Optional[str] = None) -> int:
        """Generate comprehensive test report.

        Args:
            output_file: Output file path (default: test_report.html)

        Returns:
            Exit code
        """
        if output_file is None:
            output_file = str(self.project_root / "test_report.html")

        cmd = [
            "python",
            "-m",
            "pytest",
            "--html=" + output_file,
            "--self-contained-html",
            "--cov=tinel",
            "--cov-report=html:htmlcov",
            "tests/",
        ]

        result = self._run_command(cmd)

        if result == 0:
            print(f"\nTest report generated: {output_file}")

        return result

    def _run_command(self, cmd: List[str]) -> int:
        """Run a command and return its exit code.

        Args:
            cmd: Command to run

        Returns:
            Exit code from command
        """
        print(f"Running: {' '.join(cmd)}")

        try:
            result = subprocess.run(cmd, check=False, cwd=self.project_root)
            return result.returncode
        except FileNotFoundError as e:
            print(f"Error: Command not found: {e}")
            return 1
        except KeyboardInterrupt:
            print("\nTest run interrupted by user")
            return 130

    def _check_import(self, module_name: str) -> bool:
        """Check if a module can be imported.

        Args:
            module_name: Name of module to check

        Returns:
            True if module can be imported
        """
        try:
            __import__(module_name)
            return True
        except ImportError:
            return False


def main():
    """Main entry point for test runner."""
    parser = argparse.ArgumentParser(
        description="Test runner for Tinel project",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s unit                    # Run unit tests
  %(prog)s integration             # Run integration tests  
  %(prog)s performance             # Run performance tests
  %(prog)s security                # Run security tests
  %(prog)s all                     # Run all tests
  %(prog)s fast                    # Run only fast tests
  %(prog)s slow                    # Run slow tests
  %(prog)s module system           # Run tests for system module
  %(prog)s coverage                # Run tests with coverage report
  %(prog)s lint                    # Lint test files
  %(prog)s format                  # Format test files
  %(prog)s check-requirements      # Check test requirements
  %(prog)s install-requirements    # Install test requirements
        """,
    )

    parser.add_argument(
        "command",
        choices=[
            "unit",
            "integration",
            "performance",
            "security",
            "all",
            "fast",
            "slow",
            "module",
            "coverage",
            "lint",
            "format",
            "check-requirements",
            "install-requirements",
            "report",
        ],
        help="Test command to run",
    )

    parser.add_argument(
        "module", nargs="?", help="Module name for module-specific tests"
    )

    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose output"
    )

    parser.add_argument(
        "--no-coverage", action="store_true", help="Disable coverage reporting"
    )

    parser.add_argument("--output", help="Output file for reports")

    args = parser.parse_args()

    runner = TestRunner()

    # Handle commands
    if args.command == "unit":
        return runner.run_unit_tests(args.verbose, not args.no_coverage)
    elif args.command == "integration":
        return runner.run_integration_tests(args.verbose)
    elif args.command == "performance":
        return runner.run_performance_tests(args.verbose)
    elif args.command == "security":
        return runner.run_security_tests(args.verbose)
    elif args.command == "all":
        return runner.run_all_tests(args.verbose, not args.no_coverage)
    elif args.command == "fast":
        return runner.run_fast_tests(args.verbose)
    elif args.command == "slow":
        return runner.run_slow_tests(args.verbose)
    elif args.command == "module":
        if not args.module:
            print("Error: Module name required for module command")
            return 1
        return runner.run_tests_by_module(args.module, args.verbose)
    elif args.command == "coverage":
        return runner.run_tests_with_coverage_report()
    elif args.command == "lint":
        return runner.lint_tests()
    elif args.command == "format":
        return runner.format_tests()
    elif args.command == "check-requirements":
        requirements = runner.check_test_requirements()
        print("Test Requirements Status:")
        for req, available in requirements.items():
            status = "✓ Available" if available else "✗ Missing"
            print(f"  {req}: {status}")
        return 0 if all(requirements.values()) else 1
    elif args.command == "install-requirements":
        return runner.install_test_requirements()
    elif args.command == "report":
        return runner.generate_test_report(args.output)
    else:
        print(f"Unknown command: {args.command}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
