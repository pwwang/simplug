from setuptools import setup

setup(
    name="simplug-complete-example-plugin",
    entry_points={"complete_example": ["complete-example-plugin = plugin"]},
    py_modules=["plugin"],
)
