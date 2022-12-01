# Piping

## How it works to detect piping

```R
data %>% verb(arg1, ..., key1=kwarg1, ...)
```

The above is a typical dplyr/tidyr data piping syntax.

The counterpart python syntax we expect is:

```python
data >> verb(arg1, ..., key1=kwarg1, ...)
```

To implement that, we need to defer the execution of the verb by turning it into a Verb object, which holds all information of the function to be executed later. The Verb object won't be executed until the data is piped in. It all thanks to the executing package to let us determine the ast nodes where the function is called. So that we are able to determine whether the function is called in a piping mode.

If an argument is referring to a column of the data and the column will be involved in the later computation, the it also needs to be deferred. For example, with dplyr in R:

```R
data %>% mutate(z=a)
```

is trying add a column named z with the data from column a.

In python, we want to do the same with:

```python
data >> mutate(z=f.a)
```

where f.a is a Reference object that carries the column information without fetching the data while python sees it immmediately.

Here the trick is f. Like other packages, we introduced the Symbolic object, which will connect the parts in the argument and make the whole argument an Expression object. This object is holding the execution information, which we could use later when the piping is detected.

## Fallbacks when AST node detection fails

`pipda` detects the AST node for the verb calling. If it is next to a piping
operator (defaults to `>>`, could be changed by `register_piping()`), then it
is compiled into a `VerbCall` object, awaiting data to pipe in to evalute. We
call this the `piping` mode. Otherwise, it is treated a as normal function
call, where the data should be passed directly. This is the `normal` mode.

However, the AST node is not always available. `pipda` relies on
[`executing`][1] to detect the node. There are situations AST nodes can not be
detected. One of the biggest reasons is that the source code is not
avaiable/compromised at runtime. For example, `pytest`'s assert statement,
raw python REPL, etc.

We can set up a fallback mode when we fail to determine the AST node.

- `piping`: fallback to `piping` mode if AST node not avaiable
- `normal`: fallback to `normal` node if AST node not avaiable
- `piping_warning`: fallback to `piping` mode if AST node not avaiable and given a warning
- `normal_warning` (default): fallback to `normal` mode if AST node not avaiable and given a warning
- `raise`: Raise an error

We can also pass one of the above values to `__ast_fallback` when we call the verb.

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

By default, `>>` is used for piping. We can also use other operators, including
">>", "|", "//", "@", "%", "&" and "^".

```python
from pipda import register_piping, register_verb

register_piping("|")

@register_verb(int)
def add(x, y):
    return x + y

1 | add(2)  # 3
```

[1]: https://github.com/alexmojaki/executing
