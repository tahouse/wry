"""DRY CLI - Don't Repeat Yourself CLI builder."""

from __future__ import annotations

from typing import Callable

"""DRY CLI - Don't Repeat Yourself CLI builder.

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
    from drycli import DryModel, generate_click_options, AutoOption

    class MyConfig(DryModel):
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
    # Fallback for development installs
    __version__ = "0.0.1-dev"
    __version_full__ = __version__
    __commit_id__ = None

__author__ = "Tyler House"
__email__ = "26489166+tahouse@users.noreply.github.com"

# Placeholder exports to reserve the API namespace
__all__ = [
    "DryModel",
    "AutoOption",
    "AutoArgument",
    "generate_click_options",
    "ValueSource",
    "coming_soon",
    "__version__",
    "__version_full__",
    "__commit_id__",
]


class ValueSource:
    """Placeholder for value source tracking."""

    CLI = "cli"
    CONFIG = "config"
    ENV = "env"
    DEFAULT = "default"


class AutoOption:
    """Placeholder for automatic Click option generation."""

    pass


class AutoArgument:
    """Placeholder for automatic Click argument generation."""

    pass


class DryModel:
    """Placeholder for the main configuration model base class."""

    pass


def generate_click_options(model_class: type) -> Callable[[Callable], Callable]:
    """Placeholder for generating Click options from Pydantic models.

    This will be the main decorator that extracts Annotated fields from
    your Pydantic model and generates the corresponding Click options.

    Args:
        model_class: Pydantic model class with Annotated fields

    Returns:
        Decorator function that applies Click options to the command
    """

    def decorator(func: Callable) -> Callable:
        return func

    return decorator


def coming_soon() -> str:
    """This package is under development.

    Returns:
        A message indicating the package is coming soon.
    """
    return (
        "DRY CLI is coming soon! 🚧\n\n"
        "This package will eliminate repetition in CLI development by letting you "
        "define your configuration schema once using Pydantic models and "
        "automatically generating type-safe Click interfaces.\n\n"
        "Features in development:\n"
        "• Type-safe CLI generation from Pydantic models\n"
        "• Environment variable support with auto-discovery\n"
        "• Configuration file loading (JSON/YAML)\n"
        "• Value source tracking\n"
        "• Automatic validation with helpful errors\n"
        "• Constraint integration\n\n"
        "Check back soon for the full release!"
    )


# For now, just export the coming_soon function for testing
if __name__ == "__main__":
    print(coming_soon())
