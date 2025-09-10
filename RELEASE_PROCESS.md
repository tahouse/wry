# Release Process for Wry

This document outlines the correct process for creating a new release.

## Release Checklist

Follow these steps IN ORDER for each release:

1. **Make all code changes**
   - Implement features/fixes
   - Ensure all tests pass (`./check.sh`)
   - Fix any linting issues

2. **Update documentation**
   - Update README.md if needed
   - Update any affected documentation

3. **Update CHANGELOG.md**
   - Add a new version section under `## [Unreleased]`
   - Document all changes following [Keep a Changelog](https://keepachangelog.com/) format
   - Update the comparison links at the bottom of the file

4. **Commit all changes**
   ```bash
   git add -A
   git commit -m "chore: prepare for vX.Y.Z release"
   ```

5. **Create signed tag**
   ```bash
   git tag -s vX.Y.Z -m "Release vX.Y.Z: brief description"
   ```

6. **Push changes and tag**
   ```bash
   git push origin main
   git push origin vX.Y.Z
   ```

## Example

For v0.1.8 release:

```bash
# 1. Make code changes
# ... implement type annotation improvements ...

# 2. Update CHANGELOG.md
# Add new section:
## [0.1.8] - 2025-09-10

### Fixed
- Improved type annotations for `generate_click_parameters` decorator

# 3. Commit everything
git add -A
git commit -m "chore: prepare for v0.1.8 release"

# 4. Create tag
git tag -s v0.1.8 -m "Release v0.1.8: improve type annotations"

# 5. Push
git push origin main
git push origin v0.1.8
```

## Common Mistakes to Avoid

- ❌ Creating the tag before updating CHANGELOG.md
- ❌ Forgetting to update comparison links in CHANGELOG.md
- ❌ Not running `./check.sh` before tagging
- ❌ Creating unsigned tags (always use `-s` for signed tags)

## CI/CD Pipeline

Once a tag is pushed, the GitHub Actions workflow will:
1. Run all tests across Python 3.10, 3.11, and 3.12
2. Build the distribution packages
3. Publish to PyPI (for tags) or TestPyPI (for main branch)
4. Create a GitHub release with notes from CHANGELOG.md
