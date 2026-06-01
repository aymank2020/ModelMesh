"""Tests for the AllDifferent global constraint."""

from modelmesh.core.variable import Variable
from modelmesh.global_cstr.alldiff import AllDifferent


def _vars(n, lo=1, hi=5):
    return [Variable(f"v{i}", range(lo, hi)) for i in range(n)]


class TestAllDifferentSatisfaction:
    def test_distinct_satisfied(self):
        vs = _vars(3)
        c = AllDifferent(*vs)
        assert c.is_satisfied({vs[0]: 1, vs[1]: 2, vs[2]: 3})

    def test_duplicate_unsatisfied(self):
        vs = _vars(3)
        c = AllDifferent(*vs)
        assert not c.is_satisfied({vs[0]: 1, vs[1]: 1, vs[2]: 3})

    def test_partial_distinct_ok(self):
        vs = _vars(3)
        c = AllDifferent(*vs)
        assert c.is_satisfied({vs[0]: 1})


class TestAllDifferentSupport:
    def test_supported_excludes_taken(self):
        vs = _vars(3, 1, 5)  # 1..4
        c = AllDifferent(*vs)
        supported = c.get_supported_values(vs[0], {vs[1]: 2, vs[2]: 3})
        assert 2 not in supported
        assert 3 not in supported
        assert 1 in supported and 4 in supported


class TestAllDifferentPropagation:
    def test_propagate_assignment_removes_value(self):
        vs = _vars(3, 1, 5)
        c = AllDifferent(*vs)
        pruned = c.propagate_assignment(vs[0], 2)
        assert vs[1] in pruned and 2 in pruned[vs[1]]
        assert not vs[1].domain.contains(2)
        assert not vs[2].domain.contains(2)

    def test_bound_consistency_prune_removes_assigned(self):
        vs = _vars(3, 1, 5)
        vs[0].assign(2)
        c = AllDifferent(*vs)
        pruned = c.bound_consistency_prune()
        # value 2 (assigned to vs[0]) removed from the others
        assert not vs[1].domain.contains(2)
        assert not vs[2].domain.contains(2)


class TestAllDifferentHallSet:
    def test_hall_set_ok(self):
        vs = _vars(3, 1, 5)  # 3 vars, 4 values → fine
        c = AllDifferent(*vs)
        assert c.check_hall_set()

    def test_hall_set_violation(self):
        # 3 vars all sharing domain {1,2} → pigeonhole violation
        a = Variable("a", [1, 2])
        b = Variable("b", [1, 2])
        d = Variable("d", [1, 2])
        c = AllDifferent(a, b, d)
        assert not c.check_hall_set()

    def test_hall_set_all_assigned(self):
        vs = _vars(2)
        for i, v in enumerate(vs):
            v.assign(i + 1)
        c = AllDifferent(*vs)
        assert c.check_hall_set()
