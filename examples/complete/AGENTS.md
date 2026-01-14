# EXAMPLES/COMPLETE KNOWLEDGE BASE

**Generated:** 2026-01-14

## OVERVIEW
Full demonstration of simplug plugin system with hook specs, direct plugins, and setuptools entrypoint loading.

## STRUCTURE
```
examples/complete/
├── __main__.py         # Entry point: python -m examples.complete
├── host.py             # Main application (main(), get_ingredients(), get_condiments())
├── hookspecs.py        # Hook specifications (get_food, add_ingredient, add_condiment)
├── lib.py              # Built-in plugin (priority=-99)
└── plugin/             # External plugin package
    ├── setup.py        # Setuptools configuration
    └── plugin.py       # Plugin implementation
```

## WHERE TO LOOK
| Task | Location | Notes |
|------|----------|-------|
| Hook specs | hookspecs.py | @simplug.spec decorators |
| Main app | host.py | Simplug('complete'), simplug.register() |
| Built-in plugin | lib.py | Default implementations |
| External plugin | plugin/plugin.py | Demonstrates entrypoints |
| Entrypoint config | plugin/setup.py | entry_points['complete_example'] |

## CONVENTIONS
- **Hook specs**: Define in separate file (hookspecs.py) using `@simplug.spec`
- **Priority**: lib.py has `priority = -99` to execute first
- **Parameter immutability**: Docstrings warn "don't touch them!" (ingredients list)

## COMMANDS
```bash
# Run without external plugin
python -m examples.complete

# Install and run with external plugin
pip install -e examples/complete/plugin
python -m examples.complete
```

## NOTES
- Demonstrates both direct registration (`simplug.register(Lib)`) and entrypoint loading (`simplug.load_entrypoints()`)
- Shows result collection with `SimplugResult.FIRST` and `SimplugResult.ALL`
