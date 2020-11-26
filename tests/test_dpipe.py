import unittest
from dpipe import *

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
        x = [1,2,3] >> add(X.__reversed__())
        self.assertEqual(x, [4,4,4])

        with self.assertRaises(TypeError):
            'abc' >> add('def')

    def test_int(self):
        _ = Symbolic()

        @single_dispatch(int)
        def add(data, num):
            """Split a list into two lists by one of the numbers in the list"""
            return data + num

        self.assertEqual(1 >> add(1), 2)
        self.assertEqual(2 >> add(_), 4)
        self.assertEqual(2 >> add(_ ** 3), 10)

if __name__ == "__main__":
    unittest.main()
