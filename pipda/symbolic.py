"""A framework for data piping in python"""
import sys
import ast
from copy import deepcopy

from executing import Source
from varname import varname

# pylint: disable=unused-argument,eval-used
class Transformer(ast.NodeTransformer):
    """Transform a call into the real call"""
    # pylint: disable=invalid-name
    def __init__(self, name):
        self._name__ = name

    def _wrap_op_operand(self, left):
        return ast.Call(
            func=ast.Name(id='__pipda_operators__', ctx=ast.Load()),
            args=[ast.Name(id=self._name__, ctx=ast.Load()),
                  self.visit(left)],
            keywords=[]
        )

    def _wrap_symbol(self):
        """Wrap X to __pipda_symbol__(X)"""
        return ast.Call(
            func=ast.Name(id='__pipda_symbol__', ctx=ast.Load()),
            args=[ast.Name(id=self._name__, ctx=ast.Load())],
            keywords=[]
        )

    def _is_symbol(self, node):
        if not isinstance(node, ast.Name):
            return False
        # it must be a Symbolic object for ast.Name, since other objects
        # have already compiled by python itself
        # if node.id != self._name__ or not isinstance(node.ctx, ast.Load):
        #     return False
        return True

    def visit_Attribute(self, node):
        """Turn X.a into sym_compile(X).a"""
        if not self._is_symbol(node.value):
            return self.generic_visit(node)

        return ast.Attribute(
            value=self._wrap_symbol(),
            attr=node.attr,
            ctx=ast.Load()
        )

    def visit_Subscript(self, node):
        """Turn X['a'] into sym_compile(X)['a']"""
        if not self._is_symbol(node.value):
            return self.generic_visit(node)

        return ast.Subscript(
            value=self._wrap_symbol(),
            slice=self.visit(node.slice),
            ctx=ast.Load()
        )

    def visit_BinOp(self, node):
        """Visit the binary operator"""
        node.left = self._wrap_op_operand(node.left)
        node.right = self.visit(node.right)
        return node

    def visit_UnaryOp(self, node):
        """Make -X.x available"""
        node.operand = self._wrap_op_operand(node.operand)
        return node

    def visit_Compare(self, node):
        """Comparison node"""
        node.left = self._wrap_op_operand(node.left)
        node.comparators = [self.visit(comp) for comp in node.comparators]
        return node

    def visit_Call(self, node):
        """Get the real calls"""
        node.args = [
            ast.Name(id=self._name__, ctx=ast.Load()),
            ast.Name(id='__pipda_context__', ctx=ast.Load())
        ] + node.args

        return ast.Call(
            func=ast.Attribute(value=self.visit(node.func),
                               attr='pipda',
                               ctx=ast.Load()),
            args=[self.visit(arg) for arg in node.args],
            keywords=[self.visit(kwarg) for kwarg in node.keywords]
        )

class Symbolic:
    """A symbolic representation to make X.a and alike valid python syntaxes"""
    _NAME__ = None
    _OPERATORS__ = None

    def __init__(self, name=None, exet=None):
        self._name__ = (name or
                        varname(raise_exc=False) or
                        self.__class__._NAME__)
        if not self.__class__._NAME__:
            self.__class__._NAME__ = self._name__
        if self.__class__._NAME__ != self._name__:
            raise ValueError('Only one Symbolic name is allowed.')
        self._exet__ = exet

    def __repr__(self) -> str:
        if not self._exet__:
            return f'<{self.__class__.__name__}:{self._name__}>'
        return (f'<{self.__class__.__name__}:{self._name__} ' # pragma: no cover
                f'({ast.dump(self._exet__.node)})>')

    # def _any_args(self, *args, **kwargs):
    #     return Symbolic(self._name__, Source.executing(sys._getframe(1)))

    def _no_args__(self):
        return Symbolic(self._name__, Source.executing(sys._getframe(1)))

    def _single_arg__(self, arg):
        return Symbolic(self._name__, Source.executing(sys._getframe(1)))

    # __call__ = _any_args
    __getitem__ = __getattr__ = __contains__ = _single_arg__

    __add__ = __sub__ = __mul__ = __matmul__ = __truediv__ = _single_arg__
    __floordiv__ = __mod__ = __lshift__ = _single_arg__
    __rshift__ = __and__ = __xor__ = __or__ = _single_arg__
    __pow__ = _single_arg__

    __radd__ = __rsub__ = __rmul__ = __rmatmul__ = __rtruediv__ = _single_arg__
    __rfloordiv__ = __rmod__ = __rlshift__ = _single_arg__
    __rrshift__ = __rand__ = __rxor__ = __ror__ = _single_arg__
    __rpow__ = _single_arg__

    __lt__ = __le__ = __eq__ = _single_arg__
    __ne__ = __gt__ = __ge__ = _single_arg__

    __neg__ = __pos__ = __invert__ = _no_args__

    @property
    def eval_(self):
        """Convert the symbolic representation into a callable"""

        lambody = ast.Expression(
            # see https://github.com/alexmojaki/executing/issues/17
            Transformer(self._name__).visit(
                deepcopy(self._exet__.node)
            )
            if self._exet__
            else ast.Name(id=self._name__, ctx=ast.Load())
        )
        ast.fix_missing_locations(lambody)
        # print(ast.dump(lambody))
        code = compile(lambody, filename='<pipda-ast>', mode='eval')
        if not self._exet__:
            globs = locs = globals()
        else:
            globs = self._exet__.frame.f_globals
            locs = self._exet__.frame.f_locals
        def func(data, context, context_resolver):
            return eval(code, globs, {
                **locs,
                self._name__: data,
                '__pipda_operators__': Symbolic._OPERATORS__,
                '__pipda_context__': context,
                '__pipda_symbol__': context_resolver
            })

        return func
