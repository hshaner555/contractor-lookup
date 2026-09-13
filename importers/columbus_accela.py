"""
City of Columbus adapter scaffold.

The public Accela portal exposes search fields for license type, first/last
name, business name, City License No. and State License No.

Accela commonly requires hidden ASP.NET form state and cookies for automated
searches. Do not hard-code brittle __VIEWSTATE values here. The production
adapter should use a requests.Session(), GET the form, preserve hidden fields,
POST the search criteria, then parse result/detail pages.

This file intentionally provides the normalized output contract while the exact
request payload is captured/verified.
"""

from __future__ import annotations

from contractor_lib.models import CredentialRecord

AUTHORITY = "City of Columbus"
JURISDICTION = "Columbus, Ohio"


def normalize_row(row: dict) -> CredentialRecord:
    return CredentialRecord(
        business_name=row.get("business_name"),
        person_name=row.get("person_name"),
        credential_number=row.get("city_license_number") or row.get("credential_number"),
        credential_type=row.get("license_type") or "Contractor",
        credential_kind=row.get("credential_kind") or "LICENSE",
        issuing_authority=AUTHORITY,
        jurisdiction=JURISDICTION,
        status=row.get("status"),
        expiration_date=row.get("expiration_date"),
        source_url=row.get("source_url"),
        last_verified=row.get("last_verified"),
    )
