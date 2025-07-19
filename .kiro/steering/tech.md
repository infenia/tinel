# Technical Stack

## Build System & Package Management

- **Python**: Requires Python 3.11+ (supports 3.11 and 3.12)
- **uv**: Fast Python package manager and resolver
- **Nox**: Used for test automation across multiple Python versions

## Dependencies

- **mcp**: Model Context Protocol library (>=1.0.0)
- **psutil**: Python system utilities for hardware information (>=5.9.0)

## Development Dependencies

- **pytest/pytest-cov**: Testing and code coverage
- **black**: Code formatting
- **ruff**: Fast Python linter
- **mypy**: Static type checking

## System Requirements

- Linux operating system
- Standard Linux utilities: `lscpu`, `lspci`, `lsusb`, `lsblk`, `df`, `ip`
- Optional utilities: `dmidecode`, `lshw`, `nvidia-smi`

## Common Commands

### Installation

```bash
# Install in development mode
uv pip install -e .

# Install with development dependencies
uv pip install -e ".[dev]"
```

### Development

```bash
# Run tests
python -m pytest
nox -s tests  # Test on multiple Python versions

# Linting
python -m ruff check .
python -m mypy infenix

# Formatting
python -m ruff format .
python -m black .

# Combined commands via nox
nox -s lint
nox -s format
nox -s typecheck
```

### Building

```bash
# Using build module
python -m build

# Using nox
nox -s build
```

### Running

```bash
# Run directly
python -m infenix.server

# Run as installed package
infenix
```
