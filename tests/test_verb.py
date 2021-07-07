import pytest

from pipda.verb import *
from . import identity, f

def test_fast_eval_verb(f, identity):
    func = FastEvalVerb(identity, (), {}, False)
    assert func._pipda_fast_eval() is func

    func = FastEvalVerb(identity, (f, ), {}, False)
    assert func._pipda_fast_eval() is func

    func = FastEvalVerb(identity, (func, ), {}, False)
    assert func._pipda_fast_eval() is func

    func = FastEvalVerb(identity, (1, ), {}, False)
    assert func._pipda_fast_eval() == 1
