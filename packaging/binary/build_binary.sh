#!/bin/bash
# Tinel Binary Distribution Build Script

set -e

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
BUILD_DIR="$PROJECT_ROOT/dist/binary"
VENV_DIR="$BUILD_DIR/venv"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Python version
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 not found"
        exit 1
    fi
    
    python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    log_info "Python version: $python_version"
    
    # Check if PyInstaller is available or can be installed
    if ! python3 -c "import PyInstaller" 2>/dev/null; then
        log_warning "PyInstaller not found, will be installed"
    fi
    
    log_success "Prerequisites check completed"
}

# Set up build environment
setup_build_env() {
    log_info "Setting up build environment..."
    
    # Clean previous builds
    rm -rf "$BUILD_DIR"
    mkdir -p "$BUILD_DIR"
    
    # Create virtual environment
    python3 -m venv "$VENV_DIR"
    source "$VENV_DIR/bin/activate"
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install PyInstaller and build dependencies
    pip install pyinstaller[all]
    pip install upx-ucl  # For compression (optional)
    
    # Install Tinel and its dependencies
    cd "$PROJECT_ROOT"
    pip install -e ".[dev]"
    
    log_success "Build environment ready"
}

# Build binary with PyInstaller
build_binary() {
    log_info "Building binary with PyInstaller..."
    
    source "$VENV_DIR/bin/activate"
    cd "$PROJECT_ROOT"
    
    # Build options
    local spec_file="$SCRIPT_DIR/tinel.spec"
    local dist_path="$BUILD_DIR/dist"
    local work_path="$BUILD_DIR/build"
    
    # Run PyInstaller
    pyinstaller \
        --distpath "$dist_path" \
        --workpath "$work_path" \
        --clean \
        --noconfirm \
        "$spec_file"
    
    log_success "Binary build completed"
}

# Create portable archive
create_portable_archive() {
    log_info "Creating portable archive..."
    
    cd "$BUILD_DIR/dist"
    
    # Get version info
    local version
    if [ -f "$PROJECT_ROOT/tinel/__init__.py" ]; then
        version=$(python3 -c "import sys; sys.path.insert(0, '$PROJECT_ROOT'); import tinel; print(tinel.__version__)")
    else
        version="0.1.0"
    fi
    
    # Create architecture-specific archive name
    local arch=$(uname -m)
    local os_name=$(uname -s | tr '[:upper:]' '[:lower:]')
    local archive_name="tinel-${version}-${os_name}-${arch}"
    
    # Create directory structure
    mkdir -p "$archive_name"
    
    # Copy binary and related files
    if [ -d "tinel" ]; then
        cp -r tinel/* "$archive_name/"
    else
        log_error "Binary directory not found"
        exit 1
    fi
    
    # Create launcher script
    cat > "$archive_name/tinel.sh" << 'EOF'
#!/bin/bash
# Tinel Portable Launcher

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "$SCRIPT_DIR/tinel" "$@"
EOF
    chmod +x "$archive_name/tinel.sh"
    
    # Create README for portable version
    cat > "$archive_name/README.txt" << EOF
Tinel Portable Binary Distribution
==================================

Version: $version
Architecture: $arch
OS: $os_name
Build Date: $(date)

Usage:
------
1. Extract this archive to any directory
2. Run: ./tinel --help
3. Or use the launcher: ./tinel.sh --help

System Requirements:
-------------------
- Linux kernel 3.10+ (for system analysis features)
- Standard system utilities (lscpu, lspci, lsusb recommended)

Hardware Detection:
------------------
Some features may require additional system utilities:
- lshw (hardware lister)
- dmidecode (DMI/SMBIOS decoder)
- smartmontools (disk monitoring)
- ethtool (network interface tool)

Support:
--------
Documentation: https://github.com/infenia/tinel
Issues: https://github.com/infenia/tinel/issues

License: Apache 2.0
Copyright (c) 2025 Infenia Private Limited
EOF
    
    # Create compressed archives
    log_info "Creating compressed archives..."
    
    # TAR.GZ
    tar -czf "${archive_name}.tar.gz" "$archive_name"
    log_success "Created ${archive_name}.tar.gz"
    
    # ZIP (for broader compatibility)
    zip -r "${archive_name}.zip" "$archive_name"
    log_success "Created ${archive_name}.zip"
    
    # Calculate checksums
    sha256sum "${archive_name}.tar.gz" > "${archive_name}.tar.gz.sha256"
    sha256sum "${archive_name}.zip" > "${archive_name}.zip.sha256"
    
    log_success "Portable archives created"
}

# Test binary functionality
test_binary() {
    log_info "Testing binary functionality..."
    
    local binary_path="$BUILD_DIR/dist/tinel/tinel"
    
    if [ ! -f "$binary_path" ]; then
        log_error "Binary not found at $binary_path"
        exit 1
    fi
    
    # Test basic functionality
    log_info "Testing --version..."
    if "$binary_path" --version; then
        log_success "Version check passed"
    else
        log_error "Version check failed"
        exit 1
    fi
    
    log_info "Testing --help..."
    if "$binary_path" --help > /dev/null; then
        log_success "Help check passed"
    else
        log_error "Help check failed"
        exit 1
    fi
    
    # Test hardware command (basic check)
    log_info "Testing hardware command..."
    if "$binary_path" hardware --help > /dev/null; then
        log_success "Hardware command check passed"
    else
        log_warning "Hardware command check failed (may require system tools)"
    fi
    
    log_success "Binary testing completed"
}

# Generate build report
generate_report() {
    log_info "Generating build report..."
    
    local report_file="$BUILD_DIR/build_report.txt"
    
    cat > "$report_file" << EOF
Tinel Binary Build Report
========================

Build Information:
- Date: $(date)
- Host OS: $(uname -s) $(uname -r)
- Architecture: $(uname -m)
- Python Version: $(python3 --version)
- PyInstaller Version: $(pip show pyinstaller | grep Version | cut -d' ' -f2)

Build Results:
$(ls -la "$BUILD_DIR/dist"/)

Binary Size:
$(du -h "$BUILD_DIR/dist/tinel/tinel" 2>/dev/null || echo "Binary size calculation failed")

Archive Information:
$(ls -la "$BUILD_DIR/dist"/*.tar.gz "$BUILD_DIR/dist"/*.zip 2>/dev/null || echo "No archives found")

System Dependencies Check:
$(ldd "$BUILD_DIR/dist/tinel/tinel" 2>/dev/null | head -10 || echo "Dependency check not available")

Build Status: SUCCESS
EOF
    
    log_success "Build report generated: $report_file"
}

# Show usage
show_usage() {
    echo "Tinel Binary Build Script"
    echo
    echo "Usage: $0 [OPTIONS]"
    echo
    echo "Options:"
    echo "  -h, --help     Show this help"
    echo "  --clean        Clean build directory before building"
    echo "  --test-only    Only test existing binary"
    echo "  --no-archive   Skip archive creation"
    echo
    echo "Examples:"
    echo "  $0                # Full build"
    echo "  $0 --clean       # Clean build"
    echo "  $0 --test-only   # Test existing binary"
}

# Main function
main() {
    local clean_build=false
    local test_only=false
    local create_archive=true
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_usage
                exit 0
                ;;
            --clean)
                clean_build=true
                shift
                ;;
            --test-only)
                test_only=true
                shift
                ;;
            --no-archive)
                create_archive=false
                shift
                ;;
            *)
                log_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
    
    echo "======================================="
    echo "  Tinel Binary Distribution Builder"
    echo "======================================="
    echo
    
    if [ "$test_only" = true ]; then
        test_binary
        exit 0
    fi
    
    # Build process
    check_prerequisites
    setup_build_env
    build_binary
    test_binary
    
    if [ "$create_archive" = true ]; then
        create_portable_archive
    fi
    
    generate_report
    
    echo
    echo "======================================="
    log_success "Binary build completed successfully!"
    echo "======================================="
    echo
    echo "Build outputs:"
    echo "  Binary: $BUILD_DIR/dist/tinel/tinel"
    echo "  Archives: $BUILD_DIR/dist/*.tar.gz, *.zip"
    echo "  Report: $BUILD_DIR/build_report.txt"
    echo
}

# Run main function
main "$@"