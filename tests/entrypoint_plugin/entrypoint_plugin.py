from simplug import Simplug

simplug = Simplug('simplug_entrypoint_test')

@simplug.impl
def hook(arg):
    return arg * 2
