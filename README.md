# drycli

**DRY (Don't Repeat Yourself) CLI** - Define your CLI once with Pydantic models.

[![PyPI version](https://badge.fury.io/py/drycli.svg)](https://badge.fury.io/py/drycli)
[![Python versions](https://img.shields.io/pypi/pyversions/drycli.svg)](https://pypi.org/project/drycli/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🚧 Under Development

This package is currently being developed. The namespace is reserved and the initial release is coming soon!

## What is drycli?

`drycli` is a modern Python library that eliminates repetition in CLI development. Define your configuration schema **once** using Pydantic models and automatically get:

✅ **Type-safe command-line interfaces** - Full IDE support with autocomplete
✅ **Automatic validation** - Helpful error messages with constraint checking
✅ **Environment variable support** - Auto-discovery and type conversion
✅ **Configuration file loading** - JSON/YAML with proper precedence
✅ **Value source tracking** - Know where each setting came from
✅ **Auto-generated help text** - Documentation from your model
✅ **Constraint integration** - Pydantic validators become CLI help
✅ **Zero boilerplate** - No duplicate definitions

## Preview: How It Will Work

```python
from typing import Annotated
from pydantic import Field
import click
from drycli import DryModel, click_config, AutoOption

class ServerConfig(DryModel):
    """Configuration for the server."""

    # This creates --port with validation and help text automatically
    port: Annotated[int, AutoOption] = Field(
        default=8000,
        ge=1,
        le=65535,
        description="Port number to bind to"
    )

    # This creates --host
    host: Annotated[str, AutoOption] = Field(
        default="localhost",
        description="Host address to bind to"
    )

    # This creates --debug/--no-debug flag
    debug: Annotated[bool, AutoOption] = Field(
        default=False,
        description="Enable debug mode"
    )

# Just one decorator and you get everything!
@click.command()
@click_config(ServerConfig)
def serve(config: ServerConfig) -> None:
    """Start the server with the given configuration."""
    print(f"Starting server on {config.host}:{config.port}")
    if config.debug:
        print("Debug mode enabled")

    # config is fully typed - your IDE knows all the fields!
    # You also get source tracking:
    # print(f"Port from: {config.source.port}")  # "cli", "env", "config", or "default"

if __name__ == "__main__":
    serve()
```

This single definition gives you:

- `--port` option with integer validation (1-65535)
- `--host` option with string type
- `--debug/--no-debug` boolean flag
- `--config` option for JSON/YAML files
- `--help` with auto-generated documentation
- Environment variables: `MYAPP_PORT`, `MYAPP_HOST`, `MYAPP_DEBUG`
- Full type safety and IDE support

## The Problem drycli Solves

**Before** (traditional approach):

```python
# Define your data model
class ServerConfig:
    def __init__(self, port: int, host: str, debug: bool):
        self.port = port
        self.host = host
        self.debug = debug

# Define your CLI (duplicate information!)
@click.command()
@click.option('--port', type=int, default=8000, help='Port number')
@click.option('--host', type=str, default='localhost', help='Host address')
@click.option('--debug/--no-debug', default=False, help='Debug mode')
def serve(port: int, host: str, debug: bool):
    config = ServerConfig(port, host, debug)  # Manual construction
    # No validation, no environment variables, no config files...
```

**After** (with drycli):

```python
class ServerConfig(DryModel):
    port: Annotated[int, AutoOption] = Field(default=8000, ge=1, le=65535, description="Port number")
    host: Annotated[str, AutoOption] = Field(default="localhost", description="Host address")
    debug: Annotated[bool, AutoOption] = Field(default=False, description="Debug mode")

@click.command()
@click_config(ServerConfig)
def serve(config: ServerConfig):  # Fully typed, automatically constructed!
    # Everything just works - validation, env vars, config files, help text
```

## Why Choose drycli?

- **🎯 DRY Principle**: Define once, use everywhere
- **🔒 Type Safety**: Full mypy and IDE support
- **⚡ Zero Boilerplate**: No duplicate CLI definitions
- **🌍 Environment Ready**: Automatic env var support
- **📁 Config Files**: JSON/YAML loading with precedence
- **🔍 Source Tracking**: Know where values came from
- **📚 Self-Documenting**: Help text from your models
- **✅ Validation**: Pydantic's powerful validation built-in

## Comparison with Existing Tools

| Feature | drycli | pydanclick | typer | argparse + pydantic |
|---------|--------|------------|-------|---------------------|
| Type Safety | ✅ | ✅ | ✅ | ⚠️ Manual |
| Zero Duplication | ✅ | ✅ | ❌ | ❌ |
| Environment Variables | ✅ | ❌ | ❌ | ⚠️ Manual |
| Config Files | ✅ | ❌ | ❌ | ⚠️ Manual |
| Source Tracking | ✅ | ❌ | ❌ | ❌ |
| Constraint Integration | ✅ | ⚠️ Limited | ❌ | ⚠️ Manual |
| Auto Help Generation | ✅ | ✅ | ✅ | ⚠️ Manual |

## Coming Soon

- 📦 **Initial Release** - Core functionality
- 📖 **Full Documentation** - Comprehensive guides and API reference
- 🧪 **Examples** - Real-world usage patterns
- 🔌 **Plugins** - Extensions for popular frameworks
- 🎨 **Rich Integration** - Beautiful terminal output
- 📊 **Advanced Features** - Nested configs, custom validators, and more

## Development Status

- [x] Namespace reserved on PyPI
- [x] API design finalized
- [ ] Core implementation
- [ ] Test suite
- [ ] Documentation
- [ ] Examples
- [ ] Initial release

## Stay Updated

- ⭐ **Star this repo** to get notified of updates
- 👀 **Watch releases** for the latest versions
- 🐛 **Open issues** for feature requests or bug reports

## Contributing

Interested in contributing? Great! The package is in early development and contributions are welcome.

## License

MIT License - see [LICENSE](LICENSE) file for details.

---

**drycli** - Because your CLI definitions should be as DRY as your code! 🏜️
# Trigger build
