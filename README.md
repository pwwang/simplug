# simplug

A simple plugin system for python with async hooks supported

## Installation

```shell
pip install -U simplug
```

## Examples

### A toy example

```python
from simplug import Simplug

simplug = Simplug('project')

class MySpec:
    """A hook specification namespace."""

    @simplug.spec
    def myhook(self, arg1, arg2):
        """My special little hook that you can customize."""

class Plugin_1:
    """A hook implementation namespace."""

    @simplug.impl
    def myhook(self, arg1, arg2):
        print("inside Plugin_1.myhook()")
        return arg1 + arg2

class Plugin_2:
    """A 2nd hook implementation namespace."""

    @simplug.impl
    def myhook(self, arg1, arg2):
        print("inside Plugin_2.myhook()")
        return arg1 - arg2

simplug.register(Plugin_1, Plugin_2)
results = simplug.hooks.myhook(arg1=1, arg2=2)
print(results)
```

```shell
inside Plugin_1.myhook()
inside Plugin_2.myhook()
[3, -1]
```

Note that the hooks are executed in the order the plugins are registered. This is different from `pluggy`.

### A complete example

See `examples/complete/`.

Running `python -m examples.complete` gets us:

```shell
Your food. Enjoy some egg, egg, egg, salt, pepper, egg, egg
Some condiments? We have pickled walnuts, steak sauce, mushy peas, mint sauce
```

After install the plugin:

```shell
> pip install --editable examples.complete.plugin
> python -m examples.complete # run again
```

```shell
Your food. Enjoy some egg, egg, egg, salt, pepper, egg, egg, lovely spam, wonderous spam
Some condiments? We have pickled walnuts, mushy peas, mint sauce, spam sauce
Now this is what I call a condiments tray!
```

## Usage

### Definition of hooks

Hooks are specified and implemented by decorating the functions with `simplug.spec` and `simplug.impl` respectively.

`simplug` is initialized by:

```python
simplug = Simplug('project')
```

The `'project'` is a unique name to mark the project, which makes sure `Simplug('project')` get the same instance each time.

Note that if `simplug` is initialized without `project`, then a name is generated automatically as such `project-0`, `project-1`, etc.

Hook specification is marked by `simplug.spec`:

```python
simplug = Simplug('project')

@simplug.spec
def setup(args):
    ...
```

`simplug.spec` can take some arguments:

- `required`: Whether this hook is required to be implemented in plugins
- `result`: An enumerator to specify the way to collec the results.
  - `SimplugResult.ALL`: Collect all results from all plugins
  - `SimplugResult.ALL_AVAILS`: Get all the results from the hook, as a list, not including `None`s
  - `SimplugResult.ALL_FIRST`: Executing all implementations and get the first result
  - `SimplugResult.ALL_LAST`: Executing all implementations and get the last result
  - `SimplugResult.TRY_ALL_FIRST`: Executing all implementations and get the first result, if no result is returned, return `None`
  - `SimplugResult.TRY_ALL_LAST`: Executing all implementations and get the last result, if no result is returned, return `None`
  - `SimplugResult.ALL_FIRST_AVAIL`: Executing all implementations and get the first non-`None` result
  - `SimplugResult.ALL_LAST_AVAIL`: Executing all implementations and get the last non-`None` result
  - `SimplugResult.TRY_ALL_FIRST_AVAIL`: Executing all implementations and get the first non-`None` result, if no result is returned, return `None`
  - `SimplugResult.TRY_ALL_LAST_AVAIL`: Executing all implementations and get the last non-`None` result, if no result is returned, return `None`
  - `SimplugResult.FIRST`: Get the first result, don't execute other implementations
  - `SimplugResult.LAST`: Get the last result, don't execute other implementations
  - `SimplugResult.TRY_FIRST`: Get the first result, don't execute other implementations, if no result is returned, return `None`
  - `SimplugResult.TRY_LAST`: Get the last result, don't execute other implementations, if no result is returned, return `None`
  - `SimplugResult.FIRST_AVAIL`: Get the first non-`None` result, don't execute other implementations
  - `SimplugResult.LAST_AVAIL`: Get the last non-`None` result, don't execute other implementations
  - `SimplugResult.TRY_FIRST_AVAIL`: Get the first non-`None` result, don't execute other implementations, if no result is returned, return `None`
  - `SimplugResult.TRY_LAST_AVAIL`: Get the last non-`None` result, don't execute other implementations, if no result is returned, return `None`
  - `SimplugResult.SINGLE`: Get the result from a single implementation
  - `SimplugResult.TRY_SINGLE`: Get the result from a single implementation, if no result is returned, return `None`
  - A callable to collect the result, take `calls` as the argument, a 3-element tuple with first element as the implementation, second element as the positional arguments, and third element as the keyword arguments.

Hook implementation is marked by `simplug.impl`, which takes no additional arguments.

The name of the function has to match the name of the function by `simplug.spec`. And the signatures of the specification function and the implementation function have to be the same in terms of names. This means you can specify default values in the specification function, but you don't have to write the default values in the implementation function.

Note that default values in implementation functions will be ignored.

Also note if a hook specification is under a namespace, it can take `self` as argument. However, this argument will be ignored while the hook is being called (`self` will be `None`, and you still have to specify it in the function definition).

### Loading plugins from setuptools entrypoint

You have to call `simplug.load_entrypoints(group)` after the hook specifications are defined to load the plugins registered by setuptools entrypoint. If `group` is not given, the project name will be used.

### The plugin registry

The plugins are registered by `simplug.register(*plugins)`. Each plugin of `plugins` can be either a python object or a str denoting a module that can be imported by `importlib.import_module`.

The python object must have an attribute `name`, `__name__` or `__class.__name__` for `simplug` to determine the name of the plugin. If the plugin name is determined from `__name__` or `__class__.__name__`, it will be lowercased.

If a plugin is loaded from setuptools entrypoint, then the entrypoint name will be used (no matter what name is defined inside the plugin)

You can enable or disable a plugin temporarily after registration by:

```python
simplug.disable('plugin_name')
simplug.enable('plugin_name')
```

You can use following methods to inspect the plugin registry:

- `simplug.get_plugin`: Get the plugin by name
- `simplug.get_all_plugins`: Get a dictionary of name-plugin mappings of all plugins
- `simplug.get_all_plugin_names`: Get the names of all plugins, in the order it will be executed.
- `simplug.get_enabled_plugins`: Get a dictionary of name-plugin mappings of all enabled plugins
- `simplug.get_enabled_plugin_names`: Get the names of all enabled plugins, in the order it will be executed.

### Calling hooks

Hooks are call by `simplug.hooks.<hook_name>(<arguments>)` and results are collected based on the `result` argument passed in `simplug.spec` when defining hooks.

### Async hooks

It makes no big difference to define an async hook:

```python
@simplug.spec
async def async_hook(arg):
    ...

# to supress warnings for sync implementation
@simplug.spec(warn_sync_impl_on_async=False)
async def async_hook(arg):
    ...
```

One can implement this hook in either an async or a sync way. However, when implementing it in a sync way, a warning will be raised. To suppress the warning, one can pass a `False` value of argument `warn_sync_impl_on_async` to `simplug.spec`.

To call the async hooks (`simplug.hooks.async_hook(arg)`), you will just need to call it like any other async functions (using `asyncio.run`, for example)

## API

https://pwwang.github.io/simplug/
