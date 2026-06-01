"""Tests for the static model checker."""

from modelmesh.core.variable import Variable
from modelmesh.core.constraint import BinaryConstraint, UnaryConstraint
from modelmesh.validation.model_checker import ModelChecker, CheckResult


class TestCheckResult:
    def test_flags(self):
        r = CheckResult(is_valid=True)
        assert not r.has_issues
        assert not r.has_warnings
        r.issues.append("x")
        r.warnings.append("w")
        assert r.has_issues
        assert r.has_warnings

    def test_summary_valid(self):
        r = CheckResult(is_valid=True)
        assert "VALID" in r.summary()

    def test_summary_lists_issues(self):
        r = CheckResult(is_valid=False, issues=["bad domain"])
        text = r.summary()
        assert "INVALID" in text
        assert "bad domain" in text


class TestConsistencyChecks:
    def test_valid_model(self):
        x = Variable("x", [1, 2, 3])
        y = Variable("y", [1, 2, 3])
        c = BinaryConstraint(x, y, lambda a, b: a < b, name="x<y")
        mc = ModelChecker([x, y], [c])
        result = mc.check_consistency()
        assert result.is_valid

    def test_unary_eliminates_all_is_invalid(self):
        x = Variable("x", [1, 2, 3])
        # unary requiring value > 100 → no feasible value
        u = UnaryConstraint(x, lambda v: v > 100, name="x>100")
        mc = ModelChecker([x], [u])
        result = mc.check_consistency()
        assert not result.is_valid
        assert result.has_issues

    def test_unary_partial_filter_warns(self):
        x = Variable("x", [1, 2, 3, 4, 5])
        u = UnaryConstraint(x, lambda v: v <= 3, name="x<=3")
        mc = ModelChecker([x], [u])
        result = mc.check_consistency()
        assert result.is_valid
        assert result.has_warnings

    def test_binary_no_support_invalid(self):
        # x in {5}, y in {5}, constraint x<y has no support
        x = Variable("x", [5])
        y = Variable("y", [5])
        c = BinaryConstraint(x, y, lambda a, b: a < b, name="x<y")
        mc = ModelChecker([x, y], [c])
        result = mc.check_consistency()
        assert not result.is_valid


class TestRedundancyChecks:
    def test_duplicate_constraint_warns(self):
        x = Variable("x", [1, 2, 3])
        y = Variable("y", [1, 2, 3])
        c1 = BinaryConstraint(x, y, lambda a, b: a != b, name="c1")
        c2 = BinaryConstraint(x, y, lambda a, b: a != b, name="c2")
        mc = ModelChecker([x, y], [c1, c2])
        result = mc.check_redundancy()
        assert result.has_warnings
        assert len(result.redundant_constraints) >= 1

    def test_disconnected_variable_warns(self):
        x = Variable("x", [1, 2, 3])
        lonely = Variable("lonely", [1, 2])
        c = BinaryConstraint(x, x, lambda a, b: True, name="self")
        mc = ModelChecker([x, lonely], [c])
        result = mc.check_all()
        assert any("lonely" in w for w in result.warnings)


class TestVerifySolution:
    def test_valid_solution(self):
        x = Variable("x", [1, 2, 3])
        y = Variable("y", [1, 2, 3])
        c = BinaryConstraint(x, y, lambda a, b: a < b, name="x<y")
        mc = ModelChecker([x, y], [c])
        result = mc.verify_solution({x: 1, y: 2})
        assert result.is_valid

    def test_missing_assignment(self):
        x = Variable("x", [1, 2, 3])
        y = Variable("y", [1, 2, 3])
        c = BinaryConstraint(x, y, lambda a, b: a < b, name="x<y")
        mc = ModelChecker([x, y], [c])
        result = mc.verify_solution({x: 1})
        assert not result.is_valid

    def test_value_out_of_domain(self):
        x = Variable("x", [1, 2, 3])
        y = Variable("y", [1, 2, 3])
        c = BinaryConstraint(x, y, lambda a, b: a < b, name="x<y")
        mc = ModelChecker([x, y], [c])
        result = mc.verify_solution({x: 9, y: 2})
        assert not result.is_valid

    def test_violated_constraint(self):
        x = Variable("x", [1, 2, 3])
        y = Variable("y", [1, 2, 3])
        c = BinaryConstraint(x, y, lambda a, b: a < b, name="x<y")
        mc = ModelChecker([x, y], [c])
        result = mc.verify_solution({x: 3, y: 1})
        assert not result.is_valid

    def test_check_all_runs_full_pipeline(self):
        x = Variable("x", [1, 2, 3])
        y = Variable("y", [1, 2, 3])
        c = BinaryConstraint(x, y, lambda a, b: a < b, name="x<y")
        mc = ModelChecker([x, y], [c])
        result = mc.check_all()
        assert isinstance(result, CheckResult)
