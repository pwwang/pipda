# Verbs

Verbs are functions next to the piping operator receiving the data directly.

## Basic usage

```python
from pipda import register_verb

@register_verb(int)
def increment(data):
    return data + 1

1 >> increment()  # 2
```

## Dependent verb

Dependent verbs are functions can be used in another verb without passing the
data argument. It can also work as a normal verb.

```python
from pipda import register_verb

@register_verb(int, dep=True)
def plus(data, n):
    return data + n

# plus: 1 + 2 -> 3
# increment: 3 + 1 -> 4
1 >> increment(plus(n=2))  # 4

# also works as a normal verb
1 >> plus(n=2)  # 3
plus(n=2)  # a VerbCall object awaiting data for evaluation
```

## Expression as data

Verbs can take `Expression` object when they are used as another verb.

```python
f = Symbolic()

@register_verb(int)
def sub(data, n):
    return data -n

@register_verb(int)
def add(data, n):
    return data + n

# sub: f*2 -> 20, n=f+1=21    -> -1
# note that second f refers to the data of its verb, which is f*2 = 20
# add: 10 + -1 = 9
10 >> add(n=sub(f*2, n=f+1))  # 9
```

## Dispatching other types

```python
@register_verb(int)
def mul(x, y):
    return x * y

@mul.register(str)
def _(x, y):
    return x + y

2 >> mul(3)  # 6
"abc" >> mul("def")  # abcdef
```

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
