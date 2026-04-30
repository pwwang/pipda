# Backends

Verbs and registered functions can have different implementations for different backends. Normally, dispatching distinguishes implementations by type. However, when multiple implementations are needed for the same type, you can use the `backend` argument to register a function for a specific backend.

For example, we want to implement a function `rep` for different backends.

```python
from pipda import register_func

@register_func(dispatchable="args")
def rep(x, y):
    raise NotImplementedError

@rep.register(cls=int, backend="python")
def _(x, y):
    return [x] * y

@rep.register(cls=int, backend="numpy")
def _(x, y):
    import numpy as np
    return np.repeat(x, y)

# Later-registered backend has higher priority.
# A warning is shown since two implementations exist for int.
rep(1, 3)  # np.array([1, 1, 1])
# Use __backend argument to specify the backend
rep(1, 3, __backend="python")  # [1, 1, 1]
```

To suppress the warning, mark one implementation as favored:

```python
from pipda import register_func

@register_func(dispatchable="args")
def rep(x, y):
    raise NotImplementedError

@rep.register(cls=int, backend="python")
def _(x, y):
    return [x] * y

@rep.register(cls=int, backend="numpy", favored=True)
def _(x, y):
    import numpy as np
    return np.repeat(x, y)

# Later registered backend has higher priority
# No warnings anymore
rep(1, 3)  # np.array([1, 1, 1])
rep(1, 3, __backend="python")  # [1, 1, 1]
```

Verbs apply the same rule for backends.
