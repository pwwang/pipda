import pytest

from pipda import register_verb, VerbCall, Symbolic, evaluate_expr, Context
from pipda.utils import (
    PipeableCallCheckWarning,
    PipeableCallCheckError,
    has_expr,
)


def test_is_piping_verbcall_normal():
    @register_verb(int)
    def iden(x):
        return x

    # AST node in pytest's asserts can't be detected
    # fallbacks to normal call
    with pytest.warns(PipeableCallCheckWarning):
        assert (1 >> iden()) == 1 and isinstance(1 >> iden(), int)

    # So it doesn't work with piping call
    with pytest.warns(PipeableCallCheckWarning):
        assert isinstance(iden(1), VerbCall)

    # AST node can be detected here
    a = 1 >> iden()
    assert a == 1 and isinstance(a, int)

    @register_verb(int, ast_fallback="normal")
    def iden2(x):
        return x

    # no warning
    assert iden2(1) == 1 and isinstance(iden2(1), int)


def test_is_piping_verbcall_piping():
    @register_verb(int, ast_fallback="piping")
    def iden(x):
        return x

    assert isinstance(iden(1), VerbCall)

    assert (1 >> iden()) == 1 and isinstance(1 >> iden(), int)

    a = iden(1)
    assert a == 1 and isinstance(a, int)


def test_is_piping_verbcall_normal_warning():
    @register_verb(int, ast_fallback="normal_warning")
    def iden(x):
        return x

    # AST node in pytest's asserts can't be detected
    # fallbacks to normal call
    with pytest.warns(PipeableCallCheckWarning):
        assert iden(1) == 1 and isinstance(iden(1), int)

    # So it doesn't work with piping call
    with pytest.warns(PipeableCallCheckWarning), pytest.raises(TypeError):
        assert (1 >> iden()) == 1

    # AST node can be detected here
    # No warnings
    a = 1 >> iden()
    assert a == 1 and isinstance(a, int)


def test_is_piping_verbcall_piping_warning():
    @register_verb(int, ast_fallback="piping_warning")
    def iden(x):
        return x

    with pytest.warns(PipeableCallCheckWarning):
        assert isinstance(iden(1), VerbCall)

    with pytest.warns(PipeableCallCheckWarning):
        assert (1 >> iden()) == 1 and isinstance(1 >> iden(), int)

    a = iden(1)
    assert a == 1 and isinstance(a, int)


def test_is_piping_verbcall_raise():
    @register_verb(int, ast_fallback="raise")
    def iden(x):
        return x

    with pytest.raises(PipeableCallCheckError):
        assert iden(1)

    with pytest.raises(PipeableCallCheckError):
        assert 1 >> iden()

    a = iden(1)
    assert a == 1 and isinstance(a, int)

    a = 1 >> iden()
    assert a == 1 and isinstance(a, int)


def test_has_expr():
    f = Symbolic()

    assert has_expr(f)
    assert not has_expr(1)
    assert has_expr(f + 1)
    assert has_expr([f])
    assert has_expr(slice(f, f + 1))
    assert has_expr({"a": f})


def test_evaluate_expr():
    class FakeExpr:
        def _pipda_eval(self, data, context):
            return str(data)

    assert evaluate_expr(2, 1, Context.EVAL) == 2
    assert evaluate_expr(FakeExpr(), 1, Context.EVAL) == "1"
    assert evaluate_expr([FakeExpr()], 1, Context.EVAL) == ["1"]
    assert evaluate_expr(
        slice(FakeExpr(), FakeExpr()), 1, Context.EVAL
    ) == slice("1", "1")
    assert evaluate_expr({"a": FakeExpr()}, 1, Context.EVAL) == {"a": "1"}
