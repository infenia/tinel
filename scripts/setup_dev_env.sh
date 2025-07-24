#!/bin/bash
# Setup development environment for Tinel using uv
# Copyright 2025 Infenia Private Limited
# Licensed under the Apache License, Version 2.0

set -e

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "uv is not installed. Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    # Add uv to PATH for the current session
    export PATH="$HOME/.cargo/bin:$PATH"
fi

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    uv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
uv pip install -e ".[dev,docs]"

echo "Development environment setup complete!"
echo "To activate the virtual environment in the future, run: source .venv/bin/activate"
