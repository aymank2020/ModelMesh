"""Tests for combinatorial modeling helpers."""

from modelmesh.modeling.combinatorial import (
    PermutationModel,
    SubsetSelectionModel,
    PartitionModel,
    BinPackingModel,
    BinPackingItem,
    Bin,
)


class TestPermutationModel:
    def test_build_and_solve(self):
        perm = PermutationModel(n=3)
        assert len(perm.variables) == 3
        sol = perm.solve()
        assert sol is not None
        assert sorted(sol) == [0, 1, 2]

    def test_bad_values_raises(self):
        try:
            PermutationModel(n=3, values=[1, 2])
            assert False, "expected ValueError"
        except ValueError:
            pass

    def test_fixed_point(self):
        perm = PermutationModel(n=3)
        perm.add_fixed_point(0, 2)
        sol = perm.solve()
        assert sol is not None
        assert sol[0] == 2

    def test_position_constraint(self):
        perm = PermutationModel(n=3)
        perm.add_position_constraint(0, [0, 1])
        sol = perm.solve()
        assert sol[0] in (0, 1)

    def test_solve_all_counts_permutations(self):
        perm = PermutationModel(n=3)
        all_perms = perm.solve_all()
        # 3! = 6 permutations
        assert len(all_perms) == 6


class TestSubsetSelectionModel:
    def test_select_exact_count(self):
        subset = SubsetSelectionModel(items=4, select_count=2)
        assert len(subset.indicators) == 4
        sel = subset.solve()
        assert sel is not None
        assert len(sel) == 2

    def test_mutual_exclusion(self):
        subset = SubsetSelectionModel(items=4, select_count=2)
        subset.add_mutual_exclusion(0, 1)
        sel = subset.solve()
        assert not (0 in sel and 1 in sel)

    def test_implication(self):
        subset = SubsetSelectionModel(items=4, select_count=2)
        subset.add_implication(0, 1)
        sel = subset.solve()
        if 0 in sel:
            assert 1 in sel

    def test_solve_all(self):
        subset = SubsetSelectionModel(items=3, select_count=1)
        results = subset.solve_all()
        # choose 1 of 3 → 3 subsets
        assert len(results) == 3


class TestPartitionModel:
    def test_build_and_solve(self):
        part = PartitionModel(items=4, num_groups=2)
        assert len(part.group_vars) == 4
        groups = part.solve()
        assert groups is not None
        assert len(groups) == 2
        # every item placed exactly once
        total = sum(len(g) for g in groups)
        assert total == 4

    def test_same_group(self):
        part = PartitionModel(items=4, num_groups=2)
        part.add_same_group(0, 1)
        groups = part.solve()
        # items 0 and 1 in the same group
        for g in groups:
            if 0 in g:
                assert 1 in g

    def test_different_group(self):
        part = PartitionModel(items=4, num_groups=2)
        part.add_different_group(0, 1)
        groups = part.solve()
        for g in groups:
            if 0 in g:
                assert 1 not in g


class TestBinPackingModel:
    def test_add_items_and_solve(self):
        bp = BinPackingModel(num_bins=2, bin_capacity=10)
        bp.add_item("a", size=4)
        bp.add_item("b", size=5)
        assert bp.num_items == 2
        assert bp.num_bins == 2
        sol = bp.solve()
        assert sol is not None
        assert set(sol.keys()) == {"a", "b"}

    def test_oversized_pair_different_bins(self):
        bp = BinPackingModel(num_bins=2, bin_capacity=10)
        a = bp.add_item("a", size=6)
        b = bp.add_item("b", size=6)  # 6+6 > 10 → must differ
        sol = bp.solve()
        assert sol is not None
        assert sol["a"] != sol["b"]

    def test_packing_summary(self):
        bp = BinPackingModel(num_bins=2, bin_capacity=10)
        bp.add_item("a", size=4)
        bp.add_item("b", size=5)
        sol = bp.solve()
        summary = bp.get_packing_summary(sol)
        assert "Bin Packing Solution" in summary


class TestDataclasses:
    def test_bin_packing_item(self):
        item = BinPackingItem(item_id=0, name="x", size=3)
        assert item.size == 3
        assert item.bin_var is None

    def test_bin(self):
        b = Bin(bin_id=1, name="bin_1", capacity=10)
        assert b.capacity == 10
