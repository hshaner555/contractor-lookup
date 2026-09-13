# Known Issues / Validation Checklist

## Critical

### 1. Franklin County SmartGov collector is not end-to-end validated

Reason:
The original build environment could not execute live outbound browser requests.

Action:
Run it on a normal internet-connected computer and validate:
- Type discovery
- Primary Contractor field
- Search button
- pagination
- result-table parsing
- detail-page parsing
- registration number meaning
- status / expiration fields

Do not schedule production crawling until this is validated.

---

### 2. Wrong "Franklin" Accela portal appeared during early research

The portal was Franklin Park, Illinois.

Do not use it.

Correct Ohio source:
https://co-franklin-oh.smartgovcommunity.com/

---

### 3. Ohio eLicense availability can be intermittent

The site was unavailable during part of development and later recovered.

Action:
- retry/backoff
- retain previous successful data
- log refresh failures
- never make the public website depend on a live state request

---

### 4. Ohio roster generation is session/postback based

Do not assume a permanent static roster URL.

Action:
Either automate the complete browser/session workflow or ingest the generated file after download.

---

## Data-quality cautions

### Bexley "Record #"

Not yet proven to be the actual contractor registration/license number.

Store as:
`source_record_number`

until verified.

### Municipality terminology

Never convert "registration" into "license" just for UI consistency.

### Contractor merging

Do not use fuzzy company-name matching alone for automatic merges.

### Status normalization

Different authorities may use:
- Active
- Current
- Issued
- Expired
- Inactive
- Suspended
- Revoked
- Pending

Preserve raw status and optionally add a normalized status later.

---

## Recommended first live validation

1. Franklin SmartGov
2. Ohio roster import
3. Columbus
4. Bexley refresh

Only after those are stable should scheduled automated refreshes be enabled.
