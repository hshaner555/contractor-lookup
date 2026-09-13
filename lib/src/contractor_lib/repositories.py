from __future__ import annotations

from datetime import date

from sqlalchemy import Connection, text

from contractor_lib.models import CredentialRecord
from contractor_lib.normalize import normalize_business, normalize_credential, normalize_person


def upsert_record(connection: Connection, record: CredentialRecord) -> dict[str, int | str]:
    if record.credential_kind not in {"LICENSE", "REGISTRATION", "RECORD"}:
        raise ValueError("credential_kind must be LICENSE, REGISTRATION, or RECORD")

    normalized_number = normalize_credential(record.credential_number)
    existing = None
    if normalized_number:
        existing = (
            connection.execute(
                text("""
                SELECT c.id, c.contractor_id, c.credential_number
                FROM credentials c
                WHERE c.issuing_authority = :authority
                  AND REPLACE(REPLACE(REPLACE(
                      UPPER(COALESCE(c.credential_number, '')), '.', ''), '-', ''), ' ', '') = :number
                LIMIT 1
            """),
                {"authority": record.issuing_authority, "number": normalized_number},
            )
            .mappings()
            .first()
        )

    if existing:
        connection.execute(
            text("""
                UPDATE credentials SET credential_type=:credential_type,
                    credential_kind=:credential_kind, jurisdiction=:jurisdiction,
                    status=:status, expiration_date=:expiration_date,
                    source_url=:source_url, source_record_number=:source_record_number,
                    last_verified=:last_verified, updated_at=CURRENT_TIMESTAMP
                WHERE id=:id
            """),
            {**record.as_dict(), "id": existing["id"]},
        )
        return {"action": "updated", "contractor_id": existing["contractor_id"], "credential_id": existing["id"]}

    normalized_business = normalize_business(record.business_name)
    normalized_person = normalize_person(record.person_name)
    contractor = (
        connection.execute(
            text("""
            SELECT id FROM contractors
            WHERE normalized_business_name = :business
              AND normalized_person_name = :person
            LIMIT 1
        """),
            {"business": normalized_business, "person": normalized_person},
        )
        .mappings()
        .first()
    )

    if contractor is None:
        contractor_id = connection.execute(
            text("""
                INSERT INTO contractors
                    (business_name, normalized_business_name, person_name, normalized_person_name)
                VALUES (:business_name, :normalized_business, :person_name, :normalized_person)
            """),
            {
                "business_name": record.business_name,
                "normalized_business": normalized_business,
                "person_name": record.person_name,
                "normalized_person": normalized_person,
            },
        ).lastrowid
        match_reason = "new"
    else:
        contractor_id = contractor["id"]
        match_reason = "business+person"

    result = connection.execute(
        text("""
            INSERT INTO credentials
                (contractor_id, credential_number, credential_type, credential_kind,
                 issuing_authority, jurisdiction, status, expiration_date,
                 source_url, source_record_number, last_verified)
            VALUES (:contractor_id, :credential_number, :credential_type, :credential_kind,
                    :issuing_authority, :jurisdiction, :status, :expiration_date,
                    :source_url, :source_record_number, :last_verified)
        """),
        {
            **record.as_dict(),
            "contractor_id": contractor_id,
            "last_verified": record.last_verified or date.today().isoformat(),
        },
    )
    return {
        "action": "inserted",
        "contractor_id": contractor_id,
        "credential_id": result.lastrowid,
        "match_reason": match_reason,
    }
