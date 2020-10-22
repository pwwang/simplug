import os, sys
from pathlib import Path
import pytest
from simplug import *

def test_simplug(capsys):

    simplug = Simplug('project')

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

        @simplug.spec(result=SimplugResult.ALL)
        def all_result(self, d=1):
            pass

        @simplug.spec(result=SimplugResult.ALL_BUT_NONE)
        def on_end(self, e=1):
            pass

    class System:

        def __init__(self):
            simplug.hooks.on_init('arg')

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

    class Plugin1:

        def __init__(self, name):
            self.__name__ = name

        @simplug.impl
        def on_init(self, arg):
            print('Arg:', arg)


    class Plugin2:

        @simplug.impl
        def on_init(self, arg):
            print('Arg:', arg)

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

    class Plugin5:
        ...

    class Plugin6:

        @simplug.impl
        def on_init(self, diff_arg):
            pass

    with pytest.raises(HookSpecExists):
        @simplug.spec
        def on_init(): pass

    with pytest.raises(NoSuchHookSpec):
        @simplug.impl
        def no_such_hook(): pass



    with pytest.raises(NoSuchPlugin):
        simplug.register('nosuch')
    with pytest.raises(HookRequired):
        simplug.register(Plugin5)
    with pytest.raises(HookSignatureDifferentFromSpec):
        simplug.register(Plugin6)

    plug1 = Plugin1('plugin-1')
    plug2 = Plugin2()
    simplug.register(plug1, Plugin1, plug2, Plugin3, Plugin4)
    with pytest.raises(PluginRegistered):
        simplug.register(Plugin3())

    s = System()
    s.first() == 40
    s.last() == 300
    s.all() == [None] * 5
    s.end() is None
    assert 'Arg: arg\n' * 3 == capsys.readouterr().out

    with pytest.raises(NoSuchHookSpec):
        s.no_such_hooks()

    simplug.disable('plugin2')
    System()
    assert 'Arg: arg\n' * 2 == capsys.readouterr().out

    simplug.enable('plugin2')
    System()
    assert 'Arg: arg\n' * 3 == capsys.readouterr().out

    with pytest.raises(NoSuchPlugin):
        simplug.get_plugin('nosuchplugin')

    assert simplug.get_all_plugin_names() == ['plugin4', 'plugin-1', 'plugin1',
                                              'plugin2', 'plugin3']

    all_plugins = simplug.get_all_plugins()
    assert isinstance(all_plugins, OrderedDiot)
    assert list(all_plugins.keys()) == ['plugin4', 'plugin-1', 'plugin1',
                                        'plugin2', 'plugin3']
    assert simplug.get_all_plugins(raw=True) == {
        'plugin-1': plug1,
        'plugin1': Plugin1,
        'plugin2': plug2,
        'plugin3': Plugin3,
        'plugin4': Plugin4
    }

def test_simplug_module(capsys):
    simplug = Simplug('simplug_module')

    class PluginSpec:
        @simplug.spec
        def on_init(self, arg):
            pass

    class System:

        def __init__(self):
            simplug.hooks.on_init('arg')

    simplug.register(f"{'.'.join(__name__.split('.')[:-1])}.plugin_module")
    System()

    assert 'Arg: arg\n' == capsys.readouterr().out

def test_async_hook():
    import asyncio
    simplug = Simplug('async_hook')

    class HookSpec:

        @simplug.spec
        async def ahook(self, arg):
            pass

        @simplug.spec
        async def ahook2(self, arg):
            pass

    class Plugin1:

        @simplug.impl
        async def ahook(self, arg):
            await asyncio.sleep(.01)
            return arg

    class Plugin2:

        @simplug.impl
        def ahook(self, arg):
            return arg

    class Plugin3(Plugin1):
        ...

    simplug.register(Plugin1, Plugin3)

    with pytest.warns(SyncImplOnAsyncSpecWarning):
        simplug.register(Plugin2)

    simplug.disable('plugin3')

    async def main():
        await simplug.hooks.ahook2(1)
        return await simplug.hooks.ahook(1)

    assert asyncio.run(main()) == [1, 1]

def test_entrypoint_plugin(tmp_path):

    simplug = Simplug('simplug_entrypoint_test')

    class Hooks:

        @simplug.spec
        def hook(arg):
            ...

    class Impl:

        @simplug.impl
        def hook(arg):
            return arg

    simplug.register(Impl)
    assert simplug.get_all_plugin_names() == ['impl']
    assert simplug.hooks.hook(1) == [1]

    plugin_dir = Path(__file__).parent / 'entrypoint_plugin'
    install_dir = tmp_path / 'simplug_test_lib'
    install_dir.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(plugin_dir))

    os.system(
        f'{sys.executable} {plugin_dir}/setup.py '
        f'install --install-lib {install_dir} 1>/dev/null 2>/dev/null'
    )
    simplug.load_entrypoints()
    assert simplug.hooks.hook(1) == [1, 2]


