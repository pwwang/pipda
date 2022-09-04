# Operators

Operators can be redefined with `pipda`. By default, the operators are from the
builtin library `operator`. The "right" versions (e.g. `radd`, `rsub`, etc) are
derived from the builtin ones by swapping the operands.

You can define you own operators:

```python
from pipda import Symbolic, Operator, register_operator

f = Symbolic()

@register_operator
class MyOperator(Operator):
    def add(self, x, y):
        return x * y

    def invert(self, x):
        return -x

expr = f["x"] + 10
assert str(expr) == "x + 10"
assert expr._pipda_eval({"x": 3}, Context.EVAL) == 30

expr = 10 * f["x"]
assert str(expr) == "10 * x"
assert expr._pipda_eval({"x": 2}, Context.EVAL) == 20

expr = ~f["x"]
assert str(expr) == "~x"
assert expr._pipda_eval({"x": 2}, Context.EVAL) == -2

register_operator(Operator)

expr = ~f["x"]
assert str(expr) == "~x"
assert expr._pipda_eval({"x": 2}, Context.EVAL) == -3 # ~2
```
