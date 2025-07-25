# Tinel Installation Guide

Tinel offers multiple installation methods to suit different Linux environments and user preferences. Choose the method that best fits your needs.

## 🚀 Quick Install (Recommended)

### One-Line Installation Script
```bash
curl -sSL https://install.tinel.dev | bash
```

**What it does:**
- Automatically detects your Linux distribution
- Chooses the best installation method
- Installs all necessary dependencies
- Sets up configuration files

**Options:**
```bash
# Silent installation with PyPI
curl -sSL https://install.tinel.dev | bash -s -- -y -m pip

# Force system package installation
curl -sSL https://install.tinel.dev | bash -s -- --system -m system

# Docker installation
curl -sSL https://install.tinel.dev | bash -s -- -m docker
```

## 📦 Installation Methods

### 1. PyPI (Python Package Index)

**Best for:** Developers, Python users, latest versions

#### Using pipx (Recommended)
```bash
# Install pipx if not available
python3 -m pip install --user pipx
python3 -m pipx ensurepath

# Install Tinel in isolated environment
pipx install tinel
```

#### Using pip
```bash
# User installation
pip install --user tinel

# System-wide installation (requires sudo)
sudo pip install tinel

# Virtual environment (recommended for development)
python3 -m venv tinel-env
source tinel-env/bin/activate
pip install tinel
```

**Verify installation:**
```bash
tinel --version
tinel --help
```

### 2. System Packages

**Best for:** Production servers, system integration, automatic updates

#### Ubuntu/Debian (APT)
```bash
# Add Tinel repository
curl -fsSL https://packages.tinel.dev/gpg | sudo gpg --dearmor -o /etc/apt/trusted.gpg.d/tinel.gpg
echo "deb https://packages.tinel.dev/apt stable main" | sudo tee /etc/apt/sources.list.d/tinel.list

# Update and install
sudo apt update
sudo apt install tinel
```

#### Red Hat/Fedora/CentOS (YUM/DNF)
```bash
# Add Tinel repository
sudo tee /etc/yum.repos.d/tinel.repo << 'EOF'
[tinel]
name=Tinel Repository
baseurl=https://packages.tinel.dev/rpm/
enabled=1
gpgcheck=1
gpgkey=https://packages.tinel.dev/gpg
EOF

# Install
sudo dnf install tinel  # Fedora
sudo yum install tinel  # CentOS/RHEL
```

#### Arch Linux (AUR)
```bash
# Using yay
yay -S tinel

# Using paru
paru -S tinel

# Manual installation
git clone https://aur.archlinux.org/tinel.git
cd tinel
makepkg -si
```

### 3. Universal Packages

**Best for:** Sandboxed environments, automatic updates, cross-distribution compatibility

#### Snap Package
```bash
# Install from Snap Store
sudo snap install tinel

# Connect required interfaces
sudo snap connect tinel:hardware-observe
sudo snap connect tinel:system-observe
sudo snap connect tinel:mount-observe

# Configure (optional)
sudo snap set tinel port=8080
sudo snap set tinel log-level=INFO
```

#### Flatpak Package
```bash
# Add Flathub repository (if not already added)
flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo

# Install Tinel
flatpak install flathub com.infenia.Tinel

# Run Tinel
flatpak run com.infenia.Tinel --help
```

### 4. Container Images

**Best for:** Microservices, cloud deployments, isolated execution

#### Docker
```bash
# Pull latest image
docker pull tinel/tinel:latest

# Run interactively
docker run -it --rm \
  -v /proc:/host/proc:ro \
  -v /sys:/host/sys:ro \
  -v /dev:/host/dev:ro \
  -e TINEL_HOST_PREFIX=/host \
  tinel/tinel:latest

# Run as server
docker run -d \
  --name tinel-server \
  -p 8080:8080 \
  -v /proc:/host/proc:ro \
  -v /sys:/host/sys:ro \
  -v /dev:/host/dev:ro \
  -e TINEL_HOST_PREFIX=/host \
  tinel/tinel:latest server
```

#### Docker Compose
```bash
# Download docker-compose.yml
curl -O https://raw.githubusercontent.com/infenia/tinel/main/packaging/docker/docker-compose.yml

# Start services
docker-compose up -d

# Use different variants
docker-compose --profile alpine up -d      # Alpine variant
docker-compose --profile distroless up -d  # Distroless variant
docker-compose --profile monitoring up -d  # With monitoring
```

### 5. Package Managers

**Best for:** Development environments, cross-platform compatibility

#### Homebrew (Linux/macOS)
```bash
# Add Tinel tap
brew tap infenia/tinel

# Install Tinel
brew install tinel

# Start as service (optional)
brew services start tinel
```

#### Nix Package Manager
```bash
# Install directly
nix-env -iA nixpkgs.tinel

# Run without installing
nix run nixpkgs#tinel -- --help

# Development shell
nix shell nixpkgs#tinel
```

### 6. Binary Distribution

**Best for:** Offline environments, minimal dependencies, portable usage

#### Download Pre-built Binaries
```bash
# Download latest release
wget https://github.com/infenia/tinel/releases/latest/download/tinel-linux-x86_64.tar.gz

# Extract
tar -xzf tinel-linux-x86_64.tar.gz

# Run
cd tinel-linux-x86_64
./tinel --help

# Optional: Add to PATH
sudo cp tinel /usr/local/bin/
```

#### Available Architectures
- `x86_64` (Intel/AMD 64-bit)
- `aarch64` (ARM 64-bit)
- `armv7` (ARM 32-bit)

### 7. Build from Source

**Best for:** Development, customization, bleeding-edge features

```bash
# Clone repository
git clone https://github.com/infenia/tinel.git
cd tinel

# Install dependencies
python3 -m pip install -e ".[dev]"

# Run directly
python3 -m tinel --help

# Build binary (optional)
./packaging/binary/build_binary.sh
```

## 🔧 Post-Installation Setup

### System Dependencies

Some hardware detection features require additional system utilities:

```bash
# Ubuntu/Debian
sudo apt install lshw dmidecode smartmontools hdparm ethtool

# Red Hat/Fedora
sudo dnf install lshw dmidecode smartmontools hdparm ethtool

# Arch Linux
sudo pacman -S lshw dmidecode smartmontools hdparm ethtool
```

### Configuration

Tinel looks for configuration files in these locations (in order):

1. `$TINEL_CONFIG` (environment variable)
2. `~/.config/tinel/config.yaml` (user config)
3. `/etc/tinel/config.yaml` (system config)

**Create user configuration:**
```bash
mkdir -p ~/.config/tinel

cat > ~/.config/tinel/config.yaml << 'EOF'
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
```

### Shell Completion

#### Bash
```bash
# Add to ~/.bashrc
eval "$(_TINEL_COMPLETE=bash_source tinel)"

# Or install completion file
tinel --show-completion bash > ~/.local/share/bash-completion/completions/tinel
```

#### Zsh
```bash
# Add to ~/.zshrc
eval "$(_TINEL_COMPLETE=zsh_source tinel)"

# Or install completion file
tinel --show-completion zsh > ~/.local/share/zsh/site-functions/_tinel
```

### Systemd Service (System Package)

If installed via system package, you can enable the Tinel service:

```bash
# Enable and start service
sudo systemctl enable tinel
sudo systemctl start tinel

# Check status
sudo systemctl status tinel

# View logs
sudo journalctl -u tinel -f
```

## 🧪 Verify Installation

Test your installation with these commands:

```bash
# Check version
tinel --version

# Show help
tinel --help

# Test hardware analysis
tinel hardware --cpu

# Test system information
tinel system --brief

# Test server mode (Ctrl+C to stop)
tinel server --port 8080
```

## 🔄 Updating Tinel

### PyPI Installation
```bash
pip install --upgrade tinel
# or
pipx upgrade tinel
```

### System Packages
```bash
# Ubuntu/Debian
sudo apt update && sudo apt upgrade tinel

# Red Hat/Fedora
sudo dnf update tinel
```

### Snap
```bash
sudo snap refresh tinel
```

### Flatpak
```bash
flatpak update com.infenia.Tinel
```

### Docker
```bash
docker pull tinel/tinel:latest
```

## 🚨 Troubleshooting

### Common Issues

#### Permission Denied
```bash
# Add user to required groups
sudo usermod -a -G disk,lp $USER

# Logout and login again
```

#### Missing System Tools
```bash
# Install missing utilities
sudo apt install util-linux pciutils usbutils lshw dmidecode
```

#### Python Version Issues
```bash
# Check Python version (requires 3.11+)
python3 --version

# Install newer Python if needed
sudo apt install python3.11 python3.11-pip
```

#### Network Issues (Container)
```bash
# Check container network
docker network ls
docker inspect tinel-network

# Recreate network
docker network rm tinel-network
docker-compose up -d
```

### Getting Help

- **Documentation**: https://github.com/infenia/tinel#readme
- **Issues**: https://github.com/infenia/tinel/issues
- **Discussions**: https://github.com/infenia/tinel/discussions

### Debug Mode

Enable debug logging for troubleshooting:

```bash
# Environment variable
export TINEL_LOG_LEVEL=DEBUG

# Command line
tinel --debug hardware

# Configuration file
echo "logging: { level: DEBUG }" >> ~/.config/tinel/config.yaml
```

## 📋 Summary

| Method | Best For | Installation Time | System Integration | Auto-Updates |
|--------|----------|-------------------|-------------------|--------------|
| **Install Script** | Everyone | ~1 minute | Good | Via package manager |
| **PyPI** | Developers | ~30 seconds | Basic | Manual |
| **System Packages** | Production | ~2 minutes | Excellent | Automatic |
| **Snap** | Ubuntu users | ~1 minute | Good | Automatic |
| **Flatpak** | Desktop users | ~2 minutes | Good | Automatic |
| **Docker** | Containers | ~30 seconds | Minimal | Manual |
| **Homebrew** | Developers | ~2 minutes | Good | Manual |
| **Binary** | Portable | ~10 seconds | None | Manual |

Choose the method that best fits your environment and requirements!