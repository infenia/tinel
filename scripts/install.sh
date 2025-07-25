#!/bin/bash
# Tinel Installation Script
# Automatic detection and installation for Linux systems

set -e

# Script metadata
SCRIPT_VERSION="1.0.0"
TINEL_VERSION="0.1.0"
GITHUB_REPO="infenia/tinel"
INSTALL_URL="https://install.tinel.dev"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
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

# Check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        log_warning "Running as root. Tinel will be installed system-wide."
        INSTALL_MODE="system"
    else
        log_info "Running as user. Tinel will be installed for current user."
        INSTALL_MODE="user"
    fi
}

# Detect operating system and distribution
detect_os() {
    if [[ "$OSTYPE" != "linux-gnu"* ]]; then
        log_error "This script only supports Linux systems."
        exit 1
    fi
    
    # Detect distribution
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        OS_ID="$ID"
        OS_VERSION="$VERSION_ID"
        OS_NAME="$NAME"
    else
        log_error "Cannot detect Linux distribution. /etc/os-release not found."
        exit 1
    fi
    
    log_info "Detected OS: $OS_NAME ($OS_ID $OS_VERSION)"
}

# Check system requirements
check_requirements() {
    log_info "Checking system requirements..."
    
    # Check Python version
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
        log_info "Python version: $PYTHON_VERSION"
        
        # Check if Python version is 3.11+
        if python3 -c 'import sys; exit(0 if sys.version_info >= (3, 11) else 1)'; then
            log_success "Python 3.11+ requirement satisfied"
        else
            log_error "Python 3.11 or higher required. Current version: $PYTHON_VERSION"
            exit 1
        fi
    else
        log_error "Python 3 not found. Please install Python 3.11 or higher."
        exit 1
    fi
    
    # Check for required system tools
    local required_tools=("lscpu" "lspci" "lsusb")
    local missing_tools=()
    
    for tool in "${required_tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            missing_tools+=("$tool")
        fi
    done
    
    if [[ ${#missing_tools[@]} -gt 0 ]]; then
        log_warning "Missing system tools: ${missing_tools[*]}"
        log_info "These tools provide additional hardware information but are not required."
    else
        log_success "All system tools available"
    fi
}

# Install system dependencies
install_dependencies() {
    log_info "Installing system dependencies..."
    
    case "$OS_ID" in
        ubuntu|debian)
            if [[ $INSTALL_MODE == "system" ]]; then
                apt-get update
                apt-get install -y python3-pip python3-venv util-linux pciutils usbutils lshw dmidecode
            else
                log_info "User installation: Skipping system package installation"
                log_info "Install manually if needed: sudo apt install python3-pip python3-venv util-linux pciutils usbutils lshw dmidecode"
            fi
            ;;
        fedora|rhel|centos)
            if [[ $INSTALL_MODE == "system" ]]; then
                if command -v dnf &> /dev/null; then
                    dnf install -y python3-pip python3-virtualenv util-linux pciutils usbutils lshw dmidecode
                else
                    yum install -y python3-pip python3-virtualenv util-linux pciutils usbutils lshw dmidecode
                fi
            else
                log_info "User installation: Skipping system package installation"
                log_info "Install manually if needed: sudo dnf install python3-pip python3-virtualenv util-linux pciutils usbutils lshw dmidecode"
            fi
            ;;
        arch|manjaro)
            if [[ $INSTALL_MODE == "system" ]]; then
                pacman -Sy --noconfirm python-pip python-virtualenv util-linux pciutils usbutils lshw dmidecode
            else
                log_info "User installation: Skipping system package installation"
                log_info "Install manually if needed: sudo pacman -S python-pip python-virtualenv util-linux pciutils usbutils lshw dmidecode"
            fi
            ;;
        opensuse*)
            if [[ $INSTALL_MODE == "system" ]]; then
                zypper install -y python3-pip python3-virtualenv util-linux pciutils usbutils lshw dmidecode
            else
                log_info "User installation: Skipping system package installation"
                log_info "Install manually if needed: sudo zypper install python3-pip python3-virtualenv util-linux pciutils usbutils lshw dmidecode"
            fi
            ;;
        *)
            log_warning "Unknown distribution: $OS_ID"
            log_info "Please install Python 3.11+, pip, and system utilities manually"
            ;;
    esac
}

# Choose installation method
choose_installation_method() {
    log_info "Available installation methods:"
    echo "1. PyPI (pip/pipx) - Recommended"
    echo "2. System Package (DEB/RPM)"
    echo "3. Docker Container"
    echo "4. Snap Package"
    echo "5. Installation Script (Direct)"
    
    while true; do
        read -p "Choose installation method (1-5): " method
        case $method in
            1) install_pypi; break;;
            2) install_system_package; break;;
            3) install_docker; break;;
            4) install_snap; break;;
            5) install_direct; break;;
            *) log_error "Invalid choice. Please enter 1-5.";;
        esac
    done
}

# Install via PyPI (pipx preferred)
install_pypi() {
    log_info "Installing Tinel via PyPI..."
    
    # Check if pipx is available
    if command -v pipx &> /dev/null; then
        log_info "Using pipx for isolated installation"
        pipx install tinel
        log_success "Tinel installed via pipx"
    else
        log_info "pipx not found. Installing via pip..."
        
        if [[ $INSTALL_MODE == "system" ]]; then
            pip3 install tinel
        else
            pip3 install --user tinel
            
            # Add ~/.local/bin to PATH if not already there
            if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
                echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
                log_info "Added ~/.local/bin to PATH in ~/.bashrc"
                log_warning "Please restart your shell or run: source ~/.bashrc"
            fi
        fi
        log_success "Tinel installed via pip"
    fi
}

# Install system package
install_system_package() {
    log_info "Installing Tinel system package..."
    
    case "$OS_ID" in
        ubuntu|debian)
            # Add repository and install
            curl -fsSL https://packages.tinel.dev/gpg | gpg --dearmor > /etc/apt/trusted.gpg.d/tinel.gpg
            echo "deb https://packages.tinel.dev/apt stable main" > /etc/apt/sources.list.d/tinel.list
            apt-get update
            apt-get install -y tinel
            ;;
        fedora|rhel|centos)
            # Add repository and install
            cat > /etc/yum.repos.d/tinel.repo << 'EOF'
[tinel]
name=Tinel Repository
baseurl=https://packages.tinel.dev/rpm/
enabled=1
gpgcheck=1
gpgkey=https://packages.tinel.dev/gpg
EOF
            if command -v dnf &> /dev/null; then
                dnf install -y tinel
            else
                yum install -y tinel
            fi
            ;;
        *)
            log_error "System packages not available for $OS_ID"
            log_info "Falling back to PyPI installation"
            install_pypi
            return
            ;;
    esac
    
    log_success "Tinel system package installed"
}

# Install Docker container
install_docker() {
    log_info "Setting up Tinel Docker container..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker not found. Please install Docker first."
        exit 1
    fi
    
    # Pull the image
    docker pull tinel/tinel:latest
    
    # Create docker-compose file
    mkdir -p ~/.config/tinel
    cat > ~/.config/tinel/docker-compose.yml << 'EOF'
version: '3.8'
services:
  tinel:
    image: tinel/tinel:latest
    container_name: tinel
    ports:
      - "8080:8080"
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /dev:/host/dev:ro
      - tinel-data:/var/lib/tinel
    environment:
      - TINEL_HOST_PREFIX=/host
    restart: unless-stopped

volumes:
  tinel-data:
EOF
    
    # Create convenience script
    cat > ~/.local/bin/tinel << 'EOF'
#!/bin/bash
cd ~/.config/tinel
if [[ "$1" == "server" ]]; then
    docker-compose up -d
    echo "Tinel server started at http://localhost:8080"
else
    docker run --rm -it \
        -v /proc:/host/proc:ro \
        -v /sys:/host/sys:ro \
        -e TINEL_HOST_PREFIX=/host \
        tinel/tinel:latest "$@"
fi
EOF
    chmod +x ~/.local/bin/tinel
    
    log_success "Tinel Docker setup completed"
    log_info "Use 'tinel server' to start the server or 'tinel <command>' for direct execution"
}

# Install Snap package
install_snap() {
    log_info "Installing Tinel Snap package..."
    
    if ! command -v snap &> /dev/null; then
        log_error "Snapd not found. Please install snapd first."
        exit 1
    fi
    
    snap install tinel
    
    # Connect required interfaces
    snap connect tinel:hardware-observe
    snap connect tinel:system-observe
    snap connect tinel:mount-observe
    
    log_success "Tinel Snap package installed"
}

# Direct installation from source
install_direct() {
    log_info "Installing Tinel directly from source..."
    
    # Create installation directory
    INSTALL_DIR="$HOME/.local/share/tinel"
    mkdir -p "$INSTALL_DIR"
    
    # Download and extract source
    curl -L "https://github.com/$GITHUB_REPO/archive/v$TINEL_VERSION.tar.gz" | tar -xz -C "$INSTALL_DIR" --strip-components=1
    
    # Create virtual environment
    python3 -m venv "$INSTALL_DIR/venv"
    source "$INSTALL_DIR/venv/bin/activate"
    
    # Install
    pip install -e "$INSTALL_DIR"
    
    # Create launcher script
    mkdir -p ~/.local/bin
    cat > ~/.local/bin/tinel << EOF
#!/bin/bash
source "$INSTALL_DIR/venv/bin/activate"
exec python -m tinel "\$@"
EOF
    chmod +x ~/.local/bin/tinel
    
    log_success "Tinel installed directly from source"
}

# Verify installation
verify_installation() {
    log_info "Verifying installation..."
    
    if command -v tinel &> /dev/null; then
        local version=$(tinel --version 2>/dev/null | grep -o '[0-9]\+\.[0-9]\+\.[0-9]\+' || echo "unknown")
        log_success "Tinel installed successfully (version: $version)"
        
        # Test basic functionality
        log_info "Testing basic functionality..."
        if tinel --help &> /dev/null; then
            log_success "Tinel is working correctly"
        else
            log_warning "Tinel installation may have issues"
        fi
    else
        log_error "Tinel command not found after installation"
        log_info "You may need to restart your shell or update your PATH"
        return 1
    fi
}

# Post-installation setup
post_install_setup() {
    log_info "Post-installation setup..."
    
    # Create configuration directory
    mkdir -p ~/.config/tinel
    
    # Create default configuration if it doesn't exist
    if [[ ! -f ~/.config/tinel/config.yaml ]]; then
        cat > ~/.config/tinel/config.yaml << 'EOF'
# Tinel User Configuration
server:
  host: "127.0.0.1"
  port: 8080
  debug: false

logging:
  level: "INFO"
  file: "~/.local/share/tinel/logs/tinel.log"

hardware:
  cpu: true
  memory: true
  storage: true
  network: true
  gpu: true

cache:
  directory: "~/.cache/tinel"
  ttl: 300
EOF
        log_success "Default configuration created at ~/.config/tinel/config.yaml"
    fi
    
    # Create directories
    mkdir -p ~/.local/share/tinel/logs
    mkdir -p ~/.cache/tinel
    
    log_success "Post-installation setup completed"
}

# Show usage information
show_usage() {
    echo "Tinel Installation Script v$SCRIPT_VERSION"
    echo
    echo "Usage: $0 [OPTIONS]"
    echo
    echo "Options:"
    echo "  -h, --help     Show this help message"
    echo "  -v, --version  Show script version"
    echo "  -y, --yes      Assume yes to all prompts (auto mode)"
    echo "  -m, --method   Installation method (pip|system|docker|snap|direct)"
    echo "  --no-deps      Skip dependency installation"
    echo "  --user         Force user installation"
    echo "  --system       Force system installation (requires root)"
    echo
    echo "Examples:"
    echo "  $0                    # Interactive installation"
    echo "  $0 -y -m pip         # Auto install via pip"
    echo "  $0 --user -m system  # User-mode system package install"
}

# Main installation function
main() {
    local auto_mode=false
    local method=""
    local skip_deps=false
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_usage
                exit 0
                ;;
            -v|--version)
                echo "Tinel Installation Script v$SCRIPT_VERSION"
                exit 0
                ;;
            -y|--yes)
                auto_mode=true
                shift
                ;;
            -m|--method)
                method="$2"
                shift 2
                ;;
            --no-deps)
                skip_deps=true
                shift
                ;;
            --user)
                INSTALL_MODE="user"
                shift
                ;;
            --system)
                INSTALL_MODE="system"
                shift
                ;;
            *)
                log_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
    
    # Start installation
    echo "========================================="
    echo "  Tinel Installation Script v$SCRIPT_VERSION"
    echo "========================================="
    echo
    
    # System checks
    check_root
    detect_os
    check_requirements
    
    # Install dependencies
    if [[ $skip_deps == false ]]; then
        install_dependencies
    fi
    
    # Choose installation method
    if [[ -n "$method" ]]; then
        case "$method" in
            pip|pypi) install_pypi;;
            system|package) install_system_package;;
            docker) install_docker;;
            snap) install_snap;;
            direct|source) install_direct;;
            *) log_error "Invalid method: $method"; exit 1;;
        esac
    elif [[ $auto_mode == true ]]; then
        install_pypi  # Default to PyPI for auto mode
    else
        choose_installation_method
    fi
    
    # Verify and setup
    if verify_installation; then
        post_install_setup
        
        echo
        echo "========================================="
        log_success "Tinel installation completed successfully!"
        echo "========================================="
        echo
        echo "Quick start:"
        echo "  tinel --help                 # Show help"
        echo "  tinel hardware               # Analyze hardware"
        echo "  tinel server                 # Start API server"
        echo
        echo "Configuration: ~/.config/tinel/config.yaml"
        echo "Documentation: https://github.com/$GITHUB_REPO"
        echo
    else
        log_error "Installation verification failed"
        exit 1
    fi
}

# Run main function with all arguments
main "$@"