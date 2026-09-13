FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml /app/api/pyproject.toml
COPY lib/pyproject.toml /app/lib/pyproject.toml
COPY lib/src /app/lib/src
COPY api/src /app/api/src
RUN pip install --no-cache-dir fastapi uvicorn sqlalchemy "psycopg[binary]"
ENV PYTHONPATH=/app/api/src:/app/lib/src
CMD ["uvicorn", "contractor_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
