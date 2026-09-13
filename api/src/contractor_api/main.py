from __future__ import annotations

from typing import Any

from contractor_lib.database import create_database_engine
from contractor_lib.normalize import normalize_business, normalize_credential, normalize_person
from fastapi import FastAPI, HTTPException, Query
from sqlalchemy import text

app = FastAPI(title="Construction Credential Lookup", version="0.1.0")
engine = create_database_engine()


@app.get("/health")
def health() -> dict[str, bool]:
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return {"ok": True}


@app.get("/search")
def search(
    q: str = Query(..., min_length=2),
    authority: str | None = None,
    credential_type: str | None = None,
    limit: int = Query(25, ge=1, le=100),
) -> dict[str, object]:
    params: dict[str, object] = {
        "business": f"%{normalize_business(q)}%",
        "person": f"%{normalize_person(q)}%",
        "credential": f"%{normalize_credential(q)}%",
        "limit": limit * 10,
    }
    filters = [
        "cr.normalized_business_name LIKE :business",
        "cr.normalized_person_name LIKE :person",
        "REPLACE(REPLACE(REPLACE(UPPER(COALESCE(c.credential_number, '')), "
        "'.', ''), '-', ''), ' ', '') LIKE :credential",
    ]
    if authority:
        filters.append("c.issuing_authority = :authority")
        params["authority"] = authority
    if credential_type:
        filters.append("c.credential_type LIKE :credential_type")
        params["credential_type"] = f"%{credential_type}%"

    query = text(f"""
        SELECT cr.id AS contractor_id, cr.business_name, cr.person_name,
               c.credential_number, c.credential_type, c.credential_kind,
               c.issuing_authority, c.jurisdiction, c.status,
               c.expiration_date, c.source_url, c.last_verified
        FROM contractors cr
        JOIN credentials c ON c.contractor_id = cr.id
        WHERE ({" OR ".join(filters)})
        ORDER BY cr.business_name, cr.person_name, c.issuing_authority, c.credential_type
        LIMIT :limit
    """)
    with engine.connect() as connection:
        rows = connection.execute(query, params).mappings().all()

    grouped: dict[int, dict[str, Any]] = {}
    for row in rows:
        contractor_id = row["contractor_id"]
        item = grouped.setdefault(
            contractor_id,
            {
                "contractor_id": contractor_id,
                "business_name": row["business_name"],
                "person_name": row["person_name"],
                "credentials": [],
            },
        )
        item["credentials"].append(dict(row))

    results = list(grouped.values())[:limit]
    for item in results:
        credentials = item["credentials"]
        item["credential_count"] = len(credentials)
        item["authority_count"] = len({credential["issuing_authority"] for credential in credentials})
    return {"query": q, "count": len(results), "results": results}


@app.get("/contractors/{contractor_id}")
def contractor(contractor_id: int) -> dict[str, object]:
    with engine.connect() as connection:
        row = (
            connection.execute(text("SELECT * FROM contractors WHERE id = :id"), {"id": contractor_id})
            .mappings()
            .first()
        )
        if row is None:
            raise HTTPException(404, "Contractor not found")
        credentials = (
            connection.execute(
                text("""
                SELECT * FROM credentials
                WHERE contractor_id = :id
                ORDER BY issuing_authority, credential_type
            """),
                {"id": contractor_id},
            )
            .mappings()
            .all()
        )
    return {
        "contractor_id": row["id"],
        "business_name": row["business_name"],
        "person_name": row["person_name"],
        "credentials": [dict(item) for item in credentials],
    }
