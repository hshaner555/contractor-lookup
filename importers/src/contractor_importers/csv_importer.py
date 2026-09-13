from __future__ import annotations

import csv
from pathlib import Path

from contractor_lib.database import create_database_engine
from contractor_lib.models import CredentialRecord
from contractor_lib.repositories import upsert_record

EXPECTED_FIELDS = {
    "business_name",
    "person_name",
    "credential_number",
    "credential_type",
    "credential_kind",
    "issuing_authority",
    "jurisdiction",
    "status",
    "expiration_date",
    "source_url",
    "source_record_number",
    "last_verified",
}


def import_csv(path: str) -> dict[str, int]:
    counts = {"inserted": 0, "updated": 0}
    engine = create_database_engine()
    with Path(path).open(newline="", encoding="utf-8-sig") as file, engine.begin() as connection:
        for row in csv.DictReader(file):
            record = CredentialRecord(
                business_name=row.get("business_name") or None,
                person_name=row.get("person_name") or None,
                credential_number=row.get("credential_number") or None,
                credential_type=row.get("credential_type") or "Unknown",
                credential_kind=row.get("credential_kind") or "RECORD",
                issuing_authority=row.get("issuing_authority") or "Unknown",
                jurisdiction=row.get("jurisdiction") or None,
                status=row.get("status") or None,
                expiration_date=row.get("expiration_date") or None,
                source_url=row.get("source_url") or None,
                source_record_number=row.get("source_record_number") or None,
                last_verified=row.get("last_verified") or None,
            )
            result = upsert_record(connection, record)
            action = str(result["action"])
            counts[action] += 1
    return counts
