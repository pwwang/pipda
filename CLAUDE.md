# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Tests
pytest tests/                         # Run all tests
pytest tests/test_verb.py -k <name>   # Run a single test

# Linting & type checking
flake8 pipda                          # Lint
mypy -p pipda                         # Type check

# Pre-commit (runs flake8, mypy, version check, pytest)
pre-commit run --all-files

# Build (uses hatchling + uv)
uv build
```

## Architecture

`pipda` implements dplyr-style data piping in Python: `data >> verb(...)`. The core problem is **deferred evaluation** — when a verb like `mutate(z=f.x)` is called, `f.x` must not be evaluated immediately because the data hasn't arrived yet.

### Expression tree (deferred evaluation)

Everything deferred is an `Expression` (ABC) with a `_pipda_eval(data, context)` method:

| Class | Created by | Purpose |
|---|---|---|
| `Symbolic` | `f = Symbolic()` | Singleton proxy; evaluating it just returns `data` |
| `ReferenceAttr` | `f.col` | Attribute reference; resolves to `data.col` or `'col'` depending on context |
| `ReferenceItem` | `f['col']` | Item reference; same context-dependent resolution |
| `VerbCall` | `verb(...)` in piping mode | Holds a verb + its args, awaiting data via `>>` |
| `FunctionCall` | `registered_func(...)` with `Expression` args | Deferred function call |
| `OperatorCall` | `f.x + 1` | Deferred operator expression |

### Context: how references resolve

`Context` (enum) controls how `f.col` / `f['col']` are evaluated:

- **EVAL**: `f.A` → `data.A`, `f['A']` → `data['A']`
- **SELECT**: `f.A` → `'A'`, `f['A']` → `'A'` (returns the name as a string)
- **PENDING**: Don't evaluate; leaves arguments for the function to handle itself

Each context is a `ContextBase` subclass implementing `getattr`, `getitem`, and `ref` methods.

### Verb system (`register_verb`)

A verb is a function whose **first argument is the data**. Key mechanisms:

1. **AST detection**: Uses the `executing` package to inspect the call site AST. If called as `data >> verb(...)`, wraps into a `VerbCall` instead of executing immediately. The `is_piping()` utility in `utils.py` does this check.

2. **Dispatch**: Uses `singledispatch` per backend. Multiple backends can register implementations for the same type. The `__backend` keyword argument selects a specific backend.

3. **Dependent verbs**: `dependent=True` makes the first argument invisible to callers — `verb(args)` always returns a `VerbCall`, enabling use as an argument to another verb.

4. **When `_pipda_eval` fires**: The `VerbCall._pipda_eval(data, context)` dispatches the correct implementation via `cls.__class__`, then evaluates all arguments (using `evaluate_expr`) according to the verb's registered context.

### Function system (`register_func`)

Functions don't have data as first argument. Modes:
- **plain**: No evaluation of arguments; direct call only.
- **Default**: Arguments containing `Expression` objects are wrapped in a `FunctionCall` for deferred evaluation. Otherwise called directly.
- **dispatchable**: Like verb dispatch but on any/all argument types.
- **pipeable**: Can receive data via `>>` like a verb.

### Operator system (`register_operator`)

The `Operator` class (defaults to Python's `operator` module) defines how operators work on expressions. Register a subclass to customize. All standard operators (`+`, `-`, `*`, `==`, `&`, etc.) are mapped in `expression.py:OPERATORS` and routed through `OperatorCall`.

### Piping (`register_piping`)

`>>` is the default piping operator (configurable to `|`, `//`, `@`, `%`, `&`, `^`). At import time, `_patch_default_classes()` monkey-patches known types (pandas DataFrame/Series/Index, modin, torch.Tensor, Django QuerySet) so their operator methods yield to `PipeableCall`'s reverse operator.

### Key utility: `evaluate_expr()`

Recursively walks an expression tree, calling `_pipda_eval()` on each `Expression` node and descending into `tuple`, `list`, `set`, `slice`, and `dict` containers. This is the bridge from the deferred expression world to concrete values.

### File map

| File | Contains |
|---|---|
| `pipda/__init__.py` | Public API, calls `register_piping(">>")` + `_patch_default_classes()` |
| `pipda/expression.py` | `Expression` ABC, operator dunder methods, numpy `__array_ufunc__`/`__array_function__` support |
| `pipda/symbolic.py` | `Symbolic` singleton |
| `pipda/reference.py` | `ReferenceAttr`, `ReferenceItem` |
| `pipda/context.py` | `Context` enum, `ContextSelect`, `ContextEval`, `ContextPending` |
| `pipda/verb.py` | `VerbCall`, `register_verb` |
| `pipda/function.py` | `FunctionCall`, `register_func` |
| `pipda/operator.py` | `OperatorCall`, `Operator`, `register_operator` |
| `pipda/piping.py` | `PipeableCall`, `register_piping`, class patching |
| `pipda/utils.py` | `evaluate_expr`, `is_piping`, `has_expr`, `TypeHolder`, constants |
