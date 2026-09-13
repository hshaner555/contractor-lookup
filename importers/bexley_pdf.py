"""
City of Bexley roster adapter.

Bexley publishes a registered-contractor roster as a PDF. The PDF table has
historically included Registration Type, Company Name, Applicant Name and
Expiration Date (plus contact fields we intentionally discard).

This importer accepts a LOCAL PDF path so the ingestion job can download the
official file first, archive it, and then parse it deterministically.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pdfplumber
from contractor_importers.persistence import upsert_record
from contractor_lib.models import CredentialRecord

AUTHORITY = "City of Bexley"
JURISDICTION = "Bexley, Ohio"

HEADER_ALIASES = {
    "registration type": "credential_type",
    "company name": "business_name",
    "applicant name": "person_name",
    "expiration date": "expiration_date",
    "record #": "source_record_number",
    "record number": "source_record_number",
}


def _normalize_header(v):
    return " ".join((v or "").replace("\n", " ").lower().split())


def parse_pdf(pdf_path: str, source_url: str | None = None):
    records = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            for table in page.extract_tables() or []:
                if not table:
                    continue
                headers = [_normalize_header(x) for x in table[0]]
                mapped = [HEADER_ALIASES.get(h) for h in headers]
                if "credential_type" not in mapped or "business_name" not in mapped:
                    continue
                for row in table[1:]:
                    data = {}
                    for key, value in zip(mapped, row):
                        if key:
                            data[key] = " ".join((value or "").replace("\n", " ").split()) or None
                    if not data.get("business_name"):
                        continue
                    records.append(
                        CredentialRecord(
                            business_name=data.get("business_name"),
                            person_name=data.get("person_name"),
                            credential_number=None,
                            source_record_number=data.get("source_record_number"),
                            credential_type=data.get("credential_type") or "Contractor",
                            credential_kind="REGISTRATION",
                            issuing_authority=AUTHORITY,
                            jurisdiction=JURISDICTION,
                            expiration_date=data.get("expiration_date"),
                            source_url=source_url,
                            last_verified=datetime.now(timezone.utc).date().isoformat(),
                        )
                    )
    return records


def ingest_pdf(pdf_path: str, source_url: str | None = None):
    out = {"inserted": 0, "updated": 0, "records": 0}
    for rec in parse_pdf(pdf_path, source_url):
        out["records"] += 1
        result = upsert_record(rec)
        out[result["action"]] += 1
    return out
