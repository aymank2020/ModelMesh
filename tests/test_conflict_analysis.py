"""Tests for conflict analysis and nogood learning."""

from modelmesh.core.variable import Variable
from modelmesh.core.constraint import BinaryConstraint
from modelmesh.solver.state import SearchState
from modelmesh.learning.conflict_analysis import ConflictAnalyzer
from modelmesh.learning.nogood import Nogood


def _state_with_decisions(variables, pairs):
    """Build a SearchState by making decisions for (var, value) pairs."""
    state = SearchState(variables)
    for var, val in pairs:
        state.make_decision(var, val)
    return state


class TestConflictAnalyzer:
    def test_root_level_failure_empty_nogood(self):
        x = Variable("x", [1, 2])
        analyzer = ConflictAnalyzer([])
        state = SearchState([x])
        nogood, depth = analyzer.analyze(state, x, None)
        # no conflict set → empty nogood, backjump 0
        assert nogood.size == 0
        assert depth == 0

    def test_analyze_with_failed_constraint(self):
        x = Variable("x", [1, 2, 3])
        y = Variable("y", [1, 2, 3])
        z = Variable("z", [1, 2, 3])
        c = BinaryConstraint(x, y, lambda a, b: a != b, name="x!=y")
        analyzer = ConflictAnalyzer([c])
        state = _state_with_decisions([x, y, z], [(x, 1), (y, 2)])
        nogood, depth = analyzer.analyze(state, z, c)
        # conflict involves x and y (assigned, in the constraint)
        assert isinstance(nogood, Nogood)
        assert depth >= 0

    def test_decision_level(self):
        x = Variable("x", [1, 2])
        y = Variable("y", [1, 2])
        analyzer = ConflictAnalyzer([])
        state = _state_with_decisions([x, y], [(x, 1), (y, 2)])
        assert analyzer._decision_level(state, x) == 0
        assert analyzer._decision_level(state, y) == 1

    def test_minimize_small_nogood_unchanged(self):
        x = Variable("x", [1, 2])
        y = Variable("y", [1, 2])
        analyzer = ConflictAnalyzer([])
        ng = Nogood(frozenset({(x.index, 1), (y.index, 2)}))
        state = _state_with_decisions([x, y], [(x, 1), (y, 2)])
        # size <= 2 → returned unchanged
        result = analyzer.minimize_nogood(ng, state)
        assert result.size == 2

    def test_minimize_larger_nogood_returns_nogood(self):
        x = Variable("x", [1, 2])
        y = Variable("y", [1, 2])
        z = Variable("z", [1, 2])
        analyzer = ConflictAnalyzer([])
        ng = Nogood(frozenset({(x.index, 1), (y.index, 2), (z.index, 1)}))
        state = _state_with_decisions([x, y, z], [(x, 1), (y, 2), (z, 1)])
        result = analyzer.minimize_nogood(ng, state)
        assert isinstance(result, Nogood)
        assert result.size >= 2
