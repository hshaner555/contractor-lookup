import csv
from pathlib import Path

from ingest import upsert_record
from models import CredentialRecord

EXPECTED = {
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


def import_csv(path: str):
    path = Path(path)
    inserted = updated = 0
    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            data = {k: (row.get(k) or None) for k in EXPECTED}
            rec = CredentialRecord(**data)
            result = upsert_record(rec)
            inserted += result["action"] == "inserted"
            updated += result["action"] == "updated"
    return {"inserted": inserted, "updated": updated}


if __name__ == "__main__":
    import argparse

    from db import init_db

    parser = argparse.ArgumentParser()
    parser.add_argument("csv_file")
    args = parser.parse_args()
    init_db()
    print(import_csv(args.csv_file))
