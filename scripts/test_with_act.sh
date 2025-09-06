#!/bin/bash
# Run GitHub Actions locally using act (https://github.com/nektos/act)

set -e

echo "=== Running GitHub Actions CI/CD locally with act ==="
echo

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if act is installed
if ! command -v act &> /dev/null; then
    echo -e "${RED}act is not installed!${NC}"
    echo
    echo "Install act to run GitHub Actions locally:"
    echo "  macOS: brew install act"
    echo "  Linux: curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash"
    echo
    echo "See: https://github.com/nektos/act"
    exit 1
fi

# Run the test job from CI/CD workflow
echo -e "${YELLOW}Running CI/CD test job...${NC}"
act push --job test -W .github/workflows/ci-cd.yml

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ All CI tests passed locally!${NC}"
else
    echo -e "${RED}✗ CI tests failed${NC}"
    exit 1
fi
