# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Tinel is a next-generation open-source platform designed to control, optimize, and analyze Linux-based systems using AI and LLMs. It implements a Model Context Protocol (MCP) server that provides detailed hardware information through various system utilities and filesystem interfaces.

## Development Commands

### Package Management
- Use `uv` as the package manager (not pip)
- Install dev dependencies: `uv pip install -e ".[dev]"`

### Testing
- Run all tests: `python -m pytest`
- Run with coverage: `python -m pytest --cov=tinel --cov-report=html`
- Run tests across multiple Python versions: `nox -s tests`
- Coverage threshold is set to 90%

### Code Quality
- Format code: `python -m ruff format .`
- Lint code: `python -m ruff check .`
- Auto-fix lint issues: `python -m ruff check --fix .`
- Type checking: `python -m mypy tinel`
- Run all quality checks: `nox -s check`

### Build and Documentation
- Build package: `python -m build` or `nox -s build`
- Generate docs: `python -m pdoc --html --output-dir docs tinel`

### Local Development Scripts

#### Quick Development Helper
Use `scripts/dev.sh` for common development tasks:
- `./scripts/dev.sh setup` - Setup complete development environment
- `./scripts/dev.sh fix` - Auto-fix linting issues and format code
- `./scripts/dev.sh test-cov` - Run tests with coverage
- `./scripts/dev.sh coverage` - Generate detailed coverage reports (HTML/XML)
- `./scripts/dev.sh check` - Run all quality checks (lint + typecheck + test)
- `./scripts/dev.sh pre-commit` - Run pre-commit checks
- `./scripts/dev.sh ci` - Run full CI verification locally
- `./scripts/dev.sh clean` - Clean build artifacts and caches

#### Full CI Verification
Use `scripts/local_ci_check.sh` to run comprehensive checks that mirror the GitHub workflow:
- `./scripts/local_ci_check.sh` - Run all CI checks locally
- `./scripts/local_ci_check.sh -v` - Verbose mode with detailed output
- `./scripts/local_ci_check.sh -p 3.11` - Use specific Python version
- `./scripts/local_ci_check.sh --skip-build` - Skip build verification
- `./scripts/local_ci_check.sh --help` - Show all options

**Recommended workflow:**
1. `./scripts/dev.sh setup` - One-time setup (first run)
2. `./scripts/dev.sh fix` - Fix formatting and linting
3. `./scripts/dev.sh test-cov` - Run tests with coverage
4. `./scripts/local_ci_check.sh` - Verify everything works before push

#### Additional Setup
Use `scripts/setup_dev_env.sh` for complete environment setup:
- `./scripts/setup_dev_env.sh` - Install uv, create venv, install dependencies

## Architecture Overview

### Core Components

1. **System Interface Layer** (`tinel/interfaces.py`)
   - Abstract interfaces for system interactions
   - `SystemInterface` for command execution and file operations
   - `ToolProvider` for MCP tool implementations

2. **Hardware Analysis** (`tinel/hardware/`)
   - `DeviceAnalyzer`: Unified analyzer for all hardware components
   - `CPUAnalyzer`: Specialized CPU information gathering
   - Extensible architecture for additional hardware analyzers

3. **CLI Framework** (`tinel/cli/`)
   - `main.py`: Entry point with argument validation and error handling
   - `commands/`: Command routing and execution
   - `formatters.py`: Output formatting (JSON, YAML, table formats)
   - `error_handler.py`: Centralized error handling

4. **MCP Tools** (`tinel/tools/`)
   - `hardware_tools.py`: Hardware information tool providers
   - `base.py`: Base classes for tool implementations
   - Each tool follows the MCP protocol specification

### Key Design Patterns

- **Abstract Base Classes**: Extensive use of ABC for interface definitions
- **Dependency Injection**: System interfaces are injected for testability
- **Lazy Loading**: Command router is lazily loaded to improve startup time
- **Error Handling**: Comprehensive error handling with user-friendly messages

### Entry Points

- Main CLI: `tinel` command (defined in pyproject.toml)
- Python module: `python -m tinel`
- MCP Server: `python -m tinel.server` (implied from docs)

## Development Guidelines

### Code Style
- Line length: 88 characters (Black standard)
- Python versions: 3.11, 3.12, 3.13
- Use type hints throughout (`disallow_untyped_defs = true`)
- Import order: standard library, third-party, first-party (tinel)

### Testing
- Tests located in `tests/` directory
- Test files follow `test_*.py` pattern
- Coverage reporting enabled by default
- Use pytest fixtures for common test setup

### System Requirements
- Linux operating system (tested on Ubuntu, Debian, CentOS, Fedora)
- Standard Linux utilities: `lscpu`, `lspci`, `lsusb`, `lsblk`, `df`, `ip`
- Optional utilities for enhanced information: `dmidecode`, `lshw`, `nvidia-smi`
- Some operations require sudo privileges

### Hardware Information Sources
The application gathers data from multiple kernel interfaces:
- `/proc/cpuinfo`, `/proc/meminfo`
- `/sys/devices/` device tree
- System utilities (lscpu, lspci, etc.)
- Hardware detection tools (dmidecode, lshw)

## Development Workflow

1. Install dependencies: `uv pip install -e ".[dev]"`
2. Make changes and add tests
3. Run quality checks: `nox -s check`
4. Run tests: `python -m pytest`
5. Build if needed: `python -m build`

The project uses Nox for automation across multiple Python versions and provides both Nox sessions and shell scripts for common development tasks.