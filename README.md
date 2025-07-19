# Infenix

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![CI](https://github.com/infenia/infenix/workflows/CI/badge.svg)](https://github.com/infenia/infenix/actions)

A next-generation open-source platform designed to control, optimize, and analyze Linux-based systems using AI and LLMs. Developed by Infenia Private Limited, Infenix interfaces with the Linux kernel through various system utilities and filesystem interfaces to gather real-time hardware data.

## 🚀 Features

This MCP server provides detailed hardware information including:

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
uv pip install infenix

# Or install from source
git clone https://github.com/infenia/infenix.git
cd infenix
uv pip install -e .
```

### Development Install

```bash
# Clone the repository
git clone https://github.com/infenia/infenix.git
cd infenix

# Install development dependencies
uv pip install -e ".[dev]"
```

## 🔧 Usage

### As an MCP Server

Add to your MCP client configuration:

```json
{
  "mcpServers": {
    "infenix": {
      "command": "infenix",
      "args": [],
      "env": {}
    }
  }
}
```

Alternative configurations:

```json
{
  "mcpServers": {
    "infenix": {
      "command": "python",
      "args": ["-m", "infenix.server"],
      "env": {}
    }
  }
}
```

### Available Tools

| Tool                | Description                                                          |
| ------------------- | -------------------------------------------------------------------- |
| `get_all_hardware`  | Get comprehensive hardware information for the entire system         |
| `get_cpu_info`      | Get detailed CPU information including model, cores, and features    |
| `get_memory_info`   | Get detailed memory information including RAM size and configuration |
| `get_storage_info`  | Get storage information including disks, partitions, and usage       |
| `get_pci_devices`   | Get information about all PCI devices in the system                  |
| `get_usb_devices`   | Get information about all connected USB devices                      |
| `get_network_info`  | Get network hardware and interface information                       |
| `get_graphics_info` | Get graphics hardware information including GPU details              |

### Example Output

```json
{
  "cpu": {
    "lscpu": "Architecture: x86_64\nCPU(s): 8\n...",
    "proc_cpuinfo": "processor: 0\nvendor_id: GenuineIntel\n..."
  },
  "memory": {
    "proc_meminfo": "MemTotal: 16384000 kB\nMemFree: 8192000 kB\n...",
    "dmidecode_memory": "Handle 0x0001, DMI type 17, 40 bytes\n..."
  }
}
```

## 🛠️ Development

### Setup Development Environment

```bash
# Clone and setup
git clone https://github.com/infenia/infenix.git
cd infenix
uv pip install -e ".[dev]"
```

### Running Tests

```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=infenix --cov-report=html

# Run tests on multiple Python versions
nox -s tests
```

### Code Quality

```bash
# Format code
python -m black .
python -m ruff format .

# Lint code
python -m ruff check .

# Type checking
python -m mypy infenix

# Run all quality checks
nox -s lint
```

### Building

```bash
# Build package
python -m build

# Or using nox
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

Some hardware information requires elevated privileges. The server will attempt to run commands with `sudo` when necessary. Ensure the user has appropriate sudo permissions for:

- `dmidecode` (memory details)
- `fdisk` (disk partitioning info)
- `lshw` (hardware details)

## 📊 Data Sources

The server gathers information from multiple Linux kernel interfaces:

- **`/proc/cpuinfo`** - CPU information and features
- **`/proc/meminfo`** - Memory usage and configuration
- **`/sys/devices/`** - Device tree information
- **System utilities** - `lscpu`, `lspci`, `lsusb`, `lsblk`, `df`, `ip`
- **Hardware tools** - `dmidecode`, `lshw`, `nvidia-smi`

## 🔄 Error Handling

The server gracefully handles various error conditions:

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
4. Run the test suite: `python -m pytest`
5. Submit a pull request

## 📄 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## 🐛 Issues and Support

- **Bug Reports**: [GitHub Issues](https://github.com/infenia/infenix/issues)
- **Feature Requests**: [GitHub Issues](https://github.com/infenia/infenix/issues)
- **Documentation**: [README](README.md) and [Contributing Guide](CONTRIBUTING.md)

## 🏷️ Changelog

See [CHANGELOG.md](CHANGELOG.md) for a detailed history of changes.

## 🙏 Acknowledgments

- The [Model Context Protocol](https://modelcontextprotocol.io/) team for the excellent protocol specification
- The Linux kernel developers for providing comprehensive hardware interfaces
- All contributors who help improve this project

---

**Made with ❤️ by Infenia Private Limited for the Linux and AI communities**
