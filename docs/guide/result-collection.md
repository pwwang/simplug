# Result Collection Strategies

simplug provides 18 built-in strategies for collecting results from hook implementations, plus support for custom collectors.

## Overview

Result strategies are specified in hook definition using the `result` parameter:

```python
from simplug import Simplug, SimplugResult

@simplug.spec(result=SimplugResult.ALL_AVAILS)
def my_hook(data):
    pass
```

## Strategy Categories

Strategies are organized into three categories:

1. **ALL strategies** - Execute all plugins and collect results
2. **FIRST/LAST strategies** - Execute only first or last plugin
3. **SINGLE strategies** - Execute a single plugin by name

## ALL Strategies

Execute all plugin implementations and collect results.

### ALL

Collect all results including `None` values.

```python
@simplug.spec(result=SimplugResult.ALL)
def process(data):
    pass

# Returns: ['result1', None, 'result3']
```

Use when you need to know which plugins returned `None`.

### ALL_AVAILS

Collect all non-`None` results.

```python
@simplug.spec(result=SimplugResult.ALL_AVAILS)
def process(data):
    pass

# Returns: ['result1', 'result3']
```

Most common strategy for collecting results.

### ALL_FIRST

Execute all plugins, return first result (even if `None`).

```python
@simplug.spec(result=SimplugResult.ALL_FIRST)
def process(data):
    pass

# Returns: 'result1' or None
# All plugins execute
```

Use when you want all side effects but only care about first result.

### ALL_LAST

Execute all plugins, return last result (even if `None`).

```python
@simplug.spec(result=SimplugResult.ALL_LAST)
def process(data):
    pass

# Returns: 'result3' or None
# All plugins execute
```

### ALL_FIRST_AVAIL

Execute all plugins, return first non-`None` result.

```python
@simplug.spec(result=SimplugResult.ALL_FIRST_AVAIL)
def process(data):
    pass

# Returns: 'result2' (first non-None)
# All plugins execute
```

### ALL_LAST_AVAIL

Execute all plugins, return last non-`None` result.

```python
@simplug.spec(result=SimplugResult.ALL_LAST_AVAIL)
def process(data):
    pass

# Returns: 'result3' (last non-None)
# All plugins execute
```

## FIRST/LAST Strategies

Execute only first or last plugin, skipping others.

### FIRST

Execute only first plugin, return its result (even if `None`).

```python
@simplug.spec(result=SimplugResult.FIRST)
def process(data):
    pass

# Returns: 'result1' or None
# Only first plugin executes
```

### LAST

Execute only last plugin, return its result (even if `None`).

```python
@simplug.spec(result=SimplugResult.LAST)
def process(data):
    pass

# Returns: 'result3' or None
# Only last plugin executes
```

### FIRST_AVAIL

Execute plugins until first non-`None` result, then stop.

```python
@simplug.spec(result=SimplugResult.FIRST_AVAIL)
def process(data):
    pass

# Returns: 'result2' (first non-None)
# Plugins 1 and 2 execute, then stop
```

Good for fallback chains - first plugin to provide valid result wins.

### LAST_AVAIL

Execute plugins in reverse until first non-`None` result, then stop.

```python
@simplug.spec(result=SimplugResult.LAST_AVAIL)
def process(data):
    pass

# Returns: 'result2' (first non-None from end)
# Plugins 3 and 2 execute, then stop
```

Good for overriding behavior - last valid result wins.

## SINGLE Strategies

Execute a single plugin by name.

### SINGLE

Execute plugin specified by `__plugin` parameter.

```python
@simplug.spec(result=SimplugResult.SINGLE)
def get_value(key):
    pass

# Execute specific plugin
result = simplug.hooks.get_value('key', __plugin='plugin1')

# If no __plugin, uses last plugin
result = simplug.hooks.get_value('key')
```

!!! warning
If no `__plugin` specified and multiple implementations exist, a warning is raised.

## TRY Strategies

Return `None` instead of raising exception when no result available.

All strategies above have `TRY_*` variants that:
- Return `None` instead of raising `ResultUnavailableError`
- Otherwise behave identically

### Available TRY Strategies

- `TRY_ALL` - Return `None` if no results
- `TRY_ALL_AVAILS` - Return `None` if no non-`None` results
- `TRY_ALL_FIRST` - Return `None` if no results
- `TRY_ALL_LAST` - Return `None` if no results
- `TRY_ALL_FIRST_AVAIL` - Return `None` if no non-`None` results
- `TRY_ALL_LAST_AVAIL` - Return `None` if no non-`None` results
- `TRY_FIRST` - Return `None` if no result
- `TRY_LAST` - Return `None` if no result
- `TRY_FIRST_AVAIL` - Return `None` if no non-`None` result
- `TRY_LAST_AVAIL` - Return `None` if no non-`None` result
- `TRY_SINGLE` - Return `None` if plugin not found

Example:

```python
# Would raise ResultUnavailableError if no results
@simplug.spec(result=SimplugResult.FIRST_AVAIL)
def get_data(data):
    pass

# Returns None instead of raising exception
@simplug.spec(result=SimplugResult.TRY_FIRST_AVAIL)
def get_data(data):
    pass
```

## Custom Collectors

You can provide your own result collector function:

```python
def custom_collector(calls):
    """Custom collector function.

    Args:
        calls: List of SimplugImplCall tuples
            Each tuple: (plugin_name, impl_function, args, kwargs)

    Returns:
        Collected result in any format
    """
    results = [call.impl(*call.args, **call.kwargs) for call in calls]
    return '; '.join(str(r) for r in results if r)

@simplug.spec(result=custom_collector)
def process(data):
    pass

# Returns: "result1; result2; result3"
```

### Async Custom Collectors

For async hooks, provide an async collector:

```python
async def async_custom_collector(calls):
    results = [await call.impl(*call.args, **call.kwargs) for call in calls]
    return sum(results)

@simplug.spec(result=async_custom_collector)
async def process_async(data):
    pass
```

## Strategy Selection Guide

| Use Case | Recommended Strategy |
|-----------|---------------------|
| Collect all results | `ALL_AVAILS` |
| First valid result (chain) | `FIRST_AVAIL` |
| Last valid result (override) | `LAST_AVAIL` |
| Only first plugin | `FIRST` |
| Only last plugin | `LAST` |
| Execute all, return first | `ALL_FIRST` |
| Execute all, return last | `ALL_LAST` |
| Single plugin by name | `SINGLE` |
| Handle no results gracefully | Use `TRY_*` variants |

## Examples

### Collecting Transformations

```python
@simplug.spec(result=SimplugResult.ALL_AVAILS)
def transform_text(text):
    pass

class Plugins:
    @simplug.impl
    def transform_text(self, text):
        return text.upper()

    @simplug.impl
    def transform_text(self, text):
        return text.lower()

    @simplug.impl
    def transform_text(self, text):
        return text.title()

results = simplug.hooks.transform_text("hello")
# Returns: ['HELLO', 'hello', 'Hello']
```

### Fallback Chain

```python
@simplug.spec(result=SimplugResult.FIRST_AVAIL)
def get_config(key):
    """Get config from first available source."""

# Plugins in priority order (env vars, then file, then defaults)
class EnvConfig:
    priority = -1  # First
    @simplug.impl
    def get_config(self, key):
        return os.environ.get(key)

class FileConfig:
    priority = 0
    @simplug.impl
    def get_config(self, key):
        # Returns None if not found
        return read_config(key)

class DefaultConfig:
    priority = 1  # Last (always has value)
    @simplug.impl
    def get_config(self, key):
        return DEFAULTS.get(key)

value = simplug.hooks.get_config('timeout')
# Returns env value if set, file value if set, else default
```

### Validation Pipeline

```python
@simplug.spec(result=SimplugResult.ALL)
def validate(data):
    """Run all validations."""

class SchemaValidator:
    @simplug.impl
    def validate(self, data):
        if not validate_schema(data):
            raise ValueError("Invalid schema")

class BusinessValidator:
    @simplug.impl
    def validate(self, data):
        if not meets_business_rules(data):
            raise ValueError("Invalid business rules")

results = simplug.hooks.validate(data)
# Returns [None, ValueError] - all validators run
```

## Next Steps

- **[Implementing Hooks](implementing-hooks.md)** - How to implement hooks
- **[Priority System](priority-system.md)** - Control execution order
- **[Async Hooks](async-hooks.md)** - Async-specific considerations
