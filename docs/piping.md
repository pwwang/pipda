# Piping

## How it works to detect piping

```R
data %>% verb(arg1, ..., key1=kwarg1, ...)
```

The above is a typical dplyr/tidyr data piping syntax.

The Python counterpart we expect is:

```python
data >> verb(arg1, ..., key1=kwarg1, ...)
```

To implement this, execution of the verb must be deferred by turning it into a `VerbCall` object that holds the function and its arguments. The `VerbCall` is not evaluated until data is piped in via `>>`. This detection is made possible by the [`executing`][1] package, which inspects the AST to determine whether the function call appears on the right-hand side of a pipe operator.

If an argument references a column of the data and that column will be involved in later computation, it also needs to be deferred. For example, with `dplyr` in R:

```R
data %>% mutate(z=a)
```

adds a column `z` with values from column `a`.

In Python, the equivalent is:

```python
data >> mutate(z=f.a)
```

Here `f.a` is a `Reference` object that captures the column name without immediately fetching the data.

The `Symbolic` object `f` acts as a proxy, chaining attribute/item accesses and operator expressions into a single `Expression` tree. That tree is later evaluated when data and context become available.

## Fallbacks when AST node detection fails

`pipda` detects the AST node of the verb call. If the call appears on the
right-hand side of a piping operator (`>>` by default, configurable via
`register_piping()`), it is compiled into a `VerbCall` object that awaits data.
This is *piping mode*. Otherwise, it is treated as a normal function call where
the data must be passed directly — *normal mode*.

However, the AST node is not always available. `pipda` relies on
[`executing`][1] to detect the node. There are situations where AST nodes cannot be
detected. One of the most common reasons is that the source code is not
available at runtime — for example, `pytest`'s assert rewriting,
the raw Python REPL, etc.

You can configure a fallback mode for when AST detection fails:

- `piping`: fallback to piping mode
- `normal`: fallback to normal mode
- `piping_warning`: fallback to piping mode with a warning
- `normal_warning` (default): fallback to normal mode with a warning
- `raise`: raise an error

You can also pass one of the above values as `__ast_fallback` when calling the verb.

```python
@register_verb(int, ast_fallback="normal")
def add(x, y):
    return x + y

@register_verb(int, ast_fallback="piping")
def sub(x, y):
    return x - y

@register_verb(int)
def mul(x, y):
    return x * y

# In an environment AST node cannot be detected
add(1, 2)  # 3, ok
1 >> add(2)  # TypeError, argument y missing

2 >> sub(1)  # 1, ok
sub(2, 1)  # TypeError, argument y missing

mul(1, 2, __ast_fallback="normal")  # 3
1 >> mul(2, __ast_fallback="piping")  # 3

# Change the fallback
add.ast_fallback = "piping"
1 >> add(2)  # 3, ok
add(1, 2)  # VerbCall object
```

## Using a different operator for piping

By default, `>>` is used for piping. You can also use other operators: `|`,
`//`, `@`, `%`, `&`, and `^`.

```python
from pipda import register_piping, register_verb

register_piping("|")

@register_verb(int)
def add(x, y):
    return x + y

1 | add(2)  # 3
```

[1]: https://github.com/alexmojaki/executing
