# pipda

[![Pypi][7]][8] [![Github][9]][10] [![PythonVers][11]][8] [![Codacy][16]][14] [![Codacy coverage][15]][14] ![Docs building][13] ![Building][12]

A framework for data piping in python

Inspired by [siuba][1], [dfply][2], [plydata][3] and [dplython][4], but with simple yet powerful APIs to mimic the `dplyr` and `tidyr` packages in python


[API][17] | [Change Log][18] | [Playground][19]

## Installation
```shell
pip install -U pipda
```

## Usage

Checkout [datar][6] for more detailed usages.

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

# Verbs that don't compile f.a to data, but just the column name
@register_verb(pd.DataFrame, context=Context.SELECT)
def select(data, *columns):
    return data.loc[:, columns]

# f.x won't be compiled as df.x but just 'x'
df >> mutate(z=2*f.x) >> select(f.x, f.z)
#      x    z
# 0    0    0
# 1    1    2
# 2    2    4
# 3    3    6

# Compile the args inside the verb
@register_verb(pd.DataFrame, context=Context.PENDING)
def mutate_existing(data, column, value):
    column = evaluate_expr(column, data, Context.SELECT)
    value = evaluate_expr(value, data, Context.EVAL)
    data = data.copy()
    data[column] = value
    return data

# First f.x compiled as column name, and second as Series data
df2 = df >> mutate_existing(f.x, 10 * f.x)
df2
#      x    y     z
# 0    0    zero  0
# 1    10   one   2
# 2    20   two   4
# 3    30   three 6

# Evaluate the arguments by yourself
@register_verb(pd.DataFrame, context=Context.PENDING)
def mutate_existing2(data, column, value):
    column = evaluate_expr(column, data, Context.SELECT)
    value = evaluate_expr(value, df2, Context.EVAL)
    data = data.copy()
    data[column] = value
    return data

df >> mutate_existing2(f.x, 2 * f.x)
#      x    y
# 0    0    zero
# 1    20   one
# 2    40   two
# 3    60   three

# register for multiple types
@register_verb(int)
def add(data, other):
    return data + other

# add is actually a singledispatch generic function
@add.register(float)
def _(data, other):
    return data * other

1 >> add(1)
# 2
1.1 >> add(1.0)
# 1.1

# As it's a singledispatch generic function, we can do it for multiple types
# with the same logic
@register_verb(context=Context.EVAL)
def mul(data, other):
    raise NotImplementedError # not invalid until types registered

@mul.register(int)
@mul.register(float)
# or you could do @mul.register((int, float))
# context is also supported
def _(data, other):
    return data * other

3 >> mul(2)
# 6
3.2 >> mul(2)
# 6.4
```

### Functions used in verb arguments
```python
@register_func(context=Context.EVAL)
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
@register_func(None)
def length(strings):
    return [len(s) for s in strings]

df >> mutate(z=length(f.y))

#    x     y    z
# 0  0  zero    4
# 1  1   one    3
# 2  2   two    3
# 3  3 three    5
```

```python
# register existing functions
from numpy import vectorize
len = register_func(None, context=Context.EVAL, func=vectorize(len))

# original function still works
print(len('abc'))

df >> mutate(z=len(f.y))

# 3
#   x     y z
# 0 0  zero 4
# 1 1   one 3
# 2 2   two 3
# 3 3 three 5
```

### Operators
You may also redefine the behavior of the operators
```python
@register_operator
class MyOperators(Operator):
    def xor(self, a, b):
        """Inteprete X ^ Y as pow(X, Y)."""
        return a ** b

df >> mutate(z=f.x ^ 2)
#      x    y      z
# 0    0    zero   0
# 1    1    one    1
# 2    2    two    4
# 3    3    three  9
```

### Context

The context defines how a reference (`f.A`, `f['A']`, `f.A.B` is evaluated)

```python
from pipda import ContextBase

class MyContext(ContextBase):
    name = 'my'
    def getattr(self, parent, ref):
        # double it to distinguish getattr
        return getattr(parent, ref)
    def getitem(self, parent, ref):
        return parent[ref] * 2
    @property
    def ref(self):
        # how we evaluate the ref in f[ref]
        return self


@register_verb(context=MyContext())
def mutate_mycontext(data, **kwargs):
    for key, val in kwargs.items():
        data[key] = val
    return data

df >> mutate_mycontext(z=f.x + f['x'])

#   x     y z
# 0 0  zero 0
# 1 1   one 3
# 2 2   two 6
# 3 3 three 9
```

```python
# when ref in f[ref] is also needed to be evaluated
df = df >> mutate(zero=0, one=1, two=2, three=3)
df

#    x      y  z  zero  one  two  three
# 0  0   zero  0     0    1    2      3
# 1  1    one  3     0    1    2      3
# 2  2    two  6     0    1    2      3
# 3  3  three  9     0    1    2      3
```

```python
df >> mutate_mycontext(m=f[f.y][:1].values[0])
# f.y returns ['zero', 'one', 'two', 'three']
# f[f.y] gets [[0, 2, 4, 6], [0, 2, 4, 6], [0, 2, 4, 6], [0, 2, 4, 6]]
# f[f.y][:1].values gets [[0, 4, 8, 16]]
# f[f.y][:1].values[0] returns [0, 8, 16, 32]
# Notes that each subscription ([]) will double the values

#    x      y  z  zero  one  two  three   m
# 0  0   zero  0     0    1    2      3   0
# 1  1    one  3     0    1    2      3   8
# 2  2    two  6     0    1    2      3  16
# 3  3  three  9     0    1    2      3  24
```

### Calling rules

#### Verb calling rules

1. `data >> verb(...)`\
    [PIPING_VERB]\
    First argument should not be passed, using the data
2. `data >> other_verb(verb(...))`\
   `other_verb(data, verb(...))`\
   `registered_func(verb(...))`\
    [PIPING]\
    Try using the first argument to evaluate (FastEvalVerb), if first argument
    is data. Otherwise, if it is Expression object, works as a non-data
    Function.
3. `verb(...)`\
    Called independently. The verb will be called regularly anyway.
    The first argument will be used as data to evaluate the arguments
    if there are any Expression objects
4. `verb(...)` with DataEnv\
    First argument should not be passed in, will use the DataEnv's data
    to evaluate the arguments

#### Data function calling rules

Functions that require first argument as data argument.

1. `data >> verb(func(...))` or `verb(data, func(...))`\
    First argument is not used. Will use data
2. `func(...)`\
    Called independently. The function will be called regularly anyway.
    Similar as Verb calling rule, but first argument will not be used for
    evaluation
3. `func(...)` with DataEnv\
    First argument not used, passed implicitly with DataEnv.

### Non-data function calling rules:

1. `data >> verb(func(...))` or `verb(data, func(...))`\
    Return a Function object waiting for evaluation
2. `func(...)`\
    Called regularly anyway
3. `func(...) with DataEnv`\
    Evaluate with DataEnv. For example: mean(f.x)

### Caveats

- You have to use and_ and or_ for bitwise and/or (`&`/`|`) operators, as and and or are python keywords.

- Limitations:

    Any limitations apply to `executing` to detect the AST node will apply to `pipda`. It may not work in some circumstances where other AST magics apply.

    **What if source code is not available?**

    `executing` does not work in the case where source code is not available, as there is no way to detect the AST node to check how the functions (verbs, data functions, non-data functions) are called, either they are called as a piping verb (`data >> verb(...)`), or they are called as an argument of a verb (`data >> verb(func(...))`) or even they are called independently/regularly.

    In such a case, you can set the option (`options.assume_all_piping=True` (`pipda` `v0.4.4+`)) to assume that all registered functions are called in piping mode, so that you can do `data >> verb(...)` without any changes.

    You can also use this option to enhance the performance by skipping detection of the calling environment.

- Use another piping sign

    ```python
    from pipda import register_piping
    register_piping('^')

    # register verbs and functions
    df ^ verb1(...) ^ verb2(...)
    ```

    Allowed signs are: `+`, `-`, `*`, `@`, `/`, `//`, `%`, `**`, `<<`, `>>`, `&`, `^` and `|`.

    Note that to use the new  piping sign, you have to register the verbs after the new piping sign being registered.

- The context

    The context is only applied to the `DirectReference` objects or unary operators, like `-f.A`, `+f.A`, `~f.A`, `f.A`, `f['A']`, `[f.A, f.B]`, etc. Any other `Expression` wrapping those objects or other operators getting involved will turn the context to `Context.EVAL`

## How it works
### The verbs
```R
data %>% verb(arg1, ..., key1=kwarg1, ...)
```
The above is a typical `dplyr`/`tidyr` data piping syntax.

The counterpart R syntax we expect is:
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

### The functions
Then what if we want to use some functions in the arguments of the `verb`?
For example:
```python
data >> select(starts_with('a'))
```
to select the columns with names start with `'a'`.

No doubt that we need to defer the execution of the function, too. The trick is that we let the function return a `Function` object as well, and evaluate it as the argument of the verb.

### The operators
`pipda` also opens oppotunities to change the behavior of the operators in verb/function arguments. This allows us to mimic something like this:
```python
data >> select(-f.a) # select all columns but `a`
```

To do that, we turn it into an `Operator` object. Just like a `Verb` or a `Function` object, the execution is deferred. By default, the operators we used are from the python standard library `operator`. `operator.neg` in the above example.

You can also define you own by subclassing the `Operator` class, and then register it to replace the default one by decorating it with `register_operator`.


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
[18]: https://pwwang.github.io/pipda/changelog/
[19]: https://mybinder.org/v2/gh/pwwang/pipda/master?filepath=README.ipynb
[20]: https://pwwang.github.io/datar/piping_vs_regular/
