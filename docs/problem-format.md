# Problem Format

The CLI uses the JSON format produced by `ProblemSerializer`. It is small by
design and meant for reproducible examples, fixtures, and smoke tests.

## Variables

Each variable has a name and an explicit integer domain:

```json
{
  "name": "x",
  "domain": [1, 2, 3, 4]
}
```

## Supported Constraint Records

### AllDifferent

```json
{
  "type": "AllDifferent",
  "name": "row_values",
  "variables": ["x1", "x2", "x3"]
}
```

### Sum

```json
{
  "type": "Sum",
  "name": "row_sum",
  "variables": ["x1", "x2", "x3"],
  "target": 15,
  "op": "=="
}
```

### Table

```json
{
  "type": "Table",
  "name": "allowed_pairs",
  "variables": ["x", "y"],
  "tuples": [[1, 2], [2, 3], [3, 1]]
}
```

## Complete Example

```json
{
  "version": "1.0",
  "variables": [
    {"name": "x", "domain": [1, 2, 3]},
    {"name": "y", "domain": [1, 2, 3]},
    {"name": "z", "domain": [1, 2, 3]}
  ],
  "constraints": [
    {"type": "AllDifferent", "name": "all_distinct", "variables": ["x", "y", "z"]},
    {"type": "Sum", "name": "sum_to_six", "variables": ["x", "y", "z"], "target": 6, "op": "=="}
  ]
}
```

Run:

```bash
modelmesh example.json --all
```

Unsupported constraint types and duplicate variable names raise ValueError. The CLI rejects malformed models before search and reads JSON as UTF-8. Lambda constraints must be converted to a supported table or global constraint before saving.

Legacy JSON `neq` constraints require two variables and are enforced. With `--limit`, incomplete single-solution search prints UNKNOWN; incomplete enumeration is marked explicitly. Both return exit status 2, while proven unsatisfiability returns status 1. The library exposes `solver.node_limit_reached` without changing the existing solution return types.
