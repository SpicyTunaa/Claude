from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class DomainRecord:
    domain: str
    sources: set[str] = field(default_factory=set)
    root_domain: str = ""
    is_subdomain: bool = False
    confidence_score: float = 0.0
    is_live: bool | None = None
    status_code: int | None = None
    final_url: str | None = None
    discovered_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class HuntResult:
    seed_domain: str
    vertical: str
    records: list[DomainRecord]
    started_at: datetime
    finished_at: datetime | None = None
