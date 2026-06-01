"""Tests for the constraint graph."""

from modelmesh.core.variable import Variable
from modelmesh.core.constraint import BinaryConstraint
from modelmesh.decomposition.graph import ConstraintGraph


def _path(n):
    """x0 - x1 - ... - x(n-1) path graph."""
    vs = [Variable(f"v{i}", [1, 2, 3]) for i in range(n)]
    cs = [BinaryConstraint(vs[i], vs[i + 1], lambda a, b: a != b) for i in range(n - 1)]
    return vs, cs


class TestConstraintGraphBasics:
    def test_nodes_and_edges(self):
        vs, cs = _path(4)
        g = ConstraintGraph(vs, cs)
        assert g.num_nodes == 4
        assert g.num_edges == 3

    def test_neighbors_and_degree(self):
        vs, cs = _path(3)
        g = ConstraintGraph(vs, cs)
        # middle node has 2 neighbors, endpoints have 1
        assert g.degree(vs[1]) == 2
        assert g.degree(vs[0]) == 1
        assert set(g.neighbors(vs[1])) == {vs[0], vs[2]}


class TestConnectedComponents:
    def test_single_component(self):
        vs, cs = _path(4)
        g = ConstraintGraph(vs, cs)
        comps = g.connected_components()
        assert len(comps) == 1
        assert len(comps[0]) == 4

    def test_two_components(self):
        a, b, c, d = [Variable(n, [1, 2]) for n in "abcd"]
        cs = [
            BinaryConstraint(a, b, lambda x, y: x != y),
            BinaryConstraint(c, d, lambda x, y: x != y),
        ]
        g = ConstraintGraph([a, b, c, d], cs)
        comps = g.connected_components()
        assert len(comps) == 2


class TestGraphProperties:
    def test_is_tree(self):
        vs, cs = _path(4)  # path is a tree
        g = ConstraintGraph(vs, cs)
        assert g.is_tree()

    def test_cycle_is_not_tree(self):
        a, b, c = [Variable(n, [1, 2, 3]) for n in "abc"]
        cs = [
            BinaryConstraint(a, b, lambda x, y: x != y),
            BinaryConstraint(b, c, lambda x, y: x != y),
            BinaryConstraint(c, a, lambda x, y: x != y),
        ]
        g = ConstraintGraph([a, b, c], cs)
        assert not g.is_tree()

    def test_density(self):
        vs, cs = _path(3)  # 2 edges, max 3 → density 2/3
        g = ConstraintGraph(vs, cs)
        assert abs(g.density() - (2 / 3)) < 1e-9

    def test_density_single_node(self):
        v = Variable("v", [1, 2])
        g = ConstraintGraph([v], [])
        assert g.density() == 0.0

    def test_bandwidth(self):
        vs, cs = _path(3)
        g = ConstraintGraph(vs, cs)
        assert g.bandwidth() >= 1

    def test_cutset_of_cycle(self):
        a, b, c = [Variable(n, [1, 2, 3]) for n in "abc"]
        cs = [
            BinaryConstraint(a, b, lambda x, y: x != y),
            BinaryConstraint(b, c, lambda x, y: x != y),
            BinaryConstraint(c, a, lambda x, y: x != y),
        ]
        g = ConstraintGraph([a, b, c], cs)
        cut = g.cutset()
        # removing >=1 node breaks the triangle cycle
        assert len(cut) >= 1

    def test_cutset_of_tree_is_empty(self):
        vs, cs = _path(4)
        g = ConstraintGraph(vs, cs)
        assert g.cutset() == []
