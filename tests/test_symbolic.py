import pytest

from pipda.symbolic import *


def test_symbolic():
    f = Symbolic()
    assert str(f) == ""

    assert f._pipda_eval(1) == 1
