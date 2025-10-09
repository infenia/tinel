# Makefile for Tinel testing suite
# Copyright 2025 Infenia Private Limited
# Licensed under the Apache License, Version 2.0

.PHONY: help test test-unit test-integration test-performance test-security
.PHONY: test-fast test-slow test-all test-coverage test-watch
.PHONY: lint format check install-deps clean-test
.PHONY: test-report test-html coverage-html

# Default target
help:
	@echo "Tinel Test Suite Commands"
	@echo "========================="
	@echo ""
	@echo "Test Execution:"
	@echo "  test-unit         Run unit tests (fast)"
	@echo "  test-integration  Run integration tests"
	@echo "  test-performance  Run performance tests"
	@echo "  test-security     Run security tests"
	@echo "  test-fast         Run only fast tests"
	@echo "  test-slow         Run slow tests"  
	@echo "  test-all          Run all tests"
	@echo "  test-coverage     Run tests with coverage report"
	@echo "  test-watch        Run tests in watch mode"
	@echo ""
	@echo "Code Quality:"
	@echo "  lint              Lint test files"
	@echo "  format            Format test files"
	@echo "  check             Run all quality checks"
	@echo ""
	@echo "Reports:"
	@echo "  test-report       Generate HTML test report"
	@echo "  test-html         Generate HTML test report (alias)"
	@echo "  coverage-html     Generate HTML coverage report"
	@echo ""
	@echo "Maintenance:"
	@echo "  install-deps      Install test dependencies"
	@echo "  clean-test        Clean test artifacts"
	@echo ""
	@echo "Module-specific tests:"
	@echo "  test-system       Test system module"
	@echo "  test-cpu          Test CPU analyzer module"
	@echo "  test-formatters   Test formatters module"

# Test execution targets
test: test-unit

test-unit:
	@echo "Running unit tests..."
	python -m pytest -m unit tests/unit/ -v --tb=short

test-integration:
	@echo "Running integration tests..."
	python -m pytest -m integration tests/integration/ -v

test-performance:
	@echo "Running performance tests..."
	python -m pytest -m performance tests/performance/ -v --durations=20

test-security:
	@echo "Running security tests..."
	python -m pytest -m security tests/security/ -v

test-fast:
	@echo "Running fast tests..."
	python -m pytest -m unit tests/unit/ --tb=short

test-slow:
	@echo "Running slow tests..."
	python -m pytest -m "integration or performance or security" tests/ -v --durations=20

test-all:
	@echo "Running all tests..."
	python -m pytest tests/ -v --durations=20

test-coverage:
	@echo "Running tests with coverage..."
	python -m pytest tests/ \
		--cov=tinel \
		--cov-report=term-missing \
		--cov-report=html:htmlcov \
		--cov-report=xml:coverage.xml \
		--cov-fail-under=85 \
		-v

test-watch:
	@echo "Running tests in watch mode..."
	python -m pytest-watch tests/ -- -x -v

# Module-specific test targets
test-system:
	@echo "Running system module tests..."
	python tests/test_runner.py module system -v

test-cpu:
	@echo "Running CPU analyzer tests..."
	python tests/test_runner.py module cpu_analyzer -v

test-formatters:
	@echo "Running formatters tests..."
	python tests/test_runner.py module formatters -v

# Code quality targets
lint:
	@echo "Linting test files..."
	python -m ruff check tests/
	python -m mypy tests/ --ignore-missing-imports

format:
	@echo "Formatting test files..."
	python -m ruff format tests/
	python -m black tests/

check: lint
	@echo "Running all quality checks..."
	python -m ruff check tests/
	python -m mypy tests/ --ignore-missing-imports
	@echo "Quality checks passed ✓"

# Report generation targets
test-report:
	@echo "Generating HTML test report..."
	python -m pytest tests/ \
		--html=test_report.html \
		--self-contained-html \
		--cov=tinel \
		--cov-report=html:htmlcov

test-html: test-report

coverage-html:
	@echo "Generating HTML coverage report..."
	python -m pytest tests/ \
		--cov=tinel \
		--cov-report=html:htmlcov \
		--quiet
	@echo "Coverage report generated: htmlcov/index.html"

# Maintenance targets
install-deps:
	@echo "Installing test dependencies..."
	python -m pip install pytest>=7.4.0 pytest-cov>=4.1.0 pytest-mock>=3.10.0 psutil>=5.9.0
	python -m pip install pytest-html pytest-watch
	@echo "Test dependencies installed ✓"

clean-test:
	@echo "Cleaning test artifacts..."
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -f coverage.xml
	rm -f test_report.html
	find tests/ -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find tests/ -name "*.pyc" -delete 2>/dev/null || true
	@echo "Test artifacts cleaned ✓"

# Parallel execution targets (requires pytest-xdist)
test-parallel:
	@echo "Running tests in parallel..."
	python -m pytest tests/ -n auto -v

test-parallel-coverage:
	@echo "Running tests in parallel with coverage..."
	python -m pytest tests/ -n auto \
		--cov=tinel \
		--cov-report=term-missing \
		--cov-report=html:htmlcov \
		-v

# CI/CD targets
ci-test:
	@echo "Running CI test suite..."
	python -m pytest tests/ \
		--cov=tinel \
		--cov-report=xml:coverage.xml \
		--cov-fail-under=85 \
		--durations=20 \
		--tb=short

ci-quick:
	@echo "Running quick CI tests..."
	python -m pytest -m unit tests/unit/ \
		--cov=tinel \
		--cov-report=xml:coverage.xml \
		--tb=short

# Development targets
dev-test:
	@echo "Running development test suite..."
	python -m pytest tests/ \
		--tb=short \
		--durations=10 \
		-x

dev-watch:
	@echo "Starting development test watcher..."
	python -m pytest-watch tests/unit/ -- -x --tb=short

# Benchmark targets
benchmark:
	@echo "Running performance benchmarks..."
	python -m pytest -m performance tests/performance/ \
		--durations=0 \
		--tb=short \
		-v

# Test data validation
validate-test-data:
	@echo "Validating test data and fixtures..."
	python -c "from tests.conftest import *; print('Test fixtures validated ✓')"

# Print test statistics
test-stats:
	@echo "Test Statistics:"
	@echo "==============="
	@find tests/ -name "test_*.py" | wc -l | xargs echo "Test files:"
	@grep -r "def test_" tests/ | wc -l | xargs echo "Test functions:"
	@grep -r "@.*_test" tests/ | wc -l | xargs echo "Test decorators:"
	@echo ""
	@echo "Test distribution:"
	@find tests/unit/ -name "test_*.py" 2>/dev/null | wc -l | xargs echo "  Unit tests:"
	@find tests/integration/ -name "test_*.py" 2>/dev/null | wc -l | xargs echo "  Integration tests:"
	@find tests/performance/ -name "test_*.py" 2>/dev/null | wc -l | xargs echo "  Performance tests:"
	@find tests/security/ -name "test_*.py" 2>/dev/null | xargs echo "  Security tests:"

# Help for specific categories
help-test:
	@echo "Test Execution Help"
	@echo "=================="
	@echo ""
	@echo "test-unit:        Fast, isolated unit tests"
	@echo "test-integration: Component interaction tests"
	@echo "test-performance: Performance characteristic tests"
	@echo "test-security:    Security measure verification tests"
	@echo "test-fast:        Alias for unit tests"
	@echo "test-slow:        All tests except unit tests"
	@echo "test-all:         Complete test suite"
	@echo "test-coverage:    Tests with coverage reporting"

help-quality:
	@echo "Code Quality Help"
	@echo "================"
	@echo ""
	@echo "lint:    Check code style and potential issues"
	@echo "format:  Auto-format code according to style guide"
	@echo "check:   Run all quality checks"

help-ci:
	@echo "CI/CD Help"
	@echo "=========="
	@echo ""
	@echo "ci-test:  Full CI test suite with coverage"
	@echo "ci-quick: Quick CI tests (unit only)"