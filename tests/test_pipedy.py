import unittest
from pipda import *

class TestCase(unittest.TestCase):

    def test_case(self):
        X = Symbolic()

        @single_dispatch(list)
        def split(data, num):
            """Split a list into two lists by one of the numbers in the list"""
            return [[dat for dat in data if dat < num],
                    [dat for dat in data if dat > num]]

        @single_dispatch(list)
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

        @single_dispatch(int)
        def add(data, num):
            """Split a list into two lists by one of the numbers in the list"""
            return data + num

        self.assertEqual(1 >> add(1), 2)
        self.assertEqual(2 >> add(X), 4)
        self.assertEqual(2 >> add(X ** 3), 10)

    def test_register_func(self):
        X = Symbolic()
        self.assertEqual(repr(X), '<Symbolic:X>')

        @single_dispatch(dict)
        def filter(data, keys):
            return {key: val for key, val in data.items() if key in keys}

        @single_dispatch(dict)
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


if __name__ == "__main__":
    unittest.main()
