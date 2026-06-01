"""Global constraints: AllDifferent, Sum, Element, Cardinality."""

from modelmesh.global_cstr.alldiff import AllDifferent
from modelmesh.global_cstr.linear import SumConstraint, ScalarProduct
from modelmesh.global_cstr.element import ElementConstraint
from modelmesh.global_cstr.cardinality import CardinalityConstraint

__all__ = [
    "AllDifferent",
    "SumConstraint",
    "ScalarProduct",
    "ElementConstraint",
    "CardinalityConstraint",
]
