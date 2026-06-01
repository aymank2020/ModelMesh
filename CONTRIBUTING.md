# Contributing to ModelMesh

## Development Setup

```bash
git clone <repo-url>
cd ModelMesh
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Running Tests

```bash
pytest
pytest --cov=modelmesh
```

## Code Style

- Type hints on all public functions
- Docstrings in Google style
- No external dependencies in core modules

## Pull Requests

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request
