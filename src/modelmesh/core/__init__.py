"""Core primitives: Variable, Domain, Constraint."""

from modelmesh.core.variable import Variable
from modelmesh.core.domain import Domain
from modelmesh.core.constraint import Constraint, BinaryConstraint, UnaryConstraint

__all__ = ["Variable", "Domain", "Constraint", "BinaryConstraint", "UnaryConstraint"]
