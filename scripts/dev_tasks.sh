#!/bin/bash
# Development tasks for Tinel using uv
# Copyright 2025 Infenia Private Limited
# Licensed under the Apache License, Version 2.0

set -e

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Virtual environment not activated. Please run: source .venv/bin/activate"
    exit 1
fi

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "uv is not installed. Please run: scripts/setup_dev_env.sh"
    exit 1
fi

# Parse command line arguments
case "$1" in
    install)
        echo "Installing dependencies..."
        uv pip install -e ".[dev]"
        ;;
    test)
        echo "Running tests..."
        python -m pytest
        ;;
    lint)
        echo "Running linter..."
        python -m ruff check tinel tests
        ;;
    format)
        echo "Formatting code..."
        python -m ruff format tinel tests
        python -m black tinel tests
        ;;
    typecheck)
        echo "Running type checker..."
        python -m mypy tinel
        ;;
    build)
        echo "Building package..."
        python -m build
        ;;
    clean)
        echo "Cleaning build artifacts..."
        rm -rf build/ dist/ *.egg-info/
        find . -type d -name __pycache__ -exec rm -rf {} +
        find . -type f -name "*.pyc" -delete
        ;;
    *)
        echo "Usage: $0 {install|test|lint|format|typecheck|build|clean}"
        exit 1
        ;;
esac

echo "Done!"
