"""Tests for the solution checker."""

from modelmesh.core.variable import Variable
from modelmesh.core.constraint import BinaryConstraint
from modelmesh.validation.checker import SolutionChecker, ValidationResult


def _problem():
    x = Variable("x", [1, 2, 3])
    y = Variable("y", [1, 2, 3])
    c = BinaryConstraint(x, y, lambda a, b: a < b, name="x<y")
    return x, y, c


class TestValidationResult:
    def test_counts_and_flags(self):
        x, y, c = _problem()
        r = ValidationResult(
            is_valid=False,
            violations=[(c, "bad")],
            unassigned_variables=[x],
            out_of_domain=[(y, 9)],
        )
        assert r.num_violations == 1
        assert not r.is_complete
        assert "Invalid" in r.summary()

    def test_valid_summary(self):
        r = ValidationResult(True, [], [], [])
        assert "Valid solution" in r.summary()
        assert r.is_complete


class TestSolutionChecker:
    def test_valid_complete_solution(self):
        x, y, c = _problem()
        checker = SolutionChecker([x, y], [c])
        result = checker.validate({x: 1, y: 2})
        assert result.is_valid

    def test_incomplete_assignment(self):
        x, y, c = _problem()
        checker = SolutionChecker([x, y], [c])
        result = checker.validate({x: 1})
        assert not result.is_valid
        assert y in result.unassigned_variables

    def test_out_of_domain(self):
        x, y, c = _problem()
        checker = SolutionChecker([x, y], [c])
        result = checker.validate({x: 9, y: 2})
        assert not result.is_valid
        assert (x, 9) in result.out_of_domain

    def test_constraint_violation(self):
        x, y, c = _problem()
        checker = SolutionChecker([x, y], [c])
        result = checker.validate({x: 3, y: 1})
        assert not result.is_valid
        assert result.num_violations == 1

    def test_check_partial(self):
        x, y, c = _problem()
        checker = SolutionChecker([x, y], [c])
        violated = checker.check_partial({x: 3, y: 1})
        assert c in violated
        # partial with only x assigned → no fully-assigned constraint to check
        assert checker.check_partial({x: 1}) == []

    def test_is_consistent(self):
        x, y, c = _problem()
        checker = SolutionChecker([x, y], [c])
        assert checker.is_consistent({x: 1})  # partial OK
        assert not checker.is_consistent({x: 3, y: 1})  # violates x<y
