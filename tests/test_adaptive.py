"""Tests for the adaptive (bandit-based) heuristic selector."""

from modelmesh.core.variable import Variable
from modelmesh.core.constraint import BinaryConstraint
from modelmesh.optimizer.adaptive import AdaptiveHeuristic, HeuristicStats
from modelmesh.heuristics.variable_ordering import MRVSelector, DegreeSelector


class TestHeuristicStats:
    def test_defaults(self):
        s = HeuristicStats(name="X")
        assert s.selections == 0
        assert s.avg_nodes_per_solution == float("inf")
        assert s.backtrack_ratio == 0.0
        assert s.score == float("inf")  # unselected → infinite (explore)

    def test_backtrack_ratio(self):
        s = HeuristicStats(name="X", total_nodes=10, total_backtracks=4, selections=1)
        assert s.backtrack_ratio == 0.4

    def test_avg_nodes_per_solution(self):
        s = HeuristicStats(name="X", total_nodes=20, solutions_found=4)
        assert s.avg_nodes_per_solution == 5.0

    def test_score_finite_after_selection(self):
        s = HeuristicStats(name="X", selections=5, total_nodes=10, total_backtracks=2)
        assert s.score < float("inf")


class TestAdaptiveHeuristic:
    def test_default_heuristics(self):
        a = AdaptiveHeuristic()
        assert len(a.stats) == 3
        assert isinstance(a.current_heuristic, MRVSelector)

    def test_custom_heuristics(self):
        a = AdaptiveHeuristic(heuristics=[MRVSelector(), DegreeSelector()])
        assert len(a.stats) == 2

    def test_select_returns_variable_and_counts(self):
        x = Variable("x", [1, 2, 3])
        y = Variable("y", [1, 2])
        c = BinaryConstraint(x, y, lambda a, b: a != b)
        a = AdaptiveHeuristic(heuristics=[MRVSelector()])
        chosen = a.select([x, y], [c], {})
        assert chosen in (x, y)
        assert a.stats[0].selections == 1

    def test_record_events(self):
        a = AdaptiveHeuristic(heuristics=[MRVSelector()])
        a.record_node()
        a.record_backtrack()
        a.record_solution()
        a.record_wipeout()
        assert a.stats[0].total_nodes == 1
        assert a.stats[0].total_backtracks == 1
        assert a.stats[0].solutions_found == 1
        assert a.stats[0].wipeouts_caused == 1

    def test_switch_after_window(self):
        x = Variable("x", [1, 2, 3])
        a = AdaptiveHeuristic(heuristics=[MRVSelector(), DegreeSelector()], window_size=2)
        # make enough selections to trigger a switch
        for _ in range(3):
            a.select([x], [], {})
        # after switching, current heuristic is whichever has best UCB score
        assert a.current_heuristic in a._heuristics

    def test_get_best_heuristic(self):
        a = AdaptiveHeuristic(heuristics=[MRVSelector()])
        name, score = a.get_best_heuristic()
        assert name == "MRVSelector"
        assert score >= 0 or score == float("inf")

    def test_reset_stats(self):
        x = Variable("x", [1, 2, 3])
        a = AdaptiveHeuristic(heuristics=[MRVSelector()])
        a.select([x], [], {})
        a.record_node()
        a.reset_stats()
        assert a.stats[0].selections == 0
        assert a.stats[0].total_nodes == 0
