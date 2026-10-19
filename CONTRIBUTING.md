# Contributing

## Issues

For bugs, include the command you ran, expected and actual behavior, and steps
to reproduce. Reference the relevant code lines when possible. Use
[SECURITY.md](SECURITY.md) for vulnerability reports.

## Pull Requests

Create a branch and open a pull request against `main`. Reference the issue,
describe the change, and include how you tested it. Keep changes focused and
use squash or rebase merging to maintain linear history.

## Style and Tests

Use Python 3.10 or newer, Poetry for dependencies, and Ruff for formatting and
linting. Add or update tests in `tests/` for behavior changes. Before submitting,
run:

```bash
poetry install
poetry run ruff format .
poetry run ruff check .
poetry run mypy main.py merkle_proof.py util.py
poetry run bandit -r . --exclude ./.venv
poetry run pytest
```

All checks must pass and total test coverage must remain at least 75%.
Include both `pyproject.toml` and `poetry.lock` when changing dependencies.
Do not commit credentials, private keys, virtual environments, or generated
reports.
