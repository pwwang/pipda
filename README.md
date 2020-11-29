# pipda

A framework for data piping in python

Inspired by [siuba][1], [dfply][2], [plydata][3] and [dplython][4], but with simple yet powerful APIs to mimic the `dplyr` and `tidyr` packages in python

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
To implement that, we need to defer the execution of the `verb` by turning it into a `Verb` object, which holds all information of the function to be executed later. The `Verb` object won't be executed until the `data` is piped in. This means:
```python
verb(arg1, ..., key1=kwarg1)
```
will just return a `Verb` object and not execute anything. But `data >> verb(...)` will lead it to execute.

If an argument is referring to a column of the data and the column will be involved in the later computation, the it also needs to be deferred. For example, with `dplyr` in `R`:
```R
data %>% mutate(z=a)
```
is trying add a column named `z` with the data from column `a`.

In python, we want to do the same with:
```python
data >> mutate(z=X.a)
```
where `X.a` is a `Symbolic` object that carries the column information without fetching the data while python sees it immmediately.

Here the trick is `X`. Like other packages, we introduced the `Symbolic` object, which will connect the parts in the argument and make the whole argument a `Symbolic` object. This object is holding the AST node of the argument, which we could manipulate later. The AST node is fetched by package [`executing`][5]. Any limitations that apply to `executing` will also apply to `pipda`.

### The functions
Then what if we want to use some functions in the arguments of the `verb`?
For example:
```python
data >> select(starts_with('a'))
```
to select the columns with names start with `'a'`.

No doubt that we need to defer the execution of the function, too. The trick is that we let the function return a `Symbolic` object as well, and attach the real function to `starts_with.pipda`. While executing the function, we modify the AST node to turn `starts_with` into `starts_with.pipda` to call the actual function.

### The operators
`pipda` also opens oppotunities to change the behavior of the operators in verb arguments. This allows us to mimic something like this:
```python
data >> select(-X.a) # select all columns but `a`
```

To do that, the `UnaryOp` is modified to find `Operators` class and wrap the operand so that the operator will be called on the `Operators` object. In the above example, `-X.a` is expanded to:
```python
-Symbolic.operators(X.a) # X.a should be executed value at this step.
```
So, `Operators.__neg__` will be called. `pipda` has a default `Operators` class which defines the default behavior of the operators. You can also define you own by subclassing the `Operators` class, and then register it to replace the default one.


## Installation
```shell
pip install -U pipda
```

## Usage

### Verbs

Verbs are functions next to the piping sign (`>>`) receiving the data directly.

```python
import pandas as pd
from pipda import register_verb, register_func, register_operators, Operators, Symbolic

X = Symbolic()

df = pd.DataFrame({
    'x': [0, 1, 2, 3],
    'y': ['zero', 'one', 'two', 'three']
})

df
# 	x	y
# 0	0	zero
# 1	1	one
# 2	2	two
# 3	3	three

@register_verb(pd.DataFrame)
def head(data, n=5):
    return data.head(n)

df >> head(2)
#   x	y
# 0	0	zero
# 1	1	one

@register_verb(pd.DataFrame)
def mutate(data, **kwargs):
    for key, val in kwargs.items():
        data[key] = val
    return data

df >> mutate(z=1)
#    x      y  z
# 0  0   zero  1
# 1  1    one  1
# 2  2    two  1
# 3  3  three  1

df >> mutate(z=X.x)
#    x      y  z
# 0  0   zero  0
# 1  1    one  1
# 2  2    two  2
# 3  3  three  3

# Verbs that don't compile the value of an attribute
@register_verb(pd.DataFrame, compile_attrs=False)
def select(data, *columns):
    return data.loc[:, columns]

# X.x won't be compiled as df.x but just 'x'
df >> mutate(z=2*X.x) >> select(X.x, X.z)
# 	x	z
# 0	0	0
# 1	1	2
# 2	2	4
# 3	3	6
```

### Functions used in verb arguments
```python
@register_func
def if_else(data, cond, true, false):
    cond.loc[cond.isin([True]), ] = true
    cond.loc[cond.isin([False]), ] = false
    return cond

df >> mutate(z=if_else(X.x>1, 20, 10))
#    x      y   z
# 0  0   zero  10
# 1  1    one  10
# 2  2    two  20
# 3  3  three  20
```

### Operators
You may also redefine the behavior of the operators
```python
@register_operators
class MyOperators(Operators):
    def xor_default(self, other):
        """Inteprete X ^ Y as pow(X, Y)."""
        return self.operand ** other

df >> mutate(z=X.x ^ 2)
# x	y	z
# 0	0	zero	0
# 1	1	one	1
# 2	2	two	4
# 3	3	three	9
```

### Caveats
- Only one `Symbolic` name is allowed:
    ```python
    X = Symbolic()
    _ = Symbolic() # error
    ```

- Default` v.s. non-default behavior of the operators:

    Default behavior (`xor_default`) will be first applied. If it fails, non-default (`xor`) behavior will be applied.

- Non-default behaviors for `&` and `|` operators:

    You have to use `and_` and `or_` for them, as `and` and `or` are python keywords.
    Their default behaviors are still defined as `and_default` and `or_default`, respectively.

- Limitations:

    Any limitations apply to `executing` to detect the AST node will apply to `pipda`. It may not work in some circumstances where other AST magics apply.

[1]: https://github.com/machow/siuba
[2]: https://github.com/kieferk/dfply
[3]: https://github.com/has2k1/plydata
[4]: https://github.com/dodger487/dplython
[5]: https://github.com/alexmojaki/executing
