"""A simple entrypoint-free plugin system for python"""
from __future__ import annotations

import inspect
import warnings
from collections import namedtuple
from enum import Enum
from importlib import import_module, metadata
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    Optional,
    Tuple,
)

from diot import OrderedDiot

__version__ = "0.3.1"

SimplugImpl = namedtuple("SimplugImpl", ["impl", "has_self"])
SimplugImpl.__doc__ = """A namedtuple wrapper for hook implementation.

This is used to mark the method/function to be an implementation of a hook.

Args:
    impl: The hook implementation
"""

SimplugImplCall = namedtuple(
    "SimplugImplCall",
    ["plugin", "impl", "args", "kwargs"],
)
SimplugImplCall.__doc__ = """A namedtuple wrapper for hook implementation call.

Args:
    plugin: The name of the plugin
    impl: The hook implementation
    args: The positional arguments
    kwargs: The keyword arguments
"""


class SimplugException(Exception):
    """Base exception class for simplug"""


class NoSuchPlugin(SimplugException):
    """When a plugin cannot be imported"""


class ResultUnavailableError(SimplugException):
    """When a result is not available"""


class PluginRegistered(SimplugException):
    """When a plugin with a name already registered"""


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


class SyncImplOnAsyncSpecWarning(Warning):
    """When a sync implementation on an async hook"""


class MultipleImplsForSingleResultHookWarning(Warning):
    """When multiple implementations for a single-result hook"""


class SimplugResult(Enum):
    """Way to get the results from the hooks

    ALL - Execute all implementations for the hook
    AVAIL(S) - Get non-`None` results
    FIRST - Get the first result, ordered by priority
        Don't excute the other the implementations
    LAST - Get the last result, ordered by priority
        Don't excute the other the implementations
    ALL_FIRST - Get the first result from each implementation and
        excute the other the implementations
    ALL_LAST - Get the last result from each implementation and
        excute the other the implementations
    TRY - Return `None` instead of raising `ResultUnavailableError` when
        no result is available
    SINGLE - Get the result from a single implementation
    """

    # 0b  1    1    1    1111
    #    TRY  ALL AVAIL   ID
    ALL = 0b010_0000  # 64
    ALL_AVAILS = 0b011_0001  # 97
    ALL_FIRST = 0b010_0010  # 66
    TRY_ALL_FIRST = 0b110_0010  # 194
    ALL_LAST = 0b010_0011  # 67
    TRY_ALL_LAST = 0b110_0011  # 195
    ALL_FIRST_AVAIL = 0b011_0100  # 102
    TRY_ALL_FIRST_AVAIL = 0b111_0100  # 230
    ALL_LAST_AVAIL = 0b011_0101  # 103
    TRY_ALL_LAST_AVAIL = 0b111_0101  # 231
    FIRST = 0b000_0110  # 10
    TRY_FIRST = 0b100_0110  # 138
    LAST = 0b000_0111  # 11
    TRY_LAST = 0b100_0111  # 139
    FIRST_AVAIL = 0b001_1000  # 46
    TRY_FIRST_AVAIL = 0b101_1000  # 174
    LAST_AVAIL = 0b001_1001  # 47
    TRY_LAST_AVAIL = 0b101_1001  # 175
    SINGLE = 0b000_1010  # 18
    TRY_SINGLE = 0b100_1010  # 146


def makecall(call: SimplugImplCall, async_hook: bool = False):
    """Make a call to an implementation and arguments

    Args:
        call: 3-element tuple of (implementation, args, kwargs)

    Returns:
        The result of the call
    """
    out = call.impl(*call.args, **call.kwargs)
    if not async_hook:
        return out

    if inspect.iscoroutine(out):
        return out

    async def coro():
        return out

    return coro()


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
        self.plugin = self._name = None
        if isinstance(plugin, str):
            try:
                self.plugin = import_module(plugin)
            except ImportError as exc:
                raise NoSuchPlugin(plugin).with_traceback(
                    exc.__traceback__
                ) from None

        elif isinstance(plugin, tuple):
            # plugin load from entrypoint
            # name specified as second element explicitly
            self.plugin, self._name = plugin

        else:
            self.plugin = plugin

        priority = getattr(self.plugin, "priority", None)
        self.priority: Tuple[int, int] = (
            (batch_index, index)
            if priority is None
            else (priority, batch_index)
        )

        self.enabled = True  # type: bool

    @property
    def version(self) -> Optional[str]:
        """Try to get the version of the plugin.

        If the attribute `version` is definied, use it. Otherwise, try to check
        if `__version__` is defined. If neither is defined, return None.

        Returns:
            In the priority order of plugin.version, plugin.__version__
            and None
        """
        return getattr(
            self.plugin, "version", getattr(self.plugin, "__version__", None)
        )

    __version__ = version

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
        if self._name is not None:
            return self._name

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
        except AttributeError:  # pragma: no cover
            pass

        raise NoPluginNameDefined(str(self.plugin))  # pragma: no cover

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

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, self.__class__):
            return False
        return self.plugin is other.plugin

    def __ne__(self, other: Any) -> bool:
        return not self.__eq__(other)


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

    def __init__(
        self,
        simplug_hooks: SimplugHooks,
        spec: Callable,
        required: bool,
        result: SimplugResult | Callable,
        warn_sync_impl_on_async: bool = False,
    ):
        self.simplug_hooks = simplug_hooks
        self.spec = spec
        self.name = spec.__name__
        self.required = required
        self.result = result
        self.warn_sync_impl_on_async = warn_sync_impl_on_async

    def _get_results(
        self,
        calls: List[SimplugImplCall],
        plugin: str,
        result: SimplugResult | Callable | int = None,
    ) -> Any:
        """Get the results according to self.result"""
        result = self.result if result is None else result

        if callable(result):
            return result(calls)

        if isinstance(result, SimplugResult):
            result = result.value

        # 0b  1    1    1    1111
        #    TRY  ALL AVAIL   ID
        if result & 0b100_0000:
            try:
                return self._get_results(calls, plugin, result & 0b011_1111)
            except ResultUnavailableError:
                return None

        if result & 0b010_0000:
            out = [makecall(call) for call in calls]
            if result == SimplugResult.ALL.value:
                return out
            if result == SimplugResult.ALL_AVAILS.value:
                return [x for x in out if x is not None]
            if result == SimplugResult.ALL_FIRST.value:
                if not out:
                    raise ResultUnavailableError
                return out[0]
            if result == SimplugResult.ALL_LAST.value:
                if not out:
                    raise ResultUnavailableError
                return out[-1]
            if result == SimplugResult.ALL_FIRST_AVAIL.value:
                if not out or all(x is None for x in out):
                    raise ResultUnavailableError
                return next(x for x in out if x is not None)
            if result == SimplugResult.ALL_LAST_AVAIL.value:
                if not out or all(x is None for x in out):
                    raise ResultUnavailableError
                return next(x for x in reversed(out) if x is not None)

        if result == SimplugResult.FIRST.value:
            if not calls:
                raise ResultUnavailableError
            return makecall(calls[0])
        if result == SimplugResult.LAST.value:
            if not calls:
                raise ResultUnavailableError
            return makecall(calls[-1])
        if result == SimplugResult.FIRST_AVAIL.value:
            for call in calls:
                ret = makecall(call)
                if ret is not None:
                    return ret
            raise ResultUnavailableError
        if result == SimplugResult.LAST_AVAIL.value:
            for call in reversed(calls):
                ret = makecall(call)
                if ret is not None:
                    return ret
            raise ResultUnavailableError
        if result == SimplugResult.SINGLE.value:
            if not calls:
                raise ResultUnavailableError
            for call in calls:
                if call.plugin == plugin:
                    return makecall(call)
            if plugin is not None:
                raise ResultUnavailableError
            if len(calls) > 1:
                warnings.warn(
                    f"More than one implementation of {self.name} found, "
                    "but no plugin was specified. Using the last one.",
                    MultipleImplsForSingleResultHookWarning,
                )
            return makecall(calls[-1])

    def __call__(self, *args, **kwargs):
        """Call the hook in your system

        Args:
            *args: args for the hook
            **kwargs: kwargs for the hook

        Returns:
            Depending on `self.result`:
            - SimplugResult.ALL: Get all the results from the hook, as a list
                including `NONE`s
            - SimplugResult.ALL_AVAILS: Get all the results from the hook,
                as a list, not including `NONE`s
            - SimplugResult.FIRST: Get the none-`None` result from the
                first plugin only (ordered by priority)
            - SimplugResult.LAST: Get the none-`None` result from
                the last plugin only
        """
        self.simplug_hooks._sort_registry()
        if (
            self.result not in (SimplugResult.SINGLE, SimplugResult.TRY_SINGLE)
            and "__plugin" in kwargs
        ):
            raise ValueError(
                "Cannot use __plugin with non-SimplugResult.(TRY_)SINGLE hooks"
            )

        _plugin = kwargs.pop("__plugin", None)
        calls = []
        for plugin in self.simplug_hooks._registry.values():
            if not plugin.enabled:
                continue
            hook = plugin.hook(self.name)

            if hook is not None:
                plugin_args = (plugin.plugin, *args) if hook.has_self else args
                calls.append(
                    SimplugImplCall(
                        plugin.name, hook.impl, plugin_args, kwargs
                    )
                )

        return self._get_results(calls, plugin=_plugin)


class SimplugHookAsync(SimplugHook):
    """Wrapper of an async hook"""

    async def _get_results(
        self,
        calls: List[SimplugImplCall],
        plugin: str,
        result: SimplugResult | Callable | int = None,
    ) -> Any:
        """Get the results according to self.result"""
        result = self.result if result is None else result

        if callable(result):
            return await result(calls)

        if isinstance(result, SimplugResult):
            result = result.value

        # 0b  1    1    1    1111
        #    TRY  ALL AVAIL   ID
        if result & 0b100_0000:
            try:
                return await self._get_results(
                    calls,
                    plugin,
                    result & 0b011_1111,
                )
            except ResultUnavailableError:
                return None

        if result & 0b010_0000:
            out = [await makecall(call, True) for call in calls]
            if result == SimplugResult.ALL.value:
                return out
            if result == SimplugResult.ALL_AVAILS.value:
                return [x for x in out if x is not None]
            if result == SimplugResult.ALL_FIRST.value:
                if not out:
                    raise ResultUnavailableError
                return out[0]
            if result == SimplugResult.ALL_LAST.value:
                if not out:
                    raise ResultUnavailableError
                return out[-1]
            if result == SimplugResult.ALL_FIRST_AVAIL.value:
                if not out or all(x is None for x in out):
                    raise ResultUnavailableError
                return next(x for x in out if x is not None)
            if result == SimplugResult.ALL_LAST_AVAIL.value:
                if not out or all(x is None for x in out):
                    raise ResultUnavailableError
                return next(x for x in reversed(out) if x is not None)

        if result == SimplugResult.FIRST.value:
            if not calls:
                raise ResultUnavailableError
            return await makecall(calls[0], True)
        if result == SimplugResult.LAST.value:
            if not calls:
                raise ResultUnavailableError
            return await makecall(calls[-1], True)
        if result == SimplugResult.FIRST_AVAIL.value:
            for call in calls:
                ret = await makecall(call, True)
                if ret is not None:
                    return ret
            raise ResultUnavailableError
        if result == SimplugResult.LAST_AVAIL.value:
            for call in reversed(calls):
                ret = await makecall(call, True)
                if ret is not None:
                    return ret
            raise ResultUnavailableError
        if result == SimplugResult.SINGLE.value:
            if not calls:
                raise ResultUnavailableError
            for call in calls:
                if call.plugin == plugin:
                    return await makecall(call, True)
            if plugin is not None:
                raise ResultUnavailableError
            if len(calls) > 1:
                warnings.warn(
                    f"More than one implementation of {self.name} found, "
                    "but no plugin was specified. Using the last one.",
                    MultipleImplsForSingleResultHookWarning,
                )
            return await makecall(calls[-1], True)

    async def __call__(self, *args, **kwargs):
        """Call the hook in your system asynchronously

        Args:
            *args: args for the hook
            **kwargs: kwargs for the hook

        Returns:
            Depending on `self.result`:
            - SimplugResult.ALL: Get all the results from the hook, as a list
                including `NONE`s
            - SimplugResult.ALL_AVAILS: Get all the results from the hook,
                as a list, not including `NONE`s
            - SimplugResult.FIRST: Get the none-`None` result from the
                first plugin only (ordered by priority)
            - SimplugResult.LAST: Get the none-`None` result from
                the last plugin only
        """
        self.simplug_hooks._sort_registry()
        if (
            self.result not in (SimplugResult.SINGLE, SimplugResult.TRY_SINGLE)
            and "__plugin" in kwargs
        ):
            raise ValueError(
                "Cannot use __plugin with non-SimplugResult.(TRY_)SINGLE hooks"
            )

        _plugin = kwargs.pop("__plugin", None)
        calls = []
        for plugin in self.simplug_hooks._registry.values():
            if not plugin.enabled:
                continue
            hook = plugin.hook(self.name)
            if hook is None:  # pragma: no cover
                continue

            plugin_args = (plugin.plugin, *args) if hook.has_self else args
            calls.append(
                SimplugImplCall(plugin.name, hook.impl, plugin_args, kwargs)
            )

        return await self._get_results(calls, plugin=_plugin)


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

        self._registry = OrderedDiot()  # type: OrderedDiot
        self._specs = {}  # type: Dict[str, SimplugHook]
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
        if (
            plugin.name in self._registry
            and plugin != self._registry[plugin.name]
        ):
            raise PluginRegistered(
                f"Another plugin named {plugin.name} "
                "has already been registered."
            )
        # check if required hooks implemented
        # and signature
        for specname, spec in self._specs.items():
            hook = plugin.hook(specname)
            if spec.required and hook is None:
                raise HookRequired(
                    f"{specname}, but not implemented "
                    f"in plugin {plugin.name}"
                )
            if hook is None:  # pragma: no cover
                continue

            impl_params = list(inspect.signature(hook.impl).parameters.keys())
            spec_params = list(inspect.signature(spec.spec).parameters.keys())

            if len(impl_params) > 0 and impl_params[0] == "self":
                impl_params = impl_params[1:]
            if len(spec_params) > 0 and spec_params[0] == "self":
                spec_params = spec_params[1:]

            if impl_params != spec_params:
                raise HookSignatureDifferentFromSpec(
                    f"{specname!r} in plugin {plugin.name}\n"
                    f"Expect {spec_params}, "
                    f"but got {impl_params}"
                )

            if (
                isinstance(spec, SimplugHookAsync)
                and spec.warn_sync_impl_on_async
                and not inspect.iscoroutinefunction(hook.impl)
            ):
                warnings.warn(
                    f"Sync implementation on async hook "
                    f"{specname!r} in plugin {plugin.name}",
                    SyncImplOnAsyncSpecWarning,
                )

        self._registry[plugin.name] = plugin

    def _sort_registry(self) -> None:
        """Sort the registry by the priority only once"""
        if self._registry_sorted:
            return
        orderedkeys = self._registry.__diot__["orderedkeys"]
        self._registry.__diot__["orderedkeys"] = sorted(
            orderedkeys, key=lambda plug: self._registry[plug].priority
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


class SimplugContext:
    """The context manager for enabling or disabling a set of plugins"""

    def __init__(self, simplug: "Simplug", plugins: Optional[Iterable[Any]]):
        self.plugins = plugins
        if plugins is not None:
            self.simplug = simplug
            self.orig_registry = simplug.hooks._registry.copy()
            self.orig_status = {
                name: plugin.enabled
                for name, plugin in self.orig_registry.items()
            }

    def __enter__(self):
        if self.plugins is None:
            return
        orig_registry = self.orig_registry.copy()
        # raw
        orig_names = list(orig_registry.keys())
        orig_raws = [plugin.plugin for plugin in orig_registry.values()]

        for plugin in self.plugins:
            if isinstance(plugin, str) and plugin in orig_registry:
                orig_registry[plugin].enable()
                del orig_registry[plugin]
            elif plugin in orig_registry.values():
                plugin.enable()
                del orig_registry[plugin.name]
            elif plugin in orig_raws:
                name = orig_names[orig_raws.index(plugin)]
                orig_registry[name].enable()
                del orig_registry[name]
            else:
                self.simplug.register(plugin)

        for plugin in orig_registry.values():
            plugin.disable()

    def __exit__(self, *exc):
        if self.plugins is None:
            return
        self.simplug.hooks._registry = self.orig_registry
        for name, status in self.orig_status.items():
            self.simplug.hooks._registry[name].enabled = status


class _SimplugContextOnly(SimplugContext):
    """The context manager with only given plugins enabled"""


class _SimplugContextBut(SimplugContext):
    """The context manager with only given plugins disabled"""

    def __enter__(self):
        if self.plugins is None:
            return

        orig_registry = self.orig_registry.copy()
        # raw
        orig_names = list(orig_registry.keys())
        orig_raws = [plugin.plugin for plugin in orig_registry.values()]

        for plugin in self.plugins:
            if isinstance(plugin, str) and plugin in orig_registry:
                orig_registry[plugin].disable()
                del orig_registry[plugin]
            elif plugin in orig_registry.values():
                plugin.disable()
                del orig_registry[plugin.name]
            elif plugin in orig_raws:
                name = orig_names[orig_raws.index(plugin)]
                orig_registry[name].disable()
                del orig_registry[name]
            # ignore plugin not existing

        for plugin in orig_registry.values():
            plugin.enable()


class Simplug:
    """The plugin manager for simplug

    Attributes:
        PROJECTS: The projects registry, to make sure the same `Simplug`
            object by the name project name.

        _batch_index: The batch index for plugin registration
        hooks: The hooks manager
        _inited: Whether `__init__` has already been called. Since the
            `__init__` method will be called after `__new__`, this is used to
            avoid `__init__` to be called more than once
    """

    PROJECTS: Dict[str, "Simplug"] = {}

    def __new__(cls, project: str) -> "Simplug":
        if project not in cls.PROJECTS:
            obj = super().__new__(cls)
            obj.__init__(project)  # type: ignore
            cls.PROJECTS[project] = obj

        return cls.PROJECTS[project]

    def __init__(self, project: str):
        if getattr(self, "_inited", None):
            return
        self._batch_index = 0
        self.hooks = SimplugHooks()
        self.project = project
        self._inited = True

    def load_entrypoints(
        self,
        group: Optional[str] = None,
        only: str | Iterable[str] = (),
    ) -> None:
        """Load plugins from setuptools entry_points"""
        group = group or self.project

        if isinstance(only, str):
            only = [only]

        try:
            eps = metadata.entry_points(group=group)
        except TypeError:  # pragma: no cover
            eps = metadata.entry_points().get(group, [])

        for ep in eps:
            if only and ep.name not in only:
                continue

            plugin = ep.load()
            self.register((plugin, ep.name))

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

    def get_all_plugins(self, raw: bool = False) -> Dict[str, SimplugWrapper]:
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
        return OrderedDiot(
            [
                (name, plugin.plugin)
                for name, plugin in self.hooks._registry.items()
            ]
        )

    def get_enabled_plugins(
        self, raw: bool = False
    ) -> Dict[str, SimplugWrapper]:
        """Get a mapping of all enabled plugins

        Args:
            raw: Whether return the raw plugin or not
                (the one when it's registered)
                If a plugin is registered as a module by its name, the module
                is returned.

        Returns:
            The mapping of all enabled plugins
        """
        return OrderedDiot(
            [
                (name, plugin.plugin if raw else plugin)
                for name, plugin in self.hooks._registry.items()
                if plugin.enabled
            ]
        )

    def get_all_plugin_names(self) -> List[str]:
        """Get the names of all plugins

        Returns:
            The names of all plugins
        """
        return list(self.hooks._registry.keys())

    def get_enabled_plugin_names(self) -> List[str]:
        """Get the names of all enabled plugins

        Returns:
            The names of all enabled plugins
        """
        return [
            name
            for name, plugin in self.hooks._registry.items()
            if plugin.enabled
        ]

    def plugins_only_context(
        self, plugins: Optional[Iterable[Any]]
    ) -> _SimplugContextOnly:
        """A context manager with only given plugins enabled

        Args:
            plugins: The plugin names or plugin objects
                If the given plugin does not exist, register it.
                None to not enable or disable anything

        Returns:
            The context manager
        """
        return _SimplugContextOnly(self, plugins)

    def plugins_but_context(
        self, plugins: Optional[Iterable[Any]]
    ) -> _SimplugContextBut:
        """A context manager with all plugins but given plugins
        enabled

        Args:
            *plugins: The plugin names or plugin objects to exclude
                If the given plugin does not exist, ignore it

        Returns:
            The context manager
        """
        return _SimplugContextBut(self, plugins)

    def enable(self, *names: str) -> None:
        """Enable plugins by names

        Args:
            *names: The names of the plugin
        """
        for name in names:
            self.get_plugin(name).enable()

    def disable(self, *names: str) -> None:
        """Disable plugins by names

        Args:
            names: The names of the plugin
        """
        for name in names:
            self.get_plugin(name).disable()

    def spec(
        self,
        hook: Optional[Callable] = None,
        required: bool = False,
        result: SimplugResult | Callable = SimplugResult.ALL_AVAILS,
        warn_sync_impl_on_async: bool = True,
    ) -> Callable:
        """A decorator to define the specification of a hook

        Args:
            hook: The hook spec. If it is None, that means this decorator is
                called with arguments, and it should be keyword arguments.
                Otherwise, it is called like this `simplug.spec`
            required: Whether this hook is required to be implemented.
            result: How should we collect the results from the plugins
            warn_sync_impl_on_async: Whether to warn when a sync implementation

        Raises:
            HookSpecExists: If a hook spec with the same name (`hook.__name__`)
                 is already defined.

        Returns:
            A decorator function of other argument is passed, or the hook spec
                itself.
        """
        if hook is None:
            return lambda hk: self.spec(
                hk,
                required=required,
                result=result,
                warn_sync_impl_on_async=warn_sync_impl_on_async,
            )

        hook_name = hook.__name__
        if hook_name in self.hooks._specs:
            raise HookSpecExists(hook_name)

        if inspect.iscoroutinefunction(hook):
            self.hooks._specs[hook_name] = SimplugHookAsync(
                self.hooks,
                hook,
                required,
                result,
                warn_sync_impl_on_async,
            )
        else:
            self.hooks._specs[hook_name] = SimplugHook(
                self.hooks,
                hook,
                required,
                result,
            )

        return hook

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
        return SimplugImpl(hook, "self" in inspect.signature(hook).parameters)
