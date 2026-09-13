from __future__ import annotations

import os

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine


def database_url() -> str:
    return os.environ.get(
        "DATABASE_URL",
        "mysql+pymysql://contractor:contractor@localhost:3306/contractors",
    )


def create_database_engine() -> Engine:
    return create_engine(database_url(), pool_pre_ping=True)
