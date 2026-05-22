"""Variable signal scoring (VSIDS-style) for CSP solvers.

Signal-based variable ordering is inspired by the VSIDS (Variable State
Independent Decaying Sum) heuristic from SAT solving. Variables involved in
recent conflicts have their signal bumped, and all activities decay
periodically. This focuses the search on variables that are currently
causing the most difficulty.

The signal score is used as a variable ordering heuristic: variables
with higher signal are selected first, as they are more likely to be
involved in conflicts and should be resolved early.
"""

from __future__ import annotations

from typing import Sequence

from modelmesh.core.variable import Variable
from modelmesh.core.constraint import Constraint
from modelmesh.heuristics.variable_ordering import VariableSelector


class SignalScore:
    """Tracks signal score for a single variable.

    Signal is bumped on conflict involvement and decayed periodically.
    """

    __slots__ = ("_variable", "_signal", "_bump_count", "_last_bump_conflict")

    def __init__(self, variable: Variable, initial_signal: float = 0.0) -> None:
        self._variable = variable
        self._signal = initial_signal
        self._bump_count: int = 0
        self._last_bump_conflict: int = 0

    @property
    def variable(self) -> Variable:
        return self._variable

    @property
    def signal(self) -> float:
        return self._signal

    @property
    def bump_count(self) -> int:
        """Number of times this variable's signal was bumped."""
        return self._bump_count

    @property
    def last_bump_conflict(self) -> int:
        """Conflict number at which this variable was last bumped."""
        return self._last_bump_conflict

    def bump(self, amount: float, conflict_number: int) -> None:
        """Increase signal by the given amount."""
        self._signal += amount
        self._bump_count += 1
        self._last_bump_conflict = conflict_number

    def decay(self, factor: float) -> None:
        """Multiply signal by decay factor (should be < 1)."""
        self._signal *= factor

    def reset(self) -> None:
        """Reset signal to zero."""
        self._signal = 0.0
        self._bump_count = 0
        self._last_bump_conflict = 0

    def rescale(self, divisor: float) -> None:
        """Divide signal by divisor to prevent overflow."""
        if divisor > 0:
            self._signal /= divisor


class SignalManager:
    """Manages signal scores for all variables in a CSP.

    Implements VSIDS-style signal tracking:
    - Bump: increase signal of variables involved in a conflict
    - Decay: periodically reduce all activities to favor recent conflicts
    - Rescale: prevent floating-point overflow when activities grow large

    Args:
        variables: All CSP variables to track.
        initial_bump: Initial bump increment value.
        decay_factor: Multiplicative decay applied after each conflict (0 < d < 1).
        bump_increment_factor: Factor by which bump amount increases over time.
        rescale_threshold: Signal threshold that triggers rescaling.
    """

    def __init__(
        self,
        variables: Sequence[Variable],
        initial_bump: float = 1.0,
        decay_factor: float = 0.95,
        bump_increment_factor: float = 1.05,
        rescale_threshold: float = 1e100,
    ) -> None:
        self._scores: dict[Variable, SignalScore] = {}
        for var in variables:
            self._scores[var] = SignalScore(var)
        self._bump_amount = initial_bump
        self._decay_factor = decay_factor
        self._bump_increment_factor = bump_increment_factor
        self._rescale_threshold = rescale_threshold
        self._conflict_count: int = 0
        self._total_bumps: int = 0
        self._rescale_count: int = 0

    @property
    def conflict_count(self) -> int:
        """Total number of conflicts processed."""
        return self._conflict_count

    @property
    def total_bumps(self) -> int:
        """Total number of signal bumps performed."""
        return self._total_bumps

    @property
    def rescale_count(self) -> int:
        """Number of times rescaling was triggered."""
        return self._rescale_count

    @property
    def current_bump_amount(self) -> float:
        """Current bump increment (grows over time)."""
        return self._bump_amount

    def get_signal(self, var: Variable) -> float:
        """Get the current signal score for a variable."""
        score = self._scores.get(var)
        if score is None:
            return 0.0
        return score.signal

    def bump_variable(self, var: Variable) -> None:
        """Bump the signal of a single variable.

        Called when the variable is involved in a conflict.
        """
        score = self._scores.get(var)
        if score is None:
            score = SignalScore(var)
            self._scores[var] = score

        score.bump(self._bump_amount, self._conflict_count)
        self._total_bumps += 1

        if score.signal > self._rescale_threshold:
            self._rescale_all()

    def bump_conflict_variables(self, conflict_vars: Sequence[Variable]) -> None:
        """Bump signal for all variables involved in a conflict.

        This is the main entry point called after each conflict during search.
        After bumping, applies decay and increases the bump amount.
        """
        self._conflict_count += 1

        for var in conflict_vars:
            self.bump_variable(var)

        self._decay_all()
        self._bump_amount *= self._bump_increment_factor

    def bump_from_constraint(self, constraint: Constraint) -> None:
        """Bump all variables in a constraint that caused a failure."""
        self.bump_conflict_variables(list(constraint.variables))

    def _decay_all(self) -> None:
        """Apply decay to all signal scores."""
        for score in self._scores.values():
            score.decay(self._decay_factor)

    def _rescale_all(self) -> None:
        """Rescale all activities to prevent overflow."""
        max_signal = max(
            (s.signal for s in self._scores.values()), default=1.0
        )
        if max_signal > 0:
            for score in self._scores.values():
                score.rescale(max_signal)
            self._bump_amount /= max_signal
        self._rescale_count += 1

    def get_ordering(self, unassigned: list[Variable]) -> list[Variable]:
        """Return unassigned variables ordered by decreasing signal."""
        return sorted(
            unassigned,
            key=lambda v: self.get_signal(v),
            reverse=True,
        )

    def get_top_k(self, k: int) -> list[tuple[Variable, float]]:
        """Return the k variables with highest signal."""
        all_scores = [(s.variable, s.signal) for s in self._scores.values()]
        all_scores.sort(key=lambda x: x[1], reverse=True)
        return all_scores[:k]

    def reset(self) -> None:
        """Reset all signal scores and counters."""
        for score in self._scores.values():
            score.reset()
        self._bump_amount = 1.0
        self._conflict_count = 0
        self._total_bumps = 0
        self._rescale_count = 0

    def get_statistics(self) -> dict[str, float]:
        """Return summary statistics about signal tracking."""
        activities = [s.signal for s in self._scores.values()]
        if not activities:
            return {"mean": 0.0, "max": 0.0, "min": 0.0, "std": 0.0}

        mean_act = sum(activities) / len(activities)
        max_act = max(activities)
        min_act = min(activities)
        variance = sum((a - mean_act) ** 2 for a in activities) / len(activities)
        std_act = variance ** 0.5

        return {
            "mean": mean_act,
            "max": max_act,
            "min": min_act,
            "std": std_act,
            "conflicts": float(self._conflict_count),
            "total_bumps": float(self._total_bumps),
            "rescales": float(self._rescale_count),
        }

    def create_selector(self) -> SignalSelector:
        """Create a VariableSelector that uses signal scores."""
        return SignalSelector(self)


class SignalSelector(VariableSelector):
    """Variable selector that chooses the variable with highest signal.

    Ties are broken by domain size (smaller domain first), then by
    variable index for determinism.
    """

    def __init__(self, signal_manager: SignalManager) -> None:
        self._manager = signal_manager

    def select(
        self,
        unassigned: list[Variable],
        constraints: list[Constraint],
        assignment: dict[Variable, int],
    ) -> Variable:
        """Select the unassigned variable with the highest signal score."""
        if not unassigned:
            raise ValueError("No unassigned variables")

        return max(
            unassigned,
            key=lambda v: (self._manager.get_signal(v), -v.domain_size, -v.index),
        )
