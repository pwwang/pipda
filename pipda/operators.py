"""Provide Operators class and register_operators function"""
from .symbolic import Symbolic

class Operators: # pylint: disable=too-many-public-methods
    """Operators in verb arguments"""
    def __init__(self, data, operand):
        self.data = data
        self.operand = operand

    def _try(self, op, *args):
        default_op = op.rstrip('_') + '_default'
        try:
            return getattr(self, default_op)(*args)
        except TypeError:
            if not hasattr(self, op):
                raise
            return getattr(self, op)(*args)

    def add_default(self, other):
        """Default behavior for X + Y"""
        return self.operand + other

    def sub_default(self, other):
        """Default behavior for X - Y"""
        return self.operand - other

    def mul_default(self, other):
        """Default behavior for X * Y"""
        return self.operand * other

    def matmul_default(self, other):
        """Default behavior for X @ Y"""
        return self.operand @ other

    def truediv_default(self, other):
        """Default behavior for X / Y"""
        return self.operand / other

    def floordiv_default(self, other):
        """Default behavior for X // Y"""
        return self.operand // other

    def mod_default(self, other):
        """Default behavior for X % Y"""
        return self.operand % other

    def lshift_default(self, other):
        """Default behavior for X << Y"""
        return self.operand << other

    def rshift_default(self, other):
        """Default behavior for X >> Y"""
        return self.operand >> other

    def and_default(self, other):
        """Default behavior for X & Y"""
        return self.operand & other

    def xor_default(self, other):
        """Default behavior for X ^ Y"""
        return self.operand ^ other

    def or_default(self, other):
        """Default behavior for X | Y"""
        return self.operand | other

    def pow_default(self, other):
        """Default behavior for X ** Y"""
        return self.operand ** other

    def lt_default(self, other):
        """Default behavior for X < Y"""
        return self.operand < other

    def le_default(self, other):
        """Default behavior for X <= Y"""
        return self.operand <= other

    def eq_default(self, other):
        """Default behavior for X == Y"""
        return self.operand == other

    def ne_default(self, other):
        """Default behavior for X != Y"""
        return self.operand != other

    def gt_default(self, other):
        """Default behavior for X > Y"""
        return self.operand > other

    def ge_default(self, other):
        """Default behavior for X >= Y"""
        return self.operand >= other

    def neg_default(self):
        """Default behavior for -X"""
        return -self.operand

    def pos_default(self):
        """Default behavior for +X"""
        return +self.operand

    def invert_default(self):
        """Default behavior for ~X"""
        return ~self.operand

    def __add__(self, other):
        return self._try('add', other)

    def __sub__(self, other):
        return self._try('sub', other)

    def __mul__(self, other):
        return self._try('mul', other)

    def __matmul__(self, other):
        return self._try('matmul', other)

    def __truediv__(self, other):
        return self._try('truediv', other)

    def __floordiv__(self, other):
        return self._try('floordiv', other)

    def __mod__(self, other):
        return self._try('mod', other)

    def __lshift__(self, other):
        return self._try('lshift', other)

    def __rshift__(self, other):
        return self._try('rshift', other)

    def __and__(self, other):
        return self._try('and_', other)

    def __xor__(self, other):
        return self._try('xor', other)

    def __or__(self, other):
        return self._try('or_', other)

    def __pow__(self, other):
        return self._try('pow', other)

    def __lt__(self, other):
        return self._try('lt', other)

    def __le__(self, other):
        return self._try('le', other)

    def __gt__(self, other):
        return self._try('gt', other)

    def __ge__(self, other):
        return self._try('ge', other)

    def __eq__(self, other):
        return self._try('eq', other)

    def __ne__(self, other):
        return self._try('ne', other)

    def __neg__(self):
        return self._try('neg')

    def __pos__(self):
        return self._try('pos')

    def __invert__(self):
        return self._try('invert')

def register_operators(cls):
    """Register operators"""
    Symbolic.OPERATORS = cls

register_operators(Operators)
