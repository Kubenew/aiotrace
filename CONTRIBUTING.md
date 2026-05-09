# Contributing to aiotrace

Thanks for your interest! `aiotrace` solves a real pain point for Python + OpenTelemetry users. We welcome contributions of all kinds.

## Code of Conduct

Be respectful, assume good intent, and help maintain a supportive environment.

## Development Setup

```bash
git clone https://github.com/Kubenew/aiotrace
cd aiotrace
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -e ".[test,dev]"
```

We use **ruff** for linting and **pytest** for tests.

## Running Tests

```bash
pytest tests/
```

## Running Lint

```bash
ruff check src/ tests/
```

## What to Work On

- **Missing primitives**: `asyncio.Event`, `asyncio.Semaphore`, `asyncio.Condition` still need propagation support.
- **Documentation**: Examples for FastAPI, Django, or plain asyncio.
- **Performance benchmarks**: Compare overhead against no-op and contextvars alone.
- **Python 3.13 support**: Verify compatibility.

## Submitting Changes

1. Open an issue describing what you want to fix or add (unless it's trivial).
2. Fork the repo and create a branch: `git checkout -b feature/your-feature`.
3. Write tests for new functionality.
4. Run `ruff check .` and `pytest` and ensure all pass.
5. Push and open a pull request against `main`.

## Pull Request Checklist

- [ ] Code is type-annotated.
- [ ] Tests cover new behavior (including edge cases like cancellation).
- [ ] Documentation (docstrings or README) updated.
- [ ] No performance regressions (if applicable, add a microbenchmark).

## Getting Help

Open a draft PR or use the discussions tab. We're friendly!
