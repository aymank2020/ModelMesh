"""Tests for the search tree tracer."""

from modelmesh.core.variable import Variable
from modelmesh.debug.tracer import SearchTracer, TraceEvent, EventType


def _var(name="x"):
    return Variable(name, [1, 2, 3])


class TestSearchTracerBasics:
    def test_starts_empty(self):
        t = SearchTracer()
        assert t.num_events == 0
        assert t.enabled

    def test_enable_disable(self):
        t = SearchTracer()
        t.disable()
        assert not t.enabled
        t.record_decision(_var(), 1, 0)
        assert t.num_events == 0  # disabled → nothing recorded
        t.enable()
        t.record_decision(_var(), 1, 0)
        assert t.num_events == 1

    def test_clear(self):
        t = SearchTracer()
        t.record_decision(_var(), 1, 0)
        t.clear()
        assert t.num_events == 0


class TestEventRecording:
    def test_record_all_event_types(self):
        t = SearchTracer()
        v = _var()
        t.record_decision(v, 1, 0)
        t.record_propagation(v, 2, 1)
        t.record_backtrack(v, 1)
        t.record_wipeout(v, 2)
        t.record_solution(3)
        summary = t.summary()
        assert summary[EventType.DECISION.value] == 1
        assert summary[EventType.PROPAGATION.value] == 1
        assert summary[EventType.BACKTRACK.value] == 1
        assert summary[EventType.WIPEOUT.value] == 1
        assert summary[EventType.SOLUTION.value] == 1

    def test_max_events_cap(self):
        t = SearchTracer(max_events=3)
        v = _var()
        for i in range(10):
            t.record_decision(v, i, i)
        assert t.num_events == 3

    def test_decisions_at_depth(self):
        t = SearchTracer()
        a, b = _var("a"), _var("b")
        t.record_decision(a, 1, 0)
        t.record_decision(b, 2, 1)
        d0 = t.decisions_at_depth(0)
        assert len(d0) == 1
        assert d0[0].variable == "a"

    def test_max_depth_reached(self):
        t = SearchTracer()
        v = _var()
        t.record_decision(v, 1, 0)
        t.record_decision(v, 2, 5)
        assert t.max_depth_reached() == 5

    def test_max_depth_empty(self):
        assert SearchTracer().max_depth_reached() == 0

    def test_backtrack_ratio(self):
        t = SearchTracer()
        v = _var()
        t.record_decision(v, 1, 0)
        t.record_decision(v, 2, 1)
        t.record_backtrack(v, 1)
        assert t.backtrack_ratio() == 0.5

    def test_backtrack_ratio_no_decisions(self):
        assert SearchTracer().backtrack_ratio() == 0.0


class TestTraceEvent:
    def test_fields(self):
        e = TraceEvent(event_type=EventType.DECISION, depth=2, variable="x", value=5)
        assert e.event_type == EventType.DECISION
        assert e.depth == 2
        assert e.variable == "x"
        assert e.value == 5
