"""Nox sessions for the Tinel platform.

This file configures Nox to run tests, linting, formatting, and type checking
across multiple Python versions.
"""

import nox

# Python versions to test against
PYTHON_VERSIONS = ["3.11", "3.12", "3.13"]
DEFAULT_PYTHON = "3.12"


# Source and test locations
PACKAGE = "tinel"
LOCATIONS = [PACKAGE, "tests", "noxfile.py"]


# Source and test locations
PACKAGE = "tinel"
LOCATIONS = [PACKAGE, "tests", "noxfile.py"]


def install_with_uv(session):
    """Install dependencies using global uv."""
    session.run("uv", "pip", "install", "-e", ".[dev]", external=True)


@nox.session(python=PYTHON_VERSIONS)
def tests(session):
    """Run the test suite across multiple Python versions."""
    install_with_uv(session)
    session.run("pytest", "--cov")


@nox.session(python=DEFAULT_PYTHON)
def coverage(session):
    """Run the test suite with detailed coverage reporting."""
    install_with_uv(session)
    session.run(
        "pytest", "--cov", "--cov-report=term", "--cov-report=html", "--cov-report=xml"
    )
    session.run("coverage", "report", "--fail-under=90")


@nox.session(python=DEFAULT_PYTHON)
def lint(session):
    """Lint the codebase using ruff."""
    install_with_uv(session)
    session.run("ruff", "check", *LOCATIONS)


@nox.session(python=DEFAULT_PYTHON)
def lint_fix(session):
    """Run ruff to automatically fix lint issues."""
    install_with_uv(session)
    session.run("ruff", "check", "--fix", *LOCATIONS)


@nox.session(python=DEFAULT_PYTHON)
def format(session):
    """Format the codebase using ruff and black."""
    install_with_uv(session)
    session.run("ruff", "format", *LOCATIONS)
    session.run("black", *LOCATIONS)


@nox.session(python=DEFAULT_PYTHON)
def typecheck(session):
    """Run type checking using mypy."""
    install_with_uv(session)
    session.run("mypy", PACKAGE)


@nox.session(python=DEFAULT_PYTHON)
def build(session):
    """Build the package using the build module."""
    session.run("uv", "pip", "install", "build", external=True)
    session.run("python", "-m", "build")


@nox.session(python=DEFAULT_PYTHON)
def docs(session):
    """Build the documentation using pdoc."""
    session.run("uv", "pip", "install", "pdoc", external=True)
    session.run("python", "-m", "pdoc", "--html", "--output-dir", "docs", PACKAGE)


@nox.session(python=DEFAULT_PYTHON)
def check(session):
    """Run all checks: lint, format, typecheck, and tests."""
    install_with_uv(session)
    session.run("ruff", "check", *LOCATIONS)
    session.run("black", "--check", *LOCATIONS)
    session.run("mypy", PACKAGE)
    session.run("pytest", "--cov")
