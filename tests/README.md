# Tinel Testing Suite

A comprehensive, modular testing framework for the Tinel hardware analysis platform.

## Overview

The Tinel testing suite is designed to be:
- **Modular**: Organized by test type and functionality
- **Maintainable**: Clear structure with reusable utilities
- **Comprehensive**: Covers unit, integration, performance, and security testing
- **Fast**: Efficient execution with caching and parallel support
- **Developer-friendly**: Easy to run, understand, and extend

## Test Organization

```
tests/
├── conftest.py              # Pytest configuration and fixtures
├── utils.py                 # Testing utilities and helpers
├── test_runner.py          # Custom test runner
├── Makefile                # Make targets for common tasks
├── README.md               # This file
├── unit/                   # Unit tests (fast, isolated)
│   ├── test_system.py
│   ├── test_cpu_analyzer.py
│   └── test_formatters.py
├── integration/            # Integration tests (component interactions)
│   └── test_hardware_integration.py
├── performance/            # Performance tests (timing, memory, scaling)
│   └── test_performance.py
└── security/              # Security tests (injection, traversal, etc.)
    └── test_security.py
```

## Test Categories

### Unit Tests (`tests/unit/`)
- **Purpose**: Fast, isolated tests of individual components
- **Characteristics**: No external dependencies, heavily mocked
- **Runtime**: < 100ms per test
- **Coverage**: Individual functions and classes

### Integration Tests (`tests/integration/`)
- **Purpose**: Test component interactions and workflows
- **Characteristics**: Multiple components working together
- **Runtime**: < 1 second per test
- **Coverage**: End-to-end functionality

### Performance Tests (`tests/performance/`)
- **Purpose**: Verify performance characteristics and bounds
- **Characteristics**: Timing, memory usage, concurrency
- **Runtime**: < 5 seconds per test
- **Coverage**: Performance-critical code paths

### Security Tests (`tests/security/`)
- **Purpose**: Verify security measures and prevent vulnerabilities
- **Characteristics**: Attack simulation, input validation
- **Runtime**: < 2 seconds per test
- **Coverage**: Security-sensitive operations

## Quick Start

### Running Tests

```bash
# Run all tests
make test-all

# Run specific test categories
make test-unit          # Fast unit tests
make test-integration   # Integration tests
make test-performance   # Performance tests
make test-security      # Security tests

# Run tests with coverage
make test-coverage

# Run tests for specific module
make test-system        # System interface tests
make test-cpu          # CPU analyzer tests
```

### Using the Test Runner

```bash
# Python test runner (more options)
python tests/test_runner.py unit -v
python tests/test_runner.py performance
python tests/test_runner.py module cpu_analyzer

# Generate reports
python tests/test_runner.py coverage
python tests/test_runner.py report
```

### Using Pytest Directly

```bash
# Run specific test types
pytest -m unit
pytest -m integration
pytest -m performance
pytest -m security

# Run specific test files
pytest tests/unit/test_system.py -v
pytest tests/integration/ -v

# Run with coverage
pytest --cov=tinel --cov-report=html
```

## Test Utilities

### Fixtures (`tests/conftest.py`)
- `mock_system_interface`: Mock system interface for testing
- `sample_cpuinfo`: Realistic /proc/cpuinfo content
- `sample_lscpu`: Realistic lscpu output
- `mock_filesystem`: Mock filesystem for file operations
- `performance_monitor`: Performance measurement utilities

### Helpers (`tests/utils.py`)
- `TestDataBuilder`: Create test data structures
- `SecurityTestHelpers`: Security testing utilities
- `PerformanceTestHelpers`: Performance testing utilities
- `AssertionHelpers`: Custom assertion helpers
- Test decorators: `@unit_test`, `@integration_test`, etc.

## Writing Tests

### Test Structure
```python
from tests.utils import unit_test, AssertionHelpers

class TestMyComponent:
    """Test cases for MyComponent."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.component = MyComponent()
    
    @unit_test
    def test_basic_functionality(self):
        """Test basic functionality."""
        result = self.component.do_something()
        assert result is not None
        AssertionHelpers.assert_contains_keys(result, ['key1', 'key2'])
```

### Test Markers
```python
@unit_test           # Fast, isolated unit test
@integration_test    # Component interaction test
@performance_test    # Performance verification test
@security_test       # Security measure test
@slow_test          # Test that takes longer to run
```

### Using Fixtures
```python
def test_with_fixtures(self, mock_system_interface, sample_cpuinfo):
    """Test using predefined fixtures."""
    mock_system_interface.read_file.return_value = sample_cpuinfo
    # ... test logic
```

## Performance Testing

### Timing Tests
```python
@performance_test
def test_operation_performance(self, performance_monitor):
    """Test operation completes within time bounds."""
    performance_monitor.start()
    result = expensive_operation()
    performance_monitor.stop()
    
    performance_monitor.assert_max_time(0.1)  # 100ms max
```

### Caching Tests
```python
def test_caching_improves_performance(self):
    """Test caching provides performance improvement."""
    PerformanceTestHelpers.assert_cached_performance(
        lambda: cached_call(),
        lambda: uncached_call(),
        min_improvement=2.0  # At least 2x faster
    )
```

## Security Testing

### Input Validation
```python
@security_test
def test_input_sanitization(self):
    """Test malicious input is properly sanitized."""
    malicious_inputs = SecurityTestHelpers.create_malicious_inputs()
    
    for malicious_input in malicious_inputs:
        with pytest.raises(ValueError):
            component.process_input(malicious_input)
```

### Path Traversal Prevention
```python
@security_test
def test_path_traversal_prevention(self):
    """Test path traversal attacks are blocked."""
    traversal_attempts = SecurityTestHelpers.create_path_traversal_attempts()
    
    for attempt in traversal_attempts:
        result = system.validate_path(attempt)
        assert result is None
```

## Coverage Requirements

- **Minimum Coverage**: 85% overall
- **Unit Tests**: Should achieve >95% coverage of core logic
- **Integration Tests**: Focus on workflow coverage
- **Critical Paths**: Security and performance code must be 100% covered

### Generating Coverage Reports
```bash
# HTML coverage report
make coverage-html
open htmlcov/index.html

# Terminal coverage report
pytest --cov=tinel --cov-report=term-missing

# XML coverage report (for CI)
pytest --cov=tinel --cov-report=xml
```

## CI/CD Integration

### GitHub Actions
```yaml
- name: Run Tests
  run: |
    python tests/test_runner.py all --no-coverage
    python tests/test_runner.py coverage

- name: Upload Coverage
  uses: codecov/codecov-action@v1
  with:
    file: ./coverage.xml
```

### Pre-commit Hooks
```bash
# Run tests before commit
make test-fast

# Run linting
make lint

# Format code
make format
```

## Debugging Tests

### Running Single Tests
```bash
# Run specific test
pytest tests/unit/test_system.py::TestLinuxSystemInterface::test_run_command_success -v

# Run with debugger
pytest tests/unit/test_system.py -v --pdb

# Run with verbose output
pytest tests/unit/test_system.py -v -s
```

### Test Data Inspection
```python
def test_debug_data(self, sample_cpuinfo):
    """Debug test data."""
    print(f"Sample data: {sample_cpuinfo}")
    # Add breakpoint for inspection
    import pdb; pdb.set_trace()
```

## Common Issues and Solutions

### Slow Tests
- Use appropriate test markers (`@slow_test`)
- Mock external dependencies
- Use fixtures to avoid repeated setup
- Consider parallel execution

### Flaky Tests
- Mock time-dependent operations
- Use deterministic test data
- Avoid race conditions
- Set appropriate timeouts

### Test Dependencies
- Keep tests independent
- Use fresh fixtures for each test
- Clean up resources in teardown
- Mock external systems

### Memory Issues
- Monitor memory usage in performance tests
- Clean up large test data
- Use generators for large datasets
- Profile memory-intensive operations

## Best Practices

### Test Design
1. **One concept per test**: Each test should verify one specific behavior
2. **Clear naming**: Test names should describe what they verify
3. **Arrange-Act-Assert**: Structure tests clearly
4. **Fast feedback**: Unit tests should run quickly

### Test Data
1. **Realistic data**: Use representative test data
2. **Edge cases**: Test boundary conditions
3. **Error conditions**: Test failure scenarios
4. **Reusable fixtures**: Share common test data

### Maintenance
1. **Regular review**: Review and update tests regularly
2. **Remove obsolete tests**: Clean up tests for removed features
3. **Update fixtures**: Keep test data current
4. **Documentation**: Keep test documentation updated

## Contributing

### Adding New Tests
1. Choose appropriate test category (unit/integration/performance/security)
2. Use existing utilities and fixtures when possible
3. Follow naming conventions
4. Add appropriate test markers
5. Update documentation

### Test Review Checklist
- [ ] Test names are descriptive
- [ ] Tests are properly categorized
- [ ] Appropriate markers are used  
- [ ] Tests are independent
- [ ] Edge cases are covered
- [ ] Performance bounds are reasonable
- [ ] Security implications are considered

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Python unittest Documentation](https://docs.python.org/3/library/unittest.html)
- [Test-Driven Development](https://testdriven.io/)
- [Security Testing Guidelines](https://owasp.org/www-project-web-security-testing-guide/)

---

For questions or issues with the testing suite, please see the project's main documentation or open an issue in the repository.