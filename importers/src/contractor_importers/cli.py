from __future__ import annotations

import argparse
import asyncio
import csv
import json
from pathlib import Path
from typing import Any

from contractor_lib.models import CredentialRecord

from contractor_importers.csv_importer import import_csv
from contractor_importers.persistence import upsert_record


def csv_main() -> None:
    parser = argparse.ArgumentParser(description="Import normalized contractor records from CSV")
    parser.add_argument("csv_file")
    args = parser.parse_args()
    print(json.dumps(import_csv(args.csv_file)))


def _import_records(records: list[CredentialRecord]) -> dict[str, int]:
    counts = {"records": len(records), "inserted": 0, "updated": 0}
    for record in records:
        action = str(upsert_record(record)["action"])
        counts[action] += 1
    return counts


def _rows_from_file(path: str) -> list[dict[str, Any]]:
    source = Path(path)
    if source.suffix.lower() == ".json":
        value = json.loads(source.read_text(encoding="utf-8"))
        if not isinstance(value, list) or not all(isinstance(row, dict) for row in value):
            raise ValueError("JSON input must contain an array of objects")
        return value
    with source.open(newline="", encoding="utf-8-sig") as file:
        return list(csv.DictReader(file))


def bexley_main() -> None:
    parser = argparse.ArgumentParser(description="Import a Bexley contractor PDF")
    parser.add_argument("pdf_file")
    parser.add_argument("--source-url")
    args = parser.parse_args()
    from bexley_pdf import ingest_pdf

    print(json.dumps(ingest_pdf(args.pdf_file, args.source_url)))


def columbus_main() -> None:
    parser = argparse.ArgumentParser(description="Import normalized Columbus rows")
    parser.add_argument("input_file", help="JSON array or CSV file")
    args = parser.parse_args()
    from columbus_accela import normalize_row

    print(json.dumps(_import_records([normalize_row(row) for row in _rows_from_file(args.input_file)])))


def franklin_main() -> None:
    parser = argparse.ArgumentParser(description="Import Franklin SmartGov search results")
    parser.add_argument("--type")
    parser.add_argument("--contractor")
    parser.add_argument("--headed", action="store_true")
    args = parser.parse_args()
    from franklin_smartgov import ingest_search

    result = asyncio.run(
        ingest_search(type_text=args.type, primary_contractor=args.contractor, headless=not args.headed)
    )
    print(json.dumps(result))


def ohio_main() -> None:
    parser = argparse.ArgumentParser(description="Import an Ohio OCILB roster or detail page")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--roster")
    source.add_argument("--contact")
    parser.add_argument("--credential")
    args = parser.parse_args()
    from ohio_ocilb import ingest_detail, ingest_roster_file

    if args.roster:
        result = ingest_roster_file(args.roster)
    elif args.credential:
        result = ingest_detail(args.contact, args.credential)
    else:
        parser.error("--credential is required with --contact")
    print(json.dumps(result))
