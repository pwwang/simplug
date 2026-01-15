# simplug

A simple plugin system for Python with async hooks support.

## Features

- **Decorator-based API**: Define hooks with `@simplug.spec` and implement with `@simplug.impl`
- **Async support**: First-class async hooks with sync/async bridging
- **Flexible result collection**: 18 built-in strategies for collecting plugin results
- **Priority system**: Control plugin execution order
- **Setuptools entrypoints**: Load plugins from installed packages
- **Singleton per project**: Same instance returned for same project name

## Installation

```shell
pip install -U simplug
```

## Quick Start

```python
from simplug import Simplug

# Create a plugin manager
simplug = Simplug('myproject')

# Define a hook specification
class MySpec:
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

## Documentation

Full documentation is available at [https://pwwang.github.io/simplug/](https://pwwang.github.io/simplug/)

## Getting Started

1. **Define hooks** - Specify what plugins can customize
2. **Implement hooks** - Create plugins with implementations
3. **Register plugins** - Load plugins into your application
4. **Call hooks** - Trigger plugin execution

For detailed guides and API reference, see the [full documentation](https://pwwang.github.io/simplug/).

## Examples

See the [examples](examples/) directory for complete examples:
- [`examples/toy.py`](examples/toy.py) - A minimal 30-line demo
- [`examples/complete/`](examples/complete/) - Full example with setuptools entrypoints

## License

MIT
