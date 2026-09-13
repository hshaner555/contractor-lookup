from __future__ import annotations

import json

from bexley_pdf import parse_pdf
from columbus_accela import normalize_row
from contractor_importers import cli
from contractor_lib.models import CredentialRecord
from franklin_smartgov import normalize_search_row
from ohio_ocilb import parse_roster_file


def test_columbus_normalize_row_maps_source_fields() -> None:
    record = normalize_row(
        {
            "business_name": "Acme LLC",
            "person_name": "Jane Doe",
            "city_license_number": "C-42",
            "license_type": "HVAC",
            "status": "Active",
        }
    )

    assert record.credential_number == "C-42"
    assert record.issuing_authority == "City of Columbus"


def test_rows_from_file_reads_json(tmp_path) -> None:
    source = tmp_path / "rows.json"
    source.write_text(json.dumps([{"business_name": "Acme"}]), encoding="utf-8")

    assert cli._rows_from_file(str(source)) == [{"business_name": "Acme"}]


def test_import_records_counts_actions(monkeypatch) -> None:
    monkeypatch.setattr(cli, "upsert_record", lambda _record: {"action": "inserted"})
    record = CredentialRecord(
        business_name="Acme",
        person_name=None,
        credential_number="A-1",
        credential_type="Contractor",
        credential_kind="LICENSE",
        issuing_authority="Ohio",
    )

    assert cli._import_records([record]) == {"records": 1, "inserted": 1, "updated": 0}


def test_franklin_normalize_search_row_maps_visible_fields() -> None:
    record = normalize_search_row(
        {
            "Company Name": "Acme LLC",
            "Registration Number": "F-7",
            "Status": "Active",
        },
        selected_type="HVAC",
    )

    assert record.business_name == "Acme LLC"
    assert record.credential_number == "F-7"
    assert record.credential_type == "HVAC"


def test_bexley_parse_pdf_maps_table(monkeypatch) -> None:
    class Page:
        def extract_tables(self):
            return [
                [
                    ["Registration Type", "Company Name", "Applicant Name"],
                    ["General", "Acme LLC", "Jane Doe"],
                ]
            ]

    class Pdf:
        pages = [Page()]

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

    monkeypatch.setattr("bexley_pdf.pdfplumber.open", lambda _path: Pdf())

    records = parse_pdf("roster.pdf")

    assert len(records) == 1
    assert records[0].business_name == "Acme LLC"


def test_ohio_parse_roster_file_reads_csv(tmp_path) -> None:
    source = tmp_path / "roster.csv"
    source.write_text("Credential,Name,Company\nOH-1,Jane Doe,Acme LLC\n", encoding="utf-8")

    records = parse_roster_file(str(source))

    assert records[0].credential_number == "OH-1"
    assert records[0].business_name == "Acme LLC"
