"""Tests for the consistency-level checker."""

from modelmesh.core.variable import Variable
from modelmesh.core.constraint import BinaryConstraint, UnaryConstraint
from modelmesh.validation.consistency import (
    ConsistencyChecker,
    ConsistencyReport,
    ConsistencyLevel,
)


class TestConsistencyChecker:
    def test_arc_consistent_problem(self):
        x = Variable("x", [1, 2, 3])
        y = Variable("y", [1, 2, 3])
        # already arc consistent: every x has a y!=x and vice versa
        c = BinaryConstraint(x, y, lambda a, b: a != b)
        checker = ConsistencyChecker([x, y], [c])
        report = checker.full_check()
        assert isinstance(report, ConsistencyReport)
        assert report.arc_consistent
        assert report.is_feasible

    def test_bounds_inconsistency_detected(self):
        # x in {1,2,3}, y fixed {3}, x<y leaves x's max (3) unsupported
        x = Variable("x", [1, 2, 3])
        y = Variable("y", [3])
        c = BinaryConstraint(x, y, lambda a, b: a < b)
        checker = ConsistencyChecker([x, y], [c])
        report = checker.full_check()
        # x's max value 3 has no support (no y>3) → bounds inconsistent
        assert not report.bounds_consistent
        assert report.level == ConsistencyLevel.ARC

    def test_node_inconsistency(self):
        x = Variable("x", [1, 2, 3])
        # unary says value must be > 5, but domain has none → node inconsistent
        u = UnaryConstraint(x, lambda v: v > 5)
        checker = ConsistencyChecker([x], [u])
        report = checker.full_check()
        assert not report.node_consistent
        assert report.level == ConsistencyLevel.NONE

    def test_detect_singleton_propagation(self):
        x = Variable("x", [1, 2, 3])
        y = Variable("y", [2, 3])
        # shrink x to singleton
        x.domain.remove(2)
        x.domain.remove(3)
        c = BinaryConstraint(x, y, lambda a, b: a != b)
        checker = ConsistencyChecker([x, y], [c])
        singletons = checker.detect_singleton_propagation()
        assert (x, 1) in singletons

    def test_report_feasible_flag(self):
        x = Variable("x", [1, 2])
        y = Variable("y", [1, 2])
        c = BinaryConstraint(x, y, lambda a, b: a != b)
        checker = ConsistencyChecker([x, y], [c])
        report = checker.full_check()
        assert report.is_feasible
