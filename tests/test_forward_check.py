"""Tests for the standalone forward checker."""

from modelmesh.core.variable import Variable
from modelmesh.core.constraint import BinaryConstraint
from modelmesh.solver.forward_check import ForwardChecker, ForwardCheckResult


class TestForwardCheckResult:
    def test_total_pruned(self):
        x = Variable("x", [1, 2, 3])
        r = ForwardCheckResult(consistent=True, pruned={x: [1, 2]})
        assert r.total_pruned == 2


class TestForwardChecker:
    def test_prunes_inconsistent_values(self):
        x = Variable("x", [1, 2, 3])
        y = Variable("y", [1, 2, 3])
        cstr = BinaryConstraint(x, y, lambda a, b: a < b)
        fc = ForwardChecker([x, y], [cstr])
        x.assign(2)
        result = fc.check(x, 2, {x: 2})
        assert result.consistent
        # y must be > 2 → only 3 remains
        assert sorted(y.domain.values()) == [3]
        assert result.total_pruned == 2

    def test_detects_wipeout(self):
        x = Variable("x", [3])
        y = Variable("y", [1, 2, 3])
        cstr = BinaryConstraint(x, y, lambda a, b: a < b)
        fc = ForwardChecker([x, y], [cstr])
        # assign x=3; y needs >3 → wipeout
        x.assign(3)
        result = fc.check(x, 3, {x: 3})
        assert not result.consistent
        assert result.wipeout_variable is y
        assert result.wipeout_constraint is cstr

    def test_skips_assigned_neighbors(self):
        x = Variable("x", [1, 2, 3])
        y = Variable("y", [2])
        cstr = BinaryConstraint(x, y, lambda a, b: a < b)
        fc = ForwardChecker([x, y], [cstr])
        y.assign(2)
        x.assign(1)
        result = fc.check(x, 1, {x: 1, y: 2})
        # y is assigned, so it is skipped; consistent
        assert result.consistent

    def test_check_all_constraints_initial(self):
        x = Variable("x", [1, 2, 3])
        y = Variable("y", [2])
        cstr = BinaryConstraint(x, y, lambda a, b: a < b)
        fc = ForwardChecker([x, y], [cstr])
        y.assign(2)
        result = fc.check_all_constraints({y: 2})
        assert result.consistent
        # x must be < 2 → only 1 remains
        assert sorted(x.domain.values()) == [1]

    def test_get_future_constraints(self):
        x = Variable("x", [1, 2, 3])
        y = Variable("y", [1, 2, 3])
        cstr = BinaryConstraint(x, y, lambda a, b: a < b)
        fc = ForwardChecker([x, y], [cstr])
        future = fc.get_future_constraints(x)
        assert cstr in future

    def test_get_future_constraints_excludes_fully_assigned(self):
        x = Variable("x", [1, 2, 3])
        y = Variable("y", [1, 2, 3])
        cstr = BinaryConstraint(x, y, lambda a, b: a < b)
        fc = ForwardChecker([x, y], [cstr])
        y.assign(2)
        # only neighbor of x is assigned → no future constraints
        assert fc.get_future_constraints(x) == []

    def test_estimate_pruning_power(self):
        x = Variable("x", [1, 2, 3])
        y = Variable("y", [1, 2, 3])
        cstr = BinaryConstraint(x, y, lambda a, b: a < b)
        fc = ForwardChecker([x, y], [cstr])
        # assigning x=3 removes all y>3 candidates → high pruning
        power_high = fc.estimate_pruning_power(x, 3)
        power_low = fc.estimate_pruning_power(x, 1)
        assert power_high >= power_low
