# Contractor Credential Lookup — Developer Handoff

## 1. Project goal

Build a public website that lets someone search a construction contractor and see the contractor's known licenses and registrations across multiple Ohio and Franklin County-area issuing authorities.

The user should NOT have to know which government agency issued the credential before searching.

A single contractor profile may contain:

- an Ohio state OCILB license;
- a Franklin County contractor registration;
- a City of Columbus credential;
- registrations from multiple municipalities.

The most important public-facing fields are:

- Business / company name
- Contractor / registrant name
- Credential number
- Credential type
- Credential kind: LICENSE, REGISTRATION, or RECORD
- Issuing authority
- Jurisdiction
- Status
- Expiration date
- Official source link
- Last verified date

---

## 2. Important issue encountered during development

### Franklin County collector could NOT be live-tested in the coding environment

The Franklin County SmartGov collector was written using Playwright against the public Advanced Search interface.

However, the ChatGPT coding/container environment used to build this prototype does not have usable outbound internet access for executing the browser collector against the live SmartGov site.

That means:

- the collector code exists;
- the public SmartGov search interface was separately verified;
- the collector's DOM/field-discovery logic was designed to avoid hard-coded generated IDs;
- BUT the complete search -> results -> detail extraction flow has NOT been end-to-end live-tested from this coding environment.

The next developer should treat the Franklin County collector as a **working scaffold that requires immediate live testing on a normal internet-connected development machine**.

Recommended first test:

```bash
pip install -r requirements.txt
playwright install chromium
python -m sources.franklin_smartgov --discover-types --headed
```

Then test:

```bash
python -m sources.franklin_smartgov --contractor "Yoder" --headed
```

If SmartGov's current HTML differs from the assumptions in the adapter, adjust the label/field/table selectors before using it for production ingestion.

### Why Playwright was used

SmartGov is session/browser-oriented and the underlying private request format is not documented as a stable public API.

Rather than hard-code fragile hidden/session parameters, the prototype intentionally drives the public search form like a browser.

If a stable documented endpoint is later discovered, replace Playwright with the documented API.

---

## 3. Earlier source-identification mistake to avoid

An early search surfaced an Accela portal labeled `FRANKLIN`, but it was for **Franklin Park, Illinois**, not Franklin County, Ohio.

Do not use that source.

Correct Franklin County, Ohio public portal:

https://co-franklin-oh.smartgovcommunity.com/applicationpublic/applicationhome

Advanced Search:

https://co-franklin-oh.smartgovcommunity.com/ApplicationPublic/ApplicationSearchAdvanced

This mistake is documented here so a future developer does not build against the wrong jurisdiction.

---

## 4. Ohio eLicense / OCILB caveats encountered

Official state lookup:

https://elicense4.com.ohio.gov/Lookup/LicenseLookup.aspx

During development, the Ohio state site was temporarily unavailable and later became reachable again.

This means collectors should assume intermittent availability and should have:

- retries with backoff;
- cached source snapshots;
- import logs;
- a last-successful-refresh timestamp;
- no hard dependency on the site being available for every public user search.

### Roster workflow issue

Ohio provides roster generation/download capability, which is preferable to scraping individual search pages.

However, the roster process appears to be session/postback based rather than a simple permanent file URL.

Do NOT assume a static roster download URL.

Preferred production options, in order:

1. automate the official roster-generation workflow with a persistent session;
2. import manually/generated roster files if automation proves brittle;
3. use public detail pages to refresh individual known credentials.

The included `sources/ohio_ocilb.py` supports roster-file parsing and public detail-page parsing.

---

## 5. Credential terminology matters

Do not label every municipal credential as a "license."

The data model distinguishes:

- `LICENSE`
- `REGISTRATION`
- `RECORD`

Example:

```text
HV.12345
HVAC
LICENSE
Ohio Construction Industry Licensing Board (OCILB)

REG-2026-481
HVAC Contractor Registration
REGISTRATION
Franklin County, Ohio
```

This distinction is important because municipalities may require contractor registration without independently licensing the underlying trade.

---

## 6. Database model

### contractors

```text
id
business_name
normalized_business_name
person_name
normalized_person_name
created_at
updated_at
```

### credentials

```text
id
contractor_id
credential_number
credential_type
credential_kind
issuing_authority
jurisdiction
status
expiration_date
source_url
source_record_number
last_verified
created_at
updated_at
```

### review_queue

Used for ambiguous contractor matches that should not be automatically merged.

### import_log

Tracks source refreshes and import outcomes.

---

## 7. Multiple jurisdictions for one contractor

One contractor should be represented once, with all credentials nested underneath.

Example:

```text
ABC Mechanical LLC
John Smith

HV.12345
HVAC License
Ohio Construction Industry Licensing Board (OCILB)

REG-4567
HVAC Contractor Registration
Franklin County, Ohio

COL-98765
HVAC Contractor Registration
City of Columbus

REG-26-119
Mechanical Contractor Registration
City of Dublin
```

The UI can summarize this as:

```text
4 credentials across 4 issuing authorities
```

---

## 8. Deduplication policy

The prototype intentionally uses conservative matching.

### Definite / strong match

Automatically merge when:

1. same issuing authority + same credential number; or
2. exact normalized business name + exact normalized person name.

### Do not automatically merge on:

- fuzzy business-name similarity alone;
- same surname alone;
- same person name with materially different company names;
- same trade alone.

If uncertain, keep records separate or send them to `review_queue`.

False merges are worse than duplicate profiles.

---

## 9. Initial data sources

### Ohio Construction Industry Licensing Board (OCILB)

Issuing authority:

`Ohio Construction Industry Licensing Board (OCILB)`

Jurisdiction:

`State of Ohio`

Official lookup:

https://elicense4.com.ohio.gov/Lookup/LicenseLookup.aspx

State trade categories include the OCILB construction trades such as HVAC, Electrical, Plumbing, Hydronics, and Refrigeration.

Prototype:

`prototype/sources/ohio_ocilb.py`

Supported ingest concepts:

- Excel roster
- CSV/text roster
- public detail-page parsing

---

### Franklin County, Ohio

Issuing authority:

`Franklin County, Ohio`

Portal:

https://co-franklin-oh.smartgovcommunity.com/applicationpublic/applicationhome

Advanced search:

https://co-franklin-oh.smartgovcommunity.com/ApplicationPublic/ApplicationSearchAdvanced

Prototype:

`prototype/sources/franklin_smartgov.py`

Status:

**Needs live testing on an internet-connected development machine.**

---

### City of Columbus

Issuing authority:

`City of Columbus`

Public permitting/licensing portal:

https://portal.columbus.gov/

Prototype:

`prototype/sources/columbus_accela.py`

Status:

Adapter scaffold exists. Collector still needs completion and live validation.

Columbus is important because its local contractor system covers categories beyond the five OCILB state trade licenses.

---

### City of Bexley

Prototype:

`prototype/sources/bexley_pdf.py`

Bexley publishes a contractor roster that has included fields such as:

- Record #
- Applicant Name
- Company Name
- Registration Type
- Expiration Date

Important caveat:

Do NOT automatically treat Bexley's `Record #` as a license/registration credential number unless the city confirms that meaning.

Store it as `source_record_number` unless verified.

---

## 10. Other Franklin County-area authorities to add

Priority sources identified during research:

- City of Whitehall
- City of Grove City
- City of Dublin
- City of Reynoldsburg
- City of Upper Arlington
- City of New Albany
- City of Hilliard
- City of Westerville
- City of Bexley
- City of Columbus
- Franklin County
- Ohio OCILB

Municipal rules can change.

Every imported record should therefore preserve:

- issuing authority;
- jurisdiction;
- source URL;
- last verified date;
- credential kind.

---

## 11. API prototype

Backend uses FastAPI.

Current search concept:

```http
GET /search?q=<query>
```

Results group credentials under one contractor profile.

Future filters:

```text
issuing_authority
jurisdiction
credential_type
credential_kind
status
active_only
```

---

## 12. Recommended ingestion architecture

Do NOT scrape government sites live for every end-user search.

Use:

```text
official government sources
        ↓
scheduled collectors/importers
        ↓
normalized local database
        ↓
search API
        ↓
website frontend
```

Advantages:

- faster user searches;
- less traffic to government systems;
- resilience when a government site goes down;
- consistent schema across jurisdictions;
- ability to show `last_verified`.

---

## 13. Reliability requirements

Because the state site was observed temporarily unavailable and municipal systems can change:

Every source collector should include:

- reasonable rate limits;
- timeout handling;
- retries with exponential backoff;
- source snapshot/archive when practical;
- import logging;
- failure alerts;
- last successful refresh date;
- parser tests using saved fixture HTML/PDF files.

Do not erase the last good dataset just because a refresh fails.

---

## 14. Production work still needed

Recommended order:

1. Live-test and fix Franklin County SmartGov collector.
2. Test Ohio OCILB roster import with a current real roster.
3. Finish City of Columbus collector.
4. Add source snapshots/fixtures for automated parser tests.
5. Build status/expiration normalization.
6. Add Whitehall.
7. Add Bexley production refresh.
8. Add Grove City.
9. Add Dublin.
10. Add Reynoldsburg / Upper Arlington / New Albany.
11. Add Hilliard / Westerville.
12. Build manual duplicate-review interface.
13. Build public frontend.
14. Add scheduled refresh jobs.
15. Add monitoring and failure alerts.
16. Review each source's terms, robots rules, and reasonable access limits before large recurring collection.

---

## 15. Suggested MVP

A strong first release:

1. Ohio OCILB
2. City of Columbus
3. Franklin County
4. Bexley
5. Whitehall
6. Grove City
7. Dublin

Then expand coverage.

---

## 16. Public UX recommendation

A result should emphasize WHO issued each credential.

Example:

```text
ABC MECHANICAL LLC
John Smith
4 credentials across 3 issuing authorities

Ohio Construction Industry Licensing Board (OCILB)
HV.12345 — HVAC License
Active
Expires 09/30/2028

Franklin County, Ohio
REG-4567 — HVAC Contractor Registration
Active
Expires 12/31/2026

City of Columbus
HVC-22019 — HVAC Contractor Registration
Active
Expires 12/31/2026
```

Each credential should link back to its official source whenever possible.

---

## 17. Prototype contents

The included prototype contains:

- SQLite schema
- FastAPI API
- normalization functions
- conservative contractor deduplication
- generic CSV importer
- Bexley PDF importer
- Ohio OCILB roster/detail-page parser
- Franklin County SmartGov Playwright collector scaffold
- Columbus adapter scaffold
- sample data
- live-source setup notes

Start with:

`prototype/README.md`

and:

`prototype/LIVE_SOURCES.md`
