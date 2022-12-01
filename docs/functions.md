# Functions

For functions, we mean that the registered functions, rather than the python plain functions. Function calls are used as verb arguments, but they can be used independently as well, if no expressions is passed to the function.

Functions share some features with verbs, such as that they could be pipeable and dispatchable as well. But they have a lot of differences as well. The biggest ones are that a function:

- doesn't use the type of the first argument only to dispatch
- doesn't pass the context down
- doesn't evaluate other arguments using the first one (unless specified) but the data passed to the call from a verb, unless a data is piped in.

## Register a function

To register a function, use `register_func` function/decorator. Here are the arguments:

- func: The generic function.
    If `None` (not provided), this function will return a decorator.
- cls: The default type to register for _default backend
    if TypeHolder, it is a generic function, and not counted as a
    real implementation.
    For plain or non-dispatchable functions, specify a different type
    than TypeHolder to indicate the func is a real implementation.
- plain: If True, the function will be registered as a plain function,
    which means it will be called without any evaluation of the
    arguments. It doesn't support dispatchable and pipeable.
- name: and
- qualname: and
- doc: and
- module: The meta information about the function to overwrite `func`'s
    or when it's not available from `func`
- ast_fallback: What's the supposed way to call the func when
    AST node detection fails.
    - piping - Suppose this func is called like `data >> func(...)`
    - normal - Suppose this func is called like `func(data, ...)`
    - piping_warning - Suppose piping call, but show a warning
    - normal_warning - Suppose normal call, but show a warning
    - raise - Raise an error
- dispatchable: If True, the function will be registered as a dispatchable
    function, which means it will be dispatched using the types of
    positional arguments.
- dispatch_args: Which arguments to use for dispatching.
    - "first" - Use the first argument
    - "args" - Use all positional arguments
    - "kwargs" - Use all keyword arguments
    - "all" - Use all arguments
- pipeable: If True, the function will work like a verb when a data is
    piping in. If dispatchable, the first argument will be used to
    dispatch the implementation.
    The rest of the arguments will be evaluated using the data from
    the first argument.
- context: The context used to evaluate the rest arguments using the
    first argument only when the function is pipeable and the data
    is piping in.
- kw_context: The context used to evaluate the keyword arguments

## Plain functions

One could register functions as plain functions, which means they will be called without any evaluation of the arguments. It doesn't support dispatchable and pipeable.

The reason to allow plain functions is that we could have multiple implementations for different backends for plain functions.

See [Backends](./backends) for more details.

## Dispatchable functions

One could register functions as dispatchable functions, which means they will be dispatched using the type of the first argument, the types of positional arguments, the types of of the keyword arguments, or the types of all arguments.

The types are determined after the arguments are evaluated. One could specify the context for evaluation of the arguments. See [Contexts](./contexts) for more details. If not specified, the context passed down from the verb will be used. One could also specify the context for the function and kw_context for the keyword arguments.

Once an implementation is found, the later arguments will be ignored. If no implementation is found, the default implementation (that raises `NotImplementedError`) will be used.

### Dispatching by the type of the first argument

Using the type of the first argument:

```python
from pipda import register_func

@register_func(cls=int, dispatchable="first")
def rep(x, y):
    return x + y

@rep.register(str)
def _(x, y):
    return x * y

rep(1, 2)  # 3
rep("a", 3)  # "aaa"
```

Using the types of the positional arguments:

```python
from pipda import register_func

@register_func(cls=int, dispatchable="args")
def rep(x, y):
    return x * y

@rep.register(str)
def _(x, y):
    return x + str(y)

rep(1, 2)  # 2
rep("a", 3)  # "a3"
# Type of 2nd argument used
rep([1], 2)  # [1, 1]
```

Using the types of the keyword arguments:

```python
from pipda import register_func

@register_func(cls=str, dispatchable="kwargs")
def rep(x, y):
    return x + y

@rep.register(int)
def _(x, y):
    return x * y

rep("1", y=2)  # 11
rep("1", y="2")  # "12"
```

Using the types of all arguments:

```python
from pipda import register_func

@register_func(cls=str, dispatchable="kwargs")
def rep(x, y):
    return x + str(y)

@rep.register(int)
def _(x, y):
    return x * y

# Dispatched eagerly
rep("1", y=2)  # "12"
rep("1", y="2")  # "12"
```

## Pipeable functions

One could register functions as pipeable functions, which means they will work like a verb when a data is piping in. If dispatchable, the first argument will be used to dispatch the implementation. The rest of the arguments will be evaluated using the data from the first argument.

```python
from pipda import register_func

@register_func(cls=int, pipeable=True)
def rep(x, y):
    return x + y

1 >> rep(2)  # 3
```
