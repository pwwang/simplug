# simplug

A simple plugin system for Python with async hooks support.

## Overview

simplug is a lightweight, decorator-based plugin system that makes it easy to add extensibility to your Python applications. With first-class async support, flexible result collection strategies, and a clean API, simplug is perfect for building modular applications.

### Key Features

- **Decorator-based API** - Define hooks with `@simplug.spec` and implement with `@simplug.impl`
- **Async support** - First-class async hooks with automatic sync/async bridging
- **Flexible result collection** - 18 built-in strategies for collecting plugin results
- **Priority system** - Control plugin execution order with priorities
- **Setuptools entrypoints** - Automatically discover and load plugins from installed packages
- **Singleton per project** - Same instance returned for each project name
- **Minimal dependencies** - Only depends on `diot`

## Installation

```bash
pip install -U simplug
```

## Quick Example

```python
from simplug import Simplug

# Create a plugin manager
simplug = Simplug('myapp')

# Define a hook specification
class Hooks:
    @simplug.spec
    def process_data(self, data):
        """Process data in plugins."""

# Implement the hook in plugins
class PluginA:
    @simplug.impl
    def process_data(self, data):
        return data.upper()

class PluginB:
    @simplug.impl
    def process_data(self, data):
        return data.lower()

# Register plugins
simplug.register(PluginA, PluginB)

# Call the hook
results = simplug.hooks.process_data("Hello")
print(results)  # ['HELLO', 'hello']
```

## How It Works

simplug follows a simple three-step workflow:

1. **Define hooks** - Use `@simplug.spec` to specify extension points in your application
2. **Implement hooks** - Use `@simplug.impl` to create plugins that extend functionality
3. **Register & call** - Register plugins and call hooks to execute plugin code

## Use Cases

simplug is ideal for:

- Building extensible applications
- Creating plugin-based architectures
- Implementing command systems
- Adding third-party integration points
- Modularizing large codebases

## Next Steps

- **[Getting Started](getting-started.md)** - Learn the basics
- **[Guides](guide/defining-hooks.md)** - Detailed documentation on specific features
- **[API Reference](api/index.md)** - Complete API documentation
- **[Examples](examples.md)** - Code examples and patterns

## License

MIT
