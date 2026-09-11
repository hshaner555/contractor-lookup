# Live-source collectors

## Ohio OCILB

Preferred workflow:

1. Generate an OCILB roster on the official Ohio eLicense site.
2. Download Excel or text.
3. Import it:

```python
from db import init_db
from sources.ohio_ocilb import ingest_roster_file

init_db()
print(ingest_roster_file("OCILB-roster.xlsx"))
```

The parser accepts `.xlsx`, `.csv`, and tab-delimited `.txt`.

For a known public detail record, the collector can refresh directly:

```python
from sources.ohio_ocilb import ingest_detail

print(ingest_detail(contact=29947, cred=25773))
```

A single public detail page may yield multiple credentials for the same
contractor (for example HVAC + Hydronics). They are stored separately but
deduplicated onto the same contractor profile.

## Franklin County SmartGov

Install the Playwright browser once:

```bash
playwright install chromium
```

Discover the County's current Type list dynamically:

```bash
python -m sources.franklin_smartgov --discover-types
```

Search a type:

```bash
python -m sources.franklin_smartgov --type HVAC
```

Search by contractor:

```bash
python -m sources.franklin_smartgov --contractor "Yoder"
```

Use `--headed` during development to watch SmartGov in a real browser.

### Important

The Franklin collector intentionally uses the public browser form rather than
an undocumented private endpoint. Keep delays/rate limits conservative, cache
results, and review the issuing authority's terms/robots policy before running
large recurring crawls.
