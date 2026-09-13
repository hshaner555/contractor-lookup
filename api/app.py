from db import connect, init_db
from fastapi import FastAPI, HTTPException, Query
from normalize import normalize_business, normalize_credential, normalize_person

app = FastAPI(title="Construction Credential Lookup", version="0.1.0")


@app.on_event("startup")
def startup():
    init_db()


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/search")
def search(
    q: str = Query(..., min_length=2),
    authority: str | None = None,
    credential_type: str | None = None,
    limit: int = Query(25, ge=1, le=100),
):
    nq_business = normalize_business(q)
    nq_person = normalize_person(q)
    nq_cred = normalize_credential(q)

    sql = """
    SELECT
      cr.id AS contractor_id,
      cr.business_name,
      cr.person_name,
      c.id AS credential_id,
      c.credential_number,
      c.credential_type,
      c.credential_kind,
      c.issuing_authority,
      c.jurisdiction,
      c.status,
      c.expiration_date,
      c.source_url,
      c.last_verified
    FROM contractors cr
    JOIN credentials c ON c.contractor_id=cr.id
    WHERE (
      cr.normalized_business_name LIKE ?
      OR cr.normalized_person_name LIKE ?
      OR REPLACE(REPLACE(REPLACE(UPPER(COALESCE(c.credential_number,'')),'.',''),'-',''),' ','') LIKE ?
    )
    """
    params = [f"%{nq_business}%", f"%{nq_person}%", f"%{nq_cred}%"]

    if authority:
        sql += " AND c.issuing_authority = ?"
        params.append(authority)
    if credential_type:
        sql += " AND c.credential_type LIKE ?"
        params.append(f"%{credential_type}%")

    sql += " ORDER BY cr.business_name, cr.person_name, c.issuing_authority, c.credential_type LIMIT ?"
    params.append(limit * 10)

    with connect() as conn:
        rows = conn.execute(sql, params).fetchall()

    grouped = {}
    for r in rows:
        cid = r["contractor_id"]
        if cid not in grouped:
            grouped[cid] = {
                "contractor_id": cid,
                "business_name": r["business_name"],
                "person_name": r["person_name"],
                "credential_count": 0,
                "authority_count": 0,
                "credentials": [],
            }
        grouped[cid]["credentials"].append(
            {
                "credential_number": r["credential_number"],
                "credential_type": r["credential_type"],
                "credential_kind": r["credential_kind"],
                "issuing_authority": r["issuing_authority"],
                "jurisdiction": r["jurisdiction"],
                "status": r["status"],
                "expiration_date": r["expiration_date"],
                "source_url": r["source_url"],
                "last_verified": r["last_verified"],
            }
        )

    results = list(grouped.values())[:limit]
    for item in results:
        item["credential_count"] = len(item["credentials"])
        item["authority_count"] = len(
            {x["issuing_authority"] for x in item["credentials"]}
        )
    return {"query": q, "count": len(results), "results": results}


@app.get("/contractors/{contractor_id}")
def contractor(contractor_id: int):
    with connect() as conn:
        cr = conn.execute(
            "SELECT * FROM contractors WHERE id=?", (contractor_id,)
        ).fetchone()
        if not cr:
            raise HTTPException(404, "Contractor not found")
        creds = conn.execute(
            "SELECT * FROM credentials WHERE contractor_id=? ORDER BY issuing_authority, credential_type",
            (contractor_id,),
        ).fetchall()
    return {
        "contractor_id": cr["id"],
        "business_name": cr["business_name"],
        "person_name": cr["person_name"],
        "credentials": [dict(x) for x in creds],
    }
