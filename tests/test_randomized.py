"""Tests for randomized search strategies."""

from modelmesh.core.variable import Variable
from modelmesh.core.constraint import BinaryConstraint
from modelmesh.search.randomized import (
    RandomVariableSelector,
    WeightedRandomVariableSelector,
    RandomValueOrderer,
    RandomRestartSearch,
    RandomRestartResult,
)


class TestRandomVariableSelector:
    def test_clamps_randomness(self):
        sel = RandomVariableSelector(randomness=5.0)
        assert sel.randomness == 1.0
        sel2 = RandomVariableSelector(randomness=-1.0)
        assert sel2.randomness == 0.0

    def test_set_randomness(self):
        sel = RandomVariableSelector(randomness=0.2)
        sel.set_randomness(0.8)
        assert sel.randomness == 0.8

    def test_select_returns_unassigned(self):
        a = Variable("a", range(1, 4))
        b = Variable("b", range(1, 4))
        sel = RandomVariableSelector(randomness=1.0, seed=1)
        chosen = sel.select([a, b], [], {})
        assert chosen in (a, b)
        assert sel.selections_made == 1

    def test_random_fraction_tracked(self):
        a = Variable("a", range(1, 4))
        sel = RandomVariableSelector(randomness=1.0, seed=1)
        sel.select([a], [], {})
        assert sel.random_fraction == 1.0

    def test_empty_raises(self):
        sel = RandomVariableSelector(seed=1)
        try:
            sel.select([], [], {})
            assert False, "expected ValueError"
        except ValueError:
            pass


class TestWeightedRandomVariableSelector:
    def test_single_unassigned_returned(self):
        a = Variable("a", range(1, 4))
        sel = WeightedRandomVariableSelector(seed=3)
        assert sel.select([a], [], {}) is a

    def test_selects_some_variable(self):
        a = Variable("a", range(1, 4))
        b = Variable("b", range(1, 8))
        sel = WeightedRandomVariableSelector(seed=3)
        assert sel.select([a, b], [], {}) in (a, b)

    def test_empty_raises(self):
        sel = WeightedRandomVariableSelector(seed=3)
        try:
            sel.select([], [], {})
            assert False
        except ValueError:
            pass

    def test_custom_weight_fn(self):
        a = Variable("a", range(1, 4))
        b = Variable("b", range(1, 4))
        # weight all equal -> still returns a valid var
        sel = WeightedRandomVariableSelector(weight_fn=lambda v, c, s: 1.0, seed=5)
        assert sel.select([a, b], [], {}) in (a, b)


class TestRandomValueOrderer:
    def test_pure_random_returns_all_values(self):
        x = Variable("x", range(1, 6))
        orderer = RandomValueOrderer(bias_strength=0.0, seed=7)
        ordered = orderer.order(x, [], {})
        assert sorted(ordered) == [1, 2, 3, 4, 5]

    def test_single_value(self):
        x = Variable("x", [3])
        orderer = RandomValueOrderer(seed=7)
        assert orderer.order(x, [], {}) == [3]

    def test_biased_ordering_returns_all_values(self):
        x = Variable("x", range(1, 5))
        y = Variable("y", range(1, 5))
        cstr = BinaryConstraint(x, y, lambda a, b: a < b)
        orderer = RandomValueOrderer(bias_strength=1.0, seed=7)
        ordered = orderer.order(x, [cstr], {y: 3})
        assert sorted(ordered) == [1, 2, 3, 4]


class TestRandomRestartSearch:
    def test_solves_simple_csp(self):
        x = Variable("x", range(1, 4))
        y = Variable("y", range(1, 4))
        cstr = BinaryConstraint(x, y, lambda a, b: a < b)
        search = RandomRestartSearch(
            [x, y], [cstr], max_restarts=5, nodes_per_restart=500, base_seed=1
        )
        result = search.solve()
        assert isinstance(result, RandomRestartResult)
        assert result.is_solved
        assert result.solution[x] < result.solution[y]

    def test_unsat_returns_no_solution(self):
        x = Variable("x", [1])
        y = Variable("y", [1])
        cstr = BinaryConstraint(x, y, lambda a, b: a != b)
        search = RandomRestartSearch(
            [x, y], [cstr], max_restarts=3, nodes_per_restart=100, base_seed=1
        )
        result = search.solve()
        assert not result.is_solved
        assert result.num_restarts == 3

    def test_parallel_seeds(self):
        x = Variable("x", range(1, 4))
        y = Variable("y", range(1, 4))
        cstr = BinaryConstraint(x, y, lambda a, b: a < b)
        search = RandomRestartSearch(
            [x, y], [cstr], max_restarts=5, nodes_per_restart=500, base_seed=1
        )
        result = search.solve_parallel_seeds(num_seeds=3)
        assert result.is_solved
        assert result.num_restarts == 3
