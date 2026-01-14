# PROJECT KNOWLEDGE BASE

**Generated:** 2026-01-14
**Commit:** N/A
**Branch:** main

## OVERVIEW
Simple plugin system for Python with async hooks. Single-file architecture (~1,300 lines) with comprehensive test coverage. Uses decorator-based API with 18 result collection strategies.

## STRUCTURE
```
simplug/
├── simplug.py          # Single-file module (entire library)
├── tests/              # Test suite
│   └── test_simplug.py # 2,072 lines, 68 tests
├── examples/           # Usage examples
│   ├── toy.py          # Minimal 30-line demo
│   └── complete/       # Full example with entrypoints
├── docs/               # Documentation (mkdocs)
└── pyproject.toml      # Poetry configuration
```

## WHERE TO LOOK
| Task | Location | Notes |
|------|----------|-------|
| Main API | simplug.py lines 1002-1293 | Simplug class - plugin manager |
| Hook execution | simplug.py lines 379-802 | SimplugHook/SimplugHookAsync |
| Result collection | simplug.py lines 141-182 | SimplugResult enum (18 strategies) |
| Plugin registry | simplug.py lines 804-930 | SimplugHooks class |
| Decorators | simplug.py lines 19-69 | SimplugImpl wrapper |
| Tests | tests/test_simplug.py | Comprehensive coverage of all features |
| Entrypoints | examples/complete/plugin/ | Setuptools entrypoint demo |

## CONVENTIONS
- **Decorator-based API**: `@simplug.spec` defines hooks, `@simplug.impl` implements them
- **Single-file architecture**: All library code in simplug.py (intentional, not legacy)
- **Priority system**: Plugins sorted by `(priority_attr, batch_index)`, negative = higher priority
- **Async/sync bridge**: `makecall()` handles both, warnings for sync impl on async spec
- **OrderedDiot**: Uses diot package for plugin registry (preserves insertion order)
- **Signature validation**: Spec and impl parameter names must match (excluding defaults)

## ANTI-PATTERNS (THIS PROJECT)
- **Modifying spec parameters**: Examples explicitly warn "don't touch them!" (ingredients)
- **Version mismatch**: Pre-commit hook enforces version sync between pyproject.toml and simplug.py

## UNIQUE STYLES
- **Singleton per project**: `Simplug('project_name')` returns same instance each time
- **Plugin name resolution**: Priority: `_name` → `name` → `__name__.lower()` → `__class__.__name__.lower()`
- **Auto-instantiation**: Classes auto-instantiated if no required constructor params
- **Bit-flag result types**: SimplugResult uses `0b TRY ALL AVAIL ID` pattern

## COMMANDS
```bash
# Install
poetry install

# Test
poetry run pytest tests/

# Run examples
poetry run python examples/toy.py
poetry run python -m examples.complete

# Lint
flake8 simplug.py
mypy simplug.py
```

## NOTES
- **No src/ directory**: Poetry single-file layout with `generate-setup-file = true`
- **Minimal dependencies**: Only external dependency is `diot >= 0.3`
- **Python 3.9+**: Supports 3.9, 3.10, 3.11, 3.12
- **Entrypoint testing**: Tests and examples include setup.py files for setuptools entrypoints
- **CI**: GitHub Actions with matrix testing, pre-commit hooks for quality
