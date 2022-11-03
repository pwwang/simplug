import os
import sys
from pathlib import Path

import pytest
from diot import OrderedDiot
from simplug import (
    Simplug,
    SimplugResult,
    HookSpecExists,
    NoSuchHookSpec,
    NoSuchPlugin,
    HookSignatureDifferentFromSpec,
    HookRequired,
    PluginRegistered,
    SyncImplOnAsyncSpecWarning,
)


def test_simplug(capsys):

    simplug = Simplug("project")

    class PluginSpec:
        @simplug.spec
        def pre_init(self, a=1):
            pass

        @simplug.spec(required=True)
        def on_init(self, arg):
            pass

        @simplug.spec(result=SimplugResult.FIRST)
        def first_result(self, b=1):
            pass

        @simplug.spec(result=SimplugResult.LAST)
        def last_result(self, c=1):
            pass

        @simplug.spec(
            result=SimplugResult.ALL,
            collect=lambda x: "".join(str(i) for i in x),
        )
        def all_result(self, d=1):
            pass

        @simplug.spec(result=SimplugResult.ALL_BUT_NONE)
        def on_end(self, e=1):
            pass

        @simplug.spec(result=SimplugResult.ALL_FIRST)
        def all_first_result(self, f=1):
            pass

        @simplug.spec(result=SimplugResult.ALL_LAST)
        def all_last_result(self, g=1):
            pass

    class System:
        def __init__(self):
            simplug.hooks.on_init("arg")

        def first(self):
            return simplug.hooks.first_result(1)

        def last(self):
            return simplug.hooks.last_result(1)

        def all(self):
            return simplug.hooks.all_result(1)

        def end(self):
            return simplug.hooks.on_end(1)

        def no_such_hooks(self):
            return simplug.hooks._no_such_hook()

        def all_first(self):
            return simplug.hooks.all_first_result(1)

        def all_last(self):
            return simplug.hooks.all_last_result(1)

    class Plugin1:
        __version__ = "0.0.1"

        def __init__(self, name):
            self.__name__ = name

        @simplug.impl
        def on_init(self, arg):
            print("Arg:", arg)

    class Plugin2:
        @simplug.impl
        def on_init(self, arg):
            print("Arg:", arg)

    class Plugin3:
        @simplug.impl
        def on_init(self, arg):
            pass

        @simplug.impl
        def first_result(self, b):
            return 30

        @simplug.impl
        def last_result(self, c):
            return 300

        @simplug.impl
        def all_result(self, d):
            return 5000

        @simplug.impl
        def on_end(self, e):
            return None

        @simplug.impl
        def all_first_result(self, f):
            return 100

        @simplug.impl
        def all_last_result(self, g):
            print("Plugin3: all_last_result")
            return 1000

    class Plugin4:

        priority = -1

        @simplug.impl
        def on_init(self, arg):
            pass

        @simplug.impl
        def first_result(self, b):
            return 40

        @simplug.impl
        def last_result(self, c):
            return 400

        @simplug.impl
        def all_result(self, d):
            return None

        @simplug.impl
        def on_end(self, e):
            return None

        @simplug.impl
        def all_first_result(self, f):
            print("Plugin4: all_first_result")
            return 200

        @simplug.impl
        def all_last_result(self, g):
            return 2000

    class Plugin5:
        ...

    class Plugin6:
        @simplug.impl
        def on_init(self, diff_arg):
            pass

    with pytest.raises(HookSpecExists):

        @simplug.spec
        def on_init():
            pass

    with pytest.raises(NoSuchHookSpec):

        @simplug.impl
        def no_such_hook():
            pass

    with pytest.raises(NoSuchPlugin):
        simplug.register("nosuch")
    with pytest.raises(HookRequired):
        simplug.register(Plugin5)
    with pytest.raises(HookSignatureDifferentFromSpec):
        simplug.register(Plugin6)

    plug1 = Plugin1("plugin-1")
    plug2 = Plugin2()
    simplug.register(plug1, Plugin1, plug2, Plugin3, Plugin4)

    plg1 = simplug.get_plugin("plugin-1")
    assert plg1.version == "0.0.1"

    with pytest.raises(PluginRegistered):
        simplug.register(Plugin3())

    s = System()
    s.first() == 40
    s.last() == 300
    s.all() == "None" * 5
    s.end() is None
    assert "Arg: arg\n" * 3 == capsys.readouterr().out

    s.all_first() == 100
    assert "Plugin4: all_first_result\n" == capsys.readouterr().out

    s.all_last() == 2000
    assert "Plugin3: all_last_result\n" == capsys.readouterr().out

    with pytest.raises(NoSuchHookSpec):
        s.no_such_hooks()

    simplug.disable("plugin2")
    System()
    assert "Arg: arg\n" * 2 == capsys.readouterr().out

    simplug.enable("plugin2")
    System()
    assert "Arg: arg\n" * 3 == capsys.readouterr().out

    with pytest.raises(NoSuchPlugin):
        simplug.get_plugin("nosuchplugin")

    assert simplug.get_all_plugin_names() == [
        "plugin4",
        "plugin-1",
        "plugin1",
        "plugin2",
        "plugin3",
    ]

    all_plugins = simplug.get_all_plugins()
    assert isinstance(all_plugins, OrderedDiot)
    assert list(all_plugins.keys()) == [
        "plugin4",
        "plugin-1",
        "plugin1",
        "plugin2",
        "plugin3",
    ]
    simplug.disable("plugin-1")
    assert simplug.get_all_plugins(raw=True) == {
        "plugin-1": plug1,
        "plugin1": Plugin1,
        "plugin2": plug2,
        "plugin3": Plugin3,
        "plugin4": Plugin4,
    }
    assert simplug.get_enabled_plugins(raw=True) == {
        "plugin1": Plugin1,
        "plugin2": plug2,
        "plugin3": Plugin3,
        "plugin4": Plugin4,
    }
    assert simplug.get_enabled_plugin_names() == [
        "plugin4",
        "plugin1",
        "plugin2",
        "plugin3",
    ]


def test_simplug_module(capsys):
    simplug = Simplug("simplug_module")

    class PluginSpec:
        @simplug.spec
        def on_init(self, arg):
            pass

    class System:
        def __init__(self):
            simplug.hooks.on_init("arg")

    simplug.register(f"{'.'.join(__name__.split('.')[:-1])}.plugin_module")
    System()

    assert "Arg: arg\n" == capsys.readouterr().out


def test_async_hook(capsys):
    import asyncio

    simplug = Simplug("async_hook")

    class HookSpec:
        @simplug.spec
        async def ahook(self, arg):
            pass

        @simplug.spec
        async def ahook2(self, arg):
            pass

        @simplug.spec(result=SimplugResult.FIRST)
        async def ahook3(self, arg):
            pass

        @simplug.spec(result=SimplugResult.LAST)
        async def ahook4(self, arg):
            pass

        @simplug.spec(result=SimplugResult.ALL)
        async def ahook5(self, arg):
            pass

        @simplug.spec(result=SimplugResult.ALL_FIRST)
        async def ahook6(self, arg):
            pass

        @simplug.spec(result=SimplugResult.ALL_LAST)
        async def ahook7(self, arg):
            pass

    class Plugin1:

        incr = 1

        @simplug.impl
        async def ahook(self, arg):
            await asyncio.sleep(0.01)
            return self.incr + arg

        @simplug.impl
        async def ahook3(self, arg):
            await asyncio.sleep(0.01)
            return self.incr + arg

        @simplug.impl
        async def ahook4(self, arg):
            await asyncio.sleep(0.01)
            print("Plugin1 - ahook4")
            return self.incr + arg

        @simplug.impl
        async def ahook5(self, arg):
            await asyncio.sleep(0.01)
            return self.incr + arg

        @simplug.impl
        async def ahook6(self, arg):
            await asyncio.sleep(0.01)
            return self.incr + arg

        @simplug.impl
        async def ahook7(self, arg):
            await asyncio.sleep(0.01)
            print("Plugin1 - ahook7")
            return self.incr + arg

    class Plugin2:
        incr = 2

        @simplug.impl
        def ahook(self, arg):
            return self.incr + arg

        @simplug.impl
        async def ahook3(self, arg):
            await asyncio.sleep(0.01)
            print("Plugin2 - ahook3")
            return self.incr + arg

        @simplug.impl
        async def ahook4(self, arg):
            await asyncio.sleep(0.01)
            return self.incr + arg

        @simplug.impl
        async def ahook5(self, arg):
            await asyncio.sleep(0.01)
            return self.incr + arg

        @simplug.impl
        async def ahook6(self, arg):
            await asyncio.sleep(0.01)
            print("Plugin2 - ahook6")
            return self.incr + arg

        @simplug.impl
        async def ahook7(self, arg):
            await asyncio.sleep(0.01)
            return self.incr + arg

    class Plugin3(Plugin1):
        ...

    simplug.register(Plugin1, Plugin3)

    with pytest.warns(SyncImplOnAsyncSpecWarning):
        simplug.register(Plugin2)

    simplug.disable("plugin3")

    async def main():
        await simplug.hooks.ahook2(1)
        return await simplug.hooks.ahook(1)

    async def main3():
        return await simplug.hooks.ahook3(1)

    async def main4():
        return await simplug.hooks.ahook4(1)

    async def main5():
        return await simplug.hooks.ahook5(1)

    assert asyncio.run(main()) == [2, 3]
    assert asyncio.run(main3()) == 2
    assert asyncio.run(main4()) == 3
    assert asyncio.run(main5()) == [2, 3]
    assert capsys.readouterr().out == ""

    async def main6():
        return await simplug.hooks.ahook6(1)

    assert asyncio.run(main6()) == 2
    assert capsys.readouterr().out == "Plugin2 - ahook6\n"

    async def main7():
        return await simplug.hooks.ahook7(1)

    assert asyncio.run(main7()) == 3
    assert capsys.readouterr().out == "Plugin1 - ahook7\n"


def test_entrypoint_plugin(tmp_path):

    simplug = Simplug("simplug_entrypoint_test")

    class Hooks:
        @simplug.spec
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
    simplug.load_entrypoints(only="None")
    assert simplug.hooks.hook(1) == [1]

    simplug.load_entrypoints()
    assert simplug.hooks.hook(1) == [1, 2]


def test_context():

    simplug = Simplug("context_only")

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

    with simplug.plugins_only_context([Plugin]):
        assert simplug.hooks.hook(1) == [1]

    assert simplug.hooks.hook(1) == []

    simplug.register(*(Plugin(f"plugin{i}") for i in range(5)))
    assert simplug.hooks.hook(1) == [1] * 5

    context = simplug.plugins_only_context(
        [
            "plugin0",
            simplug.get_plugin("plugin1"),
            simplug.get_plugin("plugin2", True),
            Plugin("plugin5"),
        ]
    )

    context.__enter__()
    assert simplug.hooks.hook(1) == [1] * 4
    assert simplug.get_enabled_plugin_names() == [
        "plugin0",
        "plugin1",
        "plugin2",
        "plugin5",
    ]
    context.__exit__()

    assert simplug.hooks.hook(1) == [1] * 5
    assert simplug.get_enabled_plugin_names() == [
        f"plugin{i}" for i in range(5)
    ]

    with simplug.plugins_but_context(
        [
            "plugin0",
            simplug.get_plugin("plugin1"),
            simplug.get_plugin("plugin4", True),
            "plugin5",
        ]
    ):
        assert simplug.get_enabled_plugin_names() == ["plugin2", "plugin3"]
        assert simplug.hooks.hook(1) == [1] * 2

    assert simplug.hooks.hook(1) == [1] * 5
    assert simplug.get_enabled_plugin_names() == [
        f"plugin{i}" for i in range(5)
    ]

    with simplug.plugins_only_context(None):
        assert simplug.hooks.hook(1) == [1] * 5

    with simplug.plugins_but_context(None):
        assert simplug.hooks.hook(1) == [1] * 5
