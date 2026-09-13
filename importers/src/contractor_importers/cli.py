from __future__ import annotations

import argparse
import json

from contractor_importers.csv_importer import import_csv


def csv_main() -> None:
    parser = argparse.ArgumentParser(description="Import normalized contractor records from CSV")
    parser.add_argument("csv_file")
    args = parser.parse_args()
    print(json.dumps(import_csv(args.csv_file)))


def _unimplemented(name: str) -> None:
    raise SystemExit(f"{name} importer is not yet connected to its source adapter")


def bexley_main() -> None:
    _unimplemented("Bexley")


def columbus_main() -> None:
    _unimplemented("Columbus")


def franklin_main() -> None:
    _unimplemented("Franklin")


def ohio_main() -> None:
    _unimplemented("Ohio")
