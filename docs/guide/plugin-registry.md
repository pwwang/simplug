# Plugin Registry

The plugin registry manages all registered plugins and their state.

## Registering Plugins

### Registering Classes or Instances

Register plugins using `register()` method:

```python
# Register class (auto-instantiated if no __init__ params)
simplug.register(MyPlugin)

# Register instance (use when __init__ needs params)
instance = MyPlugin(config={})
simplug.register(instance)
```

### Registering Multiple Plugins

Register multiple plugins at once:

```python
simplug.register(PluginA, PluginB, PluginC)
```

### Registering by Module Name

Register a plugin by module string:

```python
simplug.register('mypackage.plugins.myplugin')
```

The module will be imported automatically.

## Querying Plugins

### Get Plugin by Name

Get a specific plugin:

```python
plugin = simplug.get_plugin('myplugin')

# Get raw plugin object
plugin_obj = simplug.get_plugin('myplugin', raw=True)
```

Raises `NoSuchPlugin` if plugin not found.

### Get All Plugins

Get all registered plugins:

```python
# Get plugin wrappers
plugins = simplug.get_all_plugins()

# Get raw plugin objects
plugins = simplug.get_all_plugins(raw=True)
```

Returns an `OrderedDiot` (ordered dictionary).

### Get Enabled Plugins

Get only enabled plugins:

```python
# Get enabled plugin wrappers
enabled = simplug.get_enabled_plugins()

# Get enabled raw objects
enabled = simplug.get_enabled_plugins(raw=True)
```

### Get Plugin Names

Get list of all plugin names:

```python
all_names = simplug.get_all_plugin_names()
# Returns: ['plugin1', 'plugin2', 'plugin3']
```

Get enabled plugin names:

```python
enabled_names = simplug.get_enabled_plugin_names()
# Returns: ['plugin1', 'plugin3']
```

Names are in execution order (sorted by priority).

## Enabling and Disabling Plugins

### Disable Plugins

Temporarily disable plugins:

```python
# Disable specific plugin
simplug.disable('plugin1')

# Disable multiple
simplug.disable('plugin1', 'plugin2')
```

### Enable Plugins

Re-enable disabled plugins:

```python
# Enable specific plugin
simplug.enable('plugin1')

# Enable multiple
simplug.enable('plugin1', 'plugin2')
```

### Direct Plugin Access

You can also access plugins directly:

```python
# Get plugin and disable
plugin = simplug.get_plugin('myplugin')
plugin.disable()

# Get plugin and enable
plugin = simplug.get_plugin('myplugin')
plugin.enable()
```

## Plugin Context Manager

Temporarily enable or disable plugins using a context manager:

```python
# Enable only specific plugins
with simplug.plugins_context(['plugin1', 'plugin2']):
    # Only plugin1 and plugin2 are active
    simplug.hooks.my_hook(data)
# Original state restored
```

### Context Syntax

```python
# Enable only these plugins
with simplug.plugins_context(['plugin1', 'plugin2']):
    pass

# Add plugin
with simplug.plugins_context(['+plugin3']):
    # plugin3 added to enabled set
    pass

# Remove plugin
with simplug.plugins_context(['-plugin1']):
    # plugin1 removed from enabled set
    pass

# Multiple operations
with simplug.plugins_context(['-plugin1', '+plugin3']):
    # plugin1 disabled, plugin3 enabled
    pass

# No changes
with simplug.plugins_context(None):
    # All plugins maintain current state
    pass
```

### Context Rules

- All plugins without prefix (`+`/`-`): Only those are enabled, all others disabled
- With prefixes: All start current state, then apply changes
- Context exit: Original state automatically restored

## Plugin Names

Plugin names are determined in this priority:

1. `_name` attribute (when loaded from entrypoint)
2. `name` attribute
3. `__name__` attribute (lowercased)
4. `__class__.__name__` attribute (lowercased)

```python
class MyPlugin:
    name = "custom_name"  # Will use "custom_name"

# Or
class MyPlugin:
    pass  # Will use "myplugin" (lowercased)
```

## Duplicate Plugin Names

Registering a plugin with existing name raises error:

```python
simplug.register(Plugin1)  # Name: "plugin1"
simplug.register(Plugin2)  # Also has name: "plugin1"
# Raises PluginRegistered
```

Same plugin object is allowed:

```python
p = Plugin1()
simplug.register(p)
simplug.register(p)  # Same object, no error
```

## Inspection Methods

### Check if Plugin Exists

```python
try:
    plugin = simplug.get_plugin('myplugin')
    exists = True
except NoSuchPlugin:
    exists = False
```

### Get Plugin Count

```python
all_count = len(simplug.get_all_plugins())
enabled_count = len(simplug.get_enabled_plugins())
```

### List Disabled Plugins

```python
all_plugins = set(simplug.get_all_plugin_names())
enabled_plugins = set(simplug.get_enabled_plugin_names())
disabled = all_plugins - enabled_plugins
```

## Complete Example

```python
from simplug import Simplug

simplug = Simplug('app')

# Define hook
@simplug.spec
def process(data):
    pass

# Create plugins
class PluginA:
    name = "plugin_a"
    priority = -1  # Higher priority

    @simplug.impl
    def process(self, data):
        return f"A: {data}"

class PluginB:
    name = "plugin_b"

    @simplug.impl
    def process(self, data):
        return f"B: {data}"

class PluginC:
    name = "plugin_c"
    priority = 1  # Lower priority

    @simplug.impl
    def process(self, data):
        return f"C: {data}"

# Register all
simplug.register(PluginA, PluginB, PluginC)

# Check registry
print(f"All plugins: {simplug.get_all_plugin_names()}")
# Output: ['plugin_a', 'plugin_b', 'plugin_c']

print(f"Enabled: {simplug.get_enabled_plugin_names()}")
# Output: ['plugin_a', 'plugin_b', 'plugin_c']

# Disable one
simplug.disable('plugin_b')
print(f"Enabled: {simplug.get_enabled_plugin_names()}")
# Output: ['plugin_a', 'plugin_c']

# Use context to enable only plugin_b
with simplug.plugins_context(['plugin_b']):
    print(f"In context: {simplug.get_enabled_plugin_names()}")
    # Output: ['plugin_b']
    result = simplug.hooks.process("test")
    print(result)  # ["B: test"]

# Context exit - original state restored
print(f"After context: {simplug.get_enabled_plugin_names()}")
# Output: ['plugin_a', 'plugin_c']
```

## Next Steps

- **[Priority System](priority-system.md)** - How execution order is determined
- **[Setuptools Entrypoints](entrypoints.md)** - Loading plugins from packages
- **[Implementing Hooks](implementing-hooks.md)** - Creating plugins
