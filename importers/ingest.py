from datetime import datetime, timezone

from db import connect
from models import CredentialRecord
from normalize import normalize_business, normalize_credential, normalize_person


def _find_existing_credential(conn, rec: CredentialRecord):
    num = normalize_credential(rec.credential_number)
    if not num:
        return None
    rows = conn.execute(
        "SELECT c.*, cr.id AS contractor_id "
        "FROM credentials c JOIN contractors cr ON cr.id=c.contractor_id "
        "WHERE c.issuing_authority=?",
        (rec.issuing_authority,),
    ).fetchall()
    for row in rows:
        if normalize_credential(row["credential_number"]) == num:
            return row
    return None


def _find_contractor(conn, rec: CredentialRecord):
    nb = normalize_business(rec.business_name)
    np = normalize_person(rec.person_name)

    # Strong, safe match: exact normalized company AND exact normalized person.
    if nb and np:
        row = conn.execute(
            """SELECT * FROM contractors
               WHERE normalized_business_name=? AND normalized_person_name=?
               LIMIT 1""",
            (nb, np),
        ).fetchone()
        if row:
            return row, "business+person"

    # If there is no person in either source, an exact company match is usable
    # only when it identifies exactly one existing contractor.
    if nb and not np:
        rows = conn.execute(
            "SELECT * FROM contractors WHERE normalized_business_name=?", (nb,)
        ).fetchall()
        if len(rows) == 1 and not rows[0]["normalized_person_name"]:
            return rows[0], "business-only-safe"

    return None, None


def upsert_record(rec: CredentialRecord):
    if rec.credential_kind not in {"LICENSE", "REGISTRATION", "RECORD"}:
        raise ValueError("credential_kind must be LICENSE, REGISTRATION, or RECORD")

    with connect() as conn:
        existing = _find_existing_credential(conn, rec)
        if existing:
            conn.execute(
                """UPDATE credentials SET
                   credential_type=?, credential_kind=?, jurisdiction=?, status=?,
                   expiration_date=?, source_url=?, source_record_number=?,
                   last_verified=?, updated_at=CURRENT_TIMESTAMP
                   WHERE id=?""",
                (
                    rec.credential_type,
                    rec.credential_kind,
                    rec.jurisdiction,
                    rec.status,
                    rec.expiration_date,
                    rec.source_url,
                    rec.source_record_number,
                    rec.last_verified,
                    existing["id"],
                ),
            )
            return {
                "action": "updated",
                "contractor_id": existing["contractor_id"],
                "credential_id": existing["id"],
            }

        contractor, reason = _find_contractor(conn, rec)
        if contractor is None:
            cur = conn.execute(
                """INSERT INTO contractors
                   (business_name, normalized_business_name, person_name, normalized_person_name)
                   VALUES (?, ?, ?, ?)""",
                (
                    rec.business_name,
                    normalize_business(rec.business_name),
                    rec.person_name,
                    normalize_person(rec.person_name),
                ),
            )
            contractor_id = cur.lastrowid
            match_reason = "new"
        else:
            contractor_id = contractor["id"]
            match_reason = reason

        cur = conn.execute(
            """INSERT INTO credentials
               (contractor_id, credential_number, credential_type, credential_kind,
                issuing_authority, jurisdiction, status, expiration_date,
                source_url, source_record_number, last_verified)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                contractor_id,
                rec.credential_number,
                rec.credential_type,
                rec.credential_kind,
                rec.issuing_authority,
                rec.jurisdiction,
                rec.status,
                rec.expiration_date,
                rec.source_url,
                rec.source_record_number,
                rec.last_verified or datetime.now(timezone.utc).date().isoformat(),
            ),
        )
        return {
            "action": "inserted",
            "contractor_id": contractor_id,
            "credential_id": cur.lastrowid,
            "match_reason": match_reason,
        }
