"""Tests for the arithmetic expression builder."""

from modelmesh.core.variable import Variable
from modelmesh.modeling.expressions import Expr, Sum, Count


def _xy():
    return Variable("x", range(1, 6)), Variable("y", range(1, 6))


class TestExprConstruction:
    def test_single_variable(self):
        x, _ = _xy()
        e = Expr(x)
        assert e.terms == [(1, x)]
        assert e.constant == 0
        assert e.variables == [x]

    def test_constant_only(self):
        e = Expr(constant=5)
        assert e.terms == []
        assert e.constant == 5

    def test_explicit_terms(self):
        x, y = _xy()
        e = Expr(terms=[(2, x), (3, y)], constant=1)
        assert e.terms == [(2, x), (3, y)]
        assert e.constant == 1
        assert e.variables == [x, y]


class TestExprArithmetic:
    def test_add_expressions(self):
        x, y = _xy()
        e = Expr(x) + Expr(y)
        assert e.terms == [(1, x), (1, y)]

    def test_add_constant(self):
        x, _ = _xy()
        e = Expr(x) + 5
        assert e.constant == 5

    def test_radd_constant(self):
        x, _ = _xy()
        e = 5 + Expr(x)
        assert e.constant == 5

    def test_sub_expression(self):
        x, y = _xy()
        e = Expr(x) - Expr(y)
        assert (1, x) in e.terms
        assert (-1, y) in e.terms

    def test_sub_constant(self):
        x, _ = _xy()
        e = Expr(x) - 3
        assert e.constant == -3

    def test_mul_scalar(self):
        x, _ = _xy()
        e = Expr(x) * 4
        assert e.terms == [(4, x)]

    def test_rmul_scalar(self):
        x, _ = _xy()
        e = 4 * Expr(x)
        assert e.terms == [(4, x)]


class TestExprEvaluate:
    def test_evaluate(self):
        x, y = _xy()
        e = Expr(x) * 2 + Expr(y) + 1
        assert e.evaluate({x: 3, y: 4}) == 2 * 3 + 4 + 1

    def test_evaluate_missing_raises(self):
        x, y = _xy()
        e = Expr(x) + Expr(y)
        try:
            e.evaluate({x: 1})
            assert False, "expected ValueError"
        except ValueError:
            pass

    def test_repr_contains_var_names(self):
        x, y = _xy()
        e = Expr(x) * 2 - Expr(y) + 3
        text = repr(e)
        assert "x" in text and "y" in text

    def test_repr_zero(self):
        assert repr(Expr()) == "0"


class TestHelpers:
    def test_sum_helper(self):
        x, y = _xy()
        e = Sum([x, y])
        assert e.terms == [(1, x), (1, y)]

    def test_count_helper(self):
        x, y = _xy()
        e = Count([x, y], 3)
        assert e.variables == [x, y]
