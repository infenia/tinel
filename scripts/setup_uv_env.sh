#!/bin/bash
# Setup script for uv-based development environment

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "uv is not installed. Installing uv..."
    # Install uv using the recommended method
    curl -LsSf https://astral.sh/uv/install.sh | sh
fi

# Create a virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    uv venv
fi

# Install the package in development mode with all dependencies
echo "Installing package in development mode..."
uv pip install -e ".[dev]"

echo "Development environment setup complete!"
echo "You can activate the virtual environment with: source .venv/bin/activate"