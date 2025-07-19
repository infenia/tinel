"""Nox sessions for the Infenix platform."""

import nox

# Set Python versions to test against
PYTHON_VERSIONS = ["3.11", "3.12"]
DEFAULT_PYTHON = "3.11"

# Set locations
PACKAGE = "infenix"
LOCATIONS = [
    PACKAGE,
    "tests",
    "noxfile.py",
]


@nox.session(python=PYTHON_VERSIONS)
def tests(session):
    """Run the test suite."""
    session.install("uv")
    session.run("uv", "pip", "install", "-e", ".")
    session.run("uv", "pip", "install", "pytest>=7.4.0", "pytest-cov>=4.1.0")
    session.run("pytest", "--cov")


@nox.session(python=DEFAULT_PYTHON)
def lint(session):
    """Lint the codebase."""
    session.install("uv")
    session.run("uv", "pip", "install", "-e", ".")
    session.run("uv", "pip", "install", "ruff>=0.0.287")
    session.run("ruff", "check", *LOCATIONS)


@nox.session(python=DEFAULT_PYTHON)
def format(session):
    """Format the codebase."""
    session.install("uv")
    session.run("uv", "pip", "install", "-e", ".")
    session.run("uv", "pip", "install", "ruff>=0.0.287", "black>=23.7.0")
    session.run("ruff", "format", *LOCATIONS)
    session.run("black", *LOCATIONS)


@ntml:function_calls>
<invoke name="fsWrite">
<parameter name="path">noxfile.py"Nox sessions for the Infenix platform."""

import nox

# Set Python versions to test against
PYTHON_VERSIONS = ["3.11", "3.12"]
DEFAULT_PYTHON = "3.11"

# Set locations
PACKAGE = "infenix"
LOCATIONS = [
    PACKAGE,
    "tests",
    "noxfile.py",
]


@nox.session(python=PYTHON_VERSIONS)
def tests(session):
    """Run the test suite."""
    session.install("uv")
    session.run("uv", "pip", "install", "-e", ".")
    session.run("uv", "pip", "install", "pytest>=7.4.0", "pytest-cov>=4.1.0")
    session.run("pytest", "--cov")


@nox.session(python=DEFAULT_PYTHON)
def lint(session):
    """Lint the codebase."""
    session.install("uv")
    session.run("uv", "pip", "install", "-e", ".")
    session.run("uv", "pip", "install", "ruff>=0.0.287")
    session.run("ruff", "check", *LOCATIONS)


@nox.session(python=DEFAULT_PYTHON)
def format(session):
    """Format the codebase."""
    session.install("uv")
    session.run("uv", "pip", "install", "-e", ".")
    session.run("uv", "pip", "install", "ruff>=0.0.287", "black>=23.7.0")
    session.run("ruff", "format", *LOCATIONS)
    session.run("black", *LOCATIONS)


@nox.session(python=DEFAULT_PYTHON)
def typecheck(session):
    """Run type checking."""
    session.install("uv")
    session.run("uv", "pip", "install", "-e", ".")
    session.run("uv", "pip", "install", "mypy>=1.5.1")
    session.run("mypy", PACKAGE)


@nox.session(python=DEFAULT_PYTHON)
def build(session):
    """Build the package."""
    session.install("uv")
    session.run("uv", "pip", "install", "build")
    session.run("python", "-m", "build")


@nox.session(python=DEFAULT_PYTHON)
def docs(session):
    """Build the documentation."""
    session.install("uv")
    session.run("uv", "pip", "install", "-e", ".")
    session.run("uv", "pip", "install", "pdoc")
    session.run("python", "-m", "pdoc", "--html", "--output-dir", "docs", PACKAGE)