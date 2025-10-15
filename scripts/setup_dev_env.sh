#!/bin/bash
# Setup development environment for Tinel using uv
# Copyright 2025 Infenia Private Limited
# Licensed under the Apache License, Version 2.0

set -e

UV_CMD="${TINEL_UV_PATH:-uv}"

# Check if uv is installed
if ! command -v "$UV_CMD" &> /dev/null; then
    echo "uv not found or TINEL_UV_PATH is not correctly set. Please ensure uv is in your PATH or set TINEL_UV_PATH."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    "$UV_CMD" venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
"$UV_CMD" pip install -e ".[dev,docs]"

echo "Development environment setup complete!"
echo "To activate the virtual environment in the future, run: source .venv/bin/activate"
