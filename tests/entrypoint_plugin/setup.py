from setuptools import setup

setup(
    name="entrypoint_plugin",
    entry_points={"simplug_entrypoint_test": ["ep_plugin = entrypoint_plugin"]},
    py_modules=["entrypoint_plugin"],
)
