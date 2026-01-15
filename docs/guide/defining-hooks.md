# Defining Hooks

Hook specifications define the extension points in your application that plugins can implement.

## Basic Syntax

Use the `@simplug.spec` decorator to define a hook:

```python
from simplug import Simplug, SimplugResult

simplug = Simplug('myapp')

@simplug.spec
def my_hook(arg1, arg2):
    """My hook documentation."""
```

## Decorator Options

The `@simplug.spec` decorator accepts the following parameters:

### required

Whether this hook must be implemented by at least one plugin.

```python
@simplug.spec(required=True)
def critical_hook(data):
    """This hook must be implemented."""
```

If no plugin implements a required hook, calling it will raise `HookRequired` exception.

### result

Specifies how to collect results from plugin implementations. See [Result Collection](result-collection.md) for all available strategies.

```python
from simplug import SimplugResult

# Collect all non-None results
@simplug.spec(result=SimplugResult.ALL_AVAILS)
def process_data(data):
    """Process data and return results."""
```

### warn_sync_impl_on_async

For async hooks, whether to warn when a plugin provides a synchronous implementation.

```python
# Warn if plugin provides sync implementation
@simplug.spec(warn_sync_impl_on_async=True)
async def async_hook(data):
    """Async hook with sync implementation warning."""
```

Default is `True`. Set to `False` to suppress warnings.

## Parameter Names and Defaults

Hook parameters are matched by **name** between spec and implementation.

### Specifying Default Values

You can specify default values in the spec:

```python
@simplug.spec
def configure(self, timeout=30, retries=3):
    """Configure with defaults."""
```

### Implementation Requirements

Implementations must have the same parameter names, but **default values are not required**:

```python
@plugin.impl
def configure(self, timeout, retries):
    # Default values not needed in implementation
    print(f"timeout={timeout}, retries={retries}")
```

!!! note
Default values in implementation functions are ignored. Always specify defaults in the hook specification.

## The `self` Parameter

When defining hooks inside a class, you can use `self` as the first parameter:

```python
class MySpec:
    @simplug.spec
    def method_hook(self, data):
        """Method hook specification."""
```

When the hook is called, `self` will be `None`. This is just a naming convention for clarity.

## Async Hooks

Define async hooks using `async def`:

```python
@simplug.spec
async def process_async(data):
    """Async hook specification."""
```

See [Async Hooks](async-hooks.md) for more details on async hooks.

## Signature Validation

simplug validates that hook implementations match the specification:

```python
@simplug.spec
def my_hook(arg1, arg2):
    """Hook specification."""

class BadPlugin:
    @simplug.impl
    def my_hook(wrong_arg):  # Mismatched signature!
        pass

simplug.register(BadPlugin)  # Raises HookSignatureDifferentFromSpec
```

Parameter names must match exactly (excluding `self`).

## Hook Names

Hook names are derived from the function name:

```python
@simplug.spec
def process_data(data):  # Hook name is "process_data"
    pass
```

Duplicate hook names are not allowed:

```python
@simplug.spec
def my_hook(data):
    pass

@simplug.spec
def my_hook(data):  # Raises HookSpecExists
    pass
```

## Complete Example

```python
from simplug import Simplug, SimplugResult

simplug = Simplug('dataapp')

class DataHooks:
    @simplug.spec(required=True)
    def validate(self, data):
        """Validate data - required hook."""

    @simplug.spec(result=SimplugResult.ALL_AVAILS)
    def transform(self, data):
        """Transform data - collect all non-None results."""

    @simplug.spec(result=SimplugResult.FIRST_AVAIL)
    def get_cache_key(self, data):
        """Get cache key - first available result only."""

# Now plugins can implement these hooks
```

## Next Steps

- **[Implementing Hooks](implementing-hooks.md)** - How to implement hook specifications
- **[Result Collection](result-collection.md)** - All result collection strategies
- **[Async Hooks](async-hooks.md)** - Working with async hooks
