
import pytest
from pipda import Symbolic

@pytest.fixture
def f():
    g = Symbolic()
    return g
