import tldextract


def extract_registered_domain(url_or_domain: str) -> str | None:
    result = tldextract.extract(url_or_domain)
    if result.domain and result.suffix:
        return f"{result.domain}.{result.suffix}"
    return None


def is_valid_domain(value: str) -> bool:
    result = tldextract.extract(value)
    return bool(result.domain and result.suffix)
