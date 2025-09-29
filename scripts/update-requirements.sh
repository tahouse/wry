#!/usr/bin/env bash
# Update requirements-dev.txt with current environment versions
# This ensures CI/CD uses the same package versions as local development

set -euo pipefail

echo "Updating requirements-dev.txt with current environment versions..."

# Create a temporary file
TEMP_FILE=$(mktemp)

# Write header
cat > "$TEMP_FILE" << 'EOF'
# Development dependencies with pinned versions
# This file ensures consistent behavior between local and CI environments
# Generated from local environment to match CI behavior
# Last updated: $(date)

EOF

# Add current date
sed -i.bak "s/\$(date)/$(date)/" "$TEMP_FILE" && rm "$TEMP_FILE.bak"

# Extract versions for core dependencies
echo "# Core dependencies" >> "$TEMP_FILE"
pip freeze | grep -E "^click==" >> "$TEMP_FILE" || echo "click not found"
pip freeze | grep -E "^pydantic==" >> "$TEMP_FILE" || echo "pydantic not found"
pip freeze | grep -E "^pydantic[_-]core==" >> "$TEMP_FILE" || echo "pydantic-core not found"
pip freeze | grep -E "^annotated-types==" >> "$TEMP_FILE" || echo "annotated-types not found"
pip freeze | grep -E "^setuptools-scm==" >> "$TEMP_FILE" || echo "setuptools-scm not found"

echo "" >> "$TEMP_FILE"
echo "# Testing dependencies" >> "$TEMP_FILE"
pip freeze | grep -E "^pytest==" >> "$TEMP_FILE" || echo "pytest not found"
pip freeze | grep -E "^pytest-cov==" >> "$TEMP_FILE" || echo "pytest-cov not found"
pip freeze | grep -E "^pytest-xdist==" >> "$TEMP_FILE" || echo "pytest-xdist not found"
pip freeze | grep -E "^coverage\[" >> "$TEMP_FILE" || pip freeze | grep -E "^coverage==" >> "$TEMP_FILE" || echo "coverage not found"

echo "" >> "$TEMP_FILE"
echo "# Linting and formatting" >> "$TEMP_FILE"
pip freeze | grep -E "^ruff==" >> "$TEMP_FILE" || echo "ruff not found"
pip freeze | grep -E "^mypy==" >> "$TEMP_FILE" || echo "mypy not found"

echo "" >> "$TEMP_FILE"
echo "# Type stubs" >> "$TEMP_FILE"
pip freeze | grep -E "^types-" | head -5 >> "$TEMP_FILE"

echo "" >> "$TEMP_FILE"
echo "# Pre-commit (for CI)" >> "$TEMP_FILE"
pip freeze | grep -E "^pre-commit==" >> "$TEMP_FILE" || echo "pre-commit not found"

# Move temp file to final location
mv "$TEMP_FILE" requirements-dev.txt

echo "Updated requirements-dev.txt successfully!"
echo ""
echo "To use these requirements:"
echo "  pip install -r requirements-dev.txt"
echo "  pip install -e ."
