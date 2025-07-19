# Project Structure

## Core Components

- **infenix/**: Main package directory
  - \***\*init**.py\*\*: Package initialization
  - **server.py**: Core MCP server implementation with hardware information tools

## Configuration & Build Files

- **pyproject.toml**: Project metadata, dependencies, and build configuration
- **requirements.txt**: Project dependencies
- **requirements-dev.txt**: Development dependencies
- **noxfile.py**: Test automation configuration for multiple Python versions
- **tox.ini**: Additional test configuration

## Testing

- **tests/**: Test directory
  - \***\*init**.py\*\*: Test package initialization
  - **test_server.py**: Tests for server functionality
- **test_server.py**: Root-level test file (appears to be a duplicate)

## CI/CD

- **.github/workflows/**: GitHub Actions workflows
  - **ci.yml**: Continuous integration configuration

## Package Metadata

- **infenix.egg-info/**: Package metadata (generated)

## Documentation

- **README.md**: Project documentation and usage instructions
- **mcp-config-example.json**: Example MCP configuration

## Code Style & Quality

The project follows these code style conventions:

- Line length: 88 characters (Black default)
- Python target version: 3.11
- Type annotations: Required for all functions
- Linting: Uses ruff with multiple rule sets (E, F, I, N, W, B, C4, SIM, ERA, PL)
- Formatting: Black and ruff format

## Architecture Pattern

The project follows a tool-based architecture pattern where:

1. The MCP server exposes a set of tools for hardware information
2. Each tool is implemented as a function that gathers specific hardware data
3. The server handles tool registration, listing, and execution
4. System commands are executed via subprocess with proper error handling
5. Results are formatted as structured JSON responses
