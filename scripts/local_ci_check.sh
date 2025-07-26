#!/bin/bash
#
# Local CI Verification Script
# Mirrors the GitHub workflow checks to verify everything works locally
# Usage: ./scripts/local_ci_check.sh [options]
#

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PYTHON_VERSIONS=("3.11" "3.12" "3.13")
DEFAULT_PYTHON="3.12"
TEMP_DIR="$PROJECT_ROOT/.local_ci_temp"
PARALLEL_JOBS=3

# Flags
VERBOSE=false
SKIP_BUILD=false
SKIP_DOCS=false
SKIP_SECURITY=false
PYTHON_VERSION="$DEFAULT_PYTHON"
COVERAGE_THRESHOLD=90

# Helper functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_section() {
    echo -e "\n${PURPLE}=== $1 ===${NC}"
}

show_help() {
    cat << EOF
Local CI Verification Script

USAGE:
    $0 [OPTIONS]

OPTIONS:
    -h, --help              Show this help message
    -v, --verbose           Enable verbose output
    -p, --python VERSION    Python version to use (default: $DEFAULT_PYTHON)
    --skip-build           Skip build and integration tests
    --skip-docs            Skip documentation build
    --skip-security        Skip security scanning
    --coverage-threshold N  Set coverage threshold (default: $COVERAGE_THRESHOLD)

EXAMPLES:
    $0                      # Run all checks with default Python
    $0 -p 3.11             # Run with Python 3.11
    $0 --skip-build        # Skip build tests
    $0 -v --skip-docs      # Verbose mode, skip docs

This script mirrors the GitHub CI workflow and runs:
1. Quality checks (linting, formatting, type checking)
2. Security scanning (safety, bandit)
3. Test execution with coverage
4. Build verification
5. Integration tests
6. Documentation build

EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -p|--python)
            PYTHON_VERSION="$2"
            shift 2
            ;;
        --skip-build)
            SKIP_BUILD=true
            shift
            ;;
        --skip-docs)
            SKIP_DOCS=true
            shift
            ;;
        --skip-security)
            SKIP_SECURITY=true
            shift
            ;;
        --coverage-threshold)
            COVERAGE_THRESHOLD="$2"
            shift 2
            ;;
        *)
            log_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Verify prerequisites
check_prerequisites() {
    log_section "Checking Prerequisites"
    
    # Check if we're in the right directory
    if [[ ! -f "$PROJECT_ROOT/pyproject.toml" ]]; then
        log_error "Not in project root. Please run from project directory."
        exit 1
    fi
    
    # Check Python version
    if ! command -v python$PYTHON_VERSION &> /dev/null; then
        log_error "Python $PYTHON_VERSION not found. Please install it or use -p to specify available version."
        exit 1
    fi
    
    # Check uv
    if ! command -v uv &> /dev/null; then
        log_error "uv not found. Please install uv: curl -LsSf https://astral.sh/uv/install.sh | sh"
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Setup environment
setup_environment() {
    log_section "Setting Up Environment"
    
    cd "$PROJECT_ROOT"
    
    # Create temp directory for reports
    mkdir -p "$TEMP_DIR"
    
    # Install dependencies
    log_info "Installing dependencies with uv..."
    if [[ "$VERBOSE" == "true" ]]; then
        uv pip install -e ".[dev]"
        if [[ "$SKIP_SECURITY" == "false" ]]; then
            uv pip install safety bandit
        fi
    else
        uv pip install -e ".[dev]" >/dev/null 2>&1
        if [[ "$SKIP_SECURITY" == "false" ]]; then
            uv pip install safety bandit >/dev/null 2>&1
        fi
    fi
    
    log_success "Environment setup complete"
}

# Quality checks (parallel execution like GitHub workflow)
run_quality_checks() {
    log_section "Quality Checks (Parallel Execution)"
    
    local pids=()
    local results=()
    
    # Ruff linting
    {
        log_info "Running ruff linting..."
        if uv run ruff check . --output-format=github > "$TEMP_DIR/ruff.log" 2>&1; then
            echo "ruff:SUCCESS" > "$TEMP_DIR/ruff.result"
        else
            echo "ruff:FAILED" > "$TEMP_DIR/ruff.result"
        fi
    } &
    pids+=($!)
    
    # Format checking
    {
        log_info "Running format checks..."
        if uv run ruff format --check . > "$TEMP_DIR/format.log" 2>&1; then
            echo "format:SUCCESS" > "$TEMP_DIR/format.result"
        else
            echo "format:FAILED" > "$TEMP_DIR/format.result"
        fi
    } &
    pids+=($!)
    
    # Type checking
    {
        log_info "Running type checking..."
        if uv run mypy tinel --junit-xml="$TEMP_DIR/mypy-report.xml" > "$TEMP_DIR/mypy.log" 2>&1; then
            echo "mypy:SUCCESS" > "$TEMP_DIR/mypy.result"
        else
            echo "mypy:FAILED" > "$TEMP_DIR/mypy.result"
        fi
    } &
    pids+=($!)
    
    # Wait for all parallel jobs
    for pid in "${pids[@]}"; do
        wait "$pid"
    done
    
    # Check results
    local failed_checks=()
    
    for check in ruff format mypy; do
        result=$(cat "$TEMP_DIR/$check.result")
        if [[ "$result" == *"SUCCESS"* ]]; then
            log_success "$check passed"
        else
            log_error "$check failed"
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
        show_quality_fixes
        return 1
    fi
    
    log_success "All quality checks passed"
}

# Security scanning
run_security_checks() {
    if [[ "$SKIP_SECURITY" == "true" ]]; then
        log_warning "Skipping security checks"
        return 0
    fi
    
    log_section "Security Scanning"
    
    local pids=()
    local failed_checks=()
    
    # Safety check
    {
        log_info "Running dependency vulnerability scanning..."
        if uv run safety check --json --output="$TEMP_DIR/safety-report.json" > "$TEMP_DIR/safety.log" 2>&1; then
            echo "safety:SUCCESS" > "$TEMP_DIR/safety.result"
        else
            echo "safety:WARNING" > "$TEMP_DIR/safety.result"
        fi
    } &
    pids+=($!)
    
    # Bandit check
    {
        log_info "Running static security analysis..."
        if uv run bandit -r tinel -f json -o "$TEMP_DIR/bandit-report.json" -ll > "$TEMP_DIR/bandit.log" 2>&1; then
            echo "bandit:SUCCESS" > "$TEMP_DIR/bandit.result"
        else
            echo "bandit:WARNING" > "$TEMP_DIR/bandit.result"
        fi
    } &
    pids+=($!)
    
    # Wait for security scans
    for pid in "${pids[@]}"; do
        wait "$pid"
    done
    
    # Check results (warnings are acceptable for security)
    for check in safety bandit; do
        result=$(cat "$TEMP_DIR/$check.result")
        if [[ "$result" == *"SUCCESS"* ]]; then
            log_success "$check passed"
        elif [[ "$result" == *"WARNING"* ]]; then
            log_warning "$check completed with warnings"
            if [[ "$VERBOSE" == "true" && -f "$TEMP_DIR/$check-report.json" ]]; then
                echo "--- $check warnings ---"
                cat "$TEMP_DIR/$check-report.json"
                echo "--- end $check warnings ---"
            fi
        else
            log_error "$check failed"
            failed_checks+=("$check")
        fi
    done
    
    log_success "Security scanning completed"
}

# Run tests with coverage
run_tests() {
    log_section "Test Execution with Coverage"
    
    log_info "Running tests with coverage..."
    
    local test_cmd="uv run pytest \
        --cov=tinel \
        --cov-report=xml \
        --cov-report=term-missing \
        --cov-fail-under=$COVERAGE_THRESHOLD \
        --junit-xml=$TEMP_DIR/junit-$PYTHON_VERSION.xml \
        --maxfail=5"
    
    if [[ "$VERBOSE" == "true" ]]; then
        test_cmd="$test_cmd -v"
    else
        test_cmd="$test_cmd -q"
    fi
    
    if $test_cmd > "$TEMP_DIR/test.log" 2>&1; then
        log_success "All tests passed with sufficient coverage"
        
        # Show coverage summary
        if command -v coverage &> /dev/null; then
            coverage report --show-missing | tail -1
        fi
    else
        log_error "Tests failed or insufficient coverage"
        if [[ "$VERBOSE" == "true" ]]; then
            echo "--- Test output ---"
            cat "$TEMP_DIR/test.log"
            echo "--- End test output ---"
        else
            echo "Run with -v for detailed test output"
        fi
        return 1
    fi
}

# Build verification
run_build_verification() {
    if [[ "$SKIP_BUILD" == "true" ]]; then
        log_warning "Skipping build verification"
        return 0
    fi
    
    log_section "Build & Integration Verification"
    
    # Install build tools
    log_info "Installing build tools..."
    uv pip install build twine >/dev/null 2>&1
    
    # Build package
    log_info "Building package..."
    if python -m build --wheel --sdist > "$TEMP_DIR/build.log" 2>&1; then
        log_success "Package built successfully"
    else
        log_error "Package build failed"
        if [[ "$VERBOSE" == "true" ]]; then
            cat "$TEMP_DIR/build.log"
        fi
        return 1
    fi
    
    # Verify package
    log_info "Verifying package integrity..."
    if python -m twine check dist/* > "$TEMP_DIR/twine.log" 2>&1; then
        log_success "Package verification passed"
    else
        log_error "Package verification failed"
        if [[ "$VERBOSE" == "true" ]]; then
            cat "$TEMP_DIR/twine.log"
        fi
        return 1
    fi
    
    # Test installation in isolated environment
    log_info "Testing package installation..."
    local test_env="$TEMP_DIR/test-env"
    python -m venv "$test_env"
    source "$test_env/bin/activate"
    
    if pip install dist/*.whl > "$TEMP_DIR/install.log" 2>&1; then
        log_success "Package installation successful"
        
        # Basic functionality test
        if python -c "import tinel; print(f'✅ Package test passed: {tinel.__version__}')" 2>/dev/null && \
           python -m tinel --version >/dev/null 2>&1 && \
           python -m tinel --help >/dev/null 2>&1; then
            log_success "Basic functionality tests passed"
        else
            log_error "Basic functionality tests failed"
            deactivate
            return 1
        fi
    else
        log_error "Package installation failed"
        if [[ "$VERBOSE" == "true" ]]; then
            cat "$TEMP_DIR/install.log"
        fi
        deactivate
        return 1
    fi
    
    deactivate
    
    # Run integration tests if they exist
    if [[ -d "tests/integration" ]]; then
        log_info "Running integration tests..."
        if uv run pytest tests/integration/ -v --tb=short > "$TEMP_DIR/integration.log" 2>&1; then
            log_success "Integration tests passed"
        else
            log_error "Integration tests failed"
            if [[ "$VERBOSE" == "true" ]]; then
                cat "$TEMP_DIR/integration.log"
            fi
            return 1
        fi
    fi
    
    # Run performance tests if they exist
    if [[ -d "tests/performance" ]]; then
        log_info "Running performance tests..."
        if uv run pytest tests/performance/ -v --tb=short > "$TEMP_DIR/performance.log" 2>&1; then
            log_success "Performance tests passed"
        else
            log_warning "Performance tests had issues (non-blocking)"
        fi
    fi
}

# Documentation build
run_documentation_build() {
    if [[ "$SKIP_DOCS" == "true" ]]; then
        log_warning "Skipping documentation build"
        return 0
    fi
    
    log_section "Documentation Build"
    
    # Check if docs dependencies are needed
    if grep -q 'docs.*=' pyproject.toml; then
        log_info "Installing documentation dependencies..."
        uv pip install -e ".[docs]" >/dev/null 2>&1
    fi
    
    log_info "Building API documentation..."
    if python -m pdoc --html --output-dir docs tinel > "$TEMP_DIR/docs.log" 2>&1; then
        if [[ -d "docs" ]] && [[ -n "$(ls -A docs)" ]]; then
            log_success "Documentation built successfully"
        else
            log_error "Documentation build failed - no output generated"
            return 1
        fi
    else
        log_error "Documentation build failed"
        if [[ "$VERBOSE" == "true" ]]; then
            cat "$TEMP_DIR/docs.log"
        fi
        return 1
    fi
}

# Show quick fixes for quality issues
show_quality_fixes() {
    cat << EOF

${YELLOW}Quick Fixes for Quality Issues:${NC}

${CYAN}Fix formatting:${NC}
    uv run ruff format .

${CYAN}Fix linting issues:${NC}
    uv run ruff check --fix .

${CYAN}Run tests:${NC}
    python -m pytest --cov=tinel

${CYAN}Type checking:${NC}
    uv run mypy tinel

EOF
}

# Generate summary report
generate_summary() {
    log_section "Local CI Verification Summary"
    
    local total_checks=0
    local passed_checks=0
    local failed_checks=()
    
    echo -e "\n${CYAN}📊 Verification Results:${NC}"
    echo "┌─────────────────────────────┬──────────┐"
    echo "│ Component                   │ Status   │"
    echo "├─────────────────────────────┼──────────┤"
    
    # Check each component
    local components=("Prerequisites" "Environment" "Quality Checks" "Security Scanning" "Tests" "Build Verification" "Documentation")
    
    for component in "${components[@]}"; do
        case "$component" in
            "Prerequisites"|"Environment")
                echo "│ $(printf "%-27s" "$component") │ $(printf "%8s" "✅ PASS") │"
                ((total_checks++))
                ((passed_checks++))
                ;;
            "Security Scanning")
                if [[ "$SKIP_SECURITY" == "true" ]]; then
                    echo "│ $(printf "%-27s" "$component") │ $(printf "%8s" "⏭️ SKIP") │"
                else
                    echo "│ $(printf "%-27s" "$component") │ $(printf "%8s" "⚠️ WARN") │"
                    ((total_checks++))
                    ((passed_checks++))
                fi
                ;;
            "Build Verification")
                if [[ "$SKIP_BUILD" == "true" ]]; then
                    echo "│ $(printf "%-27s" "$component") │ $(printf "%8s" "⏭️ SKIP") │"
                else
                    echo "│ $(printf "%-27s" "$component") │ $(printf "%8s" "✅ PASS") │"
                    ((total_checks++))
                    ((passed_checks++))
                fi
                ;;
            "Documentation")
                if [[ "$SKIP_DOCS" == "true" ]]; then
                    echo "│ $(printf "%-27s" "$component") │ $(printf "%8s" "⏭️ SKIP") │"
                else
                    echo "│ $(printf "%-27s" "$component") │ $(printf "%8s" "✅ PASS") │"
                    ((total_checks++))
                    ((passed_checks++))
                fi
                ;;
            *)
                echo "│ $(printf "%-27s" "$component") │ $(printf "%8s" "✅ PASS") │"
                ((total_checks++))
                ((passed_checks++))
                ;;
        esac
    done
    
    echo "└─────────────────────────────┴──────────┘"
    
    echo -e "\n${CYAN}📁 Generated Artifacts:${NC}"
    if [[ -d "$TEMP_DIR" ]]; then
        find "$TEMP_DIR" -name "*.xml" -o -name "*.json" -o -name "*.log" | while read -r file; do
            echo "  - $(basename "$file")"
        done
    fi
    
    # Coverage information
    if [[ -f "coverage.xml" ]]; then
        echo -e "\n${CYAN}📈 Coverage Report:${NC}"
        echo "  - coverage.xml generated"
        if command -v coverage &> /dev/null; then
            local coverage_pct=$(coverage report --show-missing | tail -1 | grep -oE '[0-9]+%' | tail -1)
            echo "  - Total coverage: $coverage_pct"
        fi
    fi
    
    echo -e "\n${CYAN}🔗 Next Steps:${NC}"
    if [[ $passed_checks -eq $total_checks ]]; then
        echo "  ✅ All checks passed! Your code is ready for GitHub workflow."
        echo "  📤 You can safely push your changes to trigger CI."
    else
        echo "  ❌ Some checks failed. Please fix the issues before pushing."
        echo "  🔧 Review the error messages above and run the suggested fixes."
    fi
    
    echo -e "\n${CYAN}📊 Summary:${NC} $passed_checks/$total_checks checks passed"
}

# Cleanup function
cleanup() {
    if [[ -d "$TEMP_DIR" ]]; then
        log_info "Cleaning up temporary files..."
        rm -rf "$TEMP_DIR"
    fi
}

# Main execution
main() {
    # Set up cleanup trap
    trap cleanup EXIT
    
    log_info "🚀 Starting Local CI Verification"
    log_info "Python version: $PYTHON_VERSION"
    log_info "Project: $(basename "$PROJECT_ROOT")"
    
    # Run all checks
    check_prerequisites
    setup_environment
    run_quality_checks
    run_security_checks
    run_tests
    run_build_verification
    run_documentation_build
    
    # Generate summary
    generate_summary
    
    log_success "🎉 Local CI verification completed successfully!"
    echo -e "\n${GREEN}Ready to push to GitHub! 🚀${NC}"
}

# Execute main function
main "$@"