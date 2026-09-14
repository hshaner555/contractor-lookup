from __future__ import annotations

from contractor_lib.database import database_url
from contractor_lib.models import CredentialRecord
from contractor_lib.normalize import normalize_business, normalize_person
from contractor_lib.repositories import upsert_record


def test_credential_record_as_dict_contains_optional_fields() -> None:
    record = CredentialRecord(
        business_name="Acme LLC",
        person_name="Jane Doe",
        credential_number="A-1",
        credential_type="Contractor",
        credential_kind="LICENSE",
        issuing_authority="Ohio",
    )

    assert record.as_dict()["business_name"] == "Acme LLC"
    assert record.as_dict()["last_verified"] is None


def test_normalizers_handle_empty_and_unicode_values() -> None:
    assert normalize_business(None) == ""
    assert normalize_person("José O'Neil") == "jose o neil"


def test_database_url_uses_environment(monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql://example/db")

    assert database_url() == "postgresql+psycopg://example/db"


def test_database_url_preserves_psycopg_scheme(monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://example/db")

    assert database_url() == "postgresql+psycopg://example/db"


class FakeResult:
    def __init__(self, row=None, lastrowid=None):
        self.row = row
        self.lastrowid = lastrowid

    def mappings(self):
        return self

    def first(self):
        return self.row

    def scalar_one(self):
        return self.lastrowid


class FakeConnection:
    def __init__(self, results):
        self.results = iter(results)
        self.calls = []

    def execute(self, statement, params=None):
        self.calls.append((str(statement), params))
        return next(self.results)


def _record() -> CredentialRecord:
    return CredentialRecord(
        business_name="Acme LLC",
        person_name="Jane Doe",
        credential_number="A-1",
        credential_type="HVAC",
        credential_kind="LICENSE",
        issuing_authority="Ohio",
    )


def test_upsert_record_inserts_new_contractor_and_credential() -> None:
    connection = FakeConnection(
        [FakeResult(row=None), FakeResult(row=None), FakeResult(lastrowid=7), FakeResult(lastrowid=8)]
    )

    result = upsert_record(connection, _record())

    assert result == {"action": "inserted", "contractor_id": 7, "credential_id": 8, "match_reason": "new"}
    assert len(connection.calls) == 4


def test_upsert_record_updates_existing_credential() -> None:
    connection = FakeConnection([FakeResult(row={"id": 8, "contractor_id": 7}), FakeResult()])

    result = upsert_record(connection, _record())

    assert result == {"action": "updated", "contractor_id": 7, "credential_id": 8}


def test_upsert_record_rejects_unknown_kind() -> None:
    record = _record()
    invalid = CredentialRecord(**{**record.as_dict(), "credential_kind": "UNKNOWN"})

    try:
        upsert_record(FakeConnection([]), invalid)
    except ValueError as error:
        assert "credential_kind" in str(error)
    else:
        raise AssertionError("invalid credential kinds must fail")
