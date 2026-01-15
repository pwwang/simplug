# Setuptools Entrypoints

simplug can automatically discover and load plugins from installed packages using setuptools entry points.

## What are Entrypoints?

Setuptools entry points allow third-party packages to register plugins that your application can discover. This enables:

- Automatic plugin discovery from installed packages
- No need to manually import and register plugins
- Decoupled plugin distribution

## Defining Entrypoints

### In Plugin Package

Add entry points to your plugin package's `setup.py` or `pyproject.toml`:

```python
# setup.py
from setuptools import setup

setup(
    name='my-plugin',
    packages=['my_plugin'],
    install_requires=['simplug'],
    entry_points={
        'myapp': [
            'my-plugin = my_plugin:MyPlugin',
        ]
    }
)
```

Or in `pyproject.toml`:

```toml
[project.entry-points."myapp"]
my-plugin = "my_plugin:MyPlugin"
```

The entry point group (`myapp` in this example) must match your simplug project name.

### Plugin Code

Your plugin just needs to implement hooks:

```python
# my_plugin/__init__.py
from simplug import Simplug

# Assume simplug instance is available at import time
# In practice, your app loads entrypoints after defining hooks

class MyPlugin:
    name = "my_plugin"

    @simplug.impl
    def process_data(self, data):
        return data.upper()
```

## Loading Entrypoints

### Load All Plugins

Load all plugins for your project:

```python
from simplug import Simplug

simplug = Simplug('myapp')

# Define hooks first
@simplug.spec
def process_data(data):
    pass

# Load all entry points for 'myapp' group
simplug.load_entrypoints()
```

### Load Specific Plugins

Load only specific entry points:

```python
# Load only one
simplug.load_entrypoints(only='my-plugin')

# Load multiple
simplug.load_entrypoints(only=['plugin1', 'plugin2'])
```

### Custom Group

Load from a different group:

```python
# Load from custom group
simplug.load_entrypoints(group='custom_group')
```

## Timing Considerations

### Define Hooks Before Loading

Always define your hooks **before** loading entry points:

```python
from simplug import Simplug

simplug = Simplug('myapp')

# Define hooks first
@simplug.spec
def process_data(data):
    pass

# Then load entry points
simplug.load_entrypoints()
```

Entry point plugins implement hooks defined before loading.

### Load After Registration

You can mix manual registration and entry points:

```python
# Manually register core plugins
simplug.register(CorePlugin)

# Then load external plugins
simplug.load_entrypoints()
```

## Entrypoint Names

Entry point names become plugin names. Use descriptive names:

```python
entry_points={
    'myapp': [
        'data-processor = my_plugin:DataProcessor',
        'validator = my_plugin:Validator,
        'logger = my_plugin:Logger,
    ]
}
```

Plugin names: `data_processor`, `validator`, `logger`.

## Complete Example

### Application

```python
# app/main.py
from simplug import Simplug

simplug = Simplug('myapp')

# Define hooks
class AppHooks:
    @simplug.spec
    def process(self, data):
        """Process data."""

    @simplug.spec
    def on_startup(self):
        """Called on startup."""

# Load plugins from entry points
simplug.load_entrypoints()

# Use
results = simplug.hooks.process("test")
print(f"Results: {results}")

# Call startup
simplug.hooks.on_startup()
```

### Plugin Package

```python
# my_plugin/setup.py
from setuptools import setup

setup(
    name='my-plugin',
    version='1.0.0',
    packages=['my_plugin'],
    py_modules=['my_plugin'],
    install_requires=['simplug'],
    entry_points={
        'myapp': [
            'my-plugin = my_plugin:MyPlugin',
        ]
    }
)
```

```python
# my_plugin/__init__.py
from simplug import Simplug

# Import simplug instance or it will be passed automatically
# For entrypoints, app must be imported first

class MyPlugin:
    name = "my_plugin"
    version = "1.0.0"

    @simplug.impl
    def process(self, data):
        return data.upper()

    @simplug.impl
    def on_startup(self):
        print("MyPlugin initialized!")
```

### Installation and Usage

```bash
# Install application
pip install myapp

# Install plugin (development mode)
cd my_plugin
pip install -e .

# Or install plugin (published)
pip install my-plugin

# Run app - plugins automatically loaded
python -m app
```

## Discovering Available Plugins

You can discover available entry points:

```python
from importlib import metadata

eps = metadata.entry_points(group='myapp')
for ep in eps:
    print(f"Found plugin: {ep.name} from {ep.value}")
```

## Best Practices

1. **Use descriptive entry point names** - Clear and unique
2. **Follow naming conventions** - Use kebab-case for entry point names
3. **Document required hooks** - Specify which hooks your plugin implements
4. **Handle missing dependencies** - Plugin should fail gracefully if deps missing
5. **Version your plugins** - Help users track compatibility

## Next Steps

- **[Defining Hooks](defining-hooks.md)** - Specifying hooks for plugins
- **[Implementing Hooks](implementing-hooks.md)** - Creating plugins
- **[Plugin Registry](plugin-registry.md)** - Managing loaded plugins
