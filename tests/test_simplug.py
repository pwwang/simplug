import os
import sys
import asyncio
from pathlib import Path

import pytest
from simplug import (
    makecall,
    Simplug,
    SimplugResult,
    SimplugWrapper,
    SimplugException,
    ResultUnavailableError,
    ResultError,
    HookSpecExists,
    NoSuchHookSpec,
    NoSuchPlugin,
    HookSignatureDifferentFromSpec,
    HookRequired,
    PluginRegistered,
    SyncImplOnAsyncSpecWarning,
    MultipleImplsForSingleResultHookWarning,
    AsyncImplOnSyncSpecError,
)


@pytest.fixture
def test_suite(request):
    simplug = Simplug(request.node.name)
    plugins = {}

    class Suite:
        def add_hook(self, result, required=False):
            def decorator(func):
                simplug.spec(func, result=result, required=required)
            return decorator

        def add_impl(self, plugin_name):
            def decorator(func):
                if plugin_name not in plugins:
                    class Plugin:
                        name = plugin_name
                    plugins[plugin_name] = Plugin

                setattr(plugins[plugin_name], func.__name__, simplug.impl(func))
            return decorator

        def disable_plugin(self, plugin_name):
            simplug.get_plugin(plugin_name).disable()

        def enable_plugin(self, plugin_name):
            simplug.get_plugin(plugin_name).enable()

        def get_simplug(self):
            return simplug

        def get_plugin(self, name):
            return simplug.get_plugin(name)

        def get_all_plugins(self, raw=False):
            return simplug.get_all_plugins(raw=raw)

        def get_enabled_plugins(self, raw=False):
            return simplug.get_enabled_plugins(raw=raw)

        def __getattr__(self, name):
            registered = simplug.get_all_plugin_names()
            simplug.register(
                *(plugins[n] for n in plugins if n not in registered)
            )
            return getattr(simplug.hooks, name)

    return Suite()


def test_result_all(test_suite):
    @test_suite.add_hook(SimplugResult.ALL)
    def hook(arg):
        ...

    @test_suite.add_impl("plugin1")
    def hook(arg):
        return arg + 1

    @test_suite.add_impl("plugin2")
    def hook(arg):
        return arg + 2

    assert test_suite.hook(1) == [2, 3]


def test_result_all_async(test_suite):
    @test_suite.add_hook(SimplugResult.ALL)
    async def hook(arg):
        ...

    @test_suite.add_impl("plugin1")
    async def hook(arg):
        return arg + 1

    @test_suite.add_impl("plugin2")
    async def hook(arg):
        return arg + 2

    assert asyncio.run(test_suite.hook(1)) == [2, 3]


def test_result_all_avails(test_suite):
    @test_suite.add_hook(SimplugResult.ALL_AVAILS)
    def hook(arg):
        ...

    @test_suite.add_impl("plugin1")
    def hook(arg):
        return arg + 1

    @test_suite.add_impl("plugin2")
    def hook(arg):
        return None

    assert test_suite.hook(1) == [2]


def test_result_all_avails_async(test_suite):
    @test_suite.add_hook(SimplugResult.ALL_AVAILS)
    async def hook(arg):
        ...

    @test_suite.add_impl("plugin1")
    async def hook(arg):
        return arg + 1

    @test_suite.add_impl("plugin2")
    async def hook(arg):
        return None

    assert asyncio.run(test_suite.hook(1)) == [2]


def test_result_all_first(test_suite, capsys):
    @test_suite.add_hook(SimplugResult.ALL_FIRST)
    def hook(arg):
        ...

    @test_suite.add_impl("plugin1")
    def hook(arg):
        return arg + 1

    @test_suite.add_impl("plugin2")
    def hook(arg):
        print("hello")

    assert test_suite.hook(1) == 2
    assert capsys.readouterr().out.strip() == "hello"


def test_result_all_first_async(test_suite, capsys):
    @test_suite.add_hook(SimplugResult.ALL_FIRST)
    async def hook(arg):
        ...

    @test_suite.add_impl("plugin1")
    async def hook(arg):
        return arg + 1

    @test_suite.add_impl("plugin2")
    async def hook(arg):
        print("hello")

    assert asyncio.run(test_suite.hook(1)) == 2
    assert capsys.readouterr().out.strip() == "hello"


def test_result_all_first_error(test_suite):
    @test_suite.add_hook(SimplugResult.ALL_FIRST)
    def hook(arg):
        ...

    @test_suite.add_hook(SimplugResult.ALL_FIRST)
    async def ahook(arg):
        ...

    with pytest.raises(ResultUnavailableError):
        test_suite.hook(1)

    with pytest.raises(ResultUnavailableError):
        asyncio.run(test_suite.ahook(1))


def test_result_all_last(test_suite, capsys):
    @test_suite.add_hook(SimplugResult.ALL_LAST)
    def hook(arg):
        ...

    @test_suite.add_impl("plugin1")
    def hook(arg):
        print("hello")

    @test_suite.add_impl("plugin2")
    def hook(arg):
        return arg + 1

    assert test_suite.hook(1) == 2
    assert capsys.readouterr().out.strip() == "hello"


def test_result_all_last_async(test_suite, capsys):
    @test_suite.add_hook(SimplugResult.ALL_LAST)
    async def hook(arg):
        ...

    @test_suite.add_impl("plugin1")
    async def hook(arg):
        print("hello")

    @test_suite.add_impl("plugin2")
    async def hook(arg):
        return arg + 1

    assert asyncio.run(test_suite.hook(1)) == 2
    assert capsys.readouterr().out.strip() == "hello"


def test_result_all_last_error(test_suite):
    @test_suite.add_hook(SimplugResult.ALL_LAST)
    def hook(arg):
        ...

    @test_suite.add_hook(SimplugResult.ALL_LAST)
    async def ahook(arg):
        ...

    with pytest.raises(ResultUnavailableError):
        test_suite.hook(1)

    with pytest.raises(ResultUnavailableError):
        asyncio.run(test_suite.ahook(1))


def test_result_try_all_first(test_suite):

    @test_suite.add_hook(SimplugResult.TRY_ALL_FIRST)
    def hook(arg):
        ...

    assert test_suite.hook(1) is None


def test_result_try_all_first_async(test_suite):

    @test_suite.add_hook(SimplugResult.TRY_ALL_FIRST)
    async def hook(arg):
        ...

    assert asyncio.run(test_suite.hook(1)) is None


def test_result_try_all_last(test_suite):

    @test_suite.add_hook(SimplugResult.TRY_ALL_LAST)
    def hook(arg):
        ...

    assert test_suite.hook(1) is None


def test_result_try_all_last_async(test_suite):

    @test_suite.add_hook(SimplugResult.TRY_ALL_LAST)
    async def hook(arg):
        ...

    assert asyncio.run(test_suite.hook(1)) is None


def test_result_all_first_avail(test_suite, capsys):
    @test_suite.add_hook(SimplugResult.ALL_FIRST_AVAIL)
    def hook(arg):
        ...

    @test_suite.add_impl("plugin1")
    def hook(arg):
        return None

    @test_suite.add_impl("plugin2")
    def hook(arg):
        return arg + 1

    @test_suite.add_impl("plugin3")
    def hook(arg):
        print("hello")

    assert test_suite.hook(1) == 2
    assert capsys.readouterr().out.strip() == "hello"


def test_result_all_first_avail_async(test_suite, capsys):
    @test_suite.add_hook(SimplugResult.ALL_FIRST_AVAIL)
    async def hook(arg):
        ...

    @test_suite.add_impl("plugin1")
    async def hook(arg):
        return None

    @test_suite.add_impl("plugin2")
    async def hook(arg):
        return arg + 1

    @test_suite.add_impl("plugin3")
    async def hook(arg):
        print("hello")

    assert asyncio.run(test_suite.hook(1)) == 2
    assert capsys.readouterr().out.strip() == "hello"


def test_result_all_first_avail_error(test_suite):
    @test_suite.add_hook(SimplugResult.ALL_FIRST_AVAIL)
    def hook(arg):
        ...

    @test_suite.add_hook(SimplugResult.ALL_FIRST_AVAIL)
    async def ahook(arg):
        ...

    @test_suite.add_impl("plugin1")
    def hook(arg):
        return None

    @test_suite.add_impl("plugin1")
    async def ahook(arg):
        return None

    with pytest.raises(ResultUnavailableError):
        test_suite.hook(1)

    with pytest.raises(ResultUnavailableError):
        asyncio.run(test_suite.ahook(1))


def test_result_try_all_first_avail(test_suite):
    @test_suite.add_hook(SimplugResult.TRY_ALL_FIRST_AVAIL)
    def hook(arg):
        ...

    @test_suite.add_impl("plugin1")
    def hook(arg):
        return None

    assert test_suite.hook(1) is None


def test_result_try_all_first_avail_async(test_suite):
    @test_suite.add_hook(SimplugResult.TRY_ALL_FIRST_AVAIL)
    async def hook(arg):
        ...

    @test_suite.add_impl("plugin1")
    async def hook(arg):
        return None

    assert asyncio.run(test_suite.hook(1)) is None


def test_result_all_last_avail(test_suite, capsys):
    @test_suite.add_hook(SimplugResult.ALL_LAST_AVAIL)
    def hook(arg):
        ...

    @test_suite.add_impl("plugin1")
    def hook(arg):
        print("hello")

    @test_suite.add_impl("plugin2")
    def hook(arg):
        return arg + 1

    @test_suite.add_impl("plugin3")
    def hook(arg):
        return None

    assert test_suite.hook(1) == 2
    assert capsys.readouterr().out.strip() == "hello"


def test_result_all_last_avail_async(test_suite, capsys):
    @test_suite.add_hook(SimplugResult.ALL_LAST_AVAIL)
    async def hook(arg):
        ...

    @test_suite.add_impl("plugin1")
    async def hook(arg):
        print("hello")

    @test_suite.add_impl("plugin2")
    async def hook(arg):
        return arg + 1

    @test_suite.add_impl("plugin3")
    async def hook(arg):
        return None

    assert asyncio.run(test_suite.hook(1)) == 2
    assert capsys.readouterr().out.strip() == "hello"


def test_result_all_last_avail_error(test_suite):
    @test_suite.add_hook(SimplugResult.ALL_LAST_AVAIL)
    def hook(arg):
        ...

    @test_suite.add_impl("plugin1")
    def hook(arg):
        return None

    @test_suite.add_hook(SimplugResult.ALL_LAST_AVAIL)
    async def ahook(arg):
        ...

    @test_suite.add_impl("plugin1")
    async def ahook(arg):
        return None

    with pytest.raises(ResultUnavailableError):
        test_suite.hook(1)

    with pytest.raises(ResultUnavailableError):
        asyncio.run(test_suite.ahook(1))


def test_result_try_all_last_avail(test_suite):
    @test_suite.add_hook(SimplugResult.TRY_ALL_LAST_AVAIL)
    def hook(arg):
        ...

    @test_suite.add_impl("plugin1")
    def hook(arg):
        return None

    assert test_suite.hook(1) is None


def test_result_try_all_last_avail_async(test_suite):
    @test_suite.add_hook(SimplugResult.TRY_ALL_LAST_AVAIL)
    async def hook(arg):
        ...

    @test_suite.add_impl("plugin1")
    async def hook(arg):
        return None

    assert asyncio.run(test_suite.hook(1)) is None


def test_result_first(test_suite, capsys):
    @test_suite.add_hook(SimplugResult.FIRST)
    def hook(arg):
        ...

    @test_suite.add_impl("plugin1")
    def hook(arg):
        return arg + 1

    @test_suite.add_impl("plugin2")
    def hook(arg):
        print("hello")

    assert test_suite.hook(1) == 2
    assert capsys.readouterr().out.strip() == ""


def test_result_first_async(test_suite, capsys):
    @test_suite.add_hook(SimplugResult.FIRST)
    async def hook(arg):
        ...

    @test_suite.add_impl("plugin1")
    async def hook(arg):
        return arg + 1

    @test_suite.add_impl("plugin2")
    async def hook(arg):
        print("hello")

    assert asyncio.run(test_suite.hook(1)) == 2
    assert capsys.readouterr().out.strip() == ""


def test_result_first_error(test_suite):
    @test_suite.add_hook(SimplugResult.FIRST)
    def hook(arg):
        ...

    @test_suite.add_hook(SimplugResult.FIRST)
    async def ahook(arg):
        ...

    with pytest.raises(ResultUnavailableError):
        test_suite.hook(1)

    with pytest.raises(ResultUnavailableError):
        asyncio.run(test_suite.ahook(1))


def test_result_last(test_suite, capsys):
    @test_suite.add_hook(SimplugResult.LAST)
    def hook(arg):
        ...

    @test_suite.add_impl("plugin1")
    def hook(arg):
        print("hello")

    @test_suite.add_impl("plugin2")
    def hook(arg):
        return arg + 1

    assert test_suite.hook(1) == 2
    assert capsys.readouterr().out.strip() == ""


def test_result_last_async(test_suite, capsys):
    @test_suite.add_hook(SimplugResult.LAST)
    async def hook(arg):
        ...

    @test_suite.add_impl("plugin1")
    async def hook(arg):
        print("hello")

    @test_suite.add_impl("plugin2")
    async def hook(arg):
        return arg + 1

    assert asyncio.run(test_suite.hook(1)) == 2
    assert capsys.readouterr().out.strip() == ""


def test_result_last_error(test_suite):
    @test_suite.add_hook(SimplugResult.LAST)
    def hook(arg):
        ...

    @test_suite.add_hook(SimplugResult.LAST)
    async def ahook(arg):
        ...

    with pytest.raises(ResultUnavailableError):
        test_suite.hook(1)

    with pytest.raises(ResultUnavailableError):
        asyncio.run(test_suite.ahook(1))


def test_result_try_first(test_suite):
    @test_suite.add_hook(SimplugResult.TRY_FIRST)
    def hook(arg):
        ...

    @test_suite.add_hook(SimplugResult.TRY_FIRST)
    async def ahook(arg):
        ...

    assert test_suite.hook(1) is None
    assert asyncio.run(test_suite.ahook(1)) is None


def test_result_try_last(test_suite):
    @test_suite.add_hook(SimplugResult.TRY_LAST)
    def hook(arg):
        ...

    @test_suite.add_hook(SimplugResult.TRY_LAST)
    async def ahook(arg):
        ...

    assert test_suite.hook(1) is None
    assert asyncio.run(test_suite.ahook(1)) is None


def test_result_first_avail(test_suite, capsys):
    @test_suite.add_hook(SimplugResult.FIRST_AVAIL)
    def hook(arg):
        ...

    @test_suite.add_impl("plugin0")
    def hook(arg):
        return None

    @test_suite.add_impl("plugin1")
    def hook(arg):
        return arg + 1

    @test_suite.add_impl("plugin2")
    def hook(arg):
        print("hello")

    assert test_suite.hook(1) == 2
    assert capsys.readouterr().out.strip() == ""


def test_result_first_avail_async(test_suite, capsys):
    @test_suite.add_hook(SimplugResult.FIRST_AVAIL)
    async def hook(arg):
        ...

    @test_suite.add_impl("plugin0")
    async def hook(arg):
        return None

    @test_suite.add_impl("plugin1")
    async def hook(arg):
        return arg + 1

    @test_suite.add_impl("plugin2")
    async def hook(arg):
        print("hello")

    assert asyncio.run(test_suite.hook(1)) == 2
    assert capsys.readouterr().out.strip() == ""


def test_result_first_avail_error(test_suite):
    @test_suite.add_hook(SimplugResult.FIRST_AVAIL)
    def hook(arg):
        ...

    @test_suite.add_hook(SimplugResult.FIRST_AVAIL)
    async def ahook(arg):
        ...

    with pytest.raises(ResultUnavailableError):
        test_suite.hook(1)

    with pytest.raises(ResultUnavailableError):
        asyncio.run(test_suite.ahook(1))


def test_result_last_avail(test_suite, capsys):
    @test_suite.add_hook(SimplugResult.LAST_AVAIL)
    def hook(arg):
        ...

    @test_suite.add_impl("plugin0")
    def hook(arg):
        print("hello")

    @test_suite.add_impl("plugin1")
    def hook(arg):
        return arg + 1

    @test_suite.add_impl("plugin2")
    def hook(arg):
        return None

    assert test_suite.hook(1) == 2
    assert capsys.readouterr().out.strip() == ""


def test_result_last_avail_async(test_suite, capsys):
    @test_suite.add_hook(SimplugResult.LAST_AVAIL)
    async def hook(arg):
        ...

    @test_suite.add_impl("plugin0")
    async def hook(arg):
        print("hello")

    @test_suite.add_impl("plugin1")
    async def hook(arg):
        return arg + 1

    @test_suite.add_impl("plugin2")
    async def hook(arg):
        return None

    assert asyncio.run(test_suite.hook(1)) == 2
    assert capsys.readouterr().out.strip() == ""


def test_result_last_avail_error(test_suite):
    @test_suite.add_hook(SimplugResult.LAST_AVAIL)
    def hook(arg):
        ...

    @test_suite.add_hook(SimplugResult.LAST_AVAIL)
    async def ahook(arg):
        ...

    with pytest.raises(ResultUnavailableError):
        test_suite.hook(1)

    with pytest.raises(ResultUnavailableError):
        asyncio.run(test_suite.ahook(1))


def test_result_try_first_avail(test_suite):
    @test_suite.add_hook(SimplugResult.TRY_FIRST_AVAIL)
    def hook(arg):
        ...

    @test_suite.add_hook(SimplugResult.TRY_FIRST_AVAIL)
    def hook1(arg):
        ...

    @test_suite.add_hook(SimplugResult.TRY_FIRST_AVAIL)
    async def ahook(arg):
        ...

    @test_suite.add_hook(SimplugResult.TRY_FIRST_AVAIL)
    async def ahook1(arg):
        ...

    @test_suite.add_impl("plugin0")
    def hook(arg):
        return None

    @test_suite.add_impl("plugin0")
    def hook1(arg):
        return 1

    @test_suite.add_impl("plugin0")
    async def ahook(arg):
        return None

    @test_suite.add_impl("plugin0")
    async def ahook1(arg):
        return 1

    assert test_suite.hook(1) is None
    assert asyncio.run(test_suite.ahook(1)) is None
    assert test_suite.hook1(1) == 1
    assert asyncio.run(test_suite.ahook1(1)) == 1


def test_result_try_last_avail(test_suite):
    @test_suite.add_hook(SimplugResult.TRY_LAST_AVAIL)
    def hook(arg):
        ...

    @test_suite.add_hook(SimplugResult.TRY_LAST_AVAIL)
    def hook1(arg):
        ...

    @test_suite.add_hook(SimplugResult.TRY_LAST_AVAIL)
    async def ahook(arg):
        ...

    @test_suite.add_hook(SimplugResult.TRY_LAST_AVAIL)
    async def ahook1(arg):
        ...

    @test_suite.add_impl("plugin0")
    def hook(arg):
        return None

    @test_suite.add_impl("plugin0")
    def hook1(arg):
        return 1

    @test_suite.add_impl("plugin0")
    async def ahook(arg):
        return None

    @test_suite.add_impl("plugin0")
    async def ahook1(arg):
        return 1

    assert test_suite.hook(1) is None
    assert asyncio.run(test_suite.ahook(1)) is None
    assert test_suite.hook1(1) == 1
    assert asyncio.run(test_suite.ahook1(1)) == 1


def test_result_single(test_suite):
    @test_suite.add_hook(SimplugResult.SINGLE)
    def hook(arg):
        ...

    @test_suite.add_hook(SimplugResult.SINGLE)
    async def ahook(arg):
        ...

    @test_suite.add_impl("plugin0")
    def hook(arg):
        return 1

    @test_suite.add_impl("plugin1")
    def hook(arg):
        return 2

    @test_suite.add_impl("plugin0")
    async def ahook(arg):
        return 1

    @test_suite.add_impl("plugin1")
    async def ahook(arg):
        return 2

    with pytest.warns(MultipleImplsForSingleResultHookWarning):
        assert test_suite.hook(1) == 2

    with pytest.warns(MultipleImplsForSingleResultHookWarning):
        assert asyncio.run(test_suite.ahook(1)) == 2

    with pytest.raises(ResultUnavailableError):
        test_suite.hook(1, __plugin="plugin2")

    with pytest.raises(ResultUnavailableError):
        asyncio.run(test_suite.ahook(1, __plugin="plugin2"))

    assert test_suite.hook(1, __plugin="plugin0") == 1
    assert asyncio.run(test_suite.ahook(1, __plugin="plugin0")) == 1


def test_result_single_error(test_suite):
    @test_suite.add_hook(SimplugResult.SINGLE)
    def hook(arg):
        ...

    @test_suite.add_hook(SimplugResult.SINGLE)
    async def ahook(arg):
        ...

    @test_suite.add_hook(SimplugResult.ALL)
    def hook1(arg):
        ...

    @test_suite.add_hook(SimplugResult.ALL)
    async def ahook1(arg):
        ...

    with pytest.raises(ResultUnavailableError):
        test_suite.hook(1)

    with pytest.raises(ResultUnavailableError):
        asyncio.run(test_suite.ahook(1))

    with pytest.raises(ValueError):
        test_suite.hook1(1, __plugin="plugin0")

    with pytest.raises(ValueError):
        asyncio.run(test_suite.ahook1(1, __plugin="plugin0"))


def test_result_custom(test_suite):
    async def custom_result(calls):
        return " ".join([await makecall(call, True) for call in calls])

    @test_suite.add_hook(
        lambda calls: " ".join(makecall(call) for call in calls)
    )
    def hook(arg):
        ...

    @test_suite.add_hook(custom_result)
    async def ahook(arg):
        ...

    @test_suite.add_impl("plugin0")
    def hook(arg):
        return "hello"

    @test_suite.add_impl("plugin1")
    def hook(arg):
        return "world"

    @test_suite.add_impl("plugin0")
    async def ahook(arg):
        return "hello,"

    @test_suite.add_impl("plugin1")
    def ahook(arg):
        return "world!"

    with pytest.warns(SyncImplOnAsyncSpecWarning):
        out1 = test_suite.hook(1)
        out2 = asyncio.run(test_suite.ahook(1))

    assert out1 == "hello world"
    assert out2 == "hello, world!"


def test_no_such_plugin_module():
    plugin = Simplug("test_no_such_plugin_module")
    with pytest.raises(NoSuchPlugin):
        plugin.register("no_such_module")


def test_plugin_name_and_version():
    plugin1 = Simplug("test_plugin_version1")
    plugin2 = Simplug("test_plugin_version2")

    class Plugin:
        version = "0.1.0"

    plugin1.register(Plugin)
    assert plugin1.get_plugin("plugin").name == "plugin"
    assert plugin1.get_plugin("plugin").version == "0.1.0"

    plugin2.register(Plugin())
    assert plugin1.get_plugin("plugin").name == "plugin"
    assert plugin1.get_plugin("plugin").version == "0.1.0"


def test_get_hook():
    plugin = Simplug("test_get_hook")

    @plugin.spec
    def hook(arg):
        ...

    class Plugin:
        @plugin.impl
        def hook(arg):
            return arg + 1

    plugin.register(Plugin)

    assert plugin.get_plugin("plugin").hook("hook") is Plugin.hook
    assert plugin.get_plugin("plugin").hook("hook2") is None


def test_plugin_enable_disable(test_suite):
    @test_suite.add_hook(SimplugResult.ALL)
    def hook(arg):
        ...

    @test_suite.add_impl("plugin0")
    def hook(arg):
        return 1

    @test_suite.add_impl("plugin1")
    def hook(arg):
        return 2

    @test_suite.add_hook(SimplugResult.ALL)
    async def ahook(arg):
        ...

    @test_suite.add_impl("plugin0")
    async def ahook(arg):
        return 1

    @test_suite.add_impl("plugin1")
    async def ahook(arg):
        return 2

    assert test_suite.hook(1) == [1, 2]

    test_suite.disable_plugin("plugin0")
    assert test_suite.hook(1) == [2]
    assert asyncio.run(test_suite.ahook(1)) == [2]

    test_suite.enable_plugin("plugin0")
    assert test_suite.hook(1) == [1, 2]
    assert asyncio.run(test_suite.ahook(1)) == [1, 2]

    simplug = test_suite.get_simplug()

    simplug.disable("plugin0")
    assert test_suite.hook(1) == [2]
    assert asyncio.run(test_suite.ahook(1)) == [2]

    simplug.enable("plugin0")
    assert test_suite.hook(1) == [1, 2]
    assert asyncio.run(test_suite.ahook(1)) == [1, 2]


def test_plugin_eq(test_suite):

    @test_suite.add_hook(SimplugResult.ALL)
    def hook(arg):
        ...

    @test_suite.add_impl("plugin0")
    def hook(arg):
        return 1

    @test_suite.add_impl("plugin1")
    def hook(arg):
        return 2

    assert test_suite.hook(1) == [1, 2]
    assert test_suite.get_plugin("plugin0") == test_suite.get_plugin("plugin0")
    assert test_suite.get_plugin("plugin0") != test_suite.get_plugin("plugin1")


def test_plugin_registered():
    plugin = Simplug("test_plugin_registered")

    class Plugin:
        ...

    plugin.register(Plugin)
    with pytest.raises(PluginRegistered):
        plugin.register(Plugin())


def test_hook_required(test_suite):
    @test_suite.add_hook(SimplugResult.ALL, required=True)
    def hook(arg):
        ...

    @test_suite.add_hook(SimplugResult.ALL)
    def hook1(arg):
        ...

    @test_suite.add_impl("plugin0")
    def hook1(arg):
        return 1

    with pytest.raises(HookRequired):
        test_suite.hook(1)


def test_spec_self(test_suite):
    @test_suite.add_hook(SimplugResult.ALL)
    def hook(self, arg):
        ...

    @test_suite.add_impl("plugin0")
    def hook(arg):
        return arg + 1

    assert test_suite.hook(1) == [2]


def test_impl_self(test_suite):
    @test_suite.add_hook(SimplugResult.ALL)
    def hook(arg):
        ...

    @test_suite.add_impl("plugin0")
    def hook(self, arg):
        return arg + 1

    assert test_suite.hook(1) == [2]


def test_impl_signature_differs(test_suite):
    @test_suite.add_hook(SimplugResult.ALL)
    def hook(arg):
        ...

    @test_suite.add_impl("plugin0")
    def hook(arg, arg2):
        return arg + 1

    with pytest.raises(HookSignatureDifferentFromSpec):
        test_suite.hook(1)


def test_no_such_hook(test_suite):
    with pytest.raises(NoSuchHookSpec):
        test_suite.nosuchook()


def test_no_such_plugin(test_suite):
    with pytest.raises(NoSuchPlugin):
        test_suite.disable_plugin("nosuchplugin")


def test_get_all_plugins(test_suite):
    @test_suite.add_hook(SimplugResult.ALL)
    def hook(arg):
        ...

    @test_suite.add_impl("plugin0")
    def hook(arg):
        return 1

    assert test_suite.hook(1) == [1]
    assert isinstance(
        test_suite.get_all_plugins(raw=False)["plugin0"],
        SimplugWrapper,
    )
    assert not isinstance(
        test_suite.get_all_plugins(raw=True)["plugin0"],
        SimplugWrapper,
    )
    assert isinstance(
        test_suite.get_enabled_plugins(raw=False)["plugin0"],
        SimplugWrapper,
    )
    assert not isinstance(
        test_suite.get_enabled_plugins(raw=True)["plugin0"],
        SimplugWrapper,
    )


def test_hook_exists(test_suite):
    @test_suite.add_hook(SimplugResult.ALL)
    def hook(arg):
        ...

    with pytest.raises(HookSpecExists):
        @test_suite.add_hook(SimplugResult.ALL)
        def hook(arg):
            ...


def test_no_hook_spec_while_impl(test_suite):
    with pytest.raises(NoSuchHookSpec):
        @test_suite.add_impl("plugin0")
        def hook(arg):
            return 1


def test_entrypoint_plugin(tmp_path):

    simplug = Simplug("simplug_entrypoint_test")

    class Hooks:
        @simplug.spec()
        def hook(arg):
            ...

    class Impl:
        @simplug.impl
        def hook(arg):
            return arg

    simplug.register(Impl)
    assert simplug.get_all_plugin_names() == ["impl"]
    assert simplug.hooks.hook(1) == [1]

    plugin_dir = Path(__file__).parent / "entrypoint_plugin"
    install_dir = tmp_path / "simplug_test_lib"
    install_dir.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(plugin_dir))

    os.system(
        f"{sys.executable} {plugin_dir}/setup.py "
        f"install --install-lib {install_dir} 1>/dev/null 2>/dev/null"
    )
    simplug.load_entrypoints(only="None")  # Nothing loaded
    assert simplug.hooks.hook(1) == [1]

    simplug.load_entrypoints()
    assert simplug.hooks.hook(1) == [1, 2]


def test_context_only():

    simplug = Simplug("context_positive_only")

    class Specs:
        @simplug.spec
        def hook(arg):
            ...

    class Plugin:
        def __init__(self, name):
            self.name = name

        @simplug.impl
        def hook(arg):
            return arg

    with simplug.plugins_context([Plugin]):
        assert simplug.hooks.hook(1) == [1]

    assert simplug.hooks.hook(1) == []

    # enabled: plugin0, plugin1, plugin2, plugin3, plugin4
    simplug.register(*(Plugin(f"plugin{i}") for i in range(5)))
    simplug.get_plugin("plugin4").disable()
    assert simplug.hooks.hook(1) == [1] * 4

    with pytest.raises(SimplugException):
        with simplug.plugins_context(["pluginxxx"]):
            ...

    context = simplug.plugins_context(
        ["plugin0", "plugin1", "plugin2"]
    )
    #     [
    #         "plugin0",
    #         simplug.get_plugin("plugin1"),
    #         simplug.get_plugin("plugin2", True),
    #         # Plugin("plugin5"),
    #     ]
    # )

    context.__enter__()
    assert simplug.hooks.hook(1) == [1] * 3
    assert simplug.get_enabled_plugin_names() == [
        "plugin0",
        "plugin1",
        "plugin2",
    ]
    context.__exit__()

    assert simplug.hooks.hook(1) == [1] * 4
    assert simplug.get_enabled_plugin_names() == [
        f"plugin{i}" for i in range(4)
    ]

    with simplug.plugins_context(None):
        assert simplug.hooks.hook(1) == [1] * 4

    with simplug.plugins_context(None):
        assert simplug.hooks.hook(1) == [1] * 4


def test_context_non_only():

    simplug = Simplug("context_non_only")

    class Specs:
        @simplug.spec
        def hook(arg):
            ...

    class Plugin:
        def __init__(self, name):
            self.name = name

        @simplug.impl
        def hook(arg):
            return arg

    # enabled: plugin0, plugin1, plugin2, plugin3, plugin4
    simplug.register(*(Plugin(f"plugin{i}") for i in range(5)))
    simplug.get_plugin("plugin4").disable()
    assert simplug.hooks.hook(1) == [1] * 4

    with pytest.raises(SimplugException):
        with simplug.plugins_context(["plugin1", "-plugin2"]):
            ...

    # with pytest.raises(SimplugException):
    # Allow plugins to not exist with "-"
    with simplug.plugins_context(["-pluginxxx"]):
        ...

    with simplug.plugins_context(
        [
            "-plugin0",
            "-plugin1",
            simplug.get_plugin("plugin3", raw=True),
            simplug.get_plugin("plugin4"),
            Plugin("plugin5"),
        ]
    ):
        assert simplug.get_enabled_plugin_names() == [
            "plugin2", "plugin3", "plugin4", "plugin5"
        ]
        assert simplug.hooks.hook(1) == [1] * 4

    assert simplug.hooks.hook(1) == [1] * 4
    assert simplug.get_enabled_plugin_names() == [
        f"plugin{i}" for i in range(4)
    ]


def test_result_errors():
    simplug = Simplug("test_errors")

    class Specs:
        @simplug.spec
        def hook(arg):
            ...

        @simplug.spec
        async def ahook(arg):
            ...

    class Plugin1:
        @simplug.impl
        def hook(arg):
            return 1

        @simplug.impl
        async def ahook(arg):
            return 1 / 0

    class Plugin2:
        name = "SomePlugin"

        @simplug.impl
        def hook(arg):
            return 1 / 0

        @simplug.impl
        def ahook(arg):
            return 1

    with pytest.warns(SyncImplOnAsyncSpecWarning):
        simplug.register(Plugin1, Plugin2)

    with pytest.raises(ResultError, match=r"plugin=SomePlugin; spec=hook"):
        simplug.hooks.hook(1)

    with pytest.raises(ResultError, match=r"plugin=plugin1; spec=\[async\]ahook"):
        asyncio.run(simplug.hooks.ahook(1))


def test_async_impl_on_sync_spec():
    simplug = Simplug("test_async_impl_on_sync_spec")

    class Specs:
        @simplug.spec
        def hook(arg):
            ...

    class Plugin:
        @simplug.impl
        async def hook(arg):
            return arg + 1

    with pytest.raises(AsyncImplOnSyncSpecError):
        simplug.register(Plugin)
