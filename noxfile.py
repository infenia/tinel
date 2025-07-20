"""Nox sessions for the Tinel platform."""

import nox

# Python versions to test against
PYTHON_VERSIONS = ["3.11", "3.12", "3.13"]
DEFAULT_PYTHON = "3.11"

# Source and test locations
PACKAGE = "tinel"
LOCATIONS = [PACKAGE, "tests", "noxfile.py"]


@nox.session(python=PYTHON_VERSIONS)
def tests(session):
    """Run the test suite with coverage."""
    session.install(".", "pytest>=7.4.0", "pytest-cov>=4.1.0")
    session.run("pytest", "--cov")


@nox.session(python=DEFAULT_PYTHON)
def lint(session):
    """Run ruff to lint the codebase."""
    session.install("ruff>=0.0.287")
    session.run("ruff", "check", *LOCATIONS)


@nox.session(python=DEFAULT_PYTHON)
def format(session):
    """Auto-format the codebase using ruff and black."""
    session.install("black>=23.7.0", "ruff>=0.0.287")
    session.run("ruff", "format", *LOCATIONS)
    session.run("black", *LOCATIONS)


@nox.session(python=DEFAULT_PYTHON)
def typecheck(session):
    """Run type checks with mypy."""
    session.install(".", "mypy>=1.5.1")
    session.run("mypy", PACKAGE)


@nox.session(python=DEFAULT_PYTHON)
def build(session):
    """Build the project package."""
    session.install("build")
    session.run("python", "-m", "build")


@nox.session(python=DEFAULT_PYTHON)
def docs(session):
    """Generate HTML documentation using pdoc."""
    session.install(".", "pdoc")
    session.run("python", "-m", "pdoc", "--html", "--output-dir", "docs", PACKAGE)
