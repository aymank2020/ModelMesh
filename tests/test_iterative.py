"""Tests for iterative deepening search."""

from modelmesh.core.variable import Variable
from modelmesh.core.constraint import BinaryConstraint
from modelmesh.search.iterative import IterativeDeepeningStrategy


class TestIterativeDeepening:
    def test_finds_solution(self):
        x = Variable("x", [1, 2, 3])
        y = Variable("y", [1, 2, 3])
        c = BinaryConstraint(x, y, lambda a, b: a < b)
        strat = IterativeDeepeningStrategy()
        solutions = list(strat.explore([x, y], [c], {}))
        assert len(solutions) >= 1
        sol = solutions[0]
        assert sol[x] < sol[y]

    def test_nodes_explored_tracked(self):
        x = Variable("x", [1, 2, 3])
        y = Variable("y", [1, 2, 3])
        c = BinaryConstraint(x, y, lambda a, b: a < b)
        strat = IterativeDeepeningStrategy()
        list(strat.explore([x, y], [c], {}))
        assert strat.nodes_explored >= 0

    def test_max_depth_limit(self):
        x = Variable("x", [1, 2, 3])
        y = Variable("y", [1, 2, 3])
        c = BinaryConstraint(x, y, lambda a, b: a < b)
        strat = IterativeDeepeningStrategy(max_depth=2)
        solutions = list(strat.explore([x, y], [c], {}))
        # 2 variables, depth limit 2 → should still find a solution
        assert len(solutions) >= 1
