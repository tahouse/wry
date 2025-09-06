#!/bin/bash
# Test script to match CI/CD testing across Python versions

set -e  # Exit on error

echo "=== Testing wry across Python versions (matching CI/CD) ==="
echo

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if Python version is installed
check_python() {
    local version=$1
    if command -v python$version &> /dev/null; then
        echo -e "${GREEN}✓${NC} Python $version found"
        return 0
    else
        echo -e "${RED}✗${NC} Python $version not found"
        return 1
    fi
}

# Function to run tests for a specific Python version
run_tests() {
    local version=$1
    echo
    echo -e "${YELLOW}Testing with Python $version${NC}"
    echo "================================================"

    # Create a virtual environment for this Python version
    echo "Creating virtual environment..."
    python$version -m venv .venv-$version

    # Activate virtual environment
    source .venv-$version/bin/activate

    # Upgrade pip
    python -m pip install --upgrade pip --quiet

    # Install package with dev dependencies (matching CI)
    echo "Installing dependencies..."
    pip install -e ".[dev,test]" --quiet

    # Run pre-commit checks (matching CI)
    echo "Running pre-commit checks..."
    pre-commit run --all-files --show-diff-on-failure

    deactivate

    # Clean up virtual environment
    rm -rf .venv-$version

    echo -e "${GREEN}✓ Python $version tests passed${NC}"
}

# Check which Python versions are available
echo "Checking available Python versions..."
AVAILABLE_VERSIONS=()

for version in 3.10 3.11 3.12; do
    if check_python $version; then
        AVAILABLE_VERSIONS+=($version)
    fi
done

if [ ${#AVAILABLE_VERSIONS[@]} -eq 0 ]; then
    echo -e "${RED}No supported Python versions found!${NC}"
    echo "Please install Python 3.10, 3.11, or 3.12"
    exit 1
fi

echo
echo "Will test with: ${AVAILABLE_VERSIONS[@]}"
echo

# Run tests for each available version
for version in "${AVAILABLE_VERSIONS[@]}"; do
    run_tests $version
done

echo
echo -e "${GREEN}All tests passed!${NC}"
