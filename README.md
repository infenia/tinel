# Tinel

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![CI](https://github.com/infenia/tinel/workflows/CI/badge.svg)](https://github.com/infenia/tinel/actions)
[![Coverage Status](https://coveralls.io/repos/github/infenia/tinel/badge.svg?branch=main)](https://coveralls.io/github/infenia/tinel?branch=main)

A next-generation open-source platform designed to control, optimize, and analyze Linux-based systems using AI and LLMs. Developed by Infenia Private Limited, Tinel interfaces with the Linux kernel through various system utilities and filesystem interfaces to gather real-time hardware data.

## 🚀 Features

This tool provides detailed hardware information including:

- **🖥️ CPU Information**: Model, cores, frequency, features, and architecture details
- **💾 Memory Information**: RAM size, type, configuration, and usage statistics
- **💿 Storage Information**: Disks, partitions, filesystem usage, and device details
- **🔌 PCI Devices**: All PCI devices with detailed specifications and drivers
- **🔗 USB Devices**: Connected USB devices and their hierarchy
- **🌐 Network Hardware**: Network interfaces and hardware details
- **🎮 Graphics Information**: GPU details, display hardware, and driver information

## 📦 Installation

### Prerequisites

- **Linux operating system** (tested on Ubuntu, Debian, CentOS, Fedora)
- **Python 3.11+**
- **uv** (Python package manager)

### Quick Install

```bash
# Using uv
uv pip install tinel

# Or install from source
git clone https://github.com/infenia/tinel.git
cd tinel
uv pip install -e .
```

### Development Install

```bash
# Clone the repository
git clone https://github.com/infenia/tinel.git
cd tinel

# Install development dependencies
uv pip install -e ".[dev]"
```

## 🔧 Usage

Tinel is a command-line tool. To use it, simply run `tinel` with a command and subcommand.

### Examples

Get all hardware information:
```bash
tinel hardware all
```

Get CPU information:
```bash
tinel hardware cpu
```

Get help for a specific command:
```bash
tinel hardware --help
```

### Available Commands

| Command           | Description                                                          |
| ----------------- | -------------------------------------------------------------------- |
| `hardware all`    | Get comprehensive hardware information for the entire system         |
| `hardware cpu`    | Get detailed CPU information including model, cores, and features    |

## 📖 Documentation

This repository is thoroughly documented with docstrings in every file, class, method, and function. This ensures that developers can easily understand the codebase and contribute effectively.

## 🛠️ Development

### Setup Development Environment

```bash
# Clone and setup
git clone https://github.com/infenia/tinel.git
cd tinel
uv pip install -e ".[dev]"
```

### Running Tests

```bash
# Run all tests
nox -s tests

# Run with coverage
nox -s coverage
```

### Code Quality

```bash
# Format code
nox -s format

# Run all quality checks
nox -s check
```

### Building

```bash
# Build package
nox -s build
```

## 🔒 System Requirements

### Required

- **Linux operating system**
- **Python 3.11+**
- Standard Linux utilities: `lscpu`, `lspci`, `lsusb`, `lsblk`, `df`, `ip`

### Optional (for enhanced information)

- `dmidecode` - Detailed memory and hardware information
- `lshw` - Comprehensive hardware detection
- `nvidia-smi` - NVIDIA GPU information
- `sudo` access - For privileged hardware information

### Permissions

Some hardware information requires elevated privileges. Ensure the user has appropriate sudo permissions for:

- `dmidecode` (memory details)
- `fdisk` (disk partitioning info)
- `lshw` (hardware details)

## 📊 Data Sources

The tool gathers information from multiple Linux kernel interfaces:

- **`/proc/cpuinfo`** - CPU information and features
- **`/proc/meminfo`** - Memory usage and configuration
- **`/sys/devices/`** - Device tree information
- **System utilities** - `lscpu`, `lspci`, `lsusb`, `lsblk`, `df`, `ip`
- **Hardware tools** - `dmidecode`, `lshw`, `nvidia-smi`

## 🔄 Error Handling

The tool gracefully handles various error conditions:

- **Missing utilities**: Continues with available tools
- **Permission errors**: Reports specific errors while providing available data
- **Command failures**: Provides partial results when some data sources fail
- **Invalid data**: Handles malformed output from system utilities

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Quick Start for Contributors

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and add tests
4. Run the test suite: `nox -s tests`
5. Submit a pull request

## 📄 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.