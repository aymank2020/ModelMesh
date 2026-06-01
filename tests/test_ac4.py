"""Tests for the AC-4 fine-grained arc consistency propagator."""

from modelmesh.core.variable import Variable
from modelmesh.core.constraint import BinaryConstraint
from modelmesh.propagation.ac4 import AC4Propagator, SupportEntry
from modelmesh.propagation.ac3 import AC3Propagator


class TestSupportEntry:
    def test_starts_empty(self):
        e = SupportEntry()
        assert e.supporters == set()


class TestAC4Initialize:
    def test_basic_pruning(self):
        x = Variable("x", [1, 2, 3])
        y = Variable("y", [1, 2, 3])
        cstr = BinaryConstraint(x, y, lambda a, b: a < b)
        ac4 = AC4Propagator([x, y], [cstr])
        result = ac4.initialize({})
        assert result.consistent
        # x=3 has no support (no y>3); y=1 has no support (no x<1)
        assert not x.domain.contains(3)
        assert not y.domain.contains(1)

    def test_wipeout_detected(self):
        x = Variable("x", [1])
        y = Variable("y", [1])
        cstr = BinaryConstraint(x, y, lambda a, b: a != b)
        ac4 = AC4Propagator([x, y], [cstr])
        result = ac4.initialize({})
        assert not result.consistent

    def test_revisions_non_negative(self):
        x = Variable("x", [1, 2, 3])
        y = Variable("y", [1, 2, 3])
        cstr = BinaryConstraint(x, y, lambda a, b: a != b)
        ac4 = AC4Propagator([x, y], [cstr])
        result = ac4.initialize({})
        assert result.revisions >= 0

    def test_ac4_agrees_with_ac3(self):
        # Same problem solved by AC-3 and AC-4 should yield identical domains.
        def build():
            a = Variable("a", [1, 2, 3, 4])
            b = Variable("b", [1, 2, 3, 4])
            c = BinaryConstraint(a, b, lambda u, v: u + v == 5)
            return a, b, c

        a3, b3, c3 = build()
        AC3Propagator([a3, b3], [c3]).propagate({})

        a4, b4, c4 = build()
        AC4Propagator([a4, b4], [c4]).initialize({})

        assert a3.domain.values() == a4.domain.values()
        assert b3.domain.values() == b4.domain.values()


class TestAC4Incremental:
    def test_propagate_removal_after_init(self):
        x = Variable("x", [1, 2, 3])
        y = Variable("y", [1, 2, 3])
        cstr = BinaryConstraint(x, y, lambda a, b: a == b)
        ac4 = AC4Propagator([x, y], [cstr])
        ac4.initialize({})
        # remove a value from x and propagate
        x.domain.remove(2)
        result = ac4.propagate_removal(x, 2, {})
        assert result.consistent

    def test_propagate_removal_initializes_if_needed(self):
        x = Variable("x", [1, 2, 3])
        y = Variable("y", [1, 2, 3])
        cstr = BinaryConstraint(x, y, lambda a, b: a < b)
        ac4 = AC4Propagator([x, y], [cstr])
        # called before initialize -> triggers initialize internally
        result = ac4.propagate_removal(x, 1, {})
        assert result.consistent
