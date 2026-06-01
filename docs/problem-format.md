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
