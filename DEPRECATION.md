# Deprecation Tracking

This document tracks all deprecated features for easy removal in future versions.

## Deprecated in v0.6.0 → Remove in v1.0.0

### 1. AutoClickParameter Enum

**Location**: `wry/click_integration.py:97-115`
**Deprecated**: v0.6.0
**Remove**: v1.0.0
**Replacement**: `AutoOption()`, `AutoArgument()`, `AutoExclude()`

**Code markers**:

- Class definition: `wry/click_integration.py:97` (marked with `# DEPRECATED v0.6.0`)
- Detection logic: `wry/click_integration.py:492-517` (marked with `# DEPRECATED v0.6.0` and `# TODO: Remove in v1.0.0`)

**Migration**:

```python
# Old:
field: Annotated[str, AutoClickParameter.OPTION]

# New:
field: Annotated[str, AutoOption()]
```

### 2. Standalone CommaSeparated Marker

**Location**: `wry/comma_separated.py:171-203`
**Deprecated**: v0.6.0
**Remove**: v1.0.0
**Replacement**: `AutoOption(comma_separated=True)`

**Code markers**:

- Class definition: `wry/comma_separated.py:171` (marked with `# DEPRECATED v0.6.0`)
- Detection logic: `wry/click_integration.py:463-480` (marked with `# DEPRECATED v0.6.0` and `# TODO: Remove in v1.0.0`)

**Migration**:

```python
# Old:
tags: Annotated[list[str], CommaSeparated]

# New:
tags: Annotated[list[str], AutoOption(comma_separated=True)]
```

### 3. Unprefixed env_prefix ClassVar

**Location**: `wry/core/model.py:67`
**Deprecated**: v0.6.0
**Remove**: v1.0.0
**Replacement**: `wry_env_prefix`

**Code markers**:

- ClassVar definition: `wry/core/model.py:67` (marked with `# DEPRECATED v0.6.0`)
- Migration logic: `wry/core/model.py:77-88` (marked with `# DEPRECATED v0.6.0` and `# TODO: Remove in v1.0.0`)

**Migration**:

```python
# Old:
class Config(AutoWryModel):
    env_prefix: ClassVar[str] = "MYAPP_"

# New:
class Config(AutoWryModel):
    wry_env_prefix: ClassVar[str] = "MYAPP_"
```

### 4. Unprefixed comma_separated_lists ClassVar

**Location**: `wry/core/model.py:68`
**Deprecated**: v0.6.0
**Remove**: v1.0.0
**Replacement**: `wry_comma_separated_lists`

**Code markers**:

- ClassVar definition: `wry/core/model.py:68` (marked with `# DEPRECATED v0.6.0`)
- Migration logic: `wry/core/model.py:90-101` (marked with `# DEPRECATED v0.6.0` and `# TODO: Remove in v1.0.0`)

**Migration**:

```python
# Old:
class Config(AutoWryModel):
    comma_separated_lists: ClassVar[bool] = True

# New:
class Config(AutoWryModel):
    wry_comma_separated_lists: ClassVar[bool] = True
```

### 5. Using Wry Marker Classes Without Calling Them

**Location**: `wry/click_integration.py:481-491`
**Deprecated**: v0.6.0
**Remove**: v1.0.0
**Replacement**: Call the class (add parentheses)

**Code markers**:

- Detection logic: `wry/click_integration.py:481-491` (marked with `# DEPRECATED v0.6.0` and `# TODO: Remove in v1.0.0`)

**Migration**:

```python
# Old (works but not recommended):
field: Annotated[str, AutoOption]

# New:
field: Annotated[str, AutoOption()]
```

## Removal Checklist for v1.0.0

When removing deprecated features in v1.0.0:

### Code Removal

- [ ] Remove `AutoClickParameter` enum class (`wry/click_integration.py:97-115`)
- [ ] Remove AutoClickParameter detection block (`wry/click_integration.py:492-517`)
- [ ] Remove `CommaSeparated` marker class (`wry/comma_separated.py:171-203`)
- [ ] Remove CommaSeparated detection block (`wry/click_integration.py:463-480`)
- [ ] Remove `env_prefix` ClassVar (`wry/core/model.py:67`)
- [ ] Remove env_prefix migration block (`wry/core/model.py:77-88`)
- [ ] Remove `comma_separated_lists` ClassVar (`wry/core/model.py:68`)
- [ ] Remove comma_separated_lists migration block (`wry/core/model.py:90-101`)
- [ ] Remove uncalled marker class detection (`wry/click_integration.py:481-491`)

### Test Updates

- [ ] Remove or update tests using `AutoClickParameter` enum
- [ ] Remove or update tests using standalone `CommaSeparated`
- [ ] Remove or update tests using `env_prefix` without deprecation expectations
- [ ] Remove or update tests using `comma_separated_lists` without deprecation expectations
- [ ] Update `test_classvar_migration.py` - these tests won't be needed

### Documentation Updates

- [ ] Remove deprecation sections from `CHANGELOG.md`
- [ ] Remove migration guide from `CHANGELOG.md`
- [ ] Remove deprecated patterns from examples
- [ ] Update `AI_KNOWLEDGE_BASE.md` to remove old API references
- [ ] Update `README.md` to remove old patterns
- [ ] Archive this `DEPRECATION.md` file

## Search Commands for Finding Deprecated Code

Use these to find all deprecated code for removal:

```bash
# Find all TODO: Remove in v1.0.0 markers
grep -r "TODO: Remove in v1.0.0" wry/

# Find all DEPRECATED v0.6.0 markers
grep -r "DEPRECATED v0.6.0" wry/

# Find AutoClickParameter usage
grep -r "AutoClickParameter" wry/ tests/

# Find CommaSeparated standalone usage
grep -r "CommaSeparated" wry/ tests/ | grep -v "comma_separated"

# Find old ClassVar names
grep -r "env_prefix:" wry/ tests/ | grep -v "wry_env_prefix"
grep -r "comma_separated_lists:" wry/ tests/ | grep -v "wry_comma_separated_lists"
```

## Testing Deprecated Features

Before removal, ensure all deprecated features have:

1. ✅ Deprecation warnings in place
2. ✅ Backwards compatibility tests
3. ✅ Migration documented in CHANGELOG
4. ✅ Clear TODO markers in code

After removal in v1.0.0:

1. Run full test suite
2. Update all examples
3. Create migration guide
4. Update version compatibility matrix
