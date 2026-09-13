FROM python:3.12-slim

WORKDIR /app
COPY lib/pyproject.toml /app/lib/pyproject.toml
COPY importers/pyproject.toml /app/importers/pyproject.toml
COPY lib/src /app/lib/src
COPY importers/src /app/importers/src
RUN pip install --no-cache-dir /app/lib /app/importers
ENTRYPOINT ["contractor-import-csv"]
