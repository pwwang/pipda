# pipda

[![PyPI][pypi-badge]][pypi] [![GitHub][github-badge]][github] [![Codacy grade][codacy-grade-badge]][codacy] [![Codacy coverage][codacy-coverage-badge]][codacy] ![Docs][docs-badge] ![CI][ci-badge]

A framework for data piping in Python.

Inspired by [siuba][1], [dfply][2], [plydata][3], and [dplython][4]. Provides simple yet powerful APIs to mimic `dplyr` and `tidyr` in Python.

[API][api] | [Changelog][changelog] | [Documentation][docs]

## Installation

```shell
pip install -U pipda
```

## Usage

### Verbs

- A verb is pipeable (able to be called like `data >> verb(...)`)
- A verb is dispatchable by the type of its first argument
- A verb evaluates other arguments using the first one
- A verb is passing down the context if not specified in the arguments

```python
import pandas as pd
from pipda import (
    register_verb,
    register_func,
    register_operator,
    evaluate_expr,
    Operator,
    Symbolic,
    Context
)

f = Symbolic()

df = pd.DataFrame({
    'x': [0, 1, 2, 3],
    'y': ['zero', 'one', 'two', 'three']
})

df

#      x    y
# 0    0    zero
# 1    1    one
# 2    2    two
# 3    3    three

@register_verb(pd.DataFrame)
def head(data, n=5):
    return data.head(n)

df >> head(2)
#      x    y
# 0    0    zero
# 1    1    one

@register_verb(pd.DataFrame, context=Context.EVAL)
def mutate(data, **kwargs):
    data = data.copy()
    for key, val in kwargs.items():
        data[key] = val
    return data

df >> mutate(z=1)
#    x      y  z
# 0  0   zero  1
# 1  1    one  1
# 2  2    two  1
# 3  3  three  1

df >> mutate(z=f.x)
#    x      y  z
# 0  0   zero  0
# 1  1    one  1
# 2  2    two  2
# 3  3  three  3
```

### Functions used as verb arguments

```python
# verb can be used as an argument passed to another verb
# dependent=True makes the `data` argument invisible while calling
@register_verb(pd.DataFrame, context=Context.EVAL, dependent=True)
def if_else(data, cond, true, false):
    cond.loc[cond.isin([True]), ] = true
    cond.loc[cond.isin([False]), ] = false
    return cond

# The function is then also a singledispatch generic function

df >> mutate(z=if_else(f.x>1, 20, 10))
#    x      y   z
# 0  0   zero  10
# 1  1    one  10
# 2  2    two  20
# 3  3  three  20
```

```python
# function without data argument
@register_func
def length(strings):
    return [len(s) for s in strings]

df >> mutate(z=length(f.y))

#    x     y    z
# 0  0  zero    4
# 1  1   one    3
# 2  2   two    3
# 3  3 three    5
```

### Context

The context defines how a reference (`f.A`, `f['A']`, `f.A.B`) is evaluated

```python
@register_verb(pd.DataFrame, context=Context.SELECT)
def select(df, *columns):
    return df[list(columns)]

df >> select(f.x, f.y)
#    x     y
# 0  0  zero
# 1  1   one
# 2  2   two
# 3  3 three
```

## How it works

```R
data %>% verb(arg1, ..., key1=kwarg1, ...)
```

The above is a typical `dplyr`/`tidyr` data piping syntax.

The Python counterpart is:

```python
data >> verb(arg1, ..., key1=kwarg1, ...)
```

To implement this, execution of the `verb` must be deferred by turning it into a `VerbCall` object that holds the function and its arguments. The `VerbCall` is not evaluated until data is piped in via `>>`. This detection is made possible by the [`executing`][5] package, which inspects the AST to determine whether a function call appears on the right-hand side of a pipe operator.

Arguments that reference columns of the data must also be deferred. For example, in `dplyr` (R):

```R
data %>% mutate(z = a)
```

This adds a column `z` with values from column `a`. In Python, the equivalent is:

```python
data >> mutate(z=f.a)
```

Here `f.a` is a `Reference` object that captures the column name without immediately fetching the data.

The `Symbolic` object `f` acts as a proxy, chaining attribute/item accesses and operator expressions into a single `Expression` tree. That tree is later evaluated when data and context become available.

## Documentation

[https://pwwang.github.io/pipda/][docs]

See [datar][6] for real-world usage.

[1]: https://github.com/machow/siuba
[2]: https://github.com/kieferk/dfply
[3]: https://github.com/has2k1/plydata
[4]: https://github.com/dodger487/dplython
[5]: https://github.com/alexmojaki/executing
[6]: https://github.com/pwwang/datar
[pypi-badge]: https://img.shields.io/pypi/v/pipda?style=flat-square
[pypi]: https://pypi.org/project/pipda/
[github-badge]: https://img.shields.io/github/v/tag/pwwang/pipda?style=flat-square
[github]: https://github.com/pwwang/pipda
[ci-badge]: https://img.shields.io/github/actions/workflow/status/pwwang/pipda/build.yml?label=CI&style=flat-square
[pyver-badge]: https://img.shields.io/pypi/pyversions/pipda?style=flat-square
[docs-badge]: https://img.shields.io/github/actions/workflow/status/pwwang/pipda/docs.yml?label=docs&style=flat-square
[codacy]: https://app.codacy.com/gh/pwwang/pipda/dashboard
[codacy-coverage-badge]: https://img.shields.io/codacy/coverage/75d312da24c94bdda5923627fc311a99?style=flat-square
[codacy-grade-badge]: https://img.shields.io/codacy/grade/75d312da24c94bdda5923627fc311a99?style=flat-square
[api]: https://pwwang.github.io/pipda/api/pipda/
[changelog]: https://pwwang.github.io/pipda/CHANGELOG/
[docs]: https://pwwang.github.io/pipda/
