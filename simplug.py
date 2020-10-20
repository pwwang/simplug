"""A simple entrypoint-free plugin system for python"""
from typing import Any, Callable, Dict, List, Optional, Tuple

import inspect
from importlib import import_module
from collections import namedtuple
from enum import Enum
from diot import OrderedDiot

__version__ = '0.0.1'

SimplugImpl = namedtuple('SimplugImpl', ['impl'])
SimplugImpl.__doc__ = """A namedtuple wrapper for hook implementation.

This is used to mark the method/function to be an implementation of a hook.

Args:
    impl: The hook implementation
"""


class SimplugException(Exception):
    """Base exception class for simplug"""

class NoSuchPlugin(SimplugException):
    """When a plugin cannot be imported"""

class NoPluginNameDefined(SimplugException):
    """When the name of the plugin cannot be found"""

class HookSignatureDifferentFromSpec(SimplugException):
    """When the hook signature is different from spec"""

class NoSuchHookSpec(SimplugException):
    """When implemented a undefined hook or calling a non-exist hook"""

class HookRequired(SimplugException):
    """When a required hook is not implemented"""

class HookSpecExists(SimplugException):
    """When a hook has already been defined"""

class SimplugResult(Enum):
    """Way to get the results from the hooks

    Attributes:
        ALL: Get all the results from the hook, as a list
            including `NONE`s
        ALL_BUT_NONE: Get all the results from the hook, as a list
            not including `NONE`s
        FIRST: Get the none-`None` result from the first plugin only
            (ordered by priority)
        LAST: Get the none-`None` result from the last plugin only
    """
    ALL = 'all'
    ALL_BUT_NONE = 'all_but_none'
    FIRST = 'first'
    LAST = 'last'

class SimplugWrapper:
    """A wrapper for plugin

    Args:
        plugin: A object or a string indicating the plugin as a module
        batch_index: The batch_index when the plugin is registered
            >>> simplug = Simplug()
            >>> simplug.register('plugin1', 'plugin2') # batch 0
            >>>                 # index:0,  index:1
            >>> simplug.register('plugin3', 'plugin4') # batch 1
            >>>                 # index:0,  index:1
        index: The index when the plugin is registered

    Attributes:
        plugin: The raw plugin object
        priority: A 2-element tuple used to prioritize the plugins
            - If `plugin.priority` is specified, use it as the first element
                and batch_index will be the second element
            - Otherwise, batch_index the first and index the second.
            - Smaller number has higher priority
            - Negative numbers allowed

    Raises:
        NoSuchPlugin: When a string is passed in and the plugin cannot be
            imported as a module
    """

    def __init__(self, plugin: Any, batch_index: int, index: int):
        if isinstance(plugin, str):
            try:
                plugin = import_module(plugin)
            except ImportError as exc:
                raise NoSuchPlugin(plugin).with_traceback(
                    exc.__traceback__
                ) from None

        self.plugin = plugin # type: object

        priority = getattr(self.plugin, 'priority', None)
        self.priority = ((batch_index, index)
                         if priority is None
                         else (priority, batch_index)) # type: Tuple[int, int]

        self.enabled = True # type: bool

    @property
    def name(self) -> str:
        """Try to get the name of the plugin.

        A lowercase name is recommended.

        if `<plugin>.name` is defined, then the name is used. Otherwise,
        `<plugin>.__name__` is used. Finally, `<plugin>.__class__.__name__` is
        tried.

        Raises:
            NoPluginNameDefined: When a name cannot be retrieved.

        Returns:
            The name of the plugin
        """
        try:
            return self.plugin.name
        except AttributeError:
            pass

        try:
            return self.plugin.__name__.lower()
        except AttributeError:
            pass

        try:
            return self.plugin.__class__.__name__.lower()
        except AttributeError: # pragma: no cover
            pass

        raise NoPluginNameDefined(str(self.plugin)) # pragma: no cover

    def enable(self) -> None:
        """Enable this plugin"""
        self.enabled = True

    def disable(self):
        """Disable this plugin"""
        self.enabled = False

    def hook(self, name: str) -> Optional[SimplugImpl]:
        """Get the hook implementation of this plugin by name

        Args:
            name: The name of the hook

        Returns:
            The wrapper of the implementation. If the implementation is not
                found or it's not decorated by `simplug.impl`, None will be
                returned.
        """
        ret = getattr(self.plugin, name, None)
        if not isinstance(ret, SimplugImpl):
            return None
        return ret

class SimplugHook:
    """A hook of a plugin

    Args:
        simplug_hooks: The SimplugHooks object
        spec: The specification of the hook
        required: Whether this hook is required to be implemented
        result: Way to collect the results from the hook

    Attributes:
        name: The name of the hook
        simplug_hooks: The SimplugHooks object
        spec: The specification of the hook
        required: Whether this hook is required to be implemented
        result: Way to collect the results from the hook
        _has_self: Whether the parameters have `self` as the first. If so,
            it will be ignored while being called.
    """
    def __init__(self,
                 simplug_hooks: "SimplugHooks",
                 spec: Callable,
                 required: bool,
                 result: SimplugResult):
        self.simplug_hooks = simplug_hooks
        self.spec = spec
        self.name = spec.__name__
        self.required = required
        self.result = result
        self._has_self = list(inspect.signature(spec).parameters)[0] == 'self'

    def __call__(self, *args, **kwargs):
        """Call the hook in your system

        Args:
            *args: args for the hook
            **kwargs: kwargs for the hook

        Returns:
            Depending on `self.result`:
            - SimplugResult.ALL: Get all the results from the hook, as a list
                including `NONE`s
            - SimplugResult.ALL_BUT_NONE: Get all the results from the hook,
                as a list, not including `NONE`s
            - SimplugResult.FIRST: Get the none-`None` result from the
                first plugin only (ordered by priority)
            - SimplugResult.LAST: Get the none-`None` result from
                the last plugin only
        """
        self.simplug_hooks._sort_registry()
        results = []
        for plugin in self.simplug_hooks._registry.values():
            if not plugin.enabled:
                continue
            hook = plugin.hook(self.name)
            if hook is not None:
                results.append(hook.impl(None, *args, **kwargs)
                               if self._has_self
                               else hook.impl(*args, **kwargs))

        if self.result == SimplugResult.ALL:
            return results

        results = [result for result in results if result is not None]
        if self.result == SimplugResult.FIRST:
            return results[0] if results else None

        if self.result == SimplugResult.LAST:
            return results[-1] if results else None
        # ALL_BUT_NONE
        return results

class SimplugHooks:
    """The hooks manager

    Methods in this class are prefixed with a underscore to attributes clean
    for hooks.

    To call a hook in your system:
    >>> simplug.hooks.<hook_name>(<args>)

    Attributes:
        _registry: The plugin registry
        _specs: The registry for the hook specs
        _registry_sorted: Whether the plugin registry has been sorted already
    """

    def __init__(self):

        self._registry = OrderedDiot() # type: OrderedDiot
        self._specs = {}               # type: Dict[str, SimplugHook]
        self._registry_sorted = False  # type: bool

    def _register(self, plugin: SimplugWrapper) -> None:
        """Register a plugin (already wrapped by SimplugWrapper)

        Args:
            plugin: The plugin wrapper

        Raises:
            HookRequired: When a required hook is not implemented
            HookSignatureDifferentFromSpec: When the arguments of a hook
                implementation is different from its specification
        """
        # check if required hooks implemented
        # and signature
        for specname, spec in self._specs.items():
            hook = plugin.hook(specname)
            if spec.required and hook is None:
                raise HookRequired(f'{specname}, but not implemented '
                                   f'in plugin {plugin.name}')
            if hook is None:
                continue
            if (inspect.signature(hook.impl).parameters.keys() !=
                    inspect.signature(spec.spec).parameters.keys()):
                raise HookSignatureDifferentFromSpec(
                    f'{specname!r} in plugin {plugin.name}\n'
                    f'Expect {inspect.signature(spec.spec).parameters.keys()}, '
                    f'but got {inspect.signature(hook.impl).parameters.keys()}'
                )
        self._registry[plugin.name] = plugin

    def _sort_registry(self) -> None:
        """Sort the registry by the priority only once"""
        if self._registry_sorted:
            return
        orderedkeys = self._registry.__diot__['orderedkeys']
        self._registry.__diot__['orderedkeys'] = sorted(
            orderedkeys,
            key=lambda plug: self._registry[plug].priority
        )
        self._registry_sorted = True

    def __getattr__(self, name: str) -> "SimplugHook":
        """Get the hook by name

        Args:
            name: The hook name

        Returns:
            The SimplugHook object

        Raises:
            NoSuchHookSpec: When the hook has no specification defined.
        """
        try:
            return self._specs[name]
        except KeyError as exc:
            raise NoSuchHookSpec(name).with_traceback(
                exc.__traceback__
            ) from None

class Simplug:
    """The plugin manager for simplug

    Attributes:
        PROJECT_INDEX: The project index to name the project by default
        PROJECTS: The projects registry, to make sure the same `Simplug`
            object by the name project name.

        _batch_index: The batch index for plugin registration
        hooks: The hooks manager
        _inited: Whether `__init__` has already been called. Since the
            `__init__` method will be called after `__new__`, this is used to
            avoid `__init__` to be called more than once
    """

    PROJECT_INDEX: int = 0
    PROJECTS: Dict[str, "Simplug"] = {}

    def __new__(cls, project: Optional[str] = None) -> "Simplug":
        proj_name = project
        if proj_name is None:
            proj_name = f"project-{cls.PROJECT_INDEX}"
            cls.PROJECT_INDEX += 1

        if proj_name not in cls.PROJECTS:
            cls.PROJECTS[proj_name] = super().__new__(cls)

        return cls.PROJECTS[proj_name]

    def __init__(self,
                 # pylint: disable=unused-argument
                 project: Optional[str] = None):
        if getattr(self, '_inited', None):
            return
        self._batch_index = 0
        self.hooks = SimplugHooks()
        self._inited = True

    def register(self, *plugins: Any) -> None:
        """Register plugins

        Args:
            *plugins: The plugins, each of which could be a str, indicating
                that the plugin is a module and will be imported by
                `__import__`; or an object with the hook implementations as
                its attributes.
        """
        for i, plugin in enumerate(plugins):
            plugin = SimplugWrapper(plugin, self._batch_index, i)
            self.hooks._register(plugin)

        self._batch_index += 1

    def get_plugin(self, name: str, raw: bool = False) -> object:
        """Get the plugin wrapper or the raw plugin object

        Args:
            name: The name of the plugin
            raw: Get the raw plugin object (the one when it's registered)
                If a plugin is a module and registered by its name, the
                module is returned

        Raises:
            NoSuchPlugin: When the plugin does not exist

        Returns:
            The plugin wrapper or raw plugin
        """
        if name not in self.hooks._registry:
            raise NoSuchPlugin(name)
        wrapper = self.hooks._registry[name]
        return wrapper.plugin if raw else wrapper

    def get_all_plugins(self,
                        raw: bool = False) -> Dict[str, SimplugWrapper]:
        """Get a mapping of all plugins

        Args:
            raw: Whether return the raw plugin or not
                (the one when it's registered)
                If a plugin is registered as a module by its name, the module
                is returned.

        Returns:
            The mapping of all plugins
        """
        if not raw:
            return self.hooks._registry
        return OrderedDiot([(name, plugin.plugin)
                            for name, plugin
                            in self.hooks._registry.items()])

    def get_all_plugin_names(self) -> List[str]:
        """Get the names of all plugins

        Returns:
            The names of all plugins
        """
        return list(self.hooks._registry.keys())

    def enable(self, name: str) -> None:
        """Enable a plugin by name

        Args:
            name: The name of the plugin
        """
        self.get_plugin(name).enable()

    def disable(self, name: str):
        """Disable a plugin by name

        Args:
            name: The name of the plugin
        """
        self.get_plugin(name).disable()

    def spec(self,
             hook: Optional[Callable] = None,
             required: bool = False,
             result: SimplugResult = SimplugResult.ALL_BUT_NONE) -> Callable:
        """A decorator to define the specification of a hook

        Args:
            hook: The hook spec. If it is None, that means this decorator is
                called with arguments, and it should be keyword arguments.
                Otherwise, it is called like this `simplug.spec`
            required: Whether this hook is required to be implemented.
            result: How should we collect the results from the plugins

        Raises:
            HookSpecExists: If a hook spec with the same name (`hook.__name__`)
                 is already defined.

        Returns:
            A decorator function of other argument is passed, or the hook spec
                itself.
        """
        def decorator(hook_func: Callable):
            hook_name = hook_func.__name__
            if hook_name in self.hooks._specs:
                raise HookSpecExists(hook_name)
            self.hooks._specs[hook_name] = SimplugHook(self.hooks,
                                                       hook_func,
                                                       required,
                                                       result)
            return hook_func

        return decorator(hook) if hook else decorator

    def impl(self, hook: Callable):
        """A decorator for the implementation of a hook

        Args:
            hook: The hook implementation

        Raises:
            NoSuchHookSpec: When no specification is defined for this hook

        Returns:
            The wrapped hook implementation by `SimplugImpl`
        """
        if hook.__name__ not in self.hooks._specs:
            raise NoSuchHookSpec(hook.__name__)
        return SimplugImpl(hook)
