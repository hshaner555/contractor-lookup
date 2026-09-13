from __future__ import annotations

from contractor_lib.database import create_database_engine
from contractor_lib.models import CredentialRecord
from contractor_lib.repositories import upsert_record as _upsert_record


def upsert_record(record: CredentialRecord) -> dict[str, int | str]:
    with create_database_engine().begin() as connection:
        return _upsert_record(connection, record)
