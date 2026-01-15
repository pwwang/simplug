# Async Hooks

simplug provides first-class support for async hooks with automatic sync/async bridging.

## Defining Async Hooks

Use `async def` to define async hooks:

```python
@simplug.spec
async def process_async(data):
    """Async hook specification."""
    # Async operations
    result = await some_async_operation(data)
    return result
```

## Implementing Async Hooks

### Async Implementations

Implement async hooks with async functions:

```python
class AsyncPlugin:
    @simplug.impl
    async def process_async(self, data):
        return await asyncio.sleep(1, data.upper())
```

### Sync Implementations

You can also implement async hooks with sync functions:

```python
class SyncPlugin:
    @simplug.impl
    def process_async(self, data):
        # Sync implementation of async hook
        return data.lower()
```

!!! warning
By default, simplug warns when a sync implementation is used on an async hook. See [Suppressing Warnings](#suppressing-warnings).

## Calling Async Hooks

### Using asyncio.run

Call async hooks from synchronous code:

```python
import asyncio

result = asyncio.run(simplug.hooks.process_async("data"))
```

### Within Async Context

Call from within async function:

```python
async def main():
    result = await simplug.hooks.process_async("data")
```

### Mixed Sync and Async

You can mix sync and async hooks:

```python
# Sync hook
@simplug.spec
def process_sync(data):
    pass

# Async hook
@simplug.spec
async def process_async(data):
    pass

# Call appropriately
sync_result = simplug.hooks.process_sync("data")
async_result = await simplug.hooks.process_async("data")
```

## Suppressing Warnings

Suppress warnings for sync implementations:

```python
# Warn by default
@simplug.spec()
async def async_hook(data):
    pass

class Plugin:
    @simplug.impl
    def async_hook(self, data):
        return data  # Sync on async - warns

# Suppress warning
@simplug.spec(warn_sync_impl_on_async=False)
async def async_hook(data):
    pass

class Plugin:
    @simplug.impl
    def async_hook(self, data):
        return data  # No warning
```

## Error Handling

### Async Errors in Sync Code

Errors from async hooks in sync context are properly wrapped:

```python
class FailingPlugin:
    @simplug.impl
    async def failing_hook(self, data):
        raise ValueError("Failed")

# Call from sync code
try:
    result = asyncio.run(simplug.hooks.failing_hook("data"))
except ResultError as e:
    print(f"Error: {e}")
    # Error: plugin=MyPlugin; spec=[async]failing_hook
```

### Sync Errors in Async Context

```python
class FailingPlugin:
    @simplug.impl
    def failing_hook(self, data):
        raise ValueError("Failed")

# Call from async code
try:
    result = await simplug.hooks.failing_hook("data")
except ResultError as e:
    print(f"Error: {e}")
```

## Result Collection with Async Hooks

All result collection strategies work with async hooks:

```python
# Collect all results
@simplug.spec(result=SimplugResult.ALL_AVAILS)
async def process(data):
    pass

results = await simplug.hooks.process("data")
# Returns: ['RESULT1', 'RESULT2']
```

The result collection happens asynchronously - all plugin implementations run concurrently (depending on how you call them).

## Performance Considerations

### Concurrent Execution

When calling async hooks, consider execution strategy:

```python
# Sequential execution (waits for each)
results = []
for plugin in plugins:
    results.append(await plugin.hook(data))

# Concurrent execution (faster if hooks are independent)
import asyncio
tasks = [plugin.hook(data) for plugin in plugins]
results = await asyncio.gather(*tasks)
```

simplug calls implementations sequentially in the sorted plugin order. For true parallel execution, implement this pattern in your code.

### Sync Overhead

Sync implementations on async hooks add minimal overhead:

```python
# Sync implementation called from async context
async def hook(data):
    return sync_impl(data)
```

The sync function is executed and then wrapped in a coroutine.

## Complete Example

```python
import asyncio
from simplug import Simplug, SimplugResult

simplug = Simplug('asyncapp')

# Define hooks
@simplug.spec
async def fetch_data(self, url):
    """Fetch data from URL."""

@simplug.spec(result=SimplugResult.ALL_AVAILS)
async def process_data(self, data):
    """Process fetched data."""

# Implement plugins
class HttpPlugin:
    @simplug.impl
    async def fetch_data(self, url):
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                return await resp.text()

class TransformPlugin:
    @simplug.impl
    async def process_data(self, data):
        return data.upper()

class LoggerPlugin:
    @simplug.impl
    async def process_data(self, data):
        print(f"Processing: {len(data)} bytes")
        return None

# Register
simplug.register(HttpPlugin, TransformPlugin, LoggerPlugin)

# Use
async def main():
    # Fetch data
    data = await simplug.hooks.fetch_data('https://example.com')

    # Process
    results = await simplug.hooks.process_data(data)
    print(results)

asyncio.run(main())
```

## Mixing Sync and Async Implementations

```python
@simplug.spec(warn_sync_impl_on_async=False)
async def transform(self, data):
    """Transform data - can be sync or async."""

class SyncPlugin:
    @simplug.impl
    def transform(self, data):
        return data.upper()

class AsyncPlugin:
    @simplug.impl
    async def transform(self, data):
        # Simulate async work
        await asyncio.sleep(0.1)
        return data.lower()

# Both work together
async def main():
    result = await simplug.hooks.transform("Hello")
    print(result)  # ['HELLO', 'hello']

asyncio.run(main())
```

## Best Practices

1. **Use async hooks for async operations** - I/O, network calls, database queries
2. **Keep implementations consistent** - If hook is async, prefer async implementations
3. **Handle sync implementations gracefully** - Use `warn_sync_impl_on_async=False` when needed
4. **Consider performance** - Sequential execution vs concurrent patterns
5. **Document async requirements** - Clear when hooks are async

## Next Steps

- **[Defining Hooks](defining-hooks.md)** - Specifying async hooks
- **[Implementing Hooks](implementing-hooks.md)** - Creating async implementations
- **[Result Collection](result-collection.md)** - Collecting async results
