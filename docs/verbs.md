# Verbs

## Registering a verb

You can use `register_verb` to register a verb. Here are the arguments of `register_verb`:

- cls: The default type to register for _default backend
    if TypeHolder, it is a generic function, and not counted as a
    real implementation.
- func: The function works as a verb.
    If `None` (not provided), this function will return a decorator.
- context: The context to evaluate the arguments
- kw_context: The context to evaluate the keyword arguments
- name: and
- qualname: and
- doc: and
- module: The meta information about the function to overwrite `func`'s
    or when it's not available from `func`
- dependent: Whether the verb is dependent.

    ```python
    >>> @register_verb(context=Context.EVAL, dependent=True)
    >>> def length(data):
    >>>     return len(data)
    >>> # with dependent=True
    >>> # length()  -> VerbCall, waiting for data to evaluate
    >>> # with dependent=False
    >>> # length()  -> TypeError, argument data is missing
    ```

- ast_fallback: What's the supposed way to call the verb when
    AST node detection fails.
    - piping - Suppose this verb is called like `data >> verb(...)`
    - normal - Suppose this verb is called like `verb(data, ...)`
    - piping_warning - Suppose piping call, but show a warning
    - normal_warning - Suppose normal call, but show a warning
    - raise - Raise an error

## Verbs are pipeable

```python
from pipda import register_verb

@register_verb(int)
def increment(data):
    return data + 1

1 >> increment()  # 2

# You can also call it normally
increment(1)  # 2
```

More about pipeable, see [Piping](./piping).

## Verbs are dispatchable

Like single-dispatched functions, verbs are dispatchable by the type of its first argument.

```python
from pipda import register_verb


@register_verb(int)
def increment(data):
    return data + 1


@increment.register(str)
def _increment(data):
    return data + '1'


1 >> increment()  # 2
'1' >> increment()  # '11'
```

What if a verb is not registered for a type? It will be dispatched to default generic function, which raises a `NotImplementedError`.

```python
[] >> increment()  # NotImplementedError
```

If you want change the default behavior, you can register a generic function by yourself, using a type holder.

```python
from pipda import register_verb
from pipda.utils import TypeHolder

@register_verb(TypeHolder)
def increment(data):
    return data + 1

1.1 >> increment()  # 2.1
```

## Verbs evaluate other arguments using the first one as data

```python
from pipda import register_verb, Context, Symbolic

f = Symbolic()

@register_verb(list, context=Context.EVAL)
def add(data, other):
    """Add other to each element of data"""
    return [d + other for d in data]


[1, 2, 3] >> add(1)  # [2, 3, 4]
# Using the first element of data
[1, 2, 3] >> add(f[0])  # [2, 3, 4]
```

More about contexts, see [Contexts](./contexts).

## Verbs pass down the context if not specified in the arguments

```python
from pipda import register_func, register_verb, Context, Symbolic

f = Symbolic()

@register_func()  # no context specified
def double(data):
    return data * 2


@register_verb(list, context=Context.EVAL)
def add(data, other):
    return [d + other for d in data]


[1, 2, 3] >> add(double(f[0]))  # [3, 4, 5]
```

## Dependent verbs

Dependent verbs are functions can be used in another verb without passing the data argument. It can also work as a normal verb.

```python
from pipda import register_verb, Context, Symbolic

f = Symbolic()

@register_verb(list, dependent=True)
def times(data, n):
    """Times each element of data with n"""
    return [d * n for d in data]

@register_verb(list, context=Context.EVAL)
def add(data, other):
    """Add other to each element of data"""
    return [d + other for d in data]

# times 2 to each element and add the first element to all elementss
# Note that we don't pass the first argument to times
[1, 2, 3] >> add(times(2)[0])  # [3, 4, 5]

# When called directly:
times(2)  # VerbCall object
times([1, 2, 3], 2)  # VerbCall object

# But when a data piped in, it is evaluated
[1, 2, 3] >> times(2)  # [2, 4, 6]
```
