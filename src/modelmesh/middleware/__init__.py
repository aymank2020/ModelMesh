"""Middleware: hooks, plugins, and event system for solver extensibility."""

from modelmesh.middleware.hooks import SolverHook, HookManager
from modelmesh.middleware.events import SolverEvent, EventBus

__all__ = ["SolverHook", "HookManager", "SolverEvent", "EventBus"]
