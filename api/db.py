import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).with_name("contractors.db")

SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS contractors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    business_name TEXT,
    normalized_business_name TEXT,
    person_name TEXT,
    normalized_person_name TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS credentials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contractor_id INTEGER NOT NULL,
    credential_number TEXT,
    credential_type TEXT,
    credential_kind TEXT NOT NULL CHECK(credential_kind IN ('LICENSE','REGISTRATION','RECORD')),
    issuing_authority TEXT NOT NULL,
    jurisdiction TEXT,
    status TEXT,
    expiration_date TEXT,
    source_url TEXT,
    source_record_number TEXT,
    last_verified TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(contractor_id) REFERENCES contractors(id) ON DELETE CASCADE
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_credential_authority_number
ON credentials(issuing_authority, credential_number)
WHERE credential_number IS NOT NULL AND credential_number <> '';

CREATE INDEX IF NOT EXISTS idx_contractors_business
ON contractors(normalized_business_name);

CREATE INDEX IF NOT EXISTS idx_contractors_person
ON contractors(normalized_person_name);

CREATE INDEX IF NOT EXISTS idx_credentials_type
ON credentials(credential_type);

CREATE INDEX IF NOT EXISTS idx_credentials_authority
ON credentials(issuing_authority);

CREATE TABLE IF NOT EXISTS import_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_name TEXT NOT NULL,
    started_at TEXT DEFAULT CURRENT_TIMESTAMP,
    finished_at TEXT,
    rows_seen INTEGER DEFAULT 0,
    rows_inserted INTEGER DEFAULT 0,
    rows_updated INTEGER DEFAULT 0,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS review_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    incoming_json TEXT NOT NULL,
    candidate_contractor_id INTEGER,
    reason TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    resolved_at TEXT,
    resolution TEXT,
    FOREIGN KEY(candidate_contractor_id) REFERENCES contractors(id) ON DELETE SET NULL
);
"""


def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    with connect() as conn:
        conn.executescript(SCHEMA)
