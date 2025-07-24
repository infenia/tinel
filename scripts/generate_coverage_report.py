#!/usr/bin/env python3
"""
Copyright 2025 Infenia Private Limited

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

"""Script to generate code coverage reports for all modules."""

import os
import sys
import subprocess
import argparse
from pathlib import Path


def run_command(command):
    """Run a command and return the output."""
    process = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    return process


def generate_coverage_report(module=None, format="term", threshold=90):
    """Generate a coverage report for a specific module or all modules."""
    # Determine the module to test
    module_path = f"tinel/{module}" if module else "tinel"

    # Run pytest with coverage
    cmd = ["pytest", f"--cov={module_path}"]

    # Add coverage report formats
    if "term" in format:
        cmd.append("--cov-report=term")
    if "html" in format:
        cmd.append("--cov-report=html")
    if "xml" in format:
        cmd.append("--cov-report=xml")

    # Run the tests with coverage
    result = run_command(cmd)
    if result.returncode != 0:
        print(f"Error running tests: {result.stderr}")
        return False

    # Check coverage threshold
    if threshold > 0:
        threshold_cmd = ["coverage", "report", f"--fail-under={threshold}"]
        threshold_result = run_command(threshold_cmd)
        if threshold_result.returncode != 0:
            print(
                f"Coverage below threshold of {threshold}%: {threshold_result.stderr}"
            )
            return False

    return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Generate code coverage reports.")
    parser.add_argument(
        "--module",
        help="Module to generate coverage report for (e.g., 'hardware', 'kernel'). "
        "If not specified, coverage will be generated for all modules.",
    )
    parser.add_argument(
        "--format",
        choices=["term", "html", "xml", "all"],
        default="all",
        help="Coverage report format. Default is 'all'.",
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=90,
        help="Coverage threshold percentage. Default is 90.",
    )
    args = parser.parse_args()

    # Determine formats
    formats = []
    if args.format == "all":
        formats = ["term", "html", "xml"]
    else:
        formats = [args.format]

    # Generate coverage report
    success = generate_coverage_report(args.module, formats, args.threshold)

    # Print summary
    if success:
        print("\nCoverage report generated successfully.")
        if "html" in formats:
            html_path = Path("htmlcov/index.html").absolute()
            print(f"HTML report: file://{html_path}")
        if "xml" in formats:
            xml_path = Path("coverage.xml").absolute()
            print(f"XML report: {xml_path}")
    else:
        print("\nFailed to generate coverage report.")
        sys.exit(1)


if __name__ == "__main__":
    main()
