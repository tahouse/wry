"""WRY - Why Repeat Yourself? CLI builder."""

from __future__ import annotations

"""WRY - Why Repeat Yourself? CLI builder.

Define your CLI once using Pydantic models and get:
- Type-safe command-line interfaces
- Automatic validation with helpful error messages
- Environment variable support
- Configuration file loading (JSON, YAML)
- Auto-generated help text
- Value source tracking (CLI, config file, environment, defaults)
- Constraint validation with readable error messages
- And more!

Example:
    ```python
    from typing import Annotated, Any
    from pydantic import Field
    import click
    from wry import WryModel, generate_click_options, AutoOption

    class MyConfig(WryModel):
        timeout: Annotated[int, AutoOption] = Field(
            default=30,
            ge=0,
            le=3600,
            description="Timeout in seconds"
        )
        verbose: Annotated[bool, AutoOption] = Field(
            default=False,
            description="Enable verbose output"
        )

    @click.command()
    @generate_click_options(MyConfig)
    @click.pass_context
    def my_command(ctx: click.Context, **kwargs: Any) -> None:
        config = MyConfig.from_click_context(ctx, **kwargs)
        if config.verbose:
            print(f"Using timeout: {config.timeout}")
        # Access source tracking: config.source.timeout
    ```

Coming soon - this package is under active development.
"""

# Version is managed by setuptools-scm from git tags
try:
    from ._version import __commit_id__, __version__

    # Create a full version string with git info
    __version_full__ = __version__
    if __commit_id__:
        __version_full__ += f"+{__commit_id__}"
except ImportError:
    # Fallback for development/editable installs
    try:
        # Try to get version dynamically for editable installs
        from setuptools_scm import get_version

        __version__ = get_version(root="../..", relative_to=__file__)
        # Extract commit hash from version if present
        if "+" in __version__ and "g" in __version__:
            # Version like "0.0.2+g1234567" or "0.0.2.dev1+g1234567"
            __commit_id__ = __version__.split("+")[-1].split(".")[0]
            __version_full__ = __version__
        else:
            __commit_id__ = None
            __version_full__ = __version__
        # Clean version for consistency
        __version__ = __version__.split("+")[0]
    except Exception:
        # Ultimate fallback
        __version__ = "0.0.1-dev"
        __version_full__ = __version__
        __commit_id__ = None

__author__ = "Tyler House"
__email__ = "26489166+tahouse@users.noreply.github.com"

# Import the actual implementation
from .auto_model import AutoWryModel, create_auto_model  # noqa: E402
from .click_integration import (  # noqa: E402
    AutoClickParameter,
    build_config_with_sources,
    config_option,
    eager_json_config,
    generate_click_parameters,
)
from .core import (  # noqa: E402
    FieldWithSource,
    TrackedValue,
    ValueSource,
    WryModel,
    extract_field_constraints,
)
from .multi_model import (  # noqa: E402
    create_models,
    multi_model,
    singleton_option,
    split_kwargs_by_model,
)

# Convenience aliases
AutoOption = AutoClickParameter.OPTION
AutoArgument = AutoClickParameter.ARGUMENT
AutoExclude = AutoClickParameter.EXCLUDE

# Help system
from .help_system import get_help_content, print_help, show_help_index  # noqa: E402

# Re-export all public APIs
__all__ = [
    # Core functionality
    "WryModel",
    "AutoWryModel",
    "create_auto_model",
    "ValueSource",
    "TrackedValue",
    "FieldWithSource",
    "extract_field_constraints",
    # Click integration
    "AutoClickParameter",
    "generate_click_parameters",
    "eager_json_config",
    "config_option",
    "build_config_with_sources",
    # Multi-model support
    "multi_model",
    "create_models",
    "split_kwargs_by_model",
    "singleton_option",
    # Convenience exports
    "AutoOption",
    "AutoArgument",
    "AutoExclude",
    # Help system
    "get_help_content",
    "print_help",
    "show_help_index",
    # Version info
    "__version__",
    "__version_full__",
    "__commit_id__",
]
