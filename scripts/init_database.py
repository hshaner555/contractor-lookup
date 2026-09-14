from __future__ import annotations

import os
from pathlib import Path

import psycopg

SCHEMA_PATH = Path(__file__).resolve().parents[1] / "db" / "init.sql"


def main() -> None:
    database_url = os.environ["DATABASE_URL"]
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)
    database_url = database_url.replace("postgresql+psycopg://", "postgresql://", 1)

    with psycopg.connect(database_url) as connection:
        connection.execute(SCHEMA_PATH.read_text())
        connection.commit()


if __name__ == "__main__":
    main()
