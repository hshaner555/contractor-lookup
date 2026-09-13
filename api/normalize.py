import re
import unicodedata

BUSINESS_SUFFIXES = {
    "llc",
    "l l c",
    "inc",
    "incorporated",
    "corp",
    "corporation",
    "co",
    "company",
    "ltd",
    "limited",
    "lp",
    "llp",
}


def _clean(value: str | None) -> str:
    if not value:
        return ""
    value = unicodedata.normalize("NFKD", value)
    value = value.encode("ascii", "ignore").decode("ascii")
    value = value.lower()
    value = value.replace("&", " and ")
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def normalize_person(value: str | None) -> str:
    return _clean(value)


def normalize_business(value: str | None) -> str:
    parts = _clean(value).split()
    while parts and " ".join(parts[-3:]) in BUSINESS_SUFFIXES:
        parts = parts[:-3]
    while parts and " ".join(parts[-2:]) in BUSINESS_SUFFIXES:
        parts = parts[:-2]
    while parts and parts[-1] in BUSINESS_SUFFIXES:
        parts = parts[:-1]
    return " ".join(parts)


def normalize_credential(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"[^A-Z0-9]", "", value.upper())
