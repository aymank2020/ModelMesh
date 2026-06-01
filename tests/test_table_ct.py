"""Tests for Compact Table (CT) constraint and BitSet."""

from modelmesh.core.variable import Variable
from modelmesh.global_cstr.table_ct import BitSet, CompactTable


class TestBitSet:
    def test_all_ones(self):
        b = BitSet.all_ones(4)
        assert b.count() == 4
        assert not b.is_empty()

    def test_from_indices(self):
        b = BitSet.from_indices(5, [0, 2, 4])
        assert b.contains(0)
        assert not b.contains(1)
        assert b.contains(2)
        assert b.count() == 3

    def test_set_and_clear(self):
        b = BitSet(4)
        assert b.is_empty()
        b.set_bit(1)
        assert b.contains(1)
        b.clear_bit(1)
        assert not b.contains(1)

    def test_intersect_union_complement(self):
        a = BitSet.from_indices(4, [0, 1])
        b = BitSet.from_indices(4, [1, 2])
        assert a.intersect(b).iter_set_bits() == [1]
        assert sorted(a.union(b).iter_set_bits()) == [0, 1, 2]
        assert a.complement().contains(2)

    def test_inplace_ops(self):
        a = BitSet.from_indices(4, [0, 1, 2])
        a.intersect_inplace(BitSet.from_indices(4, [1, 2]))
        assert sorted(a.iter_set_bits()) == [1, 2]
        a.union_inplace(BitSet.from_indices(4, [3]))
        assert 3 in a.iter_set_bits()

    def test_out_of_range_bit(self):
        b = BitSet(3)
        assert not b.contains(5)
        b.set_bit(10)  # ignored
        assert b.is_empty()


class TestCompactTablePositive:
    def _table(self):
        x = Variable("x", [1, 2, 3])
        y = Variable("y", [1, 2, 3])
        allowed = [(1, 1), (2, 2), (3, 3)]  # x == y
        return x, y, CompactTable([x, y], allowed, is_positive=True)

    def test_metadata(self):
        x, y, ct = self._table()
        assert ct.num_tuples == 3
        assert ct.is_positive
        assert ct.variables == [x, y]
        assert ct.valid_tuple_count == 3

    def test_is_satisfied(self):
        x, y, ct = self._table()
        assert ct.is_satisfied({x: 2, y: 2})
        assert not ct.is_satisfied({x: 1, y: 2})
        assert ct.is_satisfied({x: 1})  # partial

    def test_supported_values_with_assignment(self):
        x, y, ct = self._table()
        # y fixed at 2 → x must equal 2
        supported = ct.get_supported_values(x, {y: 2})
        assert supported == {2}

    def test_propagate_prunes(self):
        x, y, ct = self._table()
        y.assign(3)
        pruned = ct.propagate({y: 3})
        # x must be 3
        assert sorted(x.domain.values()) == [3]

    def test_statistics_and_valid_tuples(self):
        x, y, ct = self._table()
        ct.propagate({})
        stats = ct.statistics()
        assert stats["num_tuples"] == 3
        assert stats["num_variables"] == 2
        assert len(ct.get_valid_tuples()) >= 1

    def test_reset(self):
        x, y, ct = self._table()
        ct.propagate({x: 1})
        ct.reset()
        assert ct.valid_tuple_count == 3


class TestCompactTableNegative:
    def test_negative_is_satisfied(self):
        x = Variable("x", [1, 2])
        y = Variable("y", [1, 2])
        forbidden = [(1, 1)]
        ct = CompactTable([x, y], forbidden, is_positive=False)
        assert not ct.is_satisfied({x: 1, y: 1})
        assert ct.is_satisfied({x: 1, y: 2})
