from types import FunctionType
import unittest
from pipda import *

class TestCase(unittest.TestCase):

    def test_case(self):
        X = Symbolic()

        @register_verb(list)
        def split(data, num):
            """Split a list into two lists by one of the numbers in the list"""
            return [[dat for dat in data if dat < num],
                    [dat for dat in data if dat > num]]

        @register_verb(list)
        def add(data, num):
            if not isinstance(num, int):
                num = list(num)
            else:
                num = [num] * len(data)
            return [dat + num[i] for i, dat in enumerate(data)]

        x = [1,2,3,4,5] >> split(4)
        self.assertEqual(x, [[1,2,3], [5]])
        x = [1,2,3,4,5] >> split(X[2])
        self.assertEqual(x, [[1,2], [4,5]])

        x = [1,2,3] >> add(2)
        self.assertEqual(x, [3,4,5])
        x = [1,2,3] >> add(X)
        self.assertEqual(x, [2,4,6])
        # x = [1,2,3] >> add(X.__reversed__())
        # self.assertEqual(x, [4,4,4])

        with self.assertRaises(TypeError):
            'abc' >> add('def')

    def test_int(self):
        X = Symbolic()

        @register_verb(int)
        def add(data, num):
            """Split a list into two lists by one of the numbers in the list"""
            return data + num

        self.assertEqual(1 >> add(1), 2)
        self.assertEqual(2 >> add(X), 4)
        self.assertEqual(2 >> add(X ** 3), 10)

    def test_register_func(self):
        X = Symbolic()
        self.assertEqual(repr(X), '<Symbolic:X>')

        @register_verb(dict)
        def filter(data, keys):
            return {key: val for key, val in data.items() if key in keys}

        @register_verb(dict)
        def length(data):
            return data.__len__()

        @register_func
        def starts_with(data, prefix):
            return [key for key in data if key.startswith(prefix)]

        @register_func()
        def ends_with(data, suffix):
            return [key for key in data if key.endswith(suffix)]

        x = {'abc': 1, 'def': 2, 'ahi': 3} >> filter(['abc', 'def'])
        self.assertEqual(x, {'abc': 1, 'def': 2})
        x = {'abc': 1, 'def': 2, 'ahi': 3} >> filter(starts_with('a'))
        self.assertEqual(x, {'abc': 1, 'ahi': 3})
        self.assertEqual(x >> length(), 2)
        x = {'abc': 1, 'def': 2, 'ahi': 3} >> length()
        self.assertEqual(x, 3)
        x = {'abc': 1, 'def': 2, 'hic': 3} >> filter(ends_with('c'))
        self.assertEqual(x, {'abc': 1, 'hic': 3})

    def test_only_one_symbolic(self):
        with self.assertRaises(ValueError):
            _ = Symbolic()

    def test_unary(self):
        X = Symbolic()
        @register_verb(dict, compile_proxy='select')
        def filter(data, keys):
            return {key: val for key, val in data.items() if key in keys}

        @register_operators
        class MyOperators(Operators):
            def neg(self):
                return [key for key in self.data if key != self.operand]

        x = {'abc': 1, 'ded': 2, 'hic': 3} >> filter(-X.abc)
        self.assertEqual(x, {'ded': 2, 'hic': 3})


        with self.assertRaises(AttributeError):
            {} >> filter(-X.abc.d)

    def test_compile_attrs(self):
        import types
        data = lambda: 0
        data.a = 1
        data.b = 2
        data.c = 3

        X = Symbolic()
        @register_verb(types.FunctionType)
        def filter_by_value(data, *values):
            return {key: getattr(data, key) for key in data.__dict__ if getattr(data, key) in values}

        d = data >> filter_by_value(X.a, X.b)
        self.assertEqual(d, {'a': 1, 'b': 2})

    def test_binop(self):
        import types
        data = lambda: 0
        data.a = 1
        data.b = 2
        data.c = 3

        X = Symbolic()
        @register_verb(types.FunctionType)
        def add(data, *values):
            return sum(values)

        @register_operators
        class MyOperators(Operators):
            def and_default(self, other):
                return self.operand + other

            def or_default(self, other):
                return self.operand - other

        self.assertEqual(data >> add(X.a + X.b, X.c), 6)
        self.assertEqual(data >> add(X.a & X.b, X.c), 6)
        self.assertEqual(data >> add(X.a | X.b, X.c), 2)

    def test_unsupported_type_for_func(self):
        X = Symbolic()
        @register_verb((int, float))
        def add(data, other):
            return data + other

        @register_func(int)
        def one(data):
            return 1

        x = 1 >> add(2)
        self.assertEqual(x, 3)

        x = 1 >> add(one())
        self.assertEqual(x, 2)

        with self.assertRaises(TypeError):
            1.1 >> add(one())

    def test_operators(self):
        X = Symbolic()
        Symbolic.OPERATORS = Operators
        @register_verb(int)
        def add(data, arg):
            return data + arg

        x = 1 >> add(X + 1)
        self.assertEqual(x, 3)
        x = 1 >> add(X - 1)
        self.assertEqual(x, 1)
        x = 1 >> add(X * 1)
        self.assertEqual(x, 2)
        x = 1 >> add(X / 1)
        self.assertEqual(x, 2)
        x = 1 >> add(X // 1)
        self.assertEqual(x, 2)
        x = 1 >> add(X % 1)
        self.assertEqual(x, 1)
        x = 1 >> add(X << 1)
        self.assertEqual(x, 3)
        x = 1 >> add(X >> 1)
        self.assertEqual(x, 1)
        x = 1 >> add(X & 1)
        self.assertEqual(x, 2)
        x = 1 >> add(X | 1)
        self.assertEqual(x, 2)
        x = 1 >> add(X ^ 1)
        self.assertEqual(x, 1)
        x = 1 >> add(X ** 1)
        self.assertEqual(x, 2)
        x = 1 >> add(X < 1)
        self.assertEqual(x, 1)
        x = 1 >> add(X <= 1)
        self.assertEqual(x, 2)
        x = 1 >> add(X > 1)
        self.assertEqual(x, 1)
        x = 1 >> add(X >= 1)
        self.assertEqual(x, 2)
        x = 1 >> add(X == 1)
        self.assertEqual(x, 2)
        x = 1 >> add(X != 1)
        self.assertEqual(x, 1)
        x = 1 >> add(-X)
        self.assertEqual(x, 0)
        x = 1 >> add(+X)
        self.assertEqual(x, 2)
        x = 1 >> add(~X)
        self.assertEqual(x, -1)



        with self.assertRaises(TypeError):
            1 >> add(X @ 1)

    def test_error_changing_piping_sign(self):
        with self.assertRaises(ValueError):
            piping_sign('~')

    def test_proxy_compiler_set_data(self):
        X = Symbolic()

        @register_verb(FunctionType, compile_proxy=None)
        def add1(data, arg):
            arg = arg.compile_to('data')
            return data.a + arg

        @register_verb(FunctionType, compile_proxy=None)
        def add2(data, arg):
            arg = arg.set_data(d2).compile_to('data')
            return data.a + arg

        d1 = lambda: 0
        d2 = lambda: 0
        d1.a = 1
        d2.a = 10

        x = d1 >> add1(X.a)
        self.assertEqual(x, 2)

        x = d1 >> add2(X.a)
        self.assertEqual(x, 11)

    def test_proxy_compiler_custom(self):
        X = Symbolic()

        @register_verb(FunctionType, compile_proxy=None)
        def add(data, arg):
            arg = arg.compile_to(lambda d, x: getattr(d, x) * 10)
            return data.a + arg

        d1 = lambda: 0
        d1.a = 1

        x = d1 >> add(X.a)
        self.assertEqual(x, 11)

        @register_verb(FunctionType, compile_proxy=True)
        def add2(data, arg):
            arg.compile_to('data')

        with self.assertRaises(ValueError):
            d1 >> add2(X.a)



if __name__ == "__main__":
    unittest.main()
