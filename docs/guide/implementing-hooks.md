# Implementing Hooks

Plugins implement hooks defined by your application's specifications.

## Basic Syntax

Use the `@simplug.impl` decorator to implement a hook:

```python
class MyPlugin:
    @simplug.impl
    def my_hook(arg1, arg2):
        """Implement the hook."""
        return arg1 + arg2
```

## Plugin Structure

Plugins can be classes or modules. They just need to have methods decorated with `@simplug.impl`.

### Class-Based Plugins

```python
class DataProcessor:
    @simplug.impl
    def process_data(self, data):
        return data.upper()

simplug.register(DataProcessor)
```

### Module-Based Plugins

```python
# mymodule.py
@simplug.impl
def process_data(data):
    return data.upper()

# main.py
simplug.register('mymodule')
```

## Parameter Matching

Your implementation must match the hook specification's parameter names:

```python
# Specification
@simplug.spec
def my_hook(arg1, arg2):
    pass

# Valid implementation
@plugin.impl
def my_hook(arg1, arg2):
    return arg1 + arg2

# Invalid implementation (wrong names)
@plugin.impl
def my_hook(x, y):  # Raises HookSignatureDifferentFromSpec
    return x + y
```

## The `self` Parameter

When a hook specification includes `self`, your implementation can optionally include it:

```python
# Specification
@simplug.spec
def method_hook(self, data):
    pass

# Implementation with self
class MyPlugin:
    @simplug.impl
    def method_hook(self, data):
        # self is the plugin instance
        return self.transform(data)

    def transform(self, data):
        return data.upper()
```

If you include `self`, simplug will automatically pass the plugin instance when calling the hook.

## Returning Values

Hook implementations can return values that are collected based on the hook's result strategy:

```python
@plugin.impl
def process_data(data):
    return data.upper()  # Return value

@plugin.impl
def process_data(data):
    print(data)  # Side effect, returns None
```

See [Result Collection](result-collection.md) for how return values are collected.

## Plugin Names

simplug determines plugin names in this priority order:

1. `name` attribute
2. `__name__` attribute (lowercased)
3. `__class__.__name__` attribute (lowercased)

```python
class MyPlugin:
    name = "custom_name"  # Will use this

# Or
class MyPlugin:
    pass  # Will use 'myplugin' (lowercased __name__)
```

## Plugin Instance vs Class

You can register either a class or an instance:

```python
# Register as class (simplug auto-instantiates if no __init__ params)
simplug.register(MyPlugin)

# Register as instance (use when __init__ needs params)
instance = MyPlugin(config={'debug': True})
simplug.register(instance)
```

## Auto-instantiation

If a class has no required constructor parameters, simplug auto-instantiates it:

```python
class SimplePlugin:
    @plugin.impl
    def hook(self):
        pass

# Auto-instantiated
simplug.register(SimplePlugin)

class ComplexPlugin:
    def __init__(self, config):
        self.config = config

    @plugin.impl
    def hook(self):
        pass

# Must pass instance
simplug.register(ComplexPlugin(config={}))
```

## Plugin Attributes

Plugins can define additional attributes:

### name

Custom plugin name:

```python
class MyPlugin:
    name = "my_custom_name"
```

### version

Plugin version:

```python
class MyPlugin:
    version = "1.0.0"
    # Or
    __version__ = "1.0.0"
```

### priority

Plugin execution priority (lower = higher priority):

```python
class MyPlugin:
    priority = -1  # Executes before default (0)
```

See [Priority System](priority-system.md) for details.

### instantiate

Force auto-instantiation even with parameters:

```python
class MyPlugin:
    instantiate = True  # Force instantiation
```

## Multiple Hooks in One Plugin

A single plugin can implement multiple hooks:

```python
class MultiHookPlugin:
    @simplug.impl
    def on_startup(self, config):
        print("Starting...")

    @simplug.impl
    def on_shutdown(self):
        print("Shutting down...")

    @simplug.impl
    def process_data(self, data):
        return data.upper()

simplug.register(MultiHookPlugin)
```

## Complete Example

```python
from simplug import Simplug

simplug = Simplug('textapp')

# Specification
@simplug.spec
def transform_text(self, text):
    pass

@simplug.spec
def validate_text(self, text):
    pass

# Plugin implementations
class UpperCasePlugin:
    name = "uppercase"

    @simplug.impl
    def transform_text(self, text):
        return text.upper()

class ReversePlugin:
    name = "reverse"

    @simplug.impl
    def transform_text(self, text):
        return text[::-1]

class LengthValidator:
    name = "length_validator"

    @simplug.impl
    def validate_text(self, text):
        if len(text) > 100:
            raise ValueError("Text too long")
        return True

# Register plugins
simplug.register(UpperCasePlugin, ReversePlugin, LengthValidator)

# Use
transforms = simplug.hooks.transform_text("hello")
print(transforms)  # ['HELLO', 'olleh']

is_valid = simplug.hooks.validate_text("test")
print(is_valid)  # [True]
```

## Next Steps

- **[Plugin Registry](plugin-registry.md)** - Managing plugins
- **[Priority System](priority-system.md)** - Controlling execution order
- **[Result Collection](result-collection.md)** - How results are gathered
