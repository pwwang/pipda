# Context

The context defines how a reference (`f.A`, `f['A']`, `f.A.B` is evaluated)

## `Context.EVAL`

This context evaluates the references directly. For example, if data is
`{"a": 1}`, `f["a"]` will be evaluted into `1`.

```python
from pipda import register_verb, Context

@register_verb(dict, context=Context.EVAL)
def mutate(data, **kwargs):
    data = data.copy()
    data.update(kwargs)
    return data

{"a": 1} >> mutate(b=f["a"] * 2)  # {"a": 1, "b": 2}
```

## `Context.SELECT`

This context evaluates the references into the attribute names or subscripts
themselves. This, for `f.key` works sometimes as a shortcut for `"key"`.

```python
@register_verb(dict, context=Context.SELECT)
def select(data, *keys):
    return {key: val for key, val in data.items() if key in keys}

{"a": 1, "b": 2} >> select(f.a)  # {"a": 1}
```

## `Context.PENDING`

This remains expressions un-evaluated so that they get passed into the function
and evaluted later inside the function.

```python
from pipda import Context, register_verb, evaluate_expr

@register_verb(dict, context=Context.PENDING)
def mutate(data, **kwargs):
    # kwargs is holding expressions
    kwargs = evaluate_expr(kwargs, data, Context.EVAL)
    data = data.copy()
    data.update(kwargs)
    return data

{"a": 1} >> mutate(b=f["a"] * 2)  # {"a": 1, "b": 2}
```

## Customizing a context

You can write your own context by subclassing `ContextBase`. Overwrite the
following methods to define the behaviors:

- `getattr`: How to evaluate `f.A`
- `getitem`: How to evaluate `f["A"]`
- `ref` (property): How to evaluate `x` in `f[x]`

```python
from pipda import Context, ContextBase, register_verb

class MyContext(ContextBase):
    def getattr(self, parent, ref, level):
        # f.A -> level 1
        # f.A.B -> level 2
        return parent[ref]

    def getitem(self, parent, ref, level):
        return ref

@register_verb(dict, context=MyContext())
def subset_and_update(data, *cols, **kwargs):
    data = {key: val for key, val in data.items() if key in cols}
    data.update(kwargs)
    return data

{"a": 1, "b": 2, "c": 3} >> subset_and_update(f.a, f.b, a=f.c)
# {"a": 3, "b": 2}
```

!!! note

    Note that for `Context.PENDING`, we need to subclass `context.ContextPending`
    to keep expressions unevaluated.

## Contexts for keyword arguments

We can set extra contexts for keyword arguments.

```python

@register_verb(
    dict,
    context=Context.EVAL,
    kw_context={"cols": Context.SELECT},
)
def subset_and_update(data, *, cols, **kwargs):
    data = {key: val for key, val in data.items() if key in cols}
    data.update(kwargs)
    return data

{"a": 1, "b": 2, "c": 3} >> subset_and_update(f.a, f.b, a=f.c)
# {"a": 3, "b": 2}
```

!!! note

    By default, the context is `None`, the expressions, including `FunctionCall`
    and `VerbCall` objects, will be awaiting next coming avaiable context to
    evaluate

!!! note

    When registering another type(s) for a verb, contexts and extra contexts
    are inherited for the first ones that registered with `register_verb`


!!! Tip

    Each implementation for the registered verbs or functions can have its own
    contexts. Specify them when registering the implementations.

    ```python
    <verb>.register(..., context=..., kw_context=...)
    <func>.register(..., context=..., kw_context=...)
    ```
