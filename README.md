# contractor-lookup

The contractor lookup site

# Development

## Initial Setup

This application uses python3.12. You must create a virtualenv with:

```
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
```

You must also install the `pre-commit` hooks with `pre-commit install` after
creating the virtualenv.

## Testing / Linting / Formatting

Testing is done by running `pytest`.

Linting is done by running `pyright <tbd>` and `ruff --check . --fix`.

Formatting is done by running `ruff --format`.
