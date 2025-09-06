#!/bin/bash
# Test script to exactly match GitHub Actions CI/CD environment using Docker

set -e  # Exit on error

echo "=== Testing wry in CI-like environment using Docker ==="
echo

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker is not installed!${NC}"
    echo "Please install Docker to run CI tests locally"
    exit 1
fi

# Python versions to test (matching CI matrix)
PYTHON_VERSIONS=("3.10" "3.11" "3.12")

# Function to run tests in Docker
test_python_version() {
    local version=$1
    echo
    echo -e "${YELLOW}Testing with Python $version (Ubuntu latest)${NC}"
    echo "================================================"

    # Run tests in Docker container matching GitHub Actions environment
    docker run --rm -v "$(pwd)":/workspace -w /workspace python:${version}-slim bash -c "
        set -e

        # Install system dependencies
        apt-get update -qq && apt-get install -y -qq git > /dev/null 2>&1

        # Configure git to trust the workspace (needed for setuptools-scm)
        git config --global --add safe.directory /workspace

        # Upgrade pip
        python -m pip install --upgrade pip --quiet

        # Install package with dev dependencies
        echo 'Installing dependencies...'
        pip install -e '.[dev,test]' --quiet

        # Install pre-commit hooks
        pre-commit install

        # Run pre-commit checks
        echo 'Running pre-commit checks...'
        pre-commit run --all-files --show-diff-on-failure
    "

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Python $version tests passed${NC}"
    else
        echo -e "${RED}✗ Python $version tests failed${NC}"
        exit 1
    fi
}

# Test each Python version
for version in "${PYTHON_VERSIONS[@]}"; do
    test_python_version $version
done

echo
echo -e "${GREEN}All CI tests passed locally!${NC}"
