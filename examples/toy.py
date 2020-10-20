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