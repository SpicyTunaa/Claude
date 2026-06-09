import tldextract

from domain_hunter.models import DomainRecord

SOURCE_WEIGHTS: dict[str, float] = {
    "crtsh":        0.9,
    "hackertarget": 0.8,
    "dns_expander": 0.8,
    "github":       0.7,
    "viewdns":      0.6,
    "duckduckgo":   0.5,
    "yandex":       0.4,
    "reddit":       0.3,
}


def _compute_confidence(sources: set[str]) -> float:
    if not sources:
        return 0.0
    weights = [SOURCE_WEIGHTS.get(s, 0.3) for s in sources]
    base = max(weights)
    bonus = 0.05 * (len(sources) - 1)
    return round(min(1.0, base + bonus), 3)


def _extract_root(domain: str) -> tuple[str, bool]:
    ext = tldextract.extract(domain)
    if ext.domain and ext.suffix:
        root = f"{ext.domain}.{ext.suffix}"
    else:
        root = domain
    return root, bool(ext.subdomain)


def merge(records: list[DomainRecord]) -> list[DomainRecord]:
    seen: dict[str, DomainRecord] = {}
    for r in records:
        key = r.domain.lower().lstrip("*.").rstrip(".")
        if not key or "." not in key:
            continue
        if key in seen:
            seen[key].sources |= r.sources
        else:
            r.domain = key
            seen[key] = r

    for record in seen.values():
        record.confidence_score = _compute_confidence(record.sources)
        record.root_domain, record.is_subdomain = _extract_root(record.domain)

    return list(seen.values())
