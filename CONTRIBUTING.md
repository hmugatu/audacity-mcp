# Contributing to audacity-mcp

Thank you for your interest in contributing! This is a small, focused project
and contributions of all sizes are welcome.

## Getting started

```bash
git clone https://github.com/tachyonshuggy/audacity-mcp
cd audacity-mcp
uv sync
uv run pytest   # all tests should pass before you start
```

## Making changes

- **New tools** — add a function to the appropriate file in `audacity_mcp/tools/`,
  write a test in `tests/`, then register the tool in `server.py`.
- **Bug fixes** — please include a test that would have caught the bug.
- **Keep PRs focused** — one feature or fix per pull request.

## Code style

- Standard Python (no formatter enforced, but please be consistent with the
  existing style — clear names, short functions, docstrings on public functions).
- Tests use `pytest` and `unittest.mock` only — no external test dependencies.

## Commit messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):
`feat:`, `fix:`, `docs:`, `chore:`, `test:`

## Reporting bugs

Use the [bug report template](.github/ISSUE_TEMPLATE/bug_report.md).
Please include your Audacity version and OS.
