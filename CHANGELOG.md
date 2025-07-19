# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Initial release of Infenix by Infenia Private Limited
- Comprehensive hardware information gathering from Linux systems
- Support for CPU, memory, storage, PCI, USB, network, and graphics information
- MCP (Model Context Protocol) server implementation
- Complete test suite with 100% statement coverage
- CI/CD pipeline with GitHub Actions
- Multi-version Python testing with Nox

### Features

- **CPU Information**: Model, cores, frequency, features, and architecture details
- **Memory Information**: RAM size, type, configuration, and usage
- **Storage Information**: Disks, partitions, filesystem usage, and device details
- **PCI Devices**: All PCI devices with detailed specifications
- **USB Devices**: Connected USB devices and their hierarchy
- **Network Hardware**: Network interfaces and hardware details
- **Graphics Information**: GPU details and display hardware

### Technical Details

- Python 3.11+ support
- Type hints throughout the codebase
- Comprehensive error handling
- Graceful degradation when utilities are unavailable
- Structured JSON output for all hardware information

## [0.1.0] - 2024-XX-XX

### Added

- Initial project setup
- Basic MCP server implementation
- Hardware information gathering functions
- Test suite and CI/CD pipeline
- Documentation and contribution guidelines

[Unreleased]: https://github.com/infenia/infenix/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/infenia/infenix/releases/tag/v0.1.0
