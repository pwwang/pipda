import pytest
from pipda.utils import options_context

from pipda.verb import *
from . import identity, f, add2, iden2

def test_fast_eval_verb(f, identity):
    func = FastEvalVerb(identity, (), {}, False)
    assert func._pipda_fast_eval() is func

    func = FastEvalVerb(identity, (f, ), {}, False)
    assert func._pipda_fast_eval() is func

    func = FastEvalVerb(identity, (func, ), {}, False)
    assert func._pipda_fast_eval() is func

    func = FastEvalVerb(identity, (1, ), {}, False)
    assert func._pipda_fast_eval() == 1


def test_verb_works_with_expression_as_data(add2, iden2, f):
    out = 3 >> add2(
        iden2(f, 1)[0]
    )
    assert out == 6

    globs = {"add2": add2, "iden2": iden2, "f": f}
    source = """out = 3 >> add2(
        (f >> iden2(1))[0]
    )
    """
    with options_context(assume_all_piping=True):
        exec(source, globs)
    assert globs["out"] == 6

    source = """out = add2(3, iden2(f, 1)[0])"""
    with options_context(assume_all_piping=False):
        with pytest.warns(UserWarning):
            exec(source, globs)
    assert globs["out"] == 6
