"""ModelMesh: Constraint satisfaction solver with propagation and learning."""

from modelmesh.core.variable import Variable
from modelmesh.core.domain import Domain
from modelmesh.core.constraint import Constraint, BinaryConstraint, UnaryConstraint
from modelmesh.solver.backtrack import BacktrackSolver
from modelmesh.global_cstr.alldiff import AllDifferent
from modelmesh.global_cstr.linear import SumConstraint

__version__ = "0.4.0"

__all__ = [
    "Variable",
    "Domain",
    "Constraint",
    "BinaryConstraint",
    "UnaryConstraint",
    "BacktrackSolver",
    "AllDifferent",
    "SumConstraint",
]
