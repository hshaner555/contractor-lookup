from __future__ import annotations

import os

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine


def database_url() -> str:
    url = os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://contractor:contractor@localhost:5432/contractors",
    )
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


def create_database_engine() -> Engine:
    return create_engine(database_url(), pool_pre_ping=True)
