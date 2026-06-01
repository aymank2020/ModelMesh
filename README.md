# ModelMesh

ModelMesh is a pure-Python constraint satisfaction toolkit for small and
medium combinatorial models. It is aimed at experiments where the solver needs
to be inspectable: domains are explicit, propagation steps are visible, and the
search heuristics can be swapped without changing the model.

The project currently focuses on finite integer domains. It includes classic
arc-consistency propagation, global constraints that are useful for scheduling
and graph problems, reversible state for backtracking, and analysis utilities
for understanding why a model is hard.

## What It Solves

The repository includes small example models and integration tests for:

- 4-Queens, including diagonal conflict constraints.
- Petersen graph coloring.
- Sudoku with row, column, and box all-different constraints.
- Magic square constraints using scalar sums.
- A small job-shop scheduling model with machine capacity constraints.

These examples are intentionally small enough to run in tests, but they use the
same APIs as larger models.

## Core Features

- Finite integer domains with generation-based restore.
- Binary, unary, table, and global constraints.
- AC-3 and AC-4 propagation.
- Probe consistency for stronger pruning.
- Backtracking with MRV, dom/wdeg, LCV, and signal-based heuristics.
- Nogood recording and conflict analysis utilities.
- Global constraints: AllDifferent, Sum, ScalarProduct, Element,
  Cardinality, Cumulative, Circuit, Regular, Table, and NValue.
- Model serialization for JSON-compatible problem definitions.
- Validation, tracing, profiling, and solution counting tools.

ModelMesh has no runtime dependencies outside the Python standard library.
The development dependencies are pytest, pytest-cov, and hypothesis.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

For direct source checkout usage:

```bash
export PYTHONPATH="$PWD/src"
```

## Quick Start

```python
from modelmesh import BacktrackSolver, BinaryConstraint, Variable, AllDifferent

x = Variable("x", range(1, 10))
y = Variable("y", range(1, 10))
z = Variable("z", range(1, 10))

constraints = [
    AllDifferent(x, y, z),
    BinaryConstraint(x, y, lambda a, b: a + b > 5, name="x_plus_y_gt_5"),
]

solution = BacktrackSolver([x, y, z], constraints).solve()
print({var.name: value for var, value in solution.items()})
```

## N-Queens Example

```python
from modelmesh.core.constraint import BinaryConstraint
from modelmesh.core.variable import Variable
from modelmesh.heuristics.value_ordering import LCVOrderer
from modelmesh.heuristics.variable_ordering import DomWdegSelector
from modelmesh.solver.backtrack import BacktrackSolver

n = 4
queens = [Variable(f"q{row}", range(n)) for row in range(n)]
constraints = []

for i in range(n):
    for j in range(i + 1, n):
        offset = j - i
        constraints.append(BinaryConstraint(queens[i], queens[j], lambda a, b: a != b))
        constraints.append(
            BinaryConstraint(queens[i], queens[j], lambda a, b, d=offset: abs(a - b) != d)
        )

solver = BacktrackSolver(
    queens,
    constraints,
    var_selector=DomWdegSelector(),
    val_orderer=LCVOrderer(),
)

solution = solver.solve()
print([solution[q] for q in queens])
```

## JSON Input

The command-line runner accepts the serializer format used by
`ProblemSerializer`. The format supports variables plus named constraints such
as `AllDifferent`, `Sum`, and `Table`.

```json
{
  "version": "1.0",
  "variables": [
    {"name": "a", "domain": [1, 2, 3]},
    {"name": "b", "domain": [1, 2, 3]}
  ],
  "constraints": [
    {"type": "AllDifferent", "variables": ["a", "b"], "name": "different"}
  ]
}
```

Run it with:

```bash
modelmesh problem.json --heuristic dom_wdeg --value-order lcv
```

## Project Layout

```text
src/modelmesh/
  core/             variable, domain, assignment, registry, constraint primitives
  propagation/      AC-3, AC-4, bounds, node consistency, candidate probing
  global_cstr/      global constraints for scheduling and combinatorial models
  solver/           backtracking and forward checking
  heuristics/       variable and value ordering
  learning/         nogood and conflict-analysis utilities
  modeling/         higher-level modeling helpers
  validation/       solution and consistency checkers
  debug/            tracing, profiling, explaining, solution counting
```

## Development

```bash
pytest --cov=modelmesh --cov-report=term-missing
python -m pip wheel . --no-deps
```

The test suite covers solver behavior through unit tests and end-to-end models.
Coverage is required to stay above 80 percent.

## Current Limits

- Domains are finite integer sets.
- The JSON format covers named constraints, not arbitrary Python lambdas.
- This is an educational and experimental solver, not a replacement for a
  production CP-SAT engine.

## License

MIT
