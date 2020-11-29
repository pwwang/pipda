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
