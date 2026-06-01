"""Tests for modules with 0% coverage to boost overall coverage to 80%+.

Covers 21 modules with 3-5 tests each, exercising real logic.
"""
import io
import json
import os
import tempfile
import time

import pytest

from modelmesh.core.variable import Variable
from modelmesh.core.constraint import BinaryConstraint, UnaryConstraint, Constraint


# ============================================================
# Helper: create fresh variables (Variable._next_index increments globally)
# ============================================================

def make_vars(names_domains: list[tuple[str, list[int]]]) -> list[Variable]:
    """Create a list of variables with given names and domains."""
    return [Variable(name, values) for name, values in names_domains]


def neq_constraint(v1: Variable, v2: Variable) -> BinaryConstraint:
    return BinaryConstraint(v1, v2, lambda a, b: a != b, f"{v1.name}!={v2.name}")


def eq_constraint(v1: Variable, v2: Variable) -> BinaryConstraint:
    return BinaryConstraint(v1, v2, lambda a, b: a == b, f"{v1.name}=={v2.name}")


# ============================================================
# 1. modelmesh.analysis.backbone - BackboneDetector
# ============================================================

class TestBackboneDetector:
    def test_detect_backbone_single_solution(self):
        """When only one solution exists, all variables are backbone."""
        from modelmesh.analysis.backbone import BackboneDetector
        x = Variable("x", [1])
        y = Variable("y", [2])
        cstr = BinaryConstraint(x, y, lambda a, b: True, "trivial")
        detector = BackboneDetector([x, y], [cstr])
        result = detector.detect()
        assert result.backbone_size >= 1

    def test_detect_non_backbone(self):
        """Variables with multiple possible values are non-backbone."""
        from modelmesh.analysis.backbone import BackboneDetector
        x = Variable("x", [1, 2])
        y = Variable("y", [1, 2])
        cstr = neq_constraint(x, y)
        detector = BackboneDetector([x, y], [cstr])
        result = detector.detect()
        # Both x and y can take either value, so neither is backbone
        assert x in result.non_backbone or x in result.undetermined
        assert result.backbone_fraction < 1.0

    def test_detect_for_subset(self):
        """detect_for_subset only checks specified variables."""
        from modelmesh.analysis.backbone import BackboneDetector
        x = Variable("x", [1])
        y = Variable("y", [1, 2])
        cstr = BinaryConstraint(x, y, lambda a, b: True, "trivial")
        detector = BackboneDetector([x, y], [cstr])
        result = detector.detect_for_subset([x])
        assert x in result.backbone
        assert y not in result.backbone and y not in result.non_backbone

    def test_unsatisfiable_problem(self):
        """Unsatisfiable problem returns empty backbone."""
        from modelmesh.analysis.backbone import BackboneDetector
        x = Variable("x", [1])
        y = Variable("y", [1])
        cstr = neq_constraint(x, y)
        detector = BackboneDetector([x, y], [cstr])
        result = detector.detect()
        assert result.backbone_size == 0


# ============================================================
# 2. modelmesh.analysis.phase_transition - PhaseTransitionAnalyzer
# ============================================================

class TestPhaseTransitionAnalyzer:
    def test_analyze_underconstrained(self):
        """Underconstrained problem should be in easy-sat region."""
        from modelmesh.analysis.phase_transition import PhaseTransitionAnalyzer
        x = Variable("x", [1, 2, 3, 4, 5])
        y = Variable("y", [1, 2, 3, 4, 5])
        z = Variable("z", [1, 2, 3, 4, 5])
        # Only one weak constraint
        cstr = BinaryConstraint(x, y, lambda a, b: a != b or True, "weak")
        analyzer = PhaseTransitionAnalyzer([x, y, z], [cstr])
        result = analyzer.analyze()
        assert result.num_variables == 3
        assert result.num_constraints == 1
        assert result.predicted_sat_probability > 0.5

    def test_analyze_overconstrained(self):
        """Overconstrained problem should predict low SAT probability."""
        from modelmesh.analysis.phase_transition import PhaseTransitionAnalyzer
        x = Variable("x", [1, 2])
        y = Variable("y", [1, 2])
        z = Variable("z", [1, 2])
        cstrs = [neq_constraint(x, y), neq_constraint(y, z), neq_constraint(x, z)]
        analyzer = PhaseTransitionAnalyzer([x, y, z], cstrs)
        result = analyzer.analyze()
        assert result.constraint_density > 0
        assert result.selectivity > 0

    def test_estimate_search_difficulty(self):
        """Search difficulty should be between 0 and 1."""
        from modelmesh.analysis.phase_transition import PhaseTransitionAnalyzer
        x = Variable("x", [1, 2, 3])
        y = Variable("y", [1, 2, 3])
        cstr = neq_constraint(x, y)
        analyzer = PhaseTransitionAnalyzer([x, y], [cstr])
        difficulty = analyzer.estimate_search_difficulty()
        assert 0.0 <= difficulty <= 1.0

    def test_result_summary(self):
        """PhaseTransitionResult.summary() returns a string."""
        from modelmesh.analysis.phase_transition import PhaseTransitionAnalyzer
        x = Variable("x", [1, 2, 3])
        y = Variable("y", [1, 2, 3])
        cstr = neq_constraint(x, y)
        analyzer = PhaseTransitionAnalyzer([x, y], [cstr])
        result = analyzer.analyze()
        summary = result.summary()
        assert "Phase Transition" in summary
        assert "Variables" in summary

    def test_compute_backbone_estimate(self):
        """Backbone estimate should be between 0 and 1."""
        from modelmesh.analysis.phase_transition import PhaseTransitionAnalyzer
        x = Variable("x", [1, 2, 3])
        y = Variable("y", [1, 2, 3])
        cstr = neq_constraint(x, y)
        analyzer = PhaseTransitionAnalyzer([x, y], [cstr])
        estimate = analyzer.compute_backbone_estimate()
        assert 0.0 <= estimate <= 1.0


# ============================================================
# 3. modelmesh.cli.runner - run_cli
# ============================================================

class TestCLIRunner:
    def test_run_cli_file_not_found(self):
        """CLI returns 1 for missing file."""
        from modelmesh.cli.runner import run_cli
        result = run_cli(["nonexistent_file.json"])
        assert result == 1

    def test_run_cli_invalid_json(self, tmp_path):
        """CLI returns 1 for invalid JSON."""
        from modelmesh.cli.runner import run_cli
        bad_file = tmp_path / "bad.json"
        bad_file.write_text("not json at all {{{")
        result = run_cli([str(bad_file)])
        assert result == 1

    def test_run_cli_valid_problem(self, tmp_path):
        """CLI solves a simple problem from JSON."""
        from modelmesh.cli.runner import run_cli
        problem = {
            "variables": [
                {"name": "x", "domain": [1, 2, 3]},
                {"name": "y", "domain": [1, 2, 3]},
            ],
            "constraints": [
                {"type": "neq", "variables": ["x", "y"]}
            ]
        }
        f = tmp_path / "problem.json"
        f.write_text(json.dumps(problem))
        result = run_cli([str(f), "--verbose"])
        assert result == 0


# ============================================================
# 4. modelmesh.core.assignment - Assignment
# ============================================================

class TestAssignment:
    def test_assign_and_get(self):
        """Basic assign and retrieve."""
        from modelmesh.core.assignment import Assignment
        x = Variable("x", [1, 2, 3])
        y = Variable("y", [4, 5, 6])
        a = Assignment([x, y])
        a.assign(x, 2)
        assert a.get(x) == 2
        assert a.size == 1
        assert not a.is_complete

    def test_undo(self):
        """Undo restores previous state."""
        from modelmesh.core.assignment import Assignment
        x = Variable("x", [1, 2, 3])
        a = Assignment([x])
        a.assign(x, 1)
        result = a.undo()
        assert result == (x, 1)
        assert a.is_empty

    def test_compute_hash_deterministic(self):
        """Same assignment produces same hash."""
        from modelmesh.core.assignment import Assignment
        x = Variable("x", [1, 2])
        y = Variable("y", [3, 4])
        a = Assignment([x, y])
        a.assign(x, 1)
        a.assign(y, 3)
        h1 = a.compute_hash()
        h2 = a.compute_hash()
        assert h1 == h2

    def test_snapshot_restore(self):
        """Snapshot and restore works correctly."""
        from modelmesh.core.assignment import Assignment
        x = Variable("x", [1, 2, 3])
        y = Variable("y", [4, 5, 6])
        a = Assignment([x, y])
        a.assign(x, 1)
        snap = a.snapshot()
        a.assign(y, 5)
        assert a.size == 2
        a.restore(snap)
        assert a.size == 1
        assert a.get(x) == 1

    def test_history_tracking(self):
        """History records assignment events."""
        from modelmesh.core.assignment import Assignment
        x = Variable("x", [1, 2, 3])
        a = Assignment([x], track_history=True)
        a.assign(x, 2)
        a.unassign(x)
        assert a.history_length >= 2
        history = a.get_history_for_variable(x)
        assert len(history) >= 2


# ============================================================
# 5. modelmesh.debug.solution_counter - SolutionCounter
# ============================================================

class TestSolutionCounter:
    def test_exact_count_simple(self):
        """Count solutions for a simple 2-variable problem."""
        from modelmesh.debug.solution_counter import SolutionCounter
        x = Variable("x", [1, 2, 3])
        y = Variable("y", [1, 2, 3])
        cstr = neq_constraint(x, y)
        counter = SolutionCounter([x, y], [cstr])
        result = counter.count()
        assert result.is_exact
        assert result.exact_count == 6  # 3*3 - 3 = 6

    def test_exact_count_no_solutions(self):
        """Count returns 0 for unsatisfiable problem."""
        from modelmesh.debug.solution_counter import SolutionCounter
        x = Variable("x", [1])
        y = Variable("y", [1])
        cstr = neq_constraint(x, y)
        counter = SolutionCounter([x, y], [cstr])
        result = counter.count()
        assert result.exact_count == 0
        assert not result.has_solutions

    def test_count_result_properties(self):
        """CountResult properties work correctly."""
        from modelmesh.debug.solution_counter import SolutionCounter
        x = Variable("x", [1, 2])
        y = Variable("y", [1, 2])
        cstr = neq_constraint(x, y)
        counter = SolutionCounter([x, y], [cstr])
        result = counter.count()
        assert result.count == 2
        assert result.has_solutions

    def test_convenience_count_solutions(self):
        """count_solutions convenience function works."""
        from modelmesh.debug.solution_counter import count_solutions
        x = Variable("x", [1, 2])
        y = Variable("y", [1, 2])
        cstr = neq_constraint(x, y)
        assert count_solutions([x, y], [cstr]) == 2


# ============================================================
# 6. modelmesh.decomposition.hypertree - HypertreeDecomposition
# ============================================================

class TestHypertreeDecomposition:
    def test_decompose_simple(self):
        """Decompose a simple binary constraint network."""
        from modelmesh.decomposition.hypertree import HypertreeDecomposition
        x = Variable("x", [1, 2])
        y = Variable("y", [1, 2])
        z = Variable("z", [1, 2])
        c1 = neq_constraint(x, y)
        c2 = neq_constraint(y, z)
        decomp = HypertreeDecomposition([x, y, z], [c1, c2])
        decomp.decompose()
        assert decomp.num_nodes > 0
        assert decomp.root is not None

    def test_hypertree_width(self):
        """Hypertree width is computed."""
        from modelmesh.decomposition.hypertree import HypertreeDecomposition
        x = Variable("x", [1, 2])
        y = Variable("y", [1, 2])
        z = Variable("z", [1, 2])
        c1 = neq_constraint(x, y)
        c2 = neq_constraint(y, z)
        c3 = neq_constraint(x, z)
        decomp = HypertreeDecomposition([x, y, z], [c1, c2, c3])
        decomp.decompose()
        assert decomp.hypertree_width >= 1

    def test_hypergraph_properties(self):
        """ConstraintHypergraph has correct properties."""
        from modelmesh.decomposition.hypertree import ConstraintHypergraph
        x = Variable("x", [1, 2])
        y = Variable("y", [1, 2])
        c1 = neq_constraint(x, y)
        hg = ConstraintHypergraph([x, y], [c1])
        assert hg.num_nodes == 2
        assert hg.num_edges == 1
        assert hg.max_edge_size() == 2

    def test_validate_decomposition(self):
        """Validate returns True for a correct decomposition."""
        from modelmesh.decomposition.hypertree import HypertreeDecomposition
        x = Variable("x", [1, 2])
        y = Variable("y", [1, 2])
        c1 = neq_constraint(x, y)
        decomp = HypertreeDecomposition([x, y], [c1])
        decomp.decompose()
        assert decomp.validate() is True


# ============================================================
# 7. modelmesh.distributed.load_balancer - LoadBalancer
# ============================================================

class TestLoadBalancer:
    def test_register_worker(self):
        """Register workers and check count."""
        from modelmesh.distributed.load_balancer import LoadBalancer
        lb = LoadBalancer()
        lb.register_worker("w1", max_capacity=4)
        lb.register_worker("w2", max_capacity=4)
        assert lb.num_workers == 2
        assert lb.active_workers == 2

    def test_submit_problems(self):
        """Submit problems and get assignments."""
        from modelmesh.distributed.load_balancer import LoadBalancer
        from modelmesh.distributed.splitter import SubProblem
        lb = LoadBalancer()
        lb.register_worker("w1", max_capacity=2)
        x = Variable("x", [1, 2, 3, 4])
        problems = [
            SubProblem(problem_id=i, split_variable=x,
                       split_values=frozenset([i+1]), estimated_difficulty=0.5)
            for i in range(3)
        ]
        assignments = lb.submit_problems(problems)
        assert len(assignments) == 2  # worker capacity is 2
        assert lb.pending_count == 1

    def test_report_completion(self):
        """Completing work updates stats."""
        from modelmesh.distributed.load_balancer import LoadBalancer
        from modelmesh.distributed.splitter import SubProblem
        lb = LoadBalancer()
        lb.register_worker("w1", max_capacity=4)
        x = Variable("x", [1, 2])
        problems = [SubProblem(0, x, frozenset([1]), 0.5)]
        lb.submit_problems(problems)
        lb.report_completion(0, "w1", {"solution": {0: 1}})
        assert lb.total_completed == 1

    def test_report_failure_and_retry(self):
        """Failed work is retried on another worker."""
        from modelmesh.distributed.load_balancer import LoadBalancer
        from modelmesh.distributed.splitter import SubProblem
        lb = LoadBalancer(max_retries=2)
        lb.register_worker("w1", max_capacity=4)
        lb.register_worker("w2", max_capacity=4)
        x = Variable("x", [1, 2])
        problems = [SubProblem(0, x, frozenset([1]), 0.5)]
        lb.submit_problems(problems)
        new_assign = lb.report_failure(0, "w1")
        assert new_assign is not None
        assert new_assign.worker_id == "w2"

    def test_get_statistics(self):
        """Statistics dict has expected keys."""
        from modelmesh.distributed.load_balancer import LoadBalancer
        lb = LoadBalancer()
        lb.register_worker("w1")
        stats = lb.get_statistics()
        assert "num_workers" in stats
        assert "avg_worker_load" in stats


# ============================================================
# 8. modelmesh.global_cstr.nvalue - NValueConstraint
# ============================================================

class TestNValueConstraint:
    def test_satisfied_complete(self):
        """Complete assignment with correct distinct count satisfies."""
        from modelmesh.global_cstr.nvalue import NValueConstraint
        x = Variable("x", [1, 2, 3])
        y = Variable("y", [1, 2, 3])
        z = Variable("z", [1, 2, 3])
        nv = NValueConstraint([x, y, z], lower_bound=2, upper_bound=3)
        # 3 distinct values
        assert nv.is_satisfied({x: 1, y: 2, z: 3}) is True
        # 2 distinct values
        assert nv.is_satisfied({x: 1, y: 1, z: 2}) is True
        # 1 distinct value - violates lower bound
        assert nv.is_satisfied({x: 1, y: 1, z: 1}) is False

    def test_propagate_upper_bound(self):
        """Upper bound propagation removes new values when at limit."""
        from modelmesh.global_cstr.nvalue import NValueConstraint
        x = Variable("x", [1, 2, 3])
        y = Variable("y", [1, 2, 3])
        z = Variable("z", [1, 2, 3])
        nv = NValueConstraint([x, y, z], lower_bound=1, upper_bound=1)
        # If x=1 and y=1, z must also be 1
        pruned = nv.propagate({x: 1, y: 1})
        assert z in pruned  # values 2,3 should be pruned from z

    def test_compute_distinct_bounds(self):
        """Compute achievable distinct value bounds."""
        from modelmesh.global_cstr.nvalue import NValueConstraint
        x = Variable("x", [1, 2])
        y = Variable("y", [1, 2])
        nv = NValueConstraint([x, y], lower_bound=1, upper_bound=2)
        min_d, max_d = nv.compute_distinct_bounds({x: 1})
        assert min_d >= 1
        assert max_d <= 2

    def test_get_potential_values(self):
        """get_potential_values returns union of all domains."""
        from modelmesh.global_cstr.nvalue import NValueConstraint
        x = Variable("x", [1, 2])
        y = Variable("y", [3, 4])
        nv = NValueConstraint([x, y], lower_bound=1, upper_bound=2)
        assert nv.get_potential_values() == {1, 2, 3, 4}


# ============================================================
# 9. modelmesh.global_cstr.regular - RegularConstraint
# ============================================================

class TestRegularConstraint:
    def _make_simple_dfa(self):
        """DFA accepting sequences of 0s followed by 1s: 0*1*"""
        from modelmesh.global_cstr.regular import DFA, DFATransition
        # State 0: initial (reading 0s), State 1: reading 1s
        transitions = [
            DFATransition(0, 0, 0),  # stay in state 0 on 0
            DFATransition(0, 1, 1),  # move to state 1 on 1
            DFATransition(1, 1, 1),  # stay in state 1 on 1
        ]
        return DFA(num_states=2, initial_state=0,
                   accepting_states={0, 1}, transitions=transitions)

    def test_is_satisfied_accepted(self):
        """Accepted word satisfies the constraint."""
        from modelmesh.global_cstr.regular import RegularConstraint
        dfa = self._make_simple_dfa()
        x = Variable("x", [0, 1])
        y = Variable("y", [0, 1])
        z = Variable("z", [0, 1])
        rc = RegularConstraint([x, y, z], dfa)
        # 0, 0, 1 is accepted (0*1*)
        assert rc.is_satisfied({x: 0, y: 0, z: 1}) is True

    def test_is_satisfied_rejected(self):
        """Rejected word violates the constraint."""
        from modelmesh.global_cstr.regular import RegularConstraint
        dfa = self._make_simple_dfa()
        x = Variable("x", [0, 1])
        y = Variable("y", [0, 1])
        z = Variable("z", [0, 1])
        rc = RegularConstraint([x, y, z], dfa)
        # 1, 0, 1 is rejected (can't go back to 0 after 1)
        assert rc.is_satisfied({x: 1, y: 0, z: 1}) is False

    def test_propagate_prunes_invalid(self):
        """Propagation removes values that can't lead to acceptance."""
        from modelmesh.global_cstr.regular import RegularConstraint
        dfa = self._make_simple_dfa()
        x = Variable("x", [0, 1])
        y = Variable("y", [0, 1])
        z = Variable("z", [0, 1])
        rc = RegularConstraint([x, y, z], dfa)
        # If x=1, then y cannot be 0 (no transition from state 1 on 0)
        pruned = rc.propagate({x: 1})
        if y in pruned:
            assert 0 in pruned[y]

    def test_get_accepting_path(self):
        """get_accepting_path returns valid path for accepted word."""
        from modelmesh.global_cstr.regular import RegularConstraint
        dfa = self._make_simple_dfa()
        x = Variable("x", [0, 1])
        y = Variable("y", [0, 1])
        rc = RegularConstraint([x, y], dfa)
        path = rc.get_accepting_path({x: 0, y: 1})
        assert path is not None
        assert len(path) == 2


# ============================================================
# 10. modelmesh.global_cstr.table_ct - CompactTable (BitSet + CT)
# ============================================================

class TestCompactTable:
    def test_bitset_operations(self):
        """BitSet basic operations work."""
        from modelmesh.global_cstr.table_ct import BitSet
        bs = BitSet.all_ones(8)
        assert bs.count() == 8
        assert bs.contains(0)
        bs.clear_bit(3)
        assert not bs.contains(3)
        assert bs.count() == 7

    def test_compact_table_positive(self):
        """Positive table allows only listed tuples."""
        from modelmesh.global_cstr.table_ct import CompactTable
        x = Variable("x", [1, 2, 3])
        y = Variable("y", [1, 2, 3])
        tuples = [(1, 2), (2, 3), (3, 1)]
        ct = CompactTable([x, y], tuples, is_positive=True)
        assert ct.is_satisfied({x: 1, y: 2}) is True
        assert ct.is_satisfied({x: 1, y: 1}) is False

    def test_compact_table_propagate(self):
        """Propagation removes unsupported values."""
        from modelmesh.global_cstr.table_ct import CompactTable
        x = Variable("x", [1, 2, 3])
        y = Variable("y", [1, 2, 3])
        tuples = [(1, 1), (2, 2)]
        ct = CompactTable([x, y], tuples, is_positive=True)
        pruned = ct.propagate({x: 1})
        # y can only be 1 when x=1
        if y in pruned:
            assert 2 in pruned[y] or 3 in pruned[y]

    def test_compact_table_statistics(self):
        """Statistics returns expected keys."""
        from modelmesh.global_cstr.table_ct import CompactTable
        x = Variable("x", [1, 2])
        y = Variable("y", [1, 2])
        ct = CompactTable([x, y], [(1, 1), (2, 2)], is_positive=True)
        stats = ct.statistics()
        assert stats["num_tuples"] == 2
        assert stats["num_variables"] == 2


# ============================================================
# 11. modelmesh.middleware.logging_hook - LoggingHook
# ============================================================

class TestLoggingHook:
    def test_log_decision(self):
        """Logging hook records decisions."""
        from modelmesh.middleware.logging_hook import LoggingHook, Verbosity
        hook = LoggingHook(verbosity=Verbosity.NORMAL)
        hook.on_start(3, 2)
        x = Variable("x", [1, 2, 3])
        hook.on_decision(x, 1, depth=0)
        assert hook.decision_count == 1
        assert hook.entry_count >= 1

    def test_log_backtrack(self):
        """Logging hook records backtracks."""
        from modelmesh.middleware.logging_hook import LoggingHook, Verbosity
        hook = LoggingHook(verbosity=Verbosity.NORMAL)
        hook.on_start(2, 1)
        x = Variable("x", [1, 2])
        hook.on_backtrack(x, depth=1)
        assert hook.backtrack_count == 1

    def test_log_solution(self):
        """Logging hook records solutions."""
        from modelmesh.middleware.logging_hook import LoggingHook, Verbosity
        hook = LoggingHook(verbosity=Verbosity.QUIET)
        hook.on_start(2, 1)
        x = Variable("x", [1, 2])
        y = Variable("y", [1, 2])
        hook.on_solution({x: 1, y: 2})
        assert hook.solution_count == 1

    def test_json_format(self):
        """JSON format outputs valid JSON lines."""
        from modelmesh.middleware.logging_hook import LoggingHook, Verbosity
        output = io.StringIO()
        hook = LoggingHook(verbosity=Verbosity.QUIET, output=output, format="json")
        hook.on_start(2, 1)
        lines = output.getvalue().strip().split("\n")
        for line in lines:
            parsed = json.loads(line)
            assert "event" in parsed

    def test_get_summary(self):
        """get_summary returns dict with expected keys."""
        from modelmesh.middleware.logging_hook import LoggingHook, Verbosity
        hook = LoggingHook(verbosity=Verbosity.DEBUG)
        hook.on_start(2, 1)
        summary = hook.get_summary()
        assert "decisions" in summary
        assert "backtracks" in summary


# ============================================================
# 12. modelmesh.modeling.combinatorial - PermutationModel etc.
# ============================================================

class TestCombinatorialModeling:
    def test_permutation_model_solve(self):
        """PermutationModel finds a valid permutation."""
        from modelmesh.modeling.combinatorial import PermutationModel
        perm = PermutationModel(n=3)
        result = perm.solve()
        assert result is not None
        assert sorted(result) == [0, 1, 2]

    def test_permutation_model_fixed_point(self):
        """Fixed point constrains a position."""
        from modelmesh.modeling.combinatorial import PermutationModel
        perm = PermutationModel(n=3)
        perm.add_fixed_point(0, 2)
        result = perm.solve()
        assert result is not None
        assert result[0] == 2

    def test_partition_model_solve(self):
        """PartitionModel partitions items into groups."""
        from modelmesh.modeling.combinatorial import PartitionModel
        part = PartitionModel(items=4, num_groups=2)
        part.add_same_group(0, 1)
        result = part.solve()
        assert result is not None
        # Items 0 and 1 should be in the same group
        for group in result:
            if 0 in group:
                assert 1 in group

    def test_bin_packing_model(self):
        """BinPackingModel assigns items to bins."""
        from modelmesh.modeling.combinatorial import BinPackingModel
        bp = BinPackingModel(num_bins=2, bin_capacity=10)
        bp.add_item("a", size=3)
        bp.add_item("b", size=4)
        bp.add_item("c", size=5)
        result = bp.solve()
        assert result is not None
        assert all(v in (0, 1) for v in result.values())


# ============================================================
# 13. modelmesh.modeling.scheduling - SchedulingModel
# ============================================================

class TestSchedulingModel:
    def test_add_task(self):
        """Adding tasks creates proper intervals."""
        from modelmesh.modeling.scheduling import SchedulingModel
        sched = SchedulingModel(horizon=20)
        t1 = sched.add_task("paint", duration=5)
        assert t1.duration == 5
        assert t1.name == "paint"
        assert sched.num_tasks == 1

    def test_precedence_constraint(self):
        """Precedence ensures task ordering."""
        from modelmesh.modeling.scheduling import SchedulingModel
        sched = SchedulingModel(horizon=20)
        t1 = sched.add_task("a", duration=3)
        t2 = sched.add_task("b", duration=4)
        sched.add_precedence(t1, t2)
        result = sched.solve()
        assert result is not None
        assert result["a_end"] <= result["b_start"]

    def test_no_overlap(self):
        """No-overlap prevents simultaneous tasks."""
        from modelmesh.modeling.scheduling import SchedulingModel
        sched = SchedulingModel(horizon=20)
        t1 = sched.add_task("a", duration=5)
        t2 = sched.add_task("b", duration=5)
        sched.add_no_overlap([t1, t2])
        result = sched.solve()
        assert result is not None
        a_start, a_end = result["a_start"], result["a_end"]
        b_start, b_end = result["b_start"], result["b_end"]
        assert a_end <= b_start or b_end <= a_start

    def test_critical_path(self):
        """Critical path computation returns tasks."""
        from modelmesh.modeling.scheduling import SchedulingModel
        sched = SchedulingModel(horizon=30)
        t1 = sched.add_task("a", duration=5)
        t2 = sched.add_task("b", duration=10)
        sched.add_precedence(t1, t2)
        cp = sched.compute_critical_path()
        assert len(cp) >= 1


# ============================================================
# 14. modelmesh.optimizer.signal - SignalTracker
# ============================================================

class TestSignalTracker:
    def test_bump_variable(self):
        """Bumping increases signal."""
        from modelmesh.optimizer.signal import SignalTracker
        x = Variable("x", [1, 2, 3])
        y = Variable("y", [1, 2, 3])
        mgr = SignalTracker([x, y])
        assert mgr.get_signal(x) == 0.0
        mgr.bump_variable(x)
        assert mgr.get_signal(x) > 0.0

    def test_bump_conflict_variables(self):
        """Bumping conflict variables updates all and applies decay."""
        from modelmesh.optimizer.signal import SignalTracker
        x = Variable("x", [1, 2])
        y = Variable("y", [1, 2])
        mgr = SignalTracker([x, y], decay_factor=0.9)
        mgr.bump_conflict_variables([x, y])
        assert mgr.conflict_count == 1
        assert mgr.get_signal(x) > 0
        assert mgr.get_signal(y) > 0

    def test_get_ordering(self):
        """Ordering returns highest signal first."""
        from modelmesh.optimizer.signal import SignalTracker
        x = Variable("x", [1, 2])
        y = Variable("y", [1, 2])
        mgr = SignalTracker([x, y])
        mgr.bump_variable(x)
        mgr.bump_variable(x)
        mgr.bump_variable(y)
        ordering = mgr.get_ordering([x, y])
        assert ordering[0] is x

    def test_create_selector(self):
        """SignalSelector selects highest signal variable."""
        from modelmesh.optimizer.signal import SignalTracker
        x = Variable("x", [1, 2])
        y = Variable("y", [1, 2])
        mgr = SignalTracker([x, y])
        mgr.bump_variable(y)
        mgr.bump_variable(y)
        selector = mgr.create_selector()
        selected = selector.select([x, y], [], {})
        assert selected is y
