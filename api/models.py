from dataclasses import asdict, dataclass


@dataclass
class CredentialRecord:
    business_name: str | None
    person_name: str | None
    credential_number: str | None
    credential_type: str
    credential_kind: str
    issuing_authority: str
    jurisdiction: str | None = None
    status: str | None = None
    expiration_date: str | None = None
    source_url: str | None = None
    source_record_number: str | None = None
    last_verified: str | None = None

    def dict(self):
        return asdict(self)
