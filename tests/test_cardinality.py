"""Tests for the Global Cardinality Constraint (GCC)."""

from modelmesh.core.variable import Variable
from modelmesh.global_cstr.cardinality import CardinalityConstraint


def _vars(n, lo=1, hi=4):
    return [Variable(f"v{i}", range(lo, hi)) for i in range(n)]


class TestCardinalitySatisfaction:
    def test_full_assignment_within_bounds(self):
        vs = _vars(3)
        # value 1 must appear 1..2 times, value 2 at most 2
        c = CardinalityConstraint(vs, {1: (1, 2), 2: (0, 2)})
        assignment = {vs[0]: 1, vs[1]: 2, vs[2]: 2}
        assert c.is_satisfied(assignment)

    def test_full_assignment_violates_lower(self):
        vs = _vars(3)
        c = CardinalityConstraint(vs, {1: (2, 3)})
        # value 1 appears only once, lower is 2
        assignment = {vs[0]: 1, vs[1]: 2, vs[2]: 3}
        assert not c.is_satisfied(assignment)

    def test_full_assignment_violates_upper(self):
        vs = _vars(3)
        c = CardinalityConstraint(vs, {1: (0, 1)})
        assignment = {vs[0]: 1, vs[1]: 1, vs[2]: 2}
        assert not c.is_satisfied(assignment)

    def test_partial_assignment_ok_until_upper_exceeded(self):
        vs = _vars(3)
        c = CardinalityConstraint(vs, {1: (0, 1)})
        # only one var assigned to 1 -> still ok (partial)
        assert c.is_satisfied({vs[0]: 1})
        # two assigned to 1 -> upper exceeded even partially
        assert not c.is_satisfied({vs[0]: 1, vs[1]: 1})

    def test_value_counts_property(self):
        vs = _vars(2)
        spec = {1: (0, 2)}
        c = CardinalityConstraint(vs, spec)
        assert c.value_counts == spec


class TestCardinalitySupportedValues:
    def test_filters_values_at_upper_bound(self):
        vs = _vars(3)
        c = CardinalityConstraint(vs, {1: (0, 1)})
        # vs[0] assigned to 1, so 1 is at its upper bound for vs[1]
        supported = c.get_supported_values(vs[1], {vs[0]: 1})
        assert 1 not in supported
        assert 2 in supported

    def test_values_outside_spec_always_allowed(self):
        vs = _vars(3, 1, 6)
        c = CardinalityConstraint(vs, {1: (0, 1)})
        supported = c.get_supported_values(vs[0], {})
        # value 5 has no spec -> allowed
        assert 5 in supported


class TestCardinalityFeasibility:
    def test_feasible_initially(self):
        vs = _vars(3)
        c = CardinalityConstraint(vs, {1: (1, 2)})
        assert c.check_feasibility({})

    def test_infeasible_when_upper_exceeded(self):
        vs = _vars(3)
        c = CardinalityConstraint(vs, {1: (0, 1)})
        assert not c.check_feasibility({vs[0]: 1, vs[1]: 1})

    def test_infeasible_when_lower_unreachable(self):
        # value 9 not in any domain, but lower bound requires it
        vs = _vars(2, 1, 4)
        c = CardinalityConstraint(vs, {9: (1, 1)})
        assert not c.check_feasibility({})
