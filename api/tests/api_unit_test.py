from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from contractor_api import main


class FakeResult:
    def __init__(self, rows: list[dict] | None = None, row: dict | None = None):
        self.rows = rows or []
        self.row = row

    def mappings(self) -> "FakeResult":
        return self

    def all(self) -> list[dict]:
        return self.rows

    def first(self) -> dict | None:
        return self.row


class FakeConnection:
    def __init__(self, results: list[FakeResult]):
        self.results = iter(results)

    def execute(self, *_args, **_kwargs) -> FakeResult:
        return next(self.results)


class FakeEngine:
    def __init__(self, connections: list[FakeConnection]):
        self.connections = iter(connections)

    @contextmanager
    def connect(self) -> Iterator[FakeConnection]:
        yield next(self.connections)


def test_health_checks_database(monkeypatch) -> None:
    connection = FakeConnection([FakeResult()])
    monkeypatch.setattr(main, "engine", FakeEngine([connection]))

    assert main.health() == {"ok": True}


def test_search_groups_credentials_and_counts_authorities(monkeypatch) -> None:
    rows = [
        {
            "contractor_id": 1,
            "business_name": "Acme LLC",
            "person_name": "Jane Doe",
            "credential_number": "A-1",
            "credential_type": "HVAC",
            "credential_kind": "LICENSE",
            "issuing_authority": "Ohio",
            "jurisdiction": "Ohio",
            "status": "Active",
            "expiration_date": None,
            "source_url": None,
            "last_verified": None,
        },
        {
            "contractor_id": 1,
            "business_name": "Acme LLC",
            "person_name": "Jane Doe",
            "credential_number": "B-2",
            "credential_type": "Registration",
            "credential_kind": "REGISTRATION",
            "issuing_authority": "Columbus",
            "jurisdiction": "Ohio",
            "status": "Active",
            "expiration_date": None,
            "source_url": None,
            "last_verified": None,
        },
    ]
    monkeypatch.setattr(main, "engine", FakeEngine([FakeConnection([FakeResult(rows=rows)])]))

    response = main.search("Acme", limit=10)

    assert response["count"] == 1
    result = response["results"][0]
    assert result["credential_count"] == 2
    assert result["authority_count"] == 2


def test_contractor_raises_for_missing_id(monkeypatch) -> None:
    connection = FakeConnection([FakeResult(row=None)])
    monkeypatch.setattr(main, "engine", FakeEngine([connection]))

    try:
        main.contractor(999)
    except main.HTTPException as error:
        assert error.status_code == 404
    else:
        raise AssertionError("missing contractors must return HTTP 404")


def test_contractor_returns_credentials(monkeypatch) -> None:
    contractor_row = {"id": 4, "business_name": "Acme", "person_name": "Jane"}
    credentials = [{"id": 9, "credential_number": "A-1"}]
    connection = FakeConnection([FakeResult(row=contractor_row), FakeResult(rows=credentials)])
    monkeypatch.setattr(main, "engine", FakeEngine([connection]))

    response = main.contractor(4)

    assert response["contractor_id"] == 4
    assert response["credentials"] == credentials
