from __future__ import annotations

from contractor_lib.normalize import normalize_business, normalize_credential


def test_normalize_business_removes_suffix_and_punctuation() -> None:
    assert normalize_business("Acme & Sons, LLC") == "acme and sons"


def test_normalize_credential_removes_formatting() -> None:
    assert normalize_credential("OH-12.34 A") == "OH1234A"
