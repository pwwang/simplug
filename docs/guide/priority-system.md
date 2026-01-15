# Priority System

simplug's priority system determines the execution order of plugins.

## How Priority Works

Priority is a 2-element tuple: `(priority_attr, batch_index)`

- **Lower values** = Higher priority (execute first)
- **Priority attr** = First sorting element
- **Batch index** = Second sorting element (registration order within a batch)

## Setting Priority

### Using priority Attribute

Set priority on plugin class:

```python
class HighPriorityPlugin:
    priority = -1  # Executes before default (0)

class NormalPlugin:
    priority = 0  # Default priority

class LowPriorityPlugin:
    priority = 1  # Executes after default
```

### No priority Attribute

If no `priority` attribute, uses `(batch_index, register_index)`:

```python
class Plugin:
    pass  # No priority attribute

# Register in batch 0
simplug.register(Plugin1, Plugin2)
# Plugin1 priority: (0, 0)
# Plugin2 priority: (0, 1)
# Plugin1 executes first

# Register in batch 1
simplug.register(Plugin3)
# Plugin3 priority: (1, 0)
# Plugins 1 and 2 execute before 3
```

## Batch Index

Plugins registered in the same `register()` call share the same batch index:

```python
# Batch 0
simplug.register(PluginA, PluginB, PluginC)
# All have batch_index=0
# Sorted by (priority_attr, 0) then (priority_attr, 1) then (priority_attr, 2)

# Batch 1
simplug.register(PluginD)
# batch_index=1
# Executes after all batch 0 plugins
```

## Priority Examples

### Override Behavior

Use negative priority to override default plugins:

```python
class DefaultPlugin:
    priority = 0  # Default priority

    @simplug.impl
    def process(self, data):
        return f"Default: {data}"

class OverridePlugin:
    priority = -1  # Higher priority

    @simplug.impl
    def process(self, data):
        return f"Override: {data}"

# OverridePlugin executes first
simplug.register(DefaultPlugin, OverridePlugin)
results = simplug.hooks.process("test")
# Returns: ['Override: test', 'Default: test']
```

### Chain of Fallbacks

Use priority for fallback chains:

```python
class CachePlugin:
    priority = -2  # First - check cache

    @simplug.impl
    def get_value(self, key):
        return cache.get(key)

class ConfigPlugin:
    priority = -1  # Second - check config

    @simplug.impl
    def get_value(self, key):
        return config.get(key)

class DefaultPlugin:
    priority = 0  # Last - use default

    @simplug.impl
    def get_value(self, key):
        return DEFAULTS[key]

# Tries cache, then config, then default
value = simplug.hooks.get_value('timeout')
```

### Layers of Processing

Use priority to layer transformations:

```python
class ParserPlugin:
    priority = -2  # First - parse data

    @simplug.impl
    def process(self, data):
        return json.loads(data)

class ValidatorPlugin:
    priority = -1  # Second - validate

    @simplug.impl
    def process(self, data):
        if not valid(data):
            raise ValueError("Invalid")
        return data

class EnricherPlugin:
    priority = 0  # Last - enrich

    @simplug.impl
    def process(self, data):
        data['timestamp'] = datetime.now().isoformat()
        return data

# Data flows through parser -> validator -> enricher
result = simplug.hooks.process(raw_json)
```

## Execution Order

### Complete Example

```python
from simplug import Simplug

simplug = Simplug('priorityapp')

@simplug.spec
def process(data):
    pass

# Register in different orders and priorities
class PluginA:
    priority = -1

    @simplug.impl
    def process(self, data):
        return f"A: {data}"

class PluginB:
    # No priority - uses batch index

    @simplug.impl
    def process(self, data):
        return f"B: {data}"

class PluginC:
    priority = 1

    @simplug.impl
    def process(self, data):
        return f"C: {data}"

class PluginD:
    priority = -2

    @simplug.impl
    def process(self, data):
        return f"D: {data}"

# Register: D (batch 0), A, B (batch 1), C (batch 2)
simplug.register(PluginD)
simplug.register(PluginA, PluginB)
simplug.register(PluginC)

# Execution order:
# 1. PluginD (priority -2, batch 0)
# 2. PluginA (priority -1, batch 1)
# 3. PluginB (no priority, batch 1, index 1)
# 4. PluginC (priority 1, batch 2)

results = simplug.hooks.process("test")
# Returns: ['D: test', 'A: test', 'B: test', 'C: test']
```

### Checking Order

Inspect plugin order:

```python
# Get all plugin names in execution order
names = simplug.get_all_plugin_names()
print(names)

# Or inspect priority
for name in names:
    plugin = simplug.get_plugin(name)
    print(f"{name}: priority={plugin.priority}")
```

## Dynamic Priority Changes

You can modify priority after registration:

```python
plugin = simplug.get_plugin('myplugin')
plugin.priority = -1  # Change priority

# Note: Registry is sorted once per hook call
# Priority changes apply to subsequent calls
```

For permanent priority changes, use the `priority` attribute on the plugin class.

## Negative Priorities

Negative priorities allow core plugins to always execute first:

```python
# Core functionality
class CorePlugin:
    priority = -100  # Always first

    @simplug.impl
    def process(self, data):
        return self.core_logic(data)

# User plugins
class UserPlugin:
    priority = 0  # After core

    @simplug.impl
    def process(self, data):
        return self.user_logic(data)
```

## Best Practices

1. **Use meaningful priority values** - Clear hierarchy (e.g., -10, -5, 0, 5, 10)
2. **Document priority behavior** - Explain why a plugin needs specific priority
3. **Avoid tight priority ranges** - Leave room for future plugins
4. **Consider batch index** - Same-batch plugins execute in registration order
5. **Use result strategies wisely** - `FIRST_AVAIL` often works well with priorities

## Common Priority Patterns

| Pattern | Priority Range | Use Case |
|---------|-----------------|-----------|
| Core system | -100 to -10 | Always execute first |
| Critical extensions | -10 to -5 | Override defaults |
| Default functionality | 0 | Standard priority |
| Optional features | 5 to 10 | Enhance functionality |
| Rare features | 10+ | Last resort |

## Next Steps

- **[Plugin Registry](plugin-registry.md)** - Managing plugin state
- **[Result Collection](result-collection.md)** - How results are collected
- **[Implementing Hooks](implementing-hooks.md)** - Creating plugins
