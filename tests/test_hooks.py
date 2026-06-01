"""Tests for the solver hook system."""

from modelmesh.core.variable import Variable
from modelmesh.core.constraint import BinaryConstraint
from modelmesh.middleware.hooks import SolverHook, HookManager


class RecordingHook(SolverHook):
    def __init__(self):
        self.events = []

    def on_decision(self, var, value, depth):
        self.events.append(("decision", var.name, value, depth))

    def on_backtrack(self, var, depth):
        self.events.append(("backtrack", var.name, depth))

    def on_propagation(self, pruned_count, depth):
        self.events.append(("propagation", pruned_count, depth))

    def on_wipeout(self, var, constraint, depth):
        self.events.append(("wipeout", var.name, depth))

    def on_solution(self, assignment):
        self.events.append(("solution", len(assignment)))

    def on_restart(self, restart_number, nodes_explored):
        self.events.append(("restart", restart_number))

    def on_start(self, num_variables, num_constraints):
        self.events.append(("start", num_variables, num_constraints))

    def on_finish(self, solved, nodes):
        self.events.append(("finish", solved))


def _var(name="x"):
    return Variable(name, [1, 2, 3])


class TestHookManager:
    def test_register_and_count(self):
        m = HookManager()
        h = RecordingHook()
        m.register(h)
        assert m.num_hooks == 1

    def test_unregister(self):
        m = HookManager()
        h = RecordingHook()
        m.register(h)
        m.unregister(h)
        assert m.num_hooks == 0

    def test_clear(self):
        m = HookManager()
        m.register(RecordingHook())
        m.register(RecordingHook())
        m.clear()
        assert m.num_hooks == 0

    def test_fire_all_events(self):
        m = HookManager()
        h = RecordingHook()
        m.register(h)
        v = _var()
        c = BinaryConstraint(v, v, lambda a, b: True)
        m.fire_start(2, 1)
        m.fire_decision(v, 1, 0)
        m.fire_propagation(3, 1)
        m.fire_backtrack(v, 0)
        m.fire_wipeout(v, c, 1)
        m.fire_solution({v: 1})
        m.fire_restart(2, 100)
        m.fire_finish(True, 50)
        kinds = [e[0] for e in h.events]
        assert kinds == [
            "start", "decision", "propagation", "backtrack",
            "wipeout", "solution", "restart", "finish",
        ]

    def test_disable_suppresses_events(self):
        m = HookManager()
        h = RecordingHook()
        m.register(h)
        m.disable()
        assert not m.enabled
        m.fire_decision(_var(), 1, 0)
        assert h.events == []
        m.enable()
        m.fire_decision(_var(), 1, 0)
        assert len(h.events) == 1

    def test_default_hook_methods_are_noops(self):
        # SolverHook base methods should not raise
        hook = SolverHook()
        v = _var()
        c = BinaryConstraint(v, v, lambda a, b: True)
        hook.on_decision(v, 1, 0)
        hook.on_backtrack(v, 0)
        hook.on_propagation(1, 0)
        hook.on_wipeout(v, c, 0)
        hook.on_solution({v: 1})
        hook.on_restart(1, 1)
        hook.on_start(1, 1)
        hook.on_finish(True, 1)
