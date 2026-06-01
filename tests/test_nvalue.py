"""Tests for the NValue global constraint (distinct value count)."""

import pytest

from modelmesh.core.variable import Variable
from modelmesh.global_cstr.nvalue import NValueConstraint


def _vars(n, lo=1, hi=5):
    return [Variable(f"v{i}", range(lo, hi)) for i in range(n)]


class TestNValueConstruction:
    def test_defaults(self):
        vs = _vars(3)
        c = NValueConstraint(vs)
        assert c.lower_bound == 1
        assert c.upper_bound == 3
        assert c.num_variables == 3

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            NValueConstraint([])

    def test_bad_lower_raises(self):
        with pytest.raises(ValueError):
            NValueConstraint(_vars(2), lower_bound=0)

    def test_upper_lt_lower_raises(self):
        with pytest.raises(ValueError):
            NValueConstraint(_vars(3), lower_bound=3, upper_bound=2)


class TestNValueSatisfaction:
    def test_complete_within_bounds(self):
        vs = _vars(3)
        c = NValueConstraint(vs, lower_bound=2, upper_bound=3)
        # values 1,1,2 → 2 distinct
        assert c.is_satisfied({vs[0]: 1, vs[1]: 1, vs[2]: 2})

    def test_complete_too_few_distinct(self):
        vs = _vars(3)
        c = NValueConstraint(vs, lower_bound=2, upper_bound=3)
        # all same → 1 distinct < lower 2
        assert not c.is_satisfied({vs[0]: 1, vs[1]: 1, vs[2]: 1})

    def test_complete_too_many_distinct(self):
        vs = _vars(3)
        c = NValueConstraint(vs, lower_bound=1, upper_bound=2)
        # 1,2,3 → 3 distinct > upper 2
        assert not c.is_satisfied({vs[0]: 1, vs[1]: 2, vs[2]: 3})

    def test_partial_over_upper_fails(self):
        vs = _vars(3)
        c = NValueConstraint(vs, lower_bound=1, upper_bound=1)
        # two distinct already assigned → exceeds upper 1
        assert not c.is_satisfied({vs[0]: 1, vs[1]: 2})

    def test_partial_feasible(self):
        vs = _vars(3)
        c = NValueConstraint(vs, lower_bound=2, upper_bound=3)
        assert c.is_satisfied({vs[0]: 1})


class TestNValueSupportAndPropagation:
    def test_supported_values_respects_upper(self):
        vs = _vars(3, 1, 5)  # domains 1..4
        c = NValueConstraint(vs, lower_bound=1, upper_bound=1)
        # vs[0] assigned to 2; with upper 1, others must reuse 2
        supported = c.get_supported_values(vs[1], {vs[0]: 2})
        assert supported == {2}

    def test_propagate_upper_bound_forces_existing(self):
        vs = _vars(3, 1, 5)
        c = NValueConstraint(vs, lower_bound=1, upper_bound=1)
        # assign vs[0]=2, propagate → unassigned vars lose all values except 2
        pruned = c.propagate({vs[0]: 2})
        for v in (vs[1], vs[2]):
            assert sorted(v.domain.values()) == [2]
        assert pruned  # something was pruned

    def test_compute_distinct_bounds(self):
        vs = _vars(3, 1, 5)
        c = NValueConstraint(vs)
        lo, hi = c.compute_distinct_bounds({vs[0]: 1})
        assert lo >= 1
        assert hi >= lo

    def test_value_frequencies(self):
        vs = _vars(3)
        c = NValueConstraint(vs)
        freqs = c.get_value_frequencies({vs[0]: 1, vs[1]: 1, vs[2]: 2})
        assert freqs == {1: 2, 2: 1}

    def test_potential_values(self):
        vs = _vars(2, 1, 4)  # 1,2,3
        c = NValueConstraint(vs)
        assert c.get_potential_values() == {1, 2, 3}
