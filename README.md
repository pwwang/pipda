# pipda

[![Pypi][7]][8] [![Github][9]][10] [![PythonVers][11]][8] [![Codacy][16]][14] [![Codacy coverage][15]][14] ![Docs building][13] ![Building][12]

A framework for data piping in python

Inspired by [siuba][1], [dfply][2], [plydata][3] and [dplython][4], but with simple yet powerful APIs to mimic the `dplyr` and `tidyr` packages in python

[API][17] | [Change Log][18] | [Documentation][19]

## Installation

```shell
pip install -U pipda
```

## Usage

### Verbs

Verbs are functions next to the piping sign (`>>`) receiving the data directly.

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
# dep=True make `data` argument invisible while calling
@register_verb(pd.DataFrame, context=Context.EVAL, dep=True)
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

The context defines how a reference (`f.A`, `f['A']`, `f.A.B` is evaluated)

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

The counterpart python syntax we expect is:

```python
data >> verb(arg1, ..., key1=kwarg1, ...)
```

To implement that, we need to defer the execution of the `verb` by turning it into a `Verb` object, which holds all information of the function to be executed later. The `Verb` object won't be executed until the `data` is piped in. It all thanks to the [`executing`][5] package to let us determine the ast nodes where the function is called. So that we are able to determine whether the function is called in a piping mode.

If an argument is referring to a column of the data and the column will be involved in the later computation, the it also needs to be deferred. For example, with `dplyr` in `R`:

```R
data %>% mutate(z=a)
```

is trying add a column named `z` with the data from column `a`.

In python, we want to do the same with:

```python
data >> mutate(z=f.a)
```

where `f.a` is a `Reference` object that carries the column information without fetching the data while python sees it immmediately.

Here the trick is `f`. Like other packages, we introduced the `Symbolic` object, which will connect the parts in the argument and make the whole argument an `Expression` object. This object is holding the execution information, which we could use later when the piping is detected.

## Documentation

[https://pwwang.github.io/pipda/][19]

See also [datar][6] for realcase usages.

[1]: https://github.com/machow/siuba
[2]: https://github.com/kieferk/dfply
[3]: https://github.com/has2k1/plydata
[4]: https://github.com/dodger487/dplython
[5]: https://github.com/alexmojaki/executing
[6]: https://github.com/pwwang/datar
[7]: https://img.shields.io/pypi/v/pipda?style=flat-square
[8]: https://pypi.org/project/pipda/
[9]: https://img.shields.io/github/v/tag/pwwang/pipda?style=flat-square
[10]: https://github.com/pwwang/pipda
[11]: https://img.shields.io/pypi/pyversions/pipda?style=flat-square
[12]: https://img.shields.io/github/workflow/status/pwwang/pipda/Build%20and%20Deploy?style=flat-square
[13]: https://img.shields.io/github/workflow/status/pwwang/pipda/Build%20Docs?style=flat-square
[14]: https://app.codacy.com/gh/pwwang/pipda/dashboard
[15]: https://img.shields.io/codacy/coverage/75d312da24c94bdda5923627fc311a99?style=flat-square
[16]: https://img.shields.io/codacy/grade/75d312da24c94bdda5923627fc311a99?style=flat-square
[17]: https://pwwang.github.io/pipda/api/pipda/
[18]: https://pwwang.github.io/pipda/CHANGELOG/
[19]: https://pwwang.github.io/pipda/
