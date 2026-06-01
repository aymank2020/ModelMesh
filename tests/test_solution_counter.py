"""Tests for solution counting."""

from modelmesh.core.variable import Variable
from modelmesh.core.constraint import BinaryConstraint
from modelmesh.debug.solution_counter import (
    SolutionCounter,
    CountResult,
    count_solutions,
    estimate_solution_count,
)


class TestCountResult:
    def test_count_prefers_exact(self):
        r = CountResult(exact_count=7, upper_bound=20)
        assert r.count == 7
        assert r.has_solutions

    def test_count_falls_back_to_upper(self):
        r = CountResult(exact_count=None, upper_bound=15, lower_bound=2)
        assert r.count == 15
        assert r.has_solutions

    def test_no_solutions(self):
        r = CountResult(exact_count=0)
        assert not r.has_solutions


class TestExactCounting:
    def test_count_lt_constraint(self):
        # x < y over {1,2,3} → pairs: (1,2)(1,3)(2,3) = 3 solutions
        x = Variable("x", [1, 2, 3])
        y = Variable("y", [1, 2, 3])
        c = BinaryConstraint(x, y, lambda a, b: a < b)
        counter = SolutionCounter([x, y], [c])
        result = counter.count()
        assert result.is_exact
        assert result.exact_count == 3

    def test_exact_count_convenience(self):
        x = Variable("x", [1, 2])
        y = Variable("y", [1, 2])
        c = BinaryConstraint(x, y, lambda a, b: a != b)
        # (1,2) and (2,1) = 2 solutions
        assert count_solutions([x, y], [c]) == 2

    def test_unsatisfiable_counts_zero(self):
        x = Variable("x", [1, 2])
        y = Variable("y", [1, 2])
        c1 = BinaryConstraint(x, y, lambda a, b: a < b)
        c2 = BinaryConstraint(x, y, lambda a, b: a > b)
        assert count_solutions([x, y], [c1, c2]) == 0

    def test_independent_components_multiply(self):
        # Two independent x<y components → counts multiply (3 * 3 = 9)
        x1 = Variable("x1", [1, 2, 3])
        y1 = Variable("y1", [1, 2, 3])
        x2 = Variable("x2", [1, 2, 3])
        y2 = Variable("y2", [1, 2, 3])
        c1 = BinaryConstraint(x1, y1, lambda a, b: a < b)
        c2 = BinaryConstraint(x2, y2, lambda a, b: a < b)
        # force component decomposition by setting exact_limit low
        counter = SolutionCounter(
            [x1, y1, x2, y2], [c1, c2], exact_limit=10
        )
        result = counter.count()
        assert result.components_counted >= 2
        assert result.count == 9


class TestEstimation:
    def test_estimate_returns_bounds(self):
        x = Variable("x", range(1, 6))
        y = Variable("y", range(1, 6))
        c = BinaryConstraint(x, y, lambda a, b: a < b)
        lower, upper = estimate_solution_count([x, y], [c], samples=200)
        assert lower >= 0
        assert upper >= lower
