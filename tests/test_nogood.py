"""Tests for nogood recording and storage."""

from modelmesh.core.variable import Variable
from modelmesh.learning.nogood import Nogood, NogoodStore


def _vars(n):
    return [Variable(f"v{i}", [1, 2, 3]) for i in range(n)]


class TestNogood:
    def test_from_dict(self):
        a, b = _vars(2)
        ng = Nogood.from_dict({a: 1, b: 2}, depth=3)
        assert ng.size == 2
        assert ng.learned_at_depth == 3

    def test_subsumes(self):
        a, b = _vars(2)
        small = Nogood(frozenset({(a.index, 1)}))
        big = Nogood(frozenset({(a.index, 1), (b.index, 2)}))
        assert small.subsumes(big)
        assert not big.subsumes(small)

    def test_is_violated_by(self):
        a, b = _vars(2)
        ng = Nogood.from_dict({a: 1, b: 2})
        assert ng.is_violated_by({a: 1, b: 2})
        assert not ng.is_violated_by({a: 1, b: 3})

    def test_get_asserting_variable(self):
        a, b = _vars(2)
        ng = Nogood.from_dict({a: 1, b: 2})
        # only a assigned → b is the single unassigned → asserting
        asserting = ng.get_asserting_variable({a: 1})
        assert asserting == b.index

    def test_no_asserting_when_multiple_unassigned(self):
        a, b = _vars(2)
        ng = Nogood.from_dict({a: 1, b: 2})
        assert ng.get_asserting_variable({}) is None


class TestNogoodStore:
    def test_add_and_size(self):
        a, b = _vars(2)
        store = NogoodStore()
        assert store.add(Nogood.from_dict({a: 1, b: 2}))
        assert store.size == 1
        assert store.total_added == 1

    def test_subsumed_not_added(self):
        a, b = _vars(2)
        store = NogoodStore()
        store.add(Nogood(frozenset({(a.index, 1)})))
        # a more specific nogood is subsumed → not added
        added = store.add(Nogood(frozenset({(a.index, 1), (b.index, 2)})))
        assert not added
        assert store.size == 1

    def test_new_general_removes_specific(self):
        a, b = _vars(2)
        store = NogoodStore()
        store.add(Nogood(frozenset({(a.index, 1), (b.index, 2)})))
        # adding more general nogood removes the specific one
        store.add(Nogood(frozenset({(a.index, 1)})))
        assert store.size == 1

    def test_eviction_at_capacity(self):
        a = _vars(1)[0]
        store = NogoodStore(capacity=2)
        store.add(Nogood(frozenset({(a.index, 1)})))
        store.add(Nogood(frozenset({(a.index, 2)})))
        store.add(Nogood(frozenset({(a.index, 3)})))
        # capacity 2 → oldest evicted
        assert store.size <= 2

    def test_check_conflict(self):
        a, b = _vars(2)
        store = NogoodStore()
        store.add(Nogood.from_dict({a: 1, b: 2}))
        hit = store.check_conflict({a: 1, b: 2})
        assert hit is not None
        assert store.total_used == 1

    def test_get_unit_nogoods(self):
        a, b = _vars(2)
        store = NogoodStore()
        store.add(Nogood.from_dict({a: 1, b: 2}))
        units = store.get_unit_nogoods({a: 1})
        assert len(units) == 1
        ng, var_idx, val = units[0]
        assert var_idx == b.index
        assert val == 2

    def test_clear_and_len(self):
        a = _vars(1)[0]
        store = NogoodStore()
        store.add(Nogood(frozenset({(a.index, 1)})))
        assert len(store) == 1
        store.clear()
        assert len(store) == 0
