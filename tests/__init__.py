from dpipe import *

def test_case():
    @single_dispatch(list)
    def split(data, num):
        return [[dat for dat in data if dat < num],
                [dat for dat in data if dat > num]]

    x = [1,2,3,4,5] >> split(X[2])
    assert x == [[1,2], [4,5]]
