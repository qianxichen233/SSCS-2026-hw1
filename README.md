# Rekor Monitor

A Python CLI for NYU CS-GY 9223 Software Supply Chain Security. It fetches
Rekor checkpoints, verifies artifact signatures and inclusion proofs, and checks
consistency between checkpoints.

Based on the [course template](https://github.com/stupendoussuperpowers/python-rekor-monitor-template).

## Installation

Install Python 3.10 or newer and [Poetry](https://python-poetry.org/docs/#installation),
then run:

```bash
git clone https://github.com/qianxichen233/SSCS-2026-hw1.git
cd SSCS-2026-hw1
poetry install
```

## Usage

Fetch a checkpoint and save it for a later consistency check:

```bash
poetry run python main.py -c > checkpoint.json
```

Verify an artifact signature and its log inclusion. Replace `LOG_INDEX` with
the artifact's Rekor log index:

```bash
poetry run python main.py --inclusion LOG_INDEX --artifact artifact.md
```

After the log grows, check consistency with the saved checkpoint. Replace
`TREE_ID`, `TREE_SIZE`, and `ROOT_HASH` with its `treeID`, `treeSize`, and `rootHash`:

```bash
poetry run python main.py --consistency --tree-id TREE_ID --tree-size TREE_SIZE --root-hash ROOT_HASH
```

Choose one command at a time. Use `--help` for options and `--debug` for debug output.

## Development

```bash
poetry run ruff format --check .
poetry run ruff check .
poetry run mypy main.py merkle_proof.py util.py
poetry run bandit -r . --exclude ./.venv
poetry run pytest
```

Pytest reports coverage and requires at least 75%. See
[CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines and
[SECURITY.md](SECURITY.md) to report vulnerabilities.

## License

MIT; see [LICENSE](LICENSE).
