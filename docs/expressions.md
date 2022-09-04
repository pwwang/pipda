# Expressions

In order to achieve the piping, we need to delay the execution of python expressions.
`pipda` turns python expressions, including operators, function calls, getattr, getitem, etc into `Expression` objects. So they can await the data to be piped in and get evaluated.

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
