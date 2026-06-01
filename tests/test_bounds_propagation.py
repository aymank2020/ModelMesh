"""Tests for the bounds-consistency propagator."""

from modelmesh.core.variable import Variable
from modelmesh.core.constraint import BinaryConstraint
from modelmesh.propagation.bounds_propagator import (
    BoundsChange,
    BoundsPropagationResult,
    VariableBounds,
    BoundsConstraint,
    BoundsPropagator,
)


class TestBoundsChange:
    def test_lower_tightened(self):
        x = Variable("x", range(1, 11))
        ch = BoundsChange(x, old_lower=1, old_upper=10, new_lower=3, new_upper=10)
        assert ch.lower_tightened is True
        assert ch.upper_tightened is False
        assert ch.is_wipeout is False

    def test_upper_tightened(self):
        x = Variable("x", range(1, 11))
        ch = BoundsChange(x, old_lower=1, old_upper=10, new_lower=1, new_upper=4)
        assert ch.upper_tightened is True
        assert ch.lower_tightened is False

    def test_wipeout(self):
        x = Variable("x", range(1, 11))
        ch = BoundsChange(x, old_lower=1, old_upper=10, new_lower=11, new_upper=10)
        assert ch.is_wipeout is True


class TestVariableBounds:
    def test_initial_bounds_from_domain(self):
        x = Variable("x", range(2, 9))
        b = VariableBounds(x)
        assert b.lower == 2
        assert b.upper == 8
        assert b.span == 7
        assert not b.is_fixed
        assert not b.is_empty

    def test_tighten_lower_changes_only_when_stricter(self):
        x = Variable("x", range(1, 11))
        b = VariableBounds(x)
        assert b.tighten_lower(5) is True
        assert b.lower == 5
        assert b.tighten_lower(3) is False  # not stricter
        assert b.lower == 5

    def test_tighten_upper_changes_only_when_stricter(self):
        x = Variable("x", range(1, 11))
        b = VariableBounds(x)
        assert b.tighten_upper(6) is True
        assert b.upper == 6
        assert b.tighten_upper(8) is False
        assert b.upper == 6

    def test_fixed_and_empty(self):
        x = Variable("x", range(1, 11))
        b = VariableBounds(x)
        b.tighten_lower(5)
        b.tighten_upper(5)
        assert b.is_fixed
        b.tighten_lower(6)  # lower 6 > upper 5
        assert b.is_empty

    def test_save_and_restore(self):
        x = Variable("x", range(1, 11))
        b = VariableBounds(x)
        cp = b.save_state()
        b.tighten_lower(4)
        b.tighten_upper(7)
        b.restore_to(cp)
        assert b.lower == 1
        assert b.upper == 10

    def test_reset(self):
        x = Variable("x", range(1, 11))
        b = VariableBounds(x)
        b.tighten_lower(5)
        b.reset()
        assert b.lower == 1
        assert b.upper == 10


class TestBoundsConstraint:
    def test_wraps_constraint(self):
        x = Variable("x", range(1, 6))
        y = Variable("y", range(1, 6))
        cstr = BinaryConstraint(x, y, lambda a, b: a < b)
        bc = BoundsConstraint(cstr)
        assert bc.constraint is cstr
        assert set(bc.variables) == {x, y}


class TestBoundsPropagator:
    def test_get_bounds_initial(self):
        x = Variable("x", range(1, 8))
        y = Variable("y", range(1, 8))
        cstr = BinaryConstraint(x, y, lambda a, b: a < b)
        prop = BoundsPropagator([x, y], [cstr])
        assert prop.get_bounds(x) == (1, 7)
        assert prop.get_bounds(y) == (1, 7)

    def test_propagate_consistent(self):
        x = Variable("x", range(1, 6))
        y = Variable("y", range(1, 6))
        cstr = BinaryConstraint(x, y, lambda a, b: a < b)
        prop = BoundsPropagator([x, y], [cstr])
        result = prop.propagate()
        assert isinstance(result, BoundsPropagationResult)
        assert result.consistent
        assert result.iterations >= 1

    def test_total_tightening_counts_changes(self):
        x = Variable("x", range(1, 6))
        y = Variable("y", range(1, 6))
        cstr = BinaryConstraint(x, y, lambda a, b: a < b)
        prop = BoundsPropagator([x, y], [cstr])
        result = prop.propagate()
        assert result.total_tightening >= 0

    def test_save_and_restore_state(self):
        x = Variable("x", range(1, 6))
        y = Variable("y", range(1, 6))
        cstr = BinaryConstraint(x, y, lambda a, b: a < b)
        prop = BoundsPropagator([x, y], [cstr])
        cps = prop.save_state()
        prop.propagate()
        prop.restore_state(cps)
        # bounds back to initial extremes
        assert prop.get_bounds(x) == (1, 5)
        assert prop.get_bounds(y) == (1, 5)

    def test_reset_restores_initial_bounds(self):
        x = Variable("x", range(1, 6))
        y = Variable("y", range(1, 6))
        cstr = BinaryConstraint(x, y, lambda a, b: a < b)
        prop = BoundsPropagator([x, y], [cstr])
        prop.propagate()
        prop.reset()
        assert prop.get_bounds(x) == (1, 5)

    def test_trigger_var_limits_initial_queue(self):
        x = Variable("x", range(1, 6))
        y = Variable("y", range(1, 6))
        cstr = BinaryConstraint(x, y, lambda a, b: a < b)
        prop = BoundsPropagator([x, y], [cstr])
        result = prop.propagate(trigger_var=x)
        assert result.consistent
