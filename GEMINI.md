# Tinel Project Overview

## Project Summary

Tinel is a Python-based, open-source platform for controlling, optimizing, and analyzing Linux-based systems using AI and LLMs. It provides detailed hardware information through a command-line interface (CLI) and can be used as a server for the Model Context Protocol (MCP). The project is developed by Infenia Private Limited and is licensed under the Apache 2.0 License.

## Key Technologies

*   **Programming Language:** Python 3.11+
*   **Package Manager:** uv
*   **Build System:** hatchling
*   **Testing:** pytest, nox
*   **Linting and Formatting:** ruff, black
*   **Type Checking:** mypy

## Project Structure

The project is organized into the following main directories:

*   `tinel/`: Contains the main source code for the project.
    *   `cli/`: The command-line interface, including argument parsing, command routing, and output formatting.
    *   `hardware/`: The hardware analysis modules, which gather information about the CPU, memory, storage, and other devices.
    *   `tools/`: The tool providers that expose the hardware information to the CLI.
*   `tests/`: Contains the unit, integration, performance, and security tests for the project.
*   `packaging/`: Contains packaging scripts for various distribution formats (Debian, RPM, Docker, etc.).
*   `scripts/`: Contains development and installation scripts.

## Building and Running

### Development Setup

To set up a development environment, clone the repository and use `uv` to install the project in editable mode with development dependencies:

```bash
git clone https://github.com/infenia/tinel.git
cd tinel
uv pip install -e ".[dev]"
```

### Running the CLI

The main entry point for the CLI is `tinel`. You can use it to get hardware information in various formats.

**Get all hardware information:**

```bash
tinel hardware all
```

**Get CPU information:**

```bash
tinel hardware cpu
```

**Get help:**

```bash
tinel --help
```

### Running Tests

Tests are run using `pytest`. You can run all tests with the following command:

```bash
python -m pytest
```

You can also run tests with coverage and generate an HTML report:

```bash
python -m pytest --cov=tinel --cov-report=html
```

The project also uses `nox` to run tests in different Python environments.

## Development Conventions

### Coding Style

The project uses `black` for code formatting and `ruff` for linting. The configuration for these tools can be found in the `pyproject.toml` file.

### Testing

The project has a comprehensive test suite in the `tests/` directory. Tests are organized into unit, integration, performance, and security tests. The project aims for a high test coverage, which is enforced by the `pytest-cov` plugin.

### Contribution Guidelines

Contributions are welcome. Please see the `CONTRIBUTING.md` file for details on how to contribute to the project.
