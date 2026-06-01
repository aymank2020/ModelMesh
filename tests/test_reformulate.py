"""Tests for constraint reformulation transforms."""

from modelmesh.core.variable import Variable
from modelmesh.core.constraint import BinaryConstraint, TableConstraint
from modelmesh.global_cstr.alldiff import AllDifferent
from modelmesh.transforms.reformulate import ConstraintReformulator


def _vars(n, lo=1, hi=4):
    return [Variable(f"v{i}", range(lo, hi)) for i in range(n)]


class TestDecomposeAllDiff:
    def test_decompose_count(self):
        vs = _vars(3)
        r = ConstraintReformulator()
        binaries = r.decompose_alldiff(AllDifferent(*vs))
        # n=3 → 3 pairwise constraints
        assert len(binaries) == 3
        assert all(isinstance(c, BinaryConstraint) for c in binaries)

    def test_decomposition_enforces_not_equal(self):
        vs = _vars(2, 1, 4)
        r = ConstraintReformulator()
        binaries = r.decompose_alldiff(AllDifferent(*vs))
        c = binaries[0]
        assert c.is_satisfied({vs[0]: 1, vs[1]: 2})
        assert not c.is_satisfied({vs[0]: 2, vs[1]: 2})


class TestMergeToTable:
    def test_merge_returns_table(self):
        x = Variable("x", [1, 2, 3])
        y = Variable("y", [1, 2, 3])
        c = BinaryConstraint(x, y, lambda a, b: a < b)
        r = ConstraintReformulator()
        table = r.merge_to_table([c], x, y)
        assert isinstance(table, TableConstraint)
        # allowed tuples are exactly the (a,b) with a<b
        assert table.is_satisfied({x: 1, y: 2})

    def test_merge_no_constraints_returns_none(self):
        x = Variable("x", [1, 2])
        y = Variable("y", [1, 2])
        r = ConstraintReformulator()
        assert r.merge_to_table([], x, y) is None


class TestTightenDomains:
    def test_removes_unsupported_values(self):
        x = Variable("x", [1, 2, 3])
        y = Variable("y", [3])
        c = BinaryConstraint(x, y, lambda a, b: a < b)
        r = ConstraintReformulator()
        pruned = r.tighten_domains([x, y], [c])
        # x=3 has no support (no y>3) → removed
        assert x in pruned
        assert not x.domain.contains(3)


class TestImpliedConstraints:
    def test_transitive_less_than(self):
        x = Variable("x", [1, 2, 3])
        y = Variable("y", [1, 2, 3])
        z = Variable("z", [1, 2, 3])
        cxy = BinaryConstraint(x, y, lambda a, b: a < b)
        cyz = BinaryConstraint(y, z, lambda a, b: a < b)
        r = ConstraintReformulator()
        implied = r.implied_constraints([cxy, cyz], [x, y, z])
        # x<y and y<z → x<z implied
        assert any(isinstance(c, BinaryConstraint) for c in implied)
