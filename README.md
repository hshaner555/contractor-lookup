# contractor-lookup

Contractor licensing lookup with a FastAPI service, independently runnable
source importers, shared Python domain code, and a MySQL database.

## Development

This application uses Python 3.12 and uv. From the root directory, run:

```bash
uv sync --dev
```

Install the pre-commit hooks with `pre-commit install` after creating the
environment.

## Running the API

```bash
uv run --package api uvicorn contractor_api.main:app --reload
```

Set `DATABASE_URL` when running against MySQL. The default points to a local
database named `contractors`.

## Running an importer

```bash
uv run --package importers contractor-import-csv importers/sample_import.csv
```

The source-specific adapters are retained under `importers/` and are being
connected to their external-source CLIs incrementally.

## Running with Compose

```bash
docker compose up --build db api
docker compose --profile importers run --rm importers
```

The database schema is initialized from `db/init.sql`. The API waits for the
MySQL health check before starting. The importer service mounts the sample
input file and runs the CSV importer by default.

## Testing, linting, and type checking

```bash
uv run ruff check .
uv run ruff format --check .
uv run pyright
uv run pytest
```
