# Construction Credential Lookup — Prototype

A small backend prototype for a unified contractor lookup.

## What it solves

One contractor can hold:

- a State of Ohio OCILB license;
- a Franklin County registration;
- one or more municipal licenses/registrations.

The database stores the contractor once and stores every credential separately,
including the **issuing authority**.

## Core result shape

```json
{
  "business_name": "Example Mechanical LLC",
  "person_name": "Jordan Example",
  "credential_count": 3,
  "authority_count": 3,
  "credentials": [
    {
      "credential_number": "HV.12345",
      "credential_type": "HVAC",
      "credential_kind": "LICENSE",
      "issuing_authority": "Ohio Construction Industry Licensing Board (OCILB)"
    }
  ]
}
```

## Conservative deduplication

Automatic merge only happens when:

1. an existing credential has the same issuing authority + credential number; or
2. normalized business name **and** normalized person name are exact matches.

We intentionally do **not** merge on fuzzy company name alone.

## Run it

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
python -c "from db import init_db; init_db()"
python import_csv.py sample_import.csv
uvicorn app:app --reload
```

Then open:

- `http://127.0.0.1:8000/docs`
- `http://127.0.0.1:8000/search?q=Example`

## Source adapters

### Implemented
- `sources/bexley_pdf.py`
  - parses a locally downloaded Bexley contractor roster PDF;
  - keeps only contractor/business/registration fields;
  - ignores phone/email.

### Scaffolds
- `sources/ohio_ocilb.py`
- `sources/franklin_smartgov.py`
- `sources/columbus_accela.py`

Those sources are session-oriented web applications, so the exact search POST
and hidden-state handling should be captured and tested before relying on them
in production.

## Production additions

Recommended next pieces:

1. source snapshots + hashes so an import can be reproduced;
2. scheduled refresh jobs;
3. `review_queue` UI for ambiguous matches;
4. source-specific status/expiration normalization;
5. issuer and jurisdiction filters;
6. frontend search page;
7. rate limiting and caching;
8. automated tests;
9. terms/robots review for every source before enabling a collector.


## Live collectors

See `LIVE_SOURCES.md` for the Ohio OCILB roster/detail importer and Franklin County SmartGov browser collector.
