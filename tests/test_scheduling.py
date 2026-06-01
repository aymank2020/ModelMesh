"""Tests for the scheduling modeling helpers.

Note: SchedulingModel.solve_minimize_makespan re-solves on shared, already-mutated
variable state and can raise on later iterations (recorded in TASK_CANDIDATES.md).
Tests avoid that broken multi-pass path.
"""

import pytest

from modelmesh.modeling.scheduling import SchedulingModel, TaskInterval, Resource
from modelmesh.core.variable import Variable


class TestTaskIntervalAndResource:
    def test_task_interval_bounds(self):
        start = Variable("s", range(0, 6))
        end = Variable("e", range(3, 9))
        t = TaskInterval(name="t", start_var=start, duration=3, end_var=end)
        assert t.earliest_start == 0
        assert t.latest_start == 5
        assert t.earliest_end == 3
        assert t.latest_end == 8

    def test_resource_defaults(self):
        r = Resource(resource_id=0, name="r")
        assert r.capacity == 1
        assert r.tasks == []


class TestSchedulingModelBasics:
    def test_add_task(self):
        sched = SchedulingModel(horizon=20)
        t = sched.add_task("paint", duration=5)
        assert sched.num_tasks == 1
        assert t.duration == 5
        assert isinstance(t, TaskInterval)

    def test_task_does_not_fit_raises(self):
        sched = SchedulingModel(horizon=3)
        with pytest.raises(ValueError):
            sched.add_task("toolong", duration=10)


class TestSchedulingConstraints:
    def test_precedence_solution(self):
        sched = SchedulingModel(horizon=20)
        a = sched.add_task("a", duration=3)
        b = sched.add_task("b", duration=2)
        sched.add_precedence(a, b)
        sol = sched.solve()
        assert sol is not None
        assert sol["a_end"] <= sol["b_start"]

    def test_no_overlap(self):
        sched = SchedulingModel(horizon=20)
        a = sched.add_task("a", duration=3)
        b = sched.add_task("b", duration=3)
        sched.add_no_overlap([a, b])
        sol = sched.solve()
        assert sol is not None
        a_s, a_e = sol["a_start"], sol["a_end"]
        b_s, b_e = sol["b_start"], sol["b_end"]
        assert a_e <= b_s or b_e <= a_s

    def test_unary_resource(self):
        sched = SchedulingModel(horizon=20)
        a = sched.add_task("a", duration=3)
        b = sched.add_task("b", duration=3)
        sched.add_unary_resource("machine", [a, b])
        assert sched.num_resources == 1
        sol = sched.solve()
        assert sol is not None

    def test_cumulative_resource(self):
        sched = SchedulingModel(horizon=20)
        a = sched.add_task("a", duration=3, resource_demand=2)
        b = sched.add_task("b", duration=3, resource_demand=2)
        sched.add_cumulative_resource("cpu", [a, b], capacity=2)
        sol = sched.solve()
        assert sol is not None


class TestMakespan:
    def test_add_makespan_objective(self):
        sched = SchedulingModel(horizon=30)
        sched.add_task("a", duration=5)
        m = sched.add_makespan_objective()
        assert m.name == "makespan"

    def test_makespan_without_tasks_raises(self):
        sched = SchedulingModel(horizon=30)
        with pytest.raises(ValueError):
            sched.add_makespan_objective()


class TestCriticalPathAndSummary:
    def test_critical_path(self):
        sched = SchedulingModel(horizon=30)
        a = sched.add_task("a", duration=3)
        b = sched.add_task("b", duration=4)
        c = sched.add_task("c", duration=2)
        sched.add_precedence(a, b)
        sched.add_precedence(b, c)
        critical = sched.compute_critical_path()
        assert len(critical) >= 1

    def test_schedule_summary(self):
        sched = SchedulingModel(horizon=20)
        sched.add_task("a", duration=3)
        sol = sched.solve()
        summary = sched.get_schedule_summary(sol)
        assert "Schedule" in summary
        assert "a" in summary
