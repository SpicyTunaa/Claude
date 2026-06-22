import csv
from datetime import datetime
from pathlib import Path

from domain_hunter.models import HuntResult

FIELDNAMES = [
    "domain", "root_domain", "is_subdomain", "sources", "confidence_score",
    "is_live", "status_code", "final_url", "discovered_at",
]


def to_csv(result: HuntResult, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    seed = result.seed_domain.replace(".", "_")
    vert = result.vertical.replace(" ", "_")
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    path = output_dir / f"{seed}_{vert}_{ts}.csv"

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for r in sorted(result.records, key=lambda x: (-x.confidence_score, x.domain)):
            writer.writerow({
                "domain": r.domain,
                "root_domain": r.root_domain,
                "is_subdomain": r.is_subdomain,
                "sources": "|".join(sorted(r.sources)),
                "confidence_score": r.confidence_score,
                "is_live": r.is_live,
                "status_code": r.status_code,
                "final_url": r.final_url or "",
                "discovered_at": r.discovered_at.isoformat(),
            })
    return path
