# Contributing to Infenix

Thank you for your interest in contributing to Infenix! This document provides guidelines for contributing to the project.

## Code of Conduct

This project adheres to a code of conduct. By participating, you are expected to uphold this code. Please report unacceptable behavior to the project maintainers.

## How to Contribute

### Reporting Issues

Before creating an issue, please:

1. Check if the issue already exists in the [issue tracker](https://github.com/infenia/infenix/issues)
2. Provide a clear and descriptive title
3. Include steps to reproduce the issue
4. Provide system information (Linux distribution, Python version, etc.)
5. Include relevant error messages or logs

### Submitting Changes

1. **Fork the repository** and create your branch from `main`
2. **Make your changes** following the coding standards below
3. **Add tests** for any new functionality
4. **Ensure all tests pass** by running `pytest`
5. **Update documentation** if necessary
6. **Submit a pull request** with a clear description of your changes

### Development Setup

1. Clone your fork:

   ```bash
   git clone https://github.com/your-username/infenix.git
   cd infenix
   ```

2. Install Python 3.11+:

   ```bash
   # Make sure you have Python 3.11+ installed
   python --version
   ```

3. Install dependencies:

   ```bash
   uv pip install -e ".[dev]"
   ```

4. Run tests to ensure everything works:
   ```bash
   python -m pytest
   ```

## Coding Standards

### Python Code Style

- Follow PEP 8 style guidelines
- Use type hints for all function parameters and return values
- Maximum line length: 88 characters
- Use descriptive variable and function names

### Code Quality Tools

We use several tools to maintain code quality:

- **Black**: Code formatting
- **Ruff**: Fast Python linter
- **MyPy**: Static type checking
- **Pytest**: Testing framework

Run these tools before submitting:

```bash
# Format code
python -m black .
python -m ruff format .

# Lint code
python -m ruff check .

# Type checking
python -m mypy infenix

# Run tests
python -m pytest --cov=infenix
```

### Testing

- Write tests for all new functionality
- Maintain test coverage above 95%
- Use descriptive test names that explain what is being tested
- Group related tests in classes
- Mock external dependencies (system commands, file operations)

### Documentation

- Update README.md for user-facing changes
- Add docstrings to all public functions and classes
- Use Google-style docstrings
- Update type hints when changing function signatures

## Project Structure

```
infenix/
├── infenix/                # Main package
│   ├── __init__.py
│   └── server.py           # MCP server implementation
├── tests/                  # Test files
│   ├── __init__.py
│   └── test_server.py      # Comprehensive tests
├── .github/                # GitHub workflows
│   └── workflows/
│       └── ci.yml          # CI/CD pipeline
├── docs/                   # Documentation (if needed)
├── LICENSE                 # Apache 2.0 license
├── README.md               # Project documentation
├── CONTRIBUTING.md         # This file
├── pyproject.toml          # Project configuration
└── noxfile.py              # Multi-version testing
```

## Commit Message Guidelines

Use clear and descriptive commit messages:

- Use the present tense ("Add feature" not "Added feature")
- Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit the first line to 72 characters or less
- Reference issues and pull requests liberally after the first line

Examples:

```
Add support for GPU temperature monitoring

- Implement nvidia-smi temperature parsing
- Add tests for temperature data extraction
- Update documentation with new feature

Fixes #123
```

## Release Process

Releases are handled by maintainers:

1. Update version in `pyproject.toml`
2. Update CHANGELOG.md
3. Create a git tag
4. Publish to PyPI
5. Create GitHub release

## Getting Help

- Check the [README](README.md) for basic usage
- Look at existing [issues](https://github.com/infenia/infenix/issues)
- Create a new issue for questions or problems

## License

By contributing to Infenix, you agree that your contributions will be licensed under the Apache License 2.0.
