# pipda

A framework for data piping in python

This allows you to mimic the `R` package `dplyr` in python

Inspired by [siuba][1], [dfply][2], [plydata][3] and [dplython][4], but implemented in only < 200 lines!

## Installation
```shell
pip install -U pipda
```

## Usage
```python
import pandas as pd
from pipda import register_verb, register_func, Symbolic

@register_verb(pd.DataFrame)
def mutate(data, **kwargs):
    for key, val in kwargs.items():
        data[key] = val
    return data

@register_func
def if_else(data, cond, true, false):
    cond.loc[cond.isin([True]), ] = true
    cond.loc[cond.isin([False]), ] = false
    return cond

X = Symbolic()

df = pd.DataFrame({
    'x': [0, 1, 2, 3],
    'y': ['zero', 'one', 'two', 'three']
})

df
#    x      y
# 0  0   zero
# 1  1    one
# 2  2    two
# 3  3  three

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

df >> mutate(z=2 * X.x)
#    x      y  z
# 0  0   zero  0
# 1  1    one  2
# 2  2    two  4
# 3  3  three  6

df >> mutate(z=if_else(X.x>1, 20, 10))
#    x      y   z
# 0  0   zero  10
# 1  1    one  10
# 2  2    two  20
# 3  3  three  20
```

[1]: https://github.com/machow/siuba
[2]: https://github.com/kieferk/dfply
[3]: https://github.com/has2k1/plydata
[4]: https://github.com/dodger487/dplython
