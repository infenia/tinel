#!/bin/bash
#
# Local CI Verification Script
# Mirrors the GitHub workflow checks to verify everything works locally.
# Optimized for local development with caching and speed.
#
# Usage: ./scripts/local_ci_check.sh [options]
#

set -euo pipefail

# --- Configuration ---
# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
TEMP_DIR="$PROJECT_ROOT/.local_ci_temp"

PYTHON_VERSIONS=("3.11" "3.12" "3.13")
DEFAULT_PYTHON="3.12"
COVERAGE_THRESHOLD=100

# --- Flags ---
VERBOSE=false
SKIP_BUILD=false
SKIP_DOCS=false
SKIP_SECURITY=false
CLEAN=false
RUN_ALL_PYTHONS=false
TARGET_PYTHON=""

# --- Helper Functions ---
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_section() { echo -e "\n${PURPLE}=== $1 ===${NC}"; }

show_help() {
    cat << EOF
Local CI Verification Script

Mirrors the GitHub CI workflow for local development, optimized for speed.

USAGE:
    $0 [OPTIONS]

OPTIONS:
    -h, --help              Show this help message.
    -v, --verbose           Enable verbose output for debugging.
    -p, --python VERSION    Specify a single Python version to run checks against (e.g., 3.12).
    --all-pythons           Run checks against all supported Python versions: ${PYTHON_VERSIONS[*]}.
    --clean                 Clean up all virtual environments and temporary files before running.
    --skip-build            Skip build, installation, and integration tests.
    --skip-docs             Skip documentation build.
    --skip-security         Skip security scanning (Safety, Bandit).
    --coverage-threshold N  Set the minimum test coverage threshold (default: $COVERAGE_THRESHOLD).

EXAMPLES:
    $0                      # Run all checks with the default Python ($DEFAULT_PYTHON).
    $0 -p 3.11              # Run all checks with Python 3.11.
    $0 --all-pythons        # Run checks against all supported Python versions.
    $0 --skip-build -v      # Run checks verbosely, skipping the build and integration tests.
    $0 --clean              # Force a clean run, removing all cached environments.

This script runs the following checks, mirroring the GitHub CI:
1. Quality checks (linting, formatting, type checking).
2. Security scanning (dependency and static analysis).
3. Unit tests with coverage.
4. Package build and installation verification.
5. Integration and performance tests.
6. Documentation build.
EOF
}

# --- Core Logic ---

# Parse command line arguments
parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help) show_help; exit 0 ;;
            -v|--verbose) VERBOSE=true; shift ;;
            -p|--python) TARGET_PYTHON="$2"; shift 2 ;;
            --all-pythons) RUN_ALL_PYTHONS=true; shift ;;
            --clean) CLEAN=true; shift ;;
            --skip-build) SKIP_BUILD=true; shift ;;
            --skip-docs) SKIP_DOCS=true; shift ;;
            --skip-security) SKIP_SECURITY=true; shift ;;
            --coverage-threshold) COVERAGE_THRESHOLD="$2"; shift 2 ;;
            *) log_error "Unknown option: $1"; show_help; exit 1 ;;
        esac
    done

    if [[ -n "$TARGET_PYTHON" && "$RUN_ALL_PYTHONS" == "true" ]]; then
        log_error "Cannot use -p and --all-pythons together."
        exit 1
    fi
}

check_prerequisites() {
    log_section "Checking Prerequisites"
    if ! command -v uv &> /dev/null; then
        log_error "'uv' is not found. Please install it: https://github.com/astral-sh/uv"
        exit 1
    fi
    log_success "uv found."

    if [[ ! -f "$PROJECT_ROOT/pyproject.toml" ]]; then
        log_error "Script must be run from the project root directory."
        exit 1
    fi
    log_success "Running in project root."
}

setup_environment() {
    local py_version=$1
    local venv_dir="$PROJECT_ROOT/.venv-$py_version"
    log_section "Setting Up Environment for Python $py_version"

    if [[ ! -d "$venv_dir" ]]; then
        log_info "Creating virtual environment for Python $py_version..."
        if ! uv venv --python "python$py_version" "$venv_dir"; then
            log_error "Failed to create virtual environment for Python $py_version. Is it installed?"
            return 1
        fi

        log_info "Installing dependencies with uv..."
        # Activate venv to install dependencies into it
        source "$venv_dir/bin/activate"
        if ! uv pip install -e ".[dev]"; then
            log_error "Failed to install [dev] dependencies."
            deactivate
            return 1
        fi
        if ! uv pip install safety bandit; then
            log_error "Failed to install security tools."
            deactivate
            return 1
        fi
        deactivate
        log_success "Environment created and dependencies installed."
    else
        log_info "Virtual environment for Python $py_version already exists. Skipping creation."
        log_info "To force a fresh install, run with the --clean flag."
    fi

    # Activate the environment for subsequent commands in the script
    source "$venv_dir/bin/activate"
}

run_quality_checks() {
    log_section "Running Quality Checks (Python $1)"
    local pids=()
    local failed_checks=()

    log_info "Running ruff lint, format check, and mypy in parallel..."

    {
        log_info "🔍 Ruff linting..."
        if uv run --quiet ruff check . > "$TEMP_DIR/ruff.log" 2>&1; then
            echo "ruff:SUCCESS" > "$TEMP_DIR/ruff.result"
        else
            echo "ruff:FAILED" > "$TEMP_DIR/ruff.result"
        fi
    } &
    pids+=($!)

    {
        log_info "📝 Format checking..."
        if uv run --quiet ruff format --check . > "$TEMP_DIR/format.log" 2>&1; then
            echo "format:SUCCESS" > "$TEMP_DIR/format.result"
        else
            echo "format:FAILED" > "$TEMP_DIR/format.result"
        fi
    } &
    pids+=($!)

    {
        log_info "🏷️ Type checking..."
        if uv run --quiet mypy tinel --junit-xml="$TEMP_DIR/mypy-report.xml" > "$TEMP_DIR/mypy.log" 2>&1; then
            echo "mypy:SUCCESS" > "$TEMP_DIR/mypy.result"
        else
            echo "mypy:FAILED" > "$TEMP_DIR/mypy.result"
        fi
    } &
    pids+=($!)

    for pid in "${pids[@]}"; do wait "$pid"; done

    for check in ruff format mypy; do
        result=$(cat "$TEMP_DIR/$check.result")
        if [[ "$result" == *"SUCCESS"* ]]; then
            log_success "$check passed."
        else
            log_error "$check failed. See logs for details."
            failed_checks+=("$check")
            if [[ "$VERBOSE" == "true" ]]; then
                echo "--- $check output ---"
                cat "$TEMP_DIR/$check.log"
                echo "--- end $check output ---"
            fi
        fi
    done

    if [[ ${#failed_checks[@]} -gt 0 ]]; then
        log_error "Quality checks failed: ${failed_checks[*]}"
        return 1
    fi
    log_success "All quality checks passed."
}

run_security_checks() {
    if [[ "$SKIP_SECURITY" == "true" ]]; then
        log_warning "Skipping security checks."
        return 0
    fi

    log_section "Running Security Scans (Python $1)"
    local pids=()

    {
        log_info "🛡️ Running Safety for dependency vulnerabilities..."
        if uv run --quiet safety check --json --output "$TEMP_DIR/safety-report.json" > "$TEMP_DIR/safety.log" 2>&1; then
            echo "safety:SUCCESS" > "$TEMP_DIR/safety.result"
        else
            # Safety exits non-zero if vulns are found, treat as a warning
            echo "safety:WARNING" > "$TEMP_DIR/safety.result"
        fi
    } &
    pids+=($!)

    {
        log_info "🕵️ Running Bandit for static security analysis..."
        if uv run --quiet bandit -r tinel -f json -o "$TEMP_DIR/bandit-report.json" > "$TEMP_DIR/bandit.log" 2>&1; then
            echo "bandit:SUCCESS" > "$TEMP_DIR/bandit.result"
        else
            # Bandit exits non-zero if issues are found, treat as a warning
            echo "bandit:WARNING" > "$TEMP_DIR/bandit.result"
        fi
    } &
    pids+=($!)

    for pid in "${pids[@]}"; do wait "$pid"; done

    log_info "Security scanning complete. Check reports for any warnings."
    if [[ -s "$TEMP_DIR/safety-report.json" ]]; then
        log_warning "Safety found potential vulnerabilities. Check 'safety-report.json'."
    else
        log_success "Safety found no vulnerabilities."
    fi
    if [[ $(jq '.results | length' "$TEMP_DIR/bandit-report.json") -gt 0 ]]; then
        log_warning "Bandit found potential issues. Check 'bandit-report.json'."
    else
        log_success "Bandit found no issues."
    fi
}

run_tests() {
    log_section "Running Unit Tests with Coverage (Python $1)"
    export PYTEST_ADDOPTS="--strict-markers --strict-config --tb=short"

    local pytest_cmd="uv run --quiet pytest \
        --cov=tinel \
        --cov-report=xml \
        --cov-report=term-missing \
        --cov-fail-under=$COVERAGE_THRESHOLD \
        --junit-xml=$TEMP_DIR/junit-$1.xml \
        tests/unit"

    if [[ "$VERBOSE" == "true" ]]; then
        pytest_cmd="$pytest_cmd -v"
    fi

    if $pytest_cmd > "$TEMP_DIR/test.log" 2>&1; then
        log_success "All unit tests passed with sufficient coverage."
    else
        log_error "Unit tests failed or coverage below threshold."
        if [[ "$VERBOSE" == "true" ]]; then
            echo "--- Test output ---"
            cat "$TEMP_DIR/test.log"
            echo "--- End test output ---"
        else
            echo "Run with -v for detailed test output."
        fi
        return 1
    fi
}

run_build_verification() {
    if [[ "$SKIP_BUILD" == "true" ]]; then
        log_warning "Skipping build and integration tests."
        return 0
    fi

    log_section "Running Build & Integration Tests (Python $1)"
    local overall_status=0

    log_info "Building package..."
    if ! uv run --quiet python -m build --wheel --sdist > "$TEMP_DIR/build.log" 2>&1; then
        log_error "Package build failed."
        [[ "$VERBOSE" == "true" ]] && cat "$TEMP_DIR/build.log"
        return 1
    fi
    log_success "Package built successfully."

    log_info "Verifying package with twine..."
    if ! uv run --quiet python -m twine check "dist/*" > "$TEMP_DIR/twine.log" 2>&1; then
        log_error "Package verification failed."
        [[ "$VERBOSE" == "true" ]] && cat "$TEMP_DIR/twine.log"
        return 1
    fi
    log_success "Package verification passed."

    # Integration tests
    if [[ -d "$PROJECT_ROOT/tests/integration" ]]; then
        log_info "Running integration tests..."
        if uv run --quiet pytest tests/integration/ -v --tb=short > "$TEMP_DIR/integration.log" 2>&1; then
            log_success "Integration tests passed."
        else
            log_error "Integration tests failed."
            [[ "$VERBOSE" == "true" ]] && cat "$TEMP_DIR/integration.log"
            overall_status=1
        fi
    fi

    # Performance tests
    if [[ -d "$PROJECT_ROOT/tests/performance" ]]; then
        log_info "Running performance tests..."
        if uv run --quiet pytest tests/performance/ -v --tb=short > "$TEMP_DIR/performance.log" 2>&1; then
            log_success "Performance tests passed."
        else
            log_warning "Performance tests failed (non-blocking)."
            [[ "$VERBOSE" == "true" ]] && cat "$TEMP_DIR/performance.log"
        fi
    fi

    return $overall_status
}

run_documentation_build() {
    if [[ "$SKIP_DOCS" == "true" ]]; then
        log_warning "Skipping documentation build."
        return 0
    fi

    log_section "Running Documentation Build (Python $1)"

    log_info "Installing documentation dependencies..."
    if ! uv pip install -e ".[docs]" --quiet; then
        log_error "Failed to install [docs] dependencies."
        return 1
    fi

    log_info "Building documentation with pdoc..."
    rm -rf "$PROJECT_ROOT/docs" # Clean previous build
    if uv run --quiet python -m pdoc --output-dir docs tinel > "$TEMP_DIR/docs.log" 2>&1; then
        log_success "Documentation built successfully."
    else
        log_error "Documentation build failed."
        [[ "$VERBOSE" == "true" ]] && cat "$TEMP_DIR/docs.log"
        return 1
    fi
}

cleanup() {
    log_section "Cleaning Up"
    if [[ -d "$TEMP_DIR" ]]; then
        log_info "Removing temporary directory: $TEMP_DIR"
        rm -rf "$TEMP_DIR"
    fi
    for py_version in "${PYTHON_VERSIONS[@]}"; do
        local venv_dir="$PROJECT_ROOT/.venv-$py_version"
        if [[ -d "$venv_dir" ]]; then
            log_info "Removing virtual environment: $venv_dir"
            rm -rf "$venv_dir"
        fi
    done
    log_info "To preserve caches, 'uv cache clean' is not run automatically."
    log_success "Cleanup complete."
}

# --- Main Execution ---
main() {
    cd "$PROJECT_ROOT"
    parse_arguments "$@"
    check_prerequisites

    if [[ "$CLEAN" == "true" ]]; then
        cleanup
    fi

    mkdir -p "$TEMP_DIR"

    local target_pythons=()
    if [[ "$RUN_ALL_PYTHONS" == "true" ]]; then
        target_pythons=("${PYTHON_VERSIONS[@]}")
    elif [[ -n "$TARGET_PYTHON" ]]; then
        target_pythons=("$TARGET_PYTHON")
    else
        target_pythons=("$DEFAULT_PYTHON")
    fi

    local overall_status=0
    for py_version in "${target_pythons[@]}"; do
        if ! setup_environment "$py_version"; then
            overall_status=1
            continue # Skip to next python version if setup fails
        fi

        run_quality_checks "$py_version" || overall_status=1
        run_security_checks "$py_version" # Warnings are non-blocking

        if [[ "$overall_status" -eq 0 ]]; then
            run_tests "$py_version" || overall_status=1
        else
            log_warning "Skipping tests for Python $py_version due to earlier failures."
        fi

        # Build and docs only run for the default python version if not otherwise specified
        if [[ "$py_version" == "$DEFAULT_PYTHON" && ${#target_pythons[@]} -eq 1 ]]; then
            if [[ "$overall_status" -eq 0 ]]; then
                run_build_verification "$py_version" || overall_status=1
                run_documentation_build "$py_version" || overall_status=1
            else
                log_warning "Skipping build and docs checks due to earlier failures."
            fi
        fi

        # Deactivate the virtual environment for this iteration
        if command -v deactivate &> /dev/null; then
            deactivate
        fi
    done

    # --- Summary ---
    log_section "Local CI Summary"
    if [[ "$overall_status" -eq 0 ]]; then
        log_success "🎉 All checks passed!"
        echo -e "${GREEN}Your code is ready to be pushed. 🚀${NC}"
    else
        log_error "❌ Some checks failed. Please review the logs above."
        echo -e "${YELLOW}Run with -v for more details on failed steps.${NC}"
        exit 1
    fi
}

main "$@"
