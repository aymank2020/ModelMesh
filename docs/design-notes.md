# Design Notes

ModelMesh is organized around explicit domain state rather than a black-box
solver kernel. The main design goal is to make each phase of solving visible:
domain pruning, propagation, decision selection, restoration, and validation.

## Domain State

`Domain` stores the currently available integer values and a removal log keyed by
generation. Search code calls `mark_generation()` before a speculative decision
and `restore_to()` when backtracking. This keeps rollback local to the domain
object and avoids copying every variable at every search node.

The same mechanism is used by stronger propagation routines such as candidate
probing. Probe checks temporarily restrict one variable to one value, run AC-3,
and then restore every domain to the generation that existed at the start of
that trial.

## Propagation

The default solver uses AC-3 after each decision. AC-4 is also implemented for
experiments where support tables are worth the memory cost. Bounds propagation is
kept separate because it works on interval-style reasoning for linear constraints
rather than enumerating all tuples.

Queue policies are deliberately pluggable. That makes it easy to compare FIFO
AC-3 against small-domain-first or weighted policies without changing the
constraint objects.

## Search

`BacktrackSolver` combines:

- MRV or dom/wdeg variable ordering.
- Ascending, descending, random, or least-constraining value ordering.
- Propagation after each decision.
- Domain generation restore on backtrack.

The solver returns dictionaries keyed by `Variable` so callers can retain object
identity and still print human-readable assignments from variable names.

## Global Constraints

Global constraints implement the same `Constraint` interface as binary and unary
constraints. They expose `get_supported_values()` so propagation can treat them
uniformly, while still allowing each global constraint to use specialized
internal reasoning.

The current set is biased toward practical examples: graph coloring, scheduling,
regular-language constraints, circuit constraints, and counting constraints.

## Validation

The validation modules are intentionally independent from search. They can check
a returned assignment, a partially pruned state, or a serialized model without
relying on private solver state.
