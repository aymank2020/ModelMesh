"""Public package API tests."""

import importlib


def test_modelmesh_is_importable():
    package = importlib.import_module("modelmesh")

    assert package.__name__ == "modelmesh"
    assert package.__version__ == "0.4.0"


def test_public_api_exports_core_solver_types():
    package = importlib.import_module("modelmesh")

    assert package.Variable.__name__ == "Variable"
    assert package.Domain.__name__ == "Domain"
    assert package.BacktrackSolver.__name__ == "BacktrackSolver"
    assert package.AllDifferent.__name__ == "AllDifferent"
    assert package.SumConstraint.__name__ == "SumConstraint"


def test_repeated_import_returns_same_public_types():
    public = importlib.import_module("modelmesh")
    second = importlib.import_module("modelmesh")

    assert second.Variable is public.Variable
    assert second.BacktrackSolver is public.BacktrackSolver
    assert second.AllDifferent is public.AllDifferent
