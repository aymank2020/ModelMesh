"""Tests for linear constraints: SumConstraint and ScalarProduct."""

from modelmesh.core.variable import Variable
from modelmesh.global_cstr.linear import SumConstraint, ScalarProduct, ComparisonOp


def _vars(n, lo=1, hi=6):
    return [Variable(f"v{i}", range(lo, hi)) for i in range(n)]


class TestSumConstraint:
    def test_eq_satisfied(self):
        vs = _vars(3)
        c = SumConstraint(vs, 9, ComparisonOp.EQ)
        assert c.is_satisfied({vs[0]: 3, vs[1]: 3, vs[2]: 3})

    def test_eq_unsatisfied(self):
        vs = _vars(3)
        c = SumConstraint(vs, 9, ComparisonOp.EQ)
        assert not c.is_satisfied({vs[0]: 1, vs[1]: 1, vs[2]: 1})

    def test_partial_is_satisfiable(self):
        vs = _vars(3)
        c = SumConstraint(vs, 9)
        assert c.is_satisfied({vs[0]: 3})

    def test_le_and_ge(self):
        vs = _vars(2)
        le = SumConstraint(vs, 5, ComparisonOp.LE)
        ge = SumConstraint(vs, 5, ComparisonOp.GE)
        assert le.is_satisfied({vs[0]: 2, vs[1]: 2})
        assert not le.is_satisfied({vs[0]: 4, vs[1]: 4})
        assert ge.is_satisfied({vs[0]: 3, vs[1]: 3})
        assert not ge.is_satisfied({vs[0]: 1, vs[1]: 1})

    def test_lt_gt_ne(self):
        vs = _vars(2)
        assert SumConstraint(vs, 5, ComparisonOp.LT).is_satisfied({vs[0]: 1, vs[1]: 2})
        assert SumConstraint(vs, 5, ComparisonOp.GT).is_satisfied({vs[0]: 3, vs[1]: 3})
        assert SumConstraint(vs, 5, ComparisonOp.NE).is_satisfied({vs[0]: 1, vs[1]: 1})

    def test_target_and_op_properties(self):
        vs = _vars(2)
        c = SumConstraint(vs, 7, ComparisonOp.LE)
        assert c.target == 7
        assert c.op == ComparisonOp.LE

    def test_supported_values_all_others_assigned(self):
        vs = _vars(2, 1, 6)
        c = SumConstraint(vs, 6, ComparisonOp.EQ)
        # vs[1] fixed at 4 -> vs[0] must be 2
        supported = c.get_supported_values(vs[0], {vs[1]: 4})
        assert supported == {2}

    def test_supported_values_bounds_based(self):
        vs = _vars(3, 1, 6)  # each in 1..5
        c = SumConstraint(vs, 9, ComparisonOp.EQ)
        # no other assigned: each value feasible if 9 reachable
        supported = c.get_supported_values(vs[0], {})
        assert supported  # non-empty
        assert all(1 <= v <= 5 for v in supported)


class TestScalarProduct:
    def test_length_mismatch_raises(self):
        vs = _vars(2)
        try:
            ScalarProduct(vs, [1], 5)
            assert False, "expected ValueError"
        except ValueError:
            pass

    def test_eq_satisfied(self):
        vs = _vars(2, 1, 10)
        c = ScalarProduct(vs, [2, 3], 13)  # 2*x + 3*y == 13
        assert c.is_satisfied({vs[0]: 2, vs[1]: 3})
        assert not c.is_satisfied({vs[0]: 1, vs[1]: 1})

    def test_partial_satisfiable(self):
        vs = _vars(2, 1, 10)
        c = ScalarProduct(vs, [2, 3], 13)
        assert c.is_satisfied({vs[0]: 2})

    def test_properties(self):
        vs = _vars(2)
        c = ScalarProduct(vs, [2, -1], 4)
        assert c.coefficients == [2, -1]
        assert c.target == 4

    def test_supported_values_for_balanced_pair(self):
        vs = _vars(2, 1, 6)  # 1..5
        c = ScalarProduct(vs, [1, -1], 0, ComparisonOp.EQ)
        supported = c.get_supported_values(vs[0], {vs[1]: 3})
        assert supported == {3}
