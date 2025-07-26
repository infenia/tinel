#!/bin/bash
#
# Development Helper Script
# Quick commands for common development tasks
# Usage: ./scripts/dev.sh <command>
#

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

# Helper functions
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

show_help() {
    cat << EOF
Development Helper Script

USAGE:
    $0 <command>

COMMANDS:
    setup           Setup development environment
    lint            Run linting checks
    format          Format code with ruff
    fix             Auto-fix linting issues and format code
    test            Run tests
    test-cov        Run tests with coverage
    coverage        Generate detailed coverage report
    typecheck       Run type checking with mypy
    security        Run security scans
    build           Build package
    docs            Build documentation
    clean           Clean build artifacts and caches
    
    check           Run all quality checks (lint + typecheck + test)
    ci              Run full CI verification locally
    pre-commit      Run pre-commit checks (format + lint + test)
    
    help            Show this help message

EXAMPLES:
    $0 setup        # First-time setup
    $0 fix          # Fix formatting and linting
    $0 test-cov     # Run tests with coverage
    $0 check        # Run all quality checks
    $0 ci           # Full CI verification

EOF
}

# Commands
cmd_setup() {
    log_info "Setting up development environment..."
    uv pip install -e ".[dev]"
    uv pip install safety bandit
    log_success "Development environment ready!"
}

cmd_lint() {
    log_info "Running linting checks..."
    uv run ruff check .
    log_success "Linting passed!"
}

cmd_format() {
    log_info "Formatting code..."
    uv run ruff format .
    log_success "Code formatted!"
}

cmd_fix() {
    log_info "Auto-fixing linting issues and formatting..."
    uv run ruff check --fix .
    uv run ruff format .
    log_success "Code fixed and formatted!"
}

cmd_test() {
    log_info "Running tests..."
    uv run pytest
    log_success "Tests passed!"
}

cmd_test_cov() {
    log_info "Running tests with coverage..."
    uv run pytest --cov=tinel --cov-report=term-missing
    log_success "Tests with coverage completed!"
}

cmd_coverage() {
    log_info "Generating detailed coverage report..."
    uv run pytest --cov=tinel --cov-report=term-missing --cov-report=html --cov-report=xml
    log_success "Coverage reports generated!"
    echo "HTML report: htmlcov/index.html"
    echo "XML report: coverage.xml"
}

cmd_typecheck() {
    log_info "Running type checking..."
    uv run mypy tinel
    log_success "Type checking passed!"
}

cmd_security() {
    log_info "Running security scans..."
    uv run safety check || log_error "Safety warnings detected"
    uv run bandit -r tinel -ll || log_error "Bandit warnings detected"
    log_success "Security scans completed!"
}

cmd_build() {
    log_info "Building package..."
    python -m build
    python -m twine check dist/*
    log_success "Package built and verified!"
}

cmd_docs() {
    log_info "Building documentation..."
    python -m pdoc --html --output-dir docs tinel
    log_success "Documentation built!"
}

cmd_clean() {
    log_info "Cleaning build artifacts and caches..."
    rm -rf build/ dist/ *.egg-info/
    rm -rf .pytest_cache/ .mypy_cache/ .ruff_cache/
    rm -rf docs/ .coverage coverage.xml
    rm -rf .local_ci_temp/
    find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
    log_success "Cleaned up!"
}

cmd_check() {
    log_info "Running all quality checks..."
    cmd_lint
    cmd_typecheck
    cmd_test_cov
    log_success "All quality checks passed!"
}

cmd_ci() {
    log_info "Running full CI verification..."
    ./scripts/local_ci_check.sh
}

cmd_setup() {
    log_info "Setting up development environment..."
    
    # Check if uv is installed
    if ! command -v uv &> /dev/null; then
        log_info "Installing uv..."
        curl -LsSf https://astral.sh/uv/install.sh | sh
        export PATH="$HOME/.cargo/bin:$PATH"
    fi
    
    # Create virtual environment if it doesn't exist
    if [ ! -d ".venv" ]; then
        log_info "Creating virtual environment..."
        uv venv
    fi
    
    # Install dependencies
    log_info "Installing dependencies..."
    uv pip install -e ".[dev]"
    
    log_success "Development environment setup complete!"
    echo "To activate: source .venv/bin/activate"
}

cmd_pre_commit() {
    log_info "Running pre-commit checks..."
    cmd_format
    cmd_lint
    cmd_test
    log_success "Pre-commit checks passed!"
}

# Main execution
if [[ $# -eq 0 ]]; then
    show_help
    exit 1
fi

command="$1"

case "$command" in
    setup)          cmd_setup ;;
    lint)           cmd_lint ;;
    format)         cmd_format ;;
    fix)            cmd_fix ;;
    test)           cmd_test ;;
    test-cov)       cmd_test_cov ;;
    coverage)       cmd_coverage ;;
    typecheck)      cmd_typecheck ;;
    security)       cmd_security ;;
    build)          cmd_build ;;
    docs)           cmd_docs ;;
    clean)          cmd_clean ;;
    check)          cmd_check ;;
    ci)             cmd_ci ;;
    pre-commit)     cmd_pre_commit ;;
    help|--help|-h) show_help ;;
    *)
        log_error "Unknown command: $command"
        echo
        show_help
        exit 1
        ;;
esac