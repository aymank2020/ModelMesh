"""Tests for propagation queue ordering policies."""

from collections import deque

from modelmesh.core.variable import Variable
from modelmesh.core.constraint import BinaryConstraint
from modelmesh.propagation.queue_policy import (
    FIFOPolicy,
    SmallDomainFirstPolicy,
    HighWeightFirstPolicy,
    ConstraintArityPolicy,
)


def _arc():
    x = Variable("x", range(1, 6))
    y = Variable("y", range(1, 4))
    cstr = BinaryConstraint(x, y, lambda a, b: a != b)
    return x, y, cstr


class TestFIFOPolicy:
    def test_preserves_insertion_order(self):
        x, y, cstr = _arc()
        arcs = [(x, cstr), (y, cstr)]
        q = FIFOPolicy().create_queue(arcs)
        assert isinstance(q, deque)
        assert list(q) == arcs

    def test_priority_is_constant(self):
        x, y, cstr = _arc()
        pol = FIFOPolicy()
        assert pol.priority(x, cstr) == pol.priority(y, cstr) == 0.0

    def test_empty_arcs(self):
        assert list(FIFOPolicy().create_queue([])) == []


class TestSmallDomainFirstPolicy:
    def test_smaller_domain_comes_first(self):
        x, y, cstr = _arc()  # x has 5 values, y has 3
        q = SmallDomainFirstPolicy().create_queue([(x, cstr), (y, cstr)])
        # y (domain 3) should be ordered before x (domain 5)
        assert q[0][0] is y
        assert q[1][0] is x

    def test_priority_equals_domain_size(self):
        x, y, cstr = _arc()
        pol = SmallDomainFirstPolicy()
        assert pol.priority(x, cstr) == float(x.domain_size)
        assert pol.priority(y, cstr) == float(y.domain_size)


class TestHighWeightFirstPolicy:
    def test_higher_weight_comes_first(self):
        x, y, cstr = _arc()
        x.increment_weight()
        x.increment_weight()
        y.increment_weight()
        q = HighWeightFirstPolicy().create_queue([(y, cstr), (x, cstr)])
        assert q[0][0] is x  # weight 2 before weight 1

    def test_priority_is_negative_weight(self):
        x, y, cstr = _arc()
        x.increment_weight()
        pol = HighWeightFirstPolicy()
        assert pol.priority(x, cstr) == -x.weight


class TestConstraintArityPolicy:
    def test_higher_arity_comes_first(self):
        x = Variable("x", range(1, 4))
        y = Variable("y", range(1, 4))
        z = Variable("z", range(1, 4))
        binary = BinaryConstraint(x, y, lambda a, b: a != b)
        ternary = BinaryConstraint(y, z, lambda a, b: a != b)
        # Force arity difference by faking a higher-arity constraint via TableConstraint
        from modelmesh.core.constraint import TableConstraint

        tern = TableConstraint([x, y, z], {(1, 2, 3)})
        q = ConstraintArityPolicy().create_queue([(x, binary), (x, tern)])
        # tern arity 3 should come before binary arity 2
        assert q[0][1] is tern

    def test_priority_is_negative_arity(self):
        x, y, cstr = _arc()
        pol = ConstraintArityPolicy()
        assert pol.priority(x, cstr) == -float(cstr.arity)
