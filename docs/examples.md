# Examples

Collection of simplug examples demonstrating various use cases.

## Included Examples

### Toy Example

A minimal 30-line demonstration of basic plugin system usage.

**Location:** `examples/toy.py`

**Features:**
- Simple hook specification
- Multiple plugin implementations
- Basic result collection

**Run:**
```bash
python examples/toy.py
```

**View source:** [examples/toy.py](https://github.com/pwwang/simplug/blob/main/examples/toy.py)

### Complete Example

Full example with setuptools entry points integration.

**Location:** `examples/complete/`

**Features:**
- Complete application structure
- Setuptools entry points for plugins
- Dynamic plugin loading

**Run:**
```bash
python -m examples.complete
```

**Install plugin:**
```bash
pip install --editable examples.complete.plugin
python -m examples.complete
```

**View source:**
- [examples/complete/__main__.py](https://github.com/pwwang/simplug/blob/main/examples/complete/__main__.py)
- [examples/complete/plugin/](https://github.com/pwwang/simplug/tree/main/examples/complete/plugin)

## Common Patterns

### Data Pipeline

```python
from simplug import Simplug, SimplugResult

simplug = Simplug('pipeline')

# Define pipeline stages
@simplug.spec(result=SimplugResult.ALL_AVAILS)
def validate(data):
    pass

@simplug.spec(result=SimplugResult.ALL_AVAILS)
def transform(data):
    pass

@simplug.spec(result=SimplugResult.ALL_AVAILS)
def enrich(data):
    pass

# Plugins for each stage
class SchemaValidator:
    @simplug.impl
    def validate(self, data):
        if not valid_schema(data):
            raise ValueError("Invalid schema")
        return True

class Normalizer:
    @simplug.impl
    def transform(self, data):
        return normalize(data)

class TimestampEnricher:
    @simplug.impl
    def enrich(self, data):
        data['timestamp'] = datetime.now().isoformat()
        return data

# Execute pipeline
validated = simplug.hooks.validate(raw_data)
normalized = simplug.hooks.transform(validated)
enriched = simplug.hooks.enrich(normalized)
```

### Configuration Management

```python
from simplug import Simplug, SimplugResult

simplug = Simplug('configapp')

@simplug.spec(result=SimplugResult.FIRST_AVAIL)
def get_config(key):
    """Get config from first available source."""

# Priority order: env vars -> file -> defaults
class EnvConfig:
    priority = -1

    @simplug.impl
    def get_config(self, key):
        return os.environ.get(key)

class FileConfig:
    priority = 0

    @simplug.impl
    def get_config(self, key):
        return read_config_file(key)

class DefaultConfig:
    priority = 1

    @simplug.impl
    def get_config(self, key):
        return DEFAULTS.get(key)

# Use with fallback
timeout = simplug.hooks.get_config('timeout')
# Returns env var if set, else file, else default
```

### Event System

```python
from simplug import Simplug, SimplugResult

simplug = Simplug('events')

@simplug.spec(result=SimplugResult.ALL)
def on_event(event):
    pass

# Event subscribers
class LoggingPlugin:
    @simplug.impl
    def on_event(self, event):
        logger.info(f"Event: {event}")

class MetricsPlugin:
    @simplug.impl
    def on_event(self, event):
        metrics.increment(event.type)

class WebhookPlugin:
    @simplug.impl
    def on_event(self, event):
        send_webhook(event)

# Publish event
simplug.hooks.on_event({'type': 'user_login', 'user_id': 123})
# All plugins execute
```

### Middleware Chain

```python
from simplug import Simplug, SimplugResult

simplug = Simplug('webapp')

@simplug.spec(result=SimplugResult.ALL)
def handle_request(request):
    pass

@simplug.spec(result=SimplugResult.ALL_AVAILS)
def get_response(request):
    pass

class AuthPlugin:
    @simplug.impl
    def handle_request(self, request):
        if not authenticated(request):
            raise UnauthorizedError()
        return request

class RateLimitPlugin:
    @simplug.impl
    def handle_request(self, request):
        check_rate_limit(request.user)
        return request

class CachingPlugin:
    @simplug.impl
    def get_response(self, request):
        return cache.get(request.url)

class ProcessingPlugin:
    @simplug.impl
    def get_response(self, request):
        return process_request(request)

# Execute middleware chain
# All handle_request hooks execute
responses = simplug.hooks.get_response(request)
# First non-None response returned
```

### Async Plugin System

```python
import asyncio
from simplug import Simplug, SimplugResult

simplug = Simplug('asyncapp')

@simplug.spec
async def fetch_data(url):
    pass

@simplug.spec(result=SimplugResult.ALL_AVAILS)
async def process_data(data):
    pass

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
        await asyncio.sleep(0.1)  # Simulate work
        return data.upper()

async def main():
    data = await simplug.hooks.fetch_data('https://api.example.com/data')
    results = await simplug.hooks.process_data(data)
    print(results)

asyncio.run(main())
```

## Real-World Use Cases

### Web Framework Integration

Define hooks for request/response processing, authentication, and middleware.

### CLI Application

Create extensible commands with hooks for argument processing, validation, and output formatting.

### Data Processing

Build pipelines with validation, transformation, and enrichment stages.

### Monitoring and Logging

Allow plugins to subscribe to events and implement custom handlers.

### Configuration

Support multiple configuration sources with priority-based fallback.

## Learning Resources

- **[Getting Started](getting-started.md)** - Basic concepts
- **[Guides](guide/defining-hooks.md)** - Feature-specific documentation
- **[API Reference](api/index.md)** - Complete API documentation
- **[Source Code](https://github.com/pwwang/simplug)** - Browse implementation

## Creating Your Own Examples

When creating examples:

1. **Keep them simple** - Focus on one feature per example
2. **Add comments** - Explain the key concepts demonstrated
3. **Make them runnable** - Users should be able to execute immediately
4. **Include expected output** - Show what to expect
5. **Document dependencies** - List required packages

## Contributing Examples

Have an example that would help others? Consider contributing!

- Fork the repository
- Add your example to `examples/`
- Update this documentation
- Submit a pull request
