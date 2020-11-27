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
from pipda import single_dispatch, Symbolic

X = Symbolic()

@single_dispatch(list)
def split(data, num):
    """Split a list into two lists by one of the numbers in the list"""
    return [[dat for dat in data if dat < num],
            [dat for dat in data if dat > num]]

[1,2,3,4,5] >> split(X[2])
# [[1, 2], [4, 5]]
```

[1]: https://github.com/machow/siuba
[2]: https://github.com/kieferk/dfply
[3]: https://github.com/has2k1/plydata
[4]: https://github.com/dodger487/dplython
