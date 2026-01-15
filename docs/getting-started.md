# Getting Started

This guide will walk you through the basics of using simplug to create an extensible application.

## Installation

```bash
pip install -U simplug
```

## Basic Concepts

simplug has three main concepts:

1. **Plugin Manager** (`Simplug`) - Manages all plugins and hooks
2. **Hook Specification** (`@simplug.spec`) - Defines extension points in your application
3. **Hook Implementation** (`@simplug.impl`) - Implements hooks in plugins

## Step 1: Create a Plugin Manager

First, create a plugin manager with a unique project name:

```python
from simplug import Simplug

simplug = Simplug('myapp')
```

The project name ensures you get the same instance across your application.

## Step 2: Define Hooks

Define hooks that plugins can implement:

```python
class MyHooks:
    @simplug.spec
    def on_startup(self, config):
        """Called when the application starts."""

    @simplug.spec(result=SimplugResult.ALL_AVAILS)
    def process_data(self, data):
        """Process data and return results."""
```

## Step 3: Implement Hooks in Plugins

Create plugins that implement your hooks:

```python
class DataProcessor:
    @simplug.impl
    def on_startup(self, config):
        print(f"Starting up with config: {config}")

    @simplug.impl
    def process_data(self, data):
        return data.upper()

class LoggerPlugin:
    @simplug.impl
    def on_startup(self, config):
        print("Logger plugin initialized")

    @simplug.impl
    def process_data(self, data):
        print(f"Processing: {data}")
        return data
```

## Step 4: Register Plugins

Register your plugins with the plugin manager:

```python
simplug.register(DataProcessor, LoggerPlugin)
```

You can also register plugins by module name:

```python
simplug.register('mypackage.myplugin')
```

## Step 5: Call Hooks

Execute all plugin implementations of a hook:

```python
# Call startup hook (all plugins execute)
simplug.hooks.on_startup(config={'debug': True})

# Call data processing hook and collect results
results = simplug.hooks.process_data("Hello")
print(results)  # ['HELLO', None]
```

## Complete Example

Here's a complete working example:

```python
from simplug import Simplug, SimplugResult

# Create plugin manager
simplug = Simplug('todoapp')

# Define hooks
class TodoHooks:
    @simplug.spec
    def add_task(self, task):
        """Add a task."""

    @simplug.spec(result=SimplugResult.ALL_AVAILS)
    def filter_tasks(self, tasks):
        """Filter tasks."""

# Implement plugins
class PriorityPlugin:
    @simplug.impl
    def add_task(self, task):
        return {**task, 'priority': 'medium'}

class DatePlugin:
    @simplug.impl
    def add_task(self, task):
        return {**task, 'created': '2024-01-01'}

    @simplug.impl
    def filter_tasks(self, tasks):
        return [t for t in tasks if t.get('priority') == 'high']

# Register plugins
simplug.register(PriorityPlugin, DatePlugin)

# Use hooks
task = {'title': 'Write documentation'}
enriched = simplug.hooks.add_task(task)
print(enriched)  # [{'title': 'Write documentation', 'priority': 'medium'}, {'title': 'Write documentation', 'created': '2024-01-01'}]
```

## Next Steps

- **[Defining Hooks](guide/defining-hooks.md)** - Learn about hook options and specifications
- **[Implementing Hooks](guide/implementing-hooks.md)** - Deep dive into plugin implementation
- **[Result Collection](guide/result-collection.md)** - Explore the 18 result strategies
- **[API Reference](api/index.md)** - Complete API documentation
