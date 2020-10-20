
simplug
=======

A simple entrypoint-free plugin system for python

Installation
------------

.. code-block::

   pip install -U simplug

Features
--------


* Entrypoint-free, meaning you can configure the plugins to be loaded in your host
* Loading priority definition while implementing a plugin
* Required hooks (hooks required to be implemented in plugins)
* Different ways to fetch results from hooks

Examples
--------

A toy example
^^^^^^^^^^^^^

.. code-block:: python

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

.. code-block::

   inside Plugin_1.myhook()
   inside Plugin_2.myhook()
   [3, -1]

Note that the hooks are executed in the order the plugins are registered. This is different from ``pluggy``.

A complete example
^^^^^^^^^^^^^^^^^^

See ``examples/complete/``.

Running ``python -m examples/complete/`` gets us:

.. code-block::

   Your food. Enjoy some egg, egg, egg, salt, pepper, egg, egg, lovely spam, wonderous spam
   Some condiments? We have pickled walnuts, mushy peas, mint sauce, spam sauce
   Now this is what I call a condiments tray!

Usage
-----

Definition of hooks
^^^^^^^^^^^^^^^^^^^

Hooks are specified and implemented by decorating the functions with ``simplug.spec`` and ``simplug.impl`` respectively.

``simplug`` is initialized by:

.. code-block:: python

   simplug = Simplug('project')

The ``'project'`` is a unique name to mark the project, which makes sure ``Simplug('project')`` get the same instance each time.

Note that if ``simplug`` is initialized without ``project``\ , then a name is generated automatically as such ``project-0``\ , ``project-1``\ , etc.

Hook specification is marked by ``simplug.spec``\ :

.. code-block:: python

   simplug = Simplug('project')

   @simplug.spec
   def setup(args):
       ...

``simplug.spec`` can take two keyword-arguments:


* ``required``\ : Whether this hook is required to be implemented in plugins
* ``result``\ : An enumerator to specify the way to collec the results.

  * SimplugResult.ALL: Get all the results from the hook, as a list
      including ``NONE``\ s
  * SimplugResult.ALL_BUT_NONE: Get all the results from the hook,
      as a list, not including ``NONE``\ s
  * SimplugResult.FIRST: Get the none-\ ``None`` result from the
      first plugin only (ordered by priority)
  * SimplugResult.LAST: Get the none-\ ``None`` result from
      the last plugin only

Hook implementation is marked by ``simplug.impl``\ , which takes no additional arguments.

The name of the function has to match the name of the function by ``simplug.spec``. And the signatures of the specification function and the implementation function have to be the same in terms of names. This means you can specify default values in the specification function, but you don't have to write the default values in the implementation function.

Note that default values in implementation functions will be ignored.

Also note if a hook specification is under a namespace, it can take ``self`` as argument. However, this argument will be ignored while the hook is being called (\ ``self`` will be ``None``\ , and you still have to specify it in the function definition).

The plugin registry
^^^^^^^^^^^^^^^^^^^

The plugins are registered by ``simplug.register(*plugins)``. Each plugin of ``plugins`` can be either a python object or a str denoting a module that can be imported by ``importlib.import_module``.

The python object must have an attribute ``name``\ , ``__name__`` or ``__class.__name__`` for ``simplug`` to determine the name of the plugin. If the plugin name is determined from ``__name__`` or ``__class__.__name__``\ , it will be lowercased.

You can enable or disable a plugin temporarily after registration by:

.. code-block:: python

   simplug.disable('plugin_name')
   simplug.enable('plugin_name')

You can use following methods to inspect the plugin registry:


* ``simplug.get_plugin``\ : Get the plugin by name
* ``simplug.get_all_plugins``\ : Get a dictionary of name-plugin mappings of all plugins
* ``simplug.get_all_plugin_names``\ : Get the names of all plugins, in the order it will be executed.

Calling hooks
^^^^^^^^^^^^^

Hooks are call by ``simplug.hooks.<hook_name>(<arguments>)`` and results are collected based on the ``result`` argument passed in ``simplug.spec`` when defining hooks.

API
---

https://pwwang.github.io/simplug/
