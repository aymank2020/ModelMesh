"""Tests for tree decomposition of constraint graphs."""

from modelmesh.core.variable import Variable
from modelmesh.core.constraint import BinaryConstraint
from modelmesh.decomposition.graph import ConstraintGraph
from modelmesh.decomposition.tree_decomp import TreeDecomposition, TreeNode


def _chain(n):
    """Build a chain x0 - x1 - ... - x(n-1) with binary constraints."""
    vs = [Variable(f"v{i}", [1, 2, 3]) for i in range(n)]
    cstrs = [
        BinaryConstraint(vs[i], vs[i + 1], lambda a, b: a != b)
        for i in range(n - 1)
    ]
    return vs, cstrs


class TestTreeNode:
    def test_width(self):
        a = Variable("a", [1, 2])
        b = Variable("b", [1, 2])
        node = TreeNode(bag_id=0, variables={a, b})
        assert node.width == 1  # 2 variables - 1

    def test_repr(self):
        a = Variable("a", [1, 2])
        node = TreeNode(bag_id=0, variables={a})
        assert "TreeNode" in repr(node)


class TestTreeDecomposition:
    def test_decompose_chain(self):
        vs, cstrs = _chain(4)
        graph = ConstraintGraph(vs, cstrs)
        td = TreeDecomposition(graph, vs)
        td.decompose()
        assert td.num_bags == 4
        assert td.root is not None
        # treewidth of a chain is 1
        assert td.width == 1

    def test_root_has_no_parent(self):
        vs, cstrs = _chain(3)
        graph = ConstraintGraph(vs, cstrs)
        td = TreeDecomposition(graph, vs)
        td.decompose()
        assert td.root.parent is None

    def test_bags_cover_all_variables(self):
        vs, cstrs = _chain(4)
        graph = ConstraintGraph(vs, cstrs)
        td = TreeDecomposition(graph, vs)
        td.decompose()
        covered = set()
        for node in td._nodes:
            covered |= node.variables
        assert covered == set(vs)

    def test_single_variable(self):
        v = Variable("v", [1, 2, 3])
        graph = ConstraintGraph([v], [])
        td = TreeDecomposition(graph, [v])
        td.decompose()
        assert td.num_bags == 1
        assert td.width == 0
