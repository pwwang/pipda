# Functions

Functions cannot be used as verb arguments if they have expression arguments. Those arguments
are not evaluated into real values yet. So we also need to turn the functions into expressions.

`Function`s can also take `context` and `extra_contexts`. If not provided, next avaiable context will be used.

## Registering functions

```python
from pipda import register_func, register_verb, Context, Symbolic

# @register_func(context=..., extra_contexts=...)
@register_func
def mean(x):
    return sum(x) / len(x)
```

## Usage of registered functions

Using as a normal function:

```python
mean([1, 2, 3])  # 2
```

Used as verb argument:

```python
f = Symbolic()

@register_verb(list, context=Context.EVAL)
def plus_each(data, n):
    return [x + n for x in data]

[1, 2, 3] >> plus_each(mean(f))  # [3, 4, 5]
```

Evaluating directly:

```python
mean(f)._pipda_eval([1, 2, 3])  # 2
```
