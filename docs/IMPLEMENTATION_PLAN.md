# Implementation Plan

This plan describes the target structure and delivery sequence for the contractor lookup monorepo.

## Target Architecture

```text
api/
  src/contractor_api/       FastAPI application and HTTP routes
importers/
  src/contractor_importers/ Independent source import commands
lib/
  src/contractor_lib/       Shared models, normalization, database, repositories
db/
  Dockerfile                MySQL image definition
  init.sql                  Initial schema
compose.yaml                db, api, and importer services
tests/                      Cross-package unit and integration tests
```

The dependency direction is one-way:

```text
api/        -> lib/
importers/  -> lib/
db/         -> MySQL schema only
```

The API and importers must not import each other. Database access belongs in `lib/`; schema definitions belong in `db/`.

## Current Baseline

The repository currently contains:

- A uv workspace with `api/`, `importers/`, and `lib/` packages.
- A FastAPI application at `api/src/contractor_api/main.py`.
- Shared models, normalization, SQLAlchemy engine setup, and repository logic in `lib/src/contractor_lib/`.
- A MySQL schema in `db/init.sql`.
- A CSV importer CLI and source-adapter scaffolding in `importers/`.
- Dockerfiles and a `compose.yaml` for MySQL, the API, and importer execution.
- Ruff, Pyright, pytest, and pre-commit validation.

The baseline was committed in `b15a0b5`.

## Delivery Phases

### 1. Stabilize package boundaries

- Keep all first-party imports package-qualified.
- Keep source parsing in importer adapters and persistence in `contractor_lib`.
- Add package-level README files if a directory needs more operational guidance.
- Remove obsolete SQLite modules and old import paths as replacements land.

### 2. Complete the MySQL persistence layer

- Treat `db/init.sql` as the initial schema and move to versioned migrations before production.
- Keep connection creation and repository operations in `lib/`.
- Add explicit repository functions for contractor search, contractor detail, credential upsert, import logging, and review-queue writes.
- Record import start, completion, row counts, and failures in `import_log`.
- Route ambiguous matching cases to `review_queue` instead of merging automatically.
- Add MySQL-backed integration tests using a disposable Compose database.
- Do not initialize or mutate the schema during FastAPI startup.

### 3. Finish the API contract

- Keep routes thin and call shared repositories/services.
- Define Pydantic response models for health, search results, contractor details, and credentials.
- Add API tests for:
  - health checks;
  - search by business, person, and credential number;
  - authority and credential-type filters;
  - result limits;
  - missing contractor responses.
- Export and maintain the API contract in `docs/`.

### 4. Make each importer independently runnable

- Provide one CLI command per source: Bexley, Columbus, Franklin County, and Ohio OCILB.
- Make each command support source-specific input/options, a dry-run mode, and structured summary output.
- Keep downloaded source files or snapshots available for deterministic reprocessing.
- Use retries, timeouts, and rate limits for external sources.
- Write import statistics and failures to `import_log`.
- Add fixture-based parser tests for every source.
- Live-test the Franklin County SmartGov Playwright collector on an internet-connected machine before production scheduling.

### 5. Harden containers and local development

- `db` owns MySQL data and schema initialization.
- `api` waits for the database health check and serves Uvicorn on port 8000.
- `importers` is a one-shot service invoked with `docker compose run --rm`.
- Replace development credentials with environment-injected secrets outside local Compose.
- Add persistent volume and backup guidance before production deployment.
- Verify `docker compose config`, image builds, database health, API health, and one importer run in CI or a Docker-enabled development environment.

### 6. Add frontend and administration later

- Build the public React client from the API contract.
- Add authentication and authorization before exposing administrative operations.
- Add review-queue and import-log workflows to the admin interface.
- Keep public search read-only and separate admin routes from public routes.

## Validation Checklist

Run from the repository root:

```bash
uv sync --dev
uv run ruff check .
uv run ruff format --check .
uv run pyright
uv run pytest

docker compose config
docker compose up --build -d db api
docker compose --profile importers run --rm importers
docker compose down
```

The Docker commands require a running Docker daemon and permission to access `/var/run/docker.sock`.

## Risks and Decisions

- MySQL schema changes need migrations before production; `init.sql` is suitable for initial local setup only.
- External government portals can change or become unavailable. Preserve source URLs, snapshots, retry behavior, and last-successful-import information.
- Conservative identity matching is intentional. False merges are more damaging than duplicate contractor profiles.
- The Franklin County SmartGov collector remains the highest-risk source because its browser flow has not been verified end to end in the original development environment.
- Production scheduling and deployment are still open decisions; the current Compose setup is for local development and repeatable smoke tests.
