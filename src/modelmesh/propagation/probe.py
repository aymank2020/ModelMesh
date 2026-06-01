"""Candidate probing consistency.

This pass checks candidate values by temporarily pinning a variable, running
arc consistency, and then restoring the domains. Values that make the local
network inconsistent can be removed from the original domain.

The pass is more expensive than AC-3, but it is useful for dense or brittle
models where local support checks leave too many candidates alive.
"""

from __future__ import annotations

from modelmesh.core.variable import Variable
from modelmesh.core.constraint import Constraint
from modelmesh.propagation.ac3 import AC3Propagator, PropagationResult


class ProbePropagator:
    """Value-probing propagator.

    For each unassigned variable x and each value v in domain(x):
    1. Tentatively assign x = v
    2. Run AC-3 propagation
    3. If any domain becomes empty, remove v from domain(x)
    4. Restore all domains

    This is expensive (O(n * d * AC3_cost)) but very effective for
    hard problems.
    """

    def __init__(self, variables: list[Variable], constraints: list[Constraint]) -> None:
        self._variables = variables
        self._constraints = constraints

    def propagate(self, assignment: dict[Variable, int]) -> PropagationResult:
        """Run probe consistency propagation.

        Returns PropagationResult with all values pruned by probe consistency.
        """
        pruned: dict[Variable, list[int]] = {}
        total_revisions = 0
        changed = True

        while changed:
            changed = False
            for var in self._variables:
                if var.is_assigned:
                    continue
                if var.domain.is_empty:
                    return PropagationResult(False, pruned, total_revisions)

                values_to_remove = []
                for val in list(var.domain):
                    if not self._candidate_survives(var, val, assignment):
                        values_to_remove.append(val)

                for val in values_to_remove:
                    if var.domain.remove(val):
                        if var not in pruned:
                            pruned[var] = []
                        pruned[var].append(val)
                        changed = True
                        total_revisions += 1

                if var.domain.is_empty:
                    return PropagationResult(False, pruned, total_revisions)

        return PropagationResult(True, pruned, total_revisions)

    def _candidate_survives(
        self,
        var: Variable,
        value: int,
        assignment: dict[Variable, int],
    ) -> bool:
        """Check whether a tentative value survives propagation.

        Tentatively assigns, runs AC-3, checks for wipeout, then restores.
        """
        # Save current domain generations so the trial can be undone.
        trial_generations = {v: v.domain.generation for v in self._variables}
        for v in self._variables:
            v.mark_generation()

        # Tentatively assign
        test_assignment = dict(assignment)
        test_assignment[var] = value
        var.domain.assign(value)

        # Run AC-3
        propagator = AC3Propagator(self._variables, self._constraints)
        result = propagator.propagate(test_assignment, trigger_var=var)

        # Restore all domains
        for v in self._variables:
            v.restore_to(trial_generations[v])

        return result.consistent

    def propagate_incremental(
        self,
        var: Variable,
        assignment: dict[Variable, int],
    ) -> PropagationResult:
        """Run probe consistency only for variables connected to var.

        More efficient than full probe consistency when only one variable changed.
        """
        pruned: dict[Variable, list[int]] = {}
        revisions = 0

        # Get neighbors of var in constraint graph
        neighbors: set[Variable] = set()
        for cstr in self._constraints:
            if cstr.involves(var):
                for other in cstr.other_variables(var):
                    if not other.is_assigned:
                        neighbors.add(other)

        for neighbor in neighbors:
            if neighbor.domain.is_empty:
                return PropagationResult(False, pruned, revisions)

            values_to_remove = []
            for val in list(neighbor.domain):
                if not self._candidate_survives(neighbor, val, assignment):
                    values_to_remove.append(val)

            for val in values_to_remove:
                if neighbor.domain.remove(val):
                    if neighbor not in pruned:
                        pruned[neighbor] = []
                    pruned[neighbor].append(val)
                    revisions += 1

            if neighbor.domain.is_empty:
                return PropagationResult(False, pruned, revisions)

        return PropagationResult(True, pruned, revisions)
