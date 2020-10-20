from simplug import Simplug

simplug = Simplug('simplug_module')

name = 'module_plugin'

@simplug.impl
def on_init(self, arg):
    print('Arg:', arg)

