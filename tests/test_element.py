"""Tests for the Element global constraint: array[index] == value."""

from modelmesh.core.variable import Variable
from modelmesh.global_cstr.element import ElementConstraint


def _setup(array=(10, 20, 30)):
    index = Variable("idx", range(0, len(array)))
    value = Variable("val", [10, 20, 30, 99])
    return index, list(array), value


class TestElementSatisfaction:
    def test_satisfied_when_matches(self):
        idx, arr, val = _setup()
        c = ElementConstraint(idx, arr, val)
        assert c.is_satisfied({idx: 1, val: 20})

    def test_unsatisfied_when_mismatch(self):
        idx, arr, val = _setup()
        c = ElementConstraint(idx, arr, val)
        assert not c.is_satisfied({idx: 1, val: 30})

    def test_out_of_bounds_index_unsatisfied(self):
        idx = Variable("idx", range(0, 5))
        val = Variable("val", [10, 20, 30])
        c = ElementConstraint(idx, [10, 20, 30], val)
        assert not c.is_satisfied({idx: 4, val: 10})

    def test_partial_assignment_is_satisfiable(self):
        idx, arr, val = _setup()
        c = ElementConstraint(idx, arr, val)
        assert c.is_satisfied({idx: 1})

    def test_properties(self):
        idx, arr, val = _setup()
        c = ElementConstraint(idx, arr, val)
        assert c.index_var is idx
        assert c.value_var is val
        assert c.array == [10, 20, 30]


class TestElementSupportedValues:
    def test_supported_indices_with_known_value(self):
        idx, arr, val = _setup()
        c = ElementConstraint(idx, arr, val)
        # value fixed at 30 -> only index 2 supported
        supported = c.get_supported_values(idx, {val: 30})
        assert supported == {2}

    def test_supported_values_with_known_index(self):
        idx, arr, val = _setup()
        c = ElementConstraint(idx, arr, val)
        # index fixed at 0 -> value must be 10
        supported = c.get_supported_values(val, {idx: 0})
        assert supported == {10}

    def test_supported_values_without_assignment(self):
        idx, arr, val = _setup()
        c = ElementConstraint(idx, arr, val)
        supported = c.get_supported_values(val, {})
        # all array entries are reachable and in value's domain
        assert supported == {10, 20, 30}

    def test_unknown_variable_raises(self):
        idx, arr, val = _setup()
        other = Variable("other", [1, 2])
        c = ElementConstraint(idx, arr, val)
        try:
            c.get_supported_values(other, {})
            assert False, "expected ValueError"
        except ValueError:
            pass


class TestElementPropagation:
    def test_propagate_index_removes_out_of_bounds(self):
        idx = Variable("idx", range(0, 6))  # 0..5
        val = Variable("val", [10, 20, 30])
        c = ElementConstraint(idx, [10, 20, 30], val)
        pruned = c.propagate_index()
        # indices 3,4,5 are out of bounds -> removed
        assert idx in pruned
        assert set(pruned[idx]) == {3, 4, 5}
        assert sorted(idx.domain.values()) == [0, 1, 2]
