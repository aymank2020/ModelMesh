"""Tests for the SparseSet data structure."""

import pytest

from modelmesh.storage.sparse_set import SparseSet


class TestSparseSetBasics:
    def test_init_full(self):
        s = SparseSet(5)
        assert s.capacity == 5
        assert s.size == 5
        assert not s.is_empty
        assert sorted(s.values()) == [0, 1, 2, 3, 4]

    def test_invalid_capacity(self):
        with pytest.raises(ValueError):
            SparseSet(0)

    def test_contains(self):
        s = SparseSet(4)
        assert s.contains(2)
        assert not s.contains(9)
        assert not s.contains(-1)
        assert 3 in s

    def test_remove(self):
        s = SparseSet(4)
        assert s.remove(1)
        assert not s.contains(1)
        assert s.size == 3
        # removing again returns False
        assert not s.remove(1)

    def test_remove_out_of_range(self):
        s = SparseSet(3)
        assert not s.remove(10)


class TestSparseSetRestore:
    def test_restore_last(self):
        s = SparseSet(4)
        s.remove(2)
        restored = s.restore_last()
        assert restored == 2
        assert s.contains(2)

    def test_restore_last_when_full(self):
        s = SparseSet(2)
        assert s.restore_last() is None

    def test_restore_to_size(self):
        s = SparseSet(5)
        s.remove(0)
        s.remove(1)
        s.remove(2)
        assert s.size == 2
        restored = s.restore_to_size(4)
        assert s.size == 4
        assert len(restored) == 2


class TestSparseSetMinMax:
    def test_min_max(self):
        s = SparseSet(6)
        s.remove(0)
        s.remove(5)
        assert s.min_value() == 1
        assert s.max_value() == 4

    def test_min_empty_raises(self):
        s = SparseSet(2)
        s.remove(0)
        s.remove(1)
        with pytest.raises(ValueError):
            s.min_value()

    def test_max_empty_raises(self):
        s = SparseSet(1)
        s.remove(0)
        with pytest.raises(ValueError):
            s.max_value()


class TestSparseSetDunders:
    def test_len_and_iter(self):
        s = SparseSet(3)
        s.remove(1)
        assert len(s) == 2
        assert sorted(iter(s)) == [0, 2]

    def test_repr_small(self):
        s = SparseSet(3)
        assert "SparseSet" in repr(s)

    def test_repr_large(self):
        s = SparseSet(20)
        assert "cap=20" in repr(s)
