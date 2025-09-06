# Scripts

This directory contains utility scripts for the wry project.

## Testing Scripts

- **`test_all_versions.sh`** - Test the project across all supported Python versions (3.10, 3.11, 3.12) locally
- **`test_ci_locally.sh`** - Run tests in a Docker container that mimics the CI environment
- **`test_with_act.sh`** - Run GitHub Actions workflows locally using the `act` tool

## Release Scripts

- **`extract_release_notes.py`** - Extract release notes from CHANGELOG.md for a specific version. Used by CI/CD to generate GitHub release descriptions.

## Usage

All scripts should be run from the project root:

```bash
# From project root
./scripts/test_all_versions.sh
./scripts/extract_release_notes.py v0.1.0
```
