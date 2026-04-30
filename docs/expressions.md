# Expressions

To achieve piping, execution of Python expressions must be delayed.
`pipda` wraps Python expressions — operators, function calls, attribute access, item access, etc. — into `Expression` objects that await data to be piped in before evaluating.

A `Symbolic` object is a root expression that is supposed to be evaluated as the data itself.

An expression can be evaluated manually by `expr._pipda_eval(data, context)`.

```python
f = Symbolic()
f._pipda_eval(1)  # 1
```

A `Symbolic` can derive into other `Expression` objects:

```python
f = Symbolic()
f.a  # ReferenceAttr object
f["a"]  # ReferenceItem object
f.a()  # FunctionCall object
f.a + f.b  # OperatorCall object
```

## numpy ufuncs on Expression objects

```python
import numpy as np
from pipda import Symbolic

f = Symbolic()

x = np.sqrt(f)

x._pipda_eval(4)  # 2.0
```

## Register your own `__array_ufunc__`

```python
import numpy as np
from pipda import Symbolic, register_array_ufunc


 @register_array_ufunc
 def my_ufunc(ufunc, x, *args, **kwargs):
    return ufunc(x, *args, **kwargs) * 2

f = Symbolic()
x = np.sqrt(f)

x._pipda_eval(4)  # 4.0
```
