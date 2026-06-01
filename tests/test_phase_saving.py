"""Tests for phase saving (last-value memory across restarts)."""

from modelmesh.core.variable import Variable
from modelmesh.optimizer.phase_saving import (
    PhaseRecord,
    PhaseSaving,
    PhaseValueOrderer,
)


class TestPhaseRecord:
    def test_initial_state(self):
        x = Variable("x", range(1, 6))
        r = PhaseRecord(x)
        assert r.last_value is None
        assert r.total_assignments == 0
        assert r.best_value() is None

    def test_record_assignment_tracks_last(self):
        x = Variable("x", range(1, 6))
        r = PhaseRecord(x)
        r.record_assignment(3)
        r.record_assignment(4)
        assert r.last_value == 4
        assert r.total_assignments == 2

    def test_assignment_frequency(self):
        x = Variable("x", range(1, 6))
        r = PhaseRecord(x)
        r.record_assignment(2)
        r.record_assignment(2)
        r.record_assignment(5)
        assert r.assignment_frequency(2) == 2 / 3
        assert r.assignment_frequency(5) == 1 / 3
        assert r.assignment_frequency(1) == 0.0

    def test_conflict_rate(self):
        x = Variable("x", range(1, 6))
        r = PhaseRecord(x)
        r.record_assignment(2)
        r.record_assignment(2)
        r.record_conflict(2)
        assert r.conflict_rate(2) == 0.5
        assert r.conflict_rate(3) == 0.0

    def test_best_value_prefers_low_conflict(self):
        x = Variable("x", range(1, 6))
        r = PhaseRecord(x)
        r.record_assignment(1)
        r.record_conflict(1)  # conflict rate 1.0
        r.record_assignment(2)  # conflict rate 0.0
        assert r.best_value() == 2

    def test_reset_counts_keeps_last_value(self):
        x = Variable("x", range(1, 6))
        r = PhaseRecord(x)
        r.record_assignment(3)
        r.reset_counts()
        assert r.total_assignments == 0
        assert r.last_value == 3


class TestPhaseSaving:
    def test_initial(self):
        xs = [Variable("x", range(1, 4)), Variable("y", range(1, 4))]
        ps = PhaseSaving(xs)
        assert ps.restart_count == 0
        assert ps.total_conflicts == 0
        assert ps.phase_hit_rate == 0.0

    def test_record_assignment_and_phase_value(self):
        x = Variable("x", range(1, 6))
        ps = PhaseSaving([x])
        ps.record_assignment(x, 4)
        assert ps.get_phase_value(x) == 4

    def test_phase_hit_rate(self):
        x = Variable("x", range(1, 6))
        ps = PhaseSaving([x])
        ps.record_assignment(x, 3)  # first, no hit/miss baseline
        ps.record_assignment(x, 3)  # hit
        ps.record_assignment(x, 5)  # miss
        # hits=1, misses=1
        assert ps.phase_hit_rate == 0.5

    def test_record_conflict_counts(self):
        x = Variable("x", range(1, 6))
        ps = PhaseSaving([x])
        ps.record_assignment(x, 2)
        ps.record_conflict(x, 2)
        assert ps.total_conflicts == 1
        assert ps.get_best_value(x) is not None

    def test_record_restart(self):
        x = Variable("x", range(1, 6))
        ps = PhaseSaving([x])
        ps.record_restart()
        ps.record_restart()
        assert ps.restart_count == 2

    def test_value_ordering_puts_phase_first(self):
        x = Variable("x", range(1, 6))
        ps = PhaseSaving([x])
        ps.record_assignment(x, 4)
        ordering = ps.get_value_ordering(x)
        assert ordering[0] == 4
        assert set(ordering) == {1, 2, 3, 4, 5}

    def test_value_ordering_no_phase_is_sorted(self):
        x = Variable("x", range(1, 6))
        ps = PhaseSaving([x])
        assert ps.get_value_ordering(x) == [1, 2, 3, 4, 5]

    def test_statistics_keys(self):
        x = Variable("x", range(1, 6))
        ps = PhaseSaving([x])
        ps.record_assignment(x, 2)
        stats = ps.get_statistics()
        assert set(stats) >= {
            "total_assignments",
            "variables_with_phase",
            "phase_hit_rate",
            "restarts",
        }
        assert stats["total_assignments"] == 1.0

    def test_reset_all(self):
        x = Variable("x", range(1, 6))
        ps = PhaseSaving([x])
        ps.record_assignment(x, 2)
        ps.record_restart()
        ps.reset_all()
        assert ps.restart_count == 0
        assert ps.total_conflicts == 0


class TestPhaseValueOrderer:
    def test_orderer_uses_phase(self):
        x = Variable("x", range(1, 6))
        ps = PhaseSaving([x])
        ps.record_assignment(x, 3)
        orderer = ps.create_value_orderer()
        assert isinstance(orderer, PhaseValueOrderer)
        assert orderer.order(x, [], {})[0] == 3
