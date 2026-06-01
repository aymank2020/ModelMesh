"""Tests for probe consistency propagation."""

from modelmesh.core.constraint import BinaryConstraint
from modelmesh.core.variable import Variable
from modelmesh.propagation.probe import ProbePropagator


def _equal(left: int, right: int) -> bool:
    return left == right


def _not_equal(left: int, right: int) -> bool:
    return left != right


class TestProbePropagator:
    def test_reports_inconsistent_when_every_candidate_collapses(self):
        x = Variable("x", [1, 2])
        y = Variable("y", [1, 2])
        constraints = [
            BinaryConstraint(x, y, _equal),
            BinaryConstraint(x, y, _not_equal),
        ]

        result = ProbePropagator([x, y], constraints).propagate({})

        assert not result.consistent
        assert result.pruned == {x: [1, 2]}
        assert x.domain.is_empty
        assert y.domain.values() == frozenset({1, 2})

    def test_incremental_pass_limits_work_to_adjacent_variables(self):
        trigger = Variable("trigger", [1])
        neighbor = Variable("neighbor", [1, 2])
        pinned = Variable("pinned", [1])
        unrelated = Variable("unrelated", [1, 2])
        constraints = [
            BinaryConstraint(trigger, neighbor, _equal),
            BinaryConstraint(neighbor, pinned, _equal),
        ]

        result = ProbePropagator(
            [trigger, neighbor, pinned, unrelated],
            constraints,
        ).propagate_incremental(trigger, {trigger: 1})

        assert result.consistent
        assert result.pruned == {neighbor: [2]}
        assert neighbor.domain.values() == frozenset({1})
        assert unrelated.domain.values() == frozenset({1, 2})

    def test_incremental_pass_reports_empty_adjacent_domain(self):
        trigger = Variable("trigger", [1])
        neighbor = Variable("neighbor", [1])
        neighbor.domain.remove(1)
        constraints = [BinaryConstraint(trigger, neighbor, _equal)]

        result = ProbePropagator([trigger, neighbor], constraints).propagate_incremental(
            trigger,
            {trigger: 1},
        )

        assert not result.consistent
        assert result.pruned == {}
        assert result.revisions == 0
